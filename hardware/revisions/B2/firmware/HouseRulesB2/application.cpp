#include <Arduino.h>
#include <Adafruit_TinyUSB.h>
#include <hardware/clocks.h>
#include <hardware/gpio.h>
#include <hardware/irq.h>
#include <hardware/timer.h>
#include <hardware/structs/usb.h>
#include <hardware/structs/scb.h>
#include <hardware/regs/usb.h>
#include <hardware/pll.h>
#include <hardware/spi.h>
#include <hardware/sync.h>
#include <hardware/watchdog.h>
#include <pico/time.h>
#include <cstdio>
#include "board_contract_generated.h"
#include "power_sequence.h"
#include "player.h"

#ifndef HR_ALLOW_UNCONFIGURED_DIM
#define HR_ALLOW_UNCONFIGURED_DIM 1
#endif

namespace {
using namespace hrb2;
class HardwareIO {
 public:
  void blank(bool high) {
    if (!driveAllowed_) { blankHiZ(); return; }
    gpio_put(PIN_BLANK,high);
  }
  void blankHigh() {
    driveAllowed_=true; gpio_put(PIN_BLANK,true); gpio_set_dir(PIN_BLANK,GPIO_OUT);
    if (!spiReady_) {
      spi_init(spi0,8000000); spi_set_format(spi0,8,SPI_CPOL_0,SPI_CPHA_0,SPI_MSB_FIRST);
      gpio_set_function(PIN_SIN,GPIO_FUNC_SPI); gpio_set_function(PIN_SCLK,GPIO_FUNC_SPI);
      spiReady_=true;
    }
  }
  void blankHiZ() { gpio_set_dir(PIN_BLANK,GPIO_IN); gpio_disable_pulls(PIN_BLANK); driveAllowed_=false; }
  void signalsLow() {
    spi_deinit(spi0); spiReady_=false;
    for (uint8_t pin: {PIN_SIN,PIN_SCLK,PIN_LAT}) {
      gpio_set_function(pin,GPIO_FUNC_SIO); gpio_put(pin,false); gpio_set_dir(pin,GPIO_OUT);
    }
  }
  void enable(bool enabled) { gpio_put(PIN_DRIVER_ENABLE,enabled); }
  bool shiftAndLatch(const uint16_t words[4]) {
    if (!driveAllowed_ || !spiReady_ || !gpio_get(PIN_BLANK)) return false;
    uint8_t bytes[8]; serialBytes(words,bytes);
    gpio_put(PIN_LAT,false);
    if (spi_write_blocking(spi0,bytes,sizeof bytes)!=sizeof bytes) return false;
    gpio_put(PIN_LAT,true); busy_wait_us_32(1); gpio_put(PIN_LAT,false);
    return true;
  }
  void waitUs(uint32_t us) { busy_wait_us_32(us); }
 private:
  bool driveAllowed_=false,spiReady_=false;
};

HardwareIO io;
ScanEngine<HardwareIO> scanner(kBoardLayout);
RailPower<HardwareIO> rails(io,RAIL_SETTLE_US);
CcQualifier cc;
Bc12Qualifier bc12;
HouseRulesPlayer player;
DisplayPattern pattern=DisplayPattern::Artwork;
uint32_t diagnosticFrameNumber=0;
volatile bool usbConfigured=false,usbSuspended=false,hostSeen=false;
volatile bool initialized=false;
volatile bool lowClock=false,watchdogArmed=false;
bool dimRequested=false;
uint16_t lastCc1Mv=0,lastCc2Mv=0,lastDutyUs=0;
bool lastCcGrant=false,lastBcGrant=false;
volatile alarm_id_t scanAlarm=0;
uint64_t alarmTarget=0,nextArtwork=0,nextPower=0;
uint32_t artworkRemainder=0;

void activeClock() {
  const uint32_t saved=save_and_disable_interrupts();
  if (lowClock) { set_sys_clock_48mhz(); lowClock=false; }
  restore_interrupts(saved);
}
void suspendClock() {
  const uint32_t saved=save_and_disable_interrupts();
  // Keep clk_usb/PLL_USB running for USB reset/resume; avoid dormant mode.
  if (!lowClock && usbSuspended && hostSeen) {
    clock_configure(clk_sys,CLOCKS_CLK_SYS_CTRL_SRC_VALUE_CLK_REF,0,12000000,12000000);
    pll_deinit(pll_sys); lowClock=true;
  }
  restore_interrupts(saved);
}
void suspendWait() {
  // WFI wakes on a pending enabled IRQ even with PRIMASK set. Restore the
  // complete clock masks before allowing its handler to execute.
  const uint32_t saved=save_and_disable_interrupts();
  if (usbSuspended && hostSeen) {
    const uint32_t en0=clocks_hw->sleep_en0,en1=clocks_hw->sleep_en1,scr=scb_hw->scr;
    clocks_hw->sleep_en0=0;
    clocks_hw->sleep_en1=CLOCKS_SLEEP_EN1_CLK_SYS_USBCTRL_BITS |
      CLOCKS_SLEEP_EN1_CLK_USB_USBCTRL_BITS | CLOCKS_SLEEP_EN1_CLK_SYS_TIMER_BITS |
      CLOCKS_SLEEP_EN1_CLK_SYS_WATCHDOG_BITS;
    scb_hw->scr=scr | M0PLUS_SCR_SLEEPDEEP_BITS;
    __dsb(); __wfi();
    scb_hw->scr=scr; clocks_hw->sleep_en0=en0; clocks_hw->sleep_en1=en1;
    __dsb();
  }
  restore_interrupts(saved);
}
void stopDisplay() {
  const uint32_t saved=save_and_disable_interrupts();
  if (scanAlarm>0) { cancel_alarm(scanAlarm); scanAlarm=0; }
  scanner.stop(io); rails.off();
  restore_interrupts(saved);
}
int64_t scanCallback(alarm_id_t,void *) {
  const uint64_t previous=alarmTarget;
  const uint64_t next=scanner.alarm(time_us_64(),io);
  if (!next) { scanAlarm=0; return 0; }
  alarmTarget=next;
  return -int64_t(next-previous); // Pico SDK: negative means relative to prior target.
}
void startScanner(uint64_t now) {
  if (scanner.running() || scanner.faulted()) return;
  if (scanner.start(now+10)) {
    alarmTarget=now+10;
    scanAlarm=add_alarm_at(from_us_since_boot(alarmTarget),scanCallback,nullptr,true);
    if (scanAlarm<0) scanner.failDark(io);
  }
}
void queueArtwork() {
  uint8_t frame[35];
  if (pattern==DisplayPattern::Artwork) player.frame(frame);
  else diagnosticFrame(pattern,diagnosticFrameNumber++,frame);
  EncodedFrame prepared; prepareFrame(frame,kBoardLayout,prepared);
  const uint32_t saved=save_and_disable_interrupts(); scanner.queuePrepared(prepared); restore_interrupts(saved);
}
void restartArtwork() { player.restart(); diagnosticFrameNumber=0; nextArtwork=time_us_64(); artworkRemainder=0; }
void hostSuspend() {
  usbSuspended=true;
  if (hostSeen && initialized) { stopDisplay(); watchdog_disable(); watchdogArmed=false; }
}
void hostResume() {
  activeClock(); usbSuspended=false;
  if (initialized) { watchdog_enable(250,true); watchdogArmed=true; }
}
void observeUsbBus() {
  // In pinned SDK6.3.1, a newly-added equal-priority shared handler runs first.
  // Observe hardware events before TinyUSB clears them. Its usual callbacks
  // intentionally skip suspend before the first SETUP packet; we must not.
  const uint32_t status=usb_hw->ints;
  if (status & USB_INTS_BUS_RESET_BITS) {
    hostSeen=true; usbConfigured=false; hostResume();
    if (initialized) stopDisplay();
  }
  if (status & USB_INTS_DEV_RESUME_FROM_HOST_BITS) hostResume();
  if ((status & USB_INTS_DEV_SUSPEND_BITS) && hostSeen) hostSuspend();
}
void serialCommands() {
  // Bounded servicing: USB flood cannot starve power-policy/scan-watchdog work.
  for (uint8_t n=0;n<16 && Serial.available();++n) {
    switch (char(Serial.read())) {
      case 'w':pattern=DisplayPattern::Walking;restartArtwork();break;
      case 'a':pattern=DisplayPattern::AllOn;restartArtwork();break;
      case 'c':pattern=DisplayPattern::Checkerboard;restartArtwork();break;
      case 'p':pattern=DisplayPattern::Artwork;restartArtwork();break;
      case 'r':restartArtwork();break;
      case 'd':dimRequested=true;break;
      case 'b':dimRequested=false;break;
      case 'i': {
        // Never wait for a host to drain CDC: diagnostics must not stall scanning
        // or power policy. The caller can repeat the command if the buffer is full.
        char status[64];
        const int length=std::snprintf(status,sizeof status,
          "CC=%u,%u C=%u B=%u USB=%u H=%u S=%u ON=%u\n",
          unsigned(lastCc1Mv),unsigned(lastCc2Mv),unsigned(lastCcGrant),
          unsigned(lastBcGrant),unsigned(usbConfigured),unsigned(hostSeen),
          unsigned(usbSuspended),unsigned(lastDutyUs));
        if (length>0 && size_t(length)<sizeof status && Serial.availableForWrite()>=length)
          Serial.write(reinterpret_cast<const uint8_t *>(status),size_t(length));
        break;
      }
      default:break;
    }
  }
}
} // namespace

// Core's weak variant hook runs before its USB initialization. Plus LEDs differ
// from the old standard-XIAO LED macros: GPIO11 powers WS2812; GPIO25 drives
// a green-LED N-MOS gate, LOW=off on the Plus native board.
void initVariant() {
  set_sys_clock_48mhz();
  for (uint8_t pin: {hrb2::PIN_DRIVER_ENABLE,uint8_t(11),uint8_t(12),uint8_t(24)}) {
    gpio_init(pin); gpio_put(pin,false); gpio_set_dir(pin,GPIO_OUT);
  }
  gpio_init(25); gpio_put(25,false); gpio_set_dir(25,GPIO_OUT);
  gpio_init(hrb2::PIN_BLANK); gpio_set_dir(hrb2::PIN_BLANK,GPIO_IN); gpio_disable_pulls(hrb2::PIN_BLANK);
  for (uint8_t pin: {hrb2::PIN_SIN,hrb2::PIN_SCLK,hrb2::PIN_LAT}) {
    gpio_init(pin); gpio_put(pin,false); gpio_set_dir(pin,GPIO_OUT);
  }
}

// Linker wrapping delays the core's early USB attachment until setup is safe.
// The installed Arduino core and USB library are left unchanged.
extern "C" void __wrap_TinyUSB_Device_Init(uint8_t) { }
extern "C" void tud_mount_cb() { hostSeen=true; usbConfigured=true; usbSuspended=false; }
extern "C" void tud_umount_cb() { usbConfigured=false; if (initialized) stopDisplay(); }
extern "C" void tud_suspend_cb(bool) {
  if (tud_connected()) hostSeen=true;
  hostSuspend();
}
extern "C" void tud_resume_cb() {
  hostResume();
}

void setup() {
  // Preempt the default-priority USB task so CDC traffic cannot stretch dim pulses.
  irq_set_priority(hardware_alarm_get_irq_num(alarm_pool_hardware_alarm_num(alarm_pool_get_default())),0x40);
  analogReadResolution(12);
  gpio_init(hrb2::PIN_CC1_ADC); gpio_init(hrb2::PIN_CC2_ADC);
  for (uint8_t pin: {hrb2::PIN_BC_DET,hrb2::PIN_BC_AL_N}) {
    gpio_init(pin); gpio_set_dir(pin,GPIO_IN); gpio_disable_pulls(pin);
  }
  io.signalsLow(); io.blankHiZ();
  const uint32_t saved=save_and_disable_interrupts();
  TinyUSBDevice.begin(0);
  // Add after TinyUSB so equal highest order inserts before its DCD handler.
  irq_add_shared_handler(USBCTRL_IRQ,observeUsbBus,PICO_SHARED_IRQ_HANDLER_HIGHEST_ORDER_PRIORITY);
  // No descriptor request can be served before this critical section completes.
  TinyUSBDevice.setConfigurationAttribute(0x80); // Bus-powered; no remote-wakeup claim.
  const bool descriptorOk=TinyUSBDevice.setConfigurationMaxPower(500);
  restore_interrupts(saved);
  Serial.begin(115200); // CDC, data diagnostics and the core's 1200-baud UF2 reset.
  if (!descriptorOk) scanner.failDark(io);
  initialized=true; restartArtwork(); watchdog_enable(250,true); watchdogArmed=true;
}

void loop() {
  if (tud_connected()) hostSeen=true;
  const bool suspended=usbSuspended && hostSeen;
  if (suspended) {
    stopDisplay(); watchdog_disable(); watchdogArmed=false; suspendClock(); suspendWait(); return;
  }
  activeClock();
  if (!watchdogArmed) { watchdog_enable(250,true); watchdogArmed=true; }
  watchdog_update();
  const uint64_t now=time_us_64();
  if (now>=nextPower) {
    nextPower=now+10000;
    {
      const uint32_t saved=save_and_disable_interrupts();
      // Also catch a lost timer callback while the foreground/USB still runs.
      if (scanner.running() && now>=scanner.deadline()+kPhaseUs) {
        if (scanAlarm>0) { cancel_alarm(scanAlarm); scanAlarm=0; }
        scanner.failDark(io); rails.off();
      }
      restore_interrupts(saved);
    }
    // 47k/47k divider: estimate raw CC millivolts from its half-voltage ADC node.
    const uint16_t a=uint16_t((uint32_t(analogRead(hrb2::PIN_CC1_ADC))*6600U)/4095U);
    const uint16_t b=uint16_t((uint32_t(analogRead(hrb2::PIN_CC2_ADC))*6600U)/4095U);
    const bool ccHigh=cc.update(uint32_t(now/1000),a,b);
    const bool bcHigh=bc12.update(uint32_t(now/1000),gpio_get(PIN_BC_DET),
      gpio_get(PIN_BC_AL_N))!=Bc12Qualifier::Grant::Unknown;
    uint16_t duty=allowedOnUs(usbConfigured,suspended,hostSeen,ccHigh,
      HR_ALLOW_UNCONFIGURED_DIM!=0,bcHigh);
    if (dimRequested && duty>kDimOnUs) duty=kDimOnUs;
    lastCc1Mv=a; lastCc2Mv=b; lastCcGrant=ccHigh; lastBcGrant=bcHigh; lastDutyUs=duty;
    const uint32_t saved=save_and_disable_interrupts();
    scanner.setDuty(duty);
    if (scanner.faulted() || rails.faulted() || !duty) { scanner.stop(io); rails.off(); }
    else {
      rails.begin(now);
      if (rails.poll(now)) startScanner(time_us_64());
    }
    restore_interrupts(saved);
  }
  if (now>=nextArtwork) {
    queueArtwork();
    // Exact rational 60 fps independent of the 400 Hz multiplex scan.
    artworkRemainder+=1000000U;
    nextArtwork+=artworkRemainder/60U; artworkRemainder%=60U;
    if (now>nextArtwork && now-nextArtwork>100000) nextArtwork=now; // Avoid a catch-up burst after suspend.
  }
  serialCommands();
  __wfi();
}
