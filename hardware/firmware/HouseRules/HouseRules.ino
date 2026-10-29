#include <Arduino.h>
#include <Wire.h>
#include "PeripheralPins.h"
#include "player.h"
extern "C" {
#include "usbd_core.h"
#include "usbd_cdc_if.h"
#include "stm32g0xx_hal_pcd_ex.h"
extern USBD_HandleTypeDef hUSBD_Device_CDC;
extern PCD_HandleTypeDef g_hpcd;
USBD_StatusTypeDef __real_USBD_Start(USBD_HandleTypeDef *device);
USBD_StatusTypeDef __real_USBD_LL_Suspend(USBD_HandleTypeDef *device);
USBD_StatusTypeDef __real_USBD_LL_Resume(USBD_HandleTypeDef *device);
HAL_StatusTypeDef __real_HAL_PCD_Init(PCD_HandleTypeDef *pcd);
}
// Override the generic variant's weak map: optional USB_NOE alternate pins are
// unnecessary with the internal PHY and would otherwise claim PA13/SWDIO.
extern const PinMap PinMap_USB_DRD_FS[] = {
  {PA_11, USB_DRD_FS, STM_PIN_DATA(STM_MODE_INPUT, LL_GPIO_PULL_NO, GPIO_AF_NONE)},
  {PA_12, USB_DRD_FS, STM_PIN_DATA(STM_MODE_INPUT, LL_GPIO_PULL_NO, GPIO_AF_NONE)},
  {NC, NP, 0}
};

// Prototype firmware: compiled for the frozen schematic; not hardware validated.
constexpr uint32_t SHUTDOWN = PB0;
constexpr uint8_t ADDRESS[4] = {0x34, 0x35, 0x36, 0x37};
enum class BcPort : uint8_t { Unknown, Standard, Charging, Dedicated, Error };
volatile BcPort bcPort = BcPort::Unknown;
volatile bool bcdFinished = false, usbSuspended = false, usbAttached = false, shutdownEvent = false;
bool fault = false, outputsEnabled = false;
volatile bool hostSeen = false;
bool ccHigh = false;
uint32_t ccSince = 0, lastCcSample = 0;
uint8_t currentGcc = 0;
uint32_t nextFrame = 0, frameRemainder = 0;
HouseRulesPlayer player;
uint8_t columns[35];
DisplayPattern displayPattern = DisplayPattern::Artwork;
uint32_t diagnosticTick = 0;

void handleSerialCommands() {
  // Read individual bytes without waiting for a newline or blocking the player.
  // These commands select pixels only; none bypasses source/GCC/shutdown policy.
  for (uint8_t n = 0; n < 16 && SerialUSB.available(); ++n) {
    const char command = char(SerialUSB.read());
    const char *reply = nullptr;
    switch (command) {
      case 'w': displayPattern = DisplayPattern::Walking; reply = "Walking: 100 ms per dot"; break;
      case 'a': displayPattern = DisplayPattern::AllOn; reply = "All 245 dots on"; break;
      case 'c': displayPattern = DisplayPattern::Checkerboard; reply = "Checkerboard"; break;
      case 'p': displayPattern = DisplayPattern::Artwork; player.restart(); reply = "Artwork"; break;
      case 'r': player.restart(); reply = "Current mode restarted"; break;
      default: break;
    }
    if (reply) {
      diagnosticTick = 0;
      nextFrame = micros();
      if (SerialUSB) SerialUSB.println(reply); // DTR is used for feedback only.
    }
  }
}

// STM32duino calls this wrapper from premain -> init -> hw_config_init, before
// setup() and before C++ global constructors have all run. Defer that automatic
// USB start completely. setup() later calls SerialUSB.begin -> CDC_init directly.
extern "C" void __wrap_USBD_CDC_init(void) { }

// The core's weak re-enumeration helper reconnects D+ before PCD initialisation.
// Keep its useful detach interval, but never attach before BC1.2 has completed.
extern "C" void USBD_reenumerate(void) {
  __HAL_RCC_USB_CLK_ENABLE();
  CLEAR_BIT(USB_DRD_FS->BCDR, USB_BCDR_DPPU);
  delay(20);
}

// Initialise the core's documented USB wake EXTI path. STOP entry is selected
// only on a real host suspend; a dedicated power supply must keep playing.
extern "C" HAL_StatusTypeDef __wrap_HAL_PCD_Init(PCD_HandleTypeDef *pcd) {
  pcd->Init.low_power_enable = ENABLE;
  HAL_StatusTypeDef status = __real_HAL_PCD_Init(pcd);
  pcd->Init.low_power_enable = DISABLE;
  return status;
}

// Strong replacement for the HAL's documented weak notification callback.
extern "C" void HAL_PCDEx_BCD_Callback(PCD_HandleTypeDef *, PCD_BCD_MsgTypeDef message) {
  switch (message) {
    case PCD_BCD_STD_DOWNSTREAM_PORT: bcPort = BcPort::Standard; break;
    case PCD_BCD_CHARGING_DOWNSTREAM_PORT: bcPort = BcPort::Charging; break;
    case PCD_BCD_DEDICATED_CHARGING_PORT: bcPort = BcPort::Dedicated; break;
    case PCD_BCD_ERROR: bcPort = BcPort::Error; bcdFinished = false; break;
    case PCD_BCD_DISCOVERY_COMPLETED: bcdFinished = true; break;
    default: break;
  }
}

// Linker --wrap hook: official core calls USBD_Start only after PCD init and
// class registration, before enabling the data pull-up. No core files edited.
extern "C" USBD_StatusTypeDef __wrap_USBD_Start(USBD_HandleTypeDef *device) {
  static bool attempted = false;
  GPIOB->BSRR = uint32_t(GPIO_PIN_0) << 16; // SDB low throughout charge detection.
  if (!attempted) {
    attempted = true;
    if (HAL_PCDEx_ActivateBCD(&g_hpcd) == HAL_OK) {
      HAL_PCDEx_BCD_VBUSDetect(&g_hpcd);
      HAL_PCDEx_DeActivateBCD(&g_hpcd);
    }
  }
  if (bcdFinished && bcPort == BcPort::Dedicated) {
    usbAttached = false; // DCP has no data host; do not attach a data function.
    return USBD_OK;
  }
  usbAttached = true;
  return __real_USBD_Start(device);
}

extern "C" USBD_StatusTypeDef __wrap_USBD_LL_Suspend(USBD_HandleTypeDef *device) {
  if (usbAttached) {
    GPIOB->BSRR = uint32_t(GPIO_PIN_0) << 16; // Immediate analogue shutdown in ISR.
    usbSuspended = true;
    shutdownEvent = true;
    const bool charging = bcdFinished && (bcPort == BcPort::Charging || bcPort == BcPort::Dedicated);
    if (hostSeen || device->dev_address || !(ccHigh || charging)) {
      __HAL_RCC_PWR_CLK_ENABLE();
      MODIFY_REG(PWR->CR1, PWR_CR1_LPMS, 0UL); // STM32G0 STOP0, SRAM retained.
      g_hpcd.Init.low_power_enable = ENABLE;
      // The core callback gates the PHY and sets SLEEPDEEP/SLEEPONEXIT after
      // this returns. Its resume callback restores USB and system clocks.
    }
  }
  return __real_USBD_LL_Suspend(device);
}

extern "C" USBD_StatusTypeDef __wrap_USBD_LL_Resume(USBD_HandleTypeDef *device) {
  USBD_StatusTypeDef status = __real_USBD_LL_Resume(device);
  usbSuspended = false;
  g_hpcd.Init.low_power_enable = DISABLE;
  return status;
}

bool writeRegisters(uint8_t driver, uint8_t start, const uint8_t *values, size_t count) {
  while (count) {
    const size_t chunk = count > 28 ? 28 : count;
    Wire.beginTransmission(ADDRESS[driver]);
    Wire.write(start);
    Wire.write(values, chunk);
    if (Wire.endTransmission() != 0) {
      digitalWrite(SHUTDOWN, LOW);
      outputsEnabled = false;
      fault = true; // Fail dark until reset; do not repeatedly energise a faulty bus.
      return false;
    }
    start += chunk; values += chunk; count -= chunk;
  }
  return true;
}

bool writeRegister(uint8_t driver, uint8_t reg, uint8_t value) {
  return writeRegisters(driver, reg, &value, 1);
}

bool initialiseDrivers() {
  delayMicroseconds(20); // 5 V and 3.3 V must already be stable.
  for (uint8_t driver = 0; driver < 4; ++driver) {
    if (!writeRegister(driver, 0xCF, 0xAE)) return false;
    if (!writeRegister(driver, 0xA0, 0x40)) return false; // n=5, software off
    if (!writeRegister(driver, 0xA1, 0)) return false;
    if (!writeRegister(driver, 0xB2, 0x01)) return false; // 32 kHz PWM
    uint8_t scale[16] = {};
    const uint8_t used = driver == 3 ? 7 : 14;
    for (uint8_t cs = 0; cs < used; ++cs) scale[cs] = 255;
    if (!writeRegisters(driver, 0x90, scale, sizeof scale)) return false;
    uint8_t clear[128] = {};
    if (!writeRegisters(driver, 0x01, clear, sizeof clear)) return false;
  }
  return true;
}

void sampleCc() {
  const uint32_t now = millis();
  if (uint32_t(now - lastCcSample) < 10) return;
  lastCcSample = now;
  uint32_t a = 0, b = 0;
  for (uint8_t i = 0; i < 8; ++i) { a += analogRead(PA0); b += analogRead(PA1); }
  // 47k/47k divider; nominal VDDA=3.3 V. Long ADC sample is configured below.
  const uint32_t cc1mv = a * 6600UL / (8UL * 4095UL);
  const uint32_t cc2mv = b * 6600UL / (8UL * 4095UL);
  // Conservative threshold: never mistake default-current Rp for 1.5 A.
  // Some valid low-end 1.5 A advertisements may remain dim: verify on hardware.
  const bool candidate = (cc1mv >= 800 && cc1mv <= 2200) || (cc2mv >= 800 && cc2mv <= 2200);
  if (!candidate) { ccSince = 0; ccHigh = false; }
  else {
    if (!ccSince) ccSince = now;
    ccHigh = uint32_t(now - ccSince) >= 100;
  }
}

void applyGcc(uint8_t gcc) {
  if (!gcc) {
    digitalWrite(SHUTDOWN, LOW);
    outputsEnabled = false;
    currentGcc = 0;
    return;
  }
  if (gcc != currentGcc || !outputsEnabled) {
    for (uint8_t driver = 0; driver < 4; ++driver)
      if (!writeRegister(driver, 0xA1, gcc)) return;
    // Function registers are accessible while SDB is low. Respect I2C quiet
    // windows on both sides of SDB rising; keep software shutdown until after.
    if (!outputsEnabled) {
      delayMicroseconds(12);
      // Recheck the live USB state immediately before energising the matrix.
      const bool charging = bcdFinished && (bcPort == BcPort::Charging || bcPort == BcPort::Dedicated);
      if (usbSuspended && (hostSeen || !(ccHigh || charging))) return;
      const uint32_t irqState = __get_PRIMASK();
      __disable_irq();
      digitalWrite(SHUTDOWN, HIGH);
      if (!irqState) __enable_irq(); // A pending USB suspend IRQ blanks SDB immediately.
      delayMicroseconds(12);
      for (uint8_t driver = 0; driver < 4; ++driver)
        if (!writeRegister(driver, 0xA0, 0x41)) return;
      outputsEnabled = true;
    }
    currentGcc = gcc;
  }
}

void setup() {
  digitalWrite(SHUTDOWN, LOW);
  pinMode(SHUTDOWN, OUTPUT);
  analogReadResolution(12);
  pinMode(PA0, INPUT_ANALOG);
  pinMode(PA1, INPUT_ANALOG);
  Wire.setSCL(PB6);
  Wire.setSDA(PB7);
  Wire.begin();
  Wire.setClock(400000);
  initialiseDrivers();
  const uint32_t ccStart = millis();
  while (uint32_t(millis() - ccStart) < 120) { sampleCc(); delay(1); }
  SerialUSB.begin(); // Link wrapper performs BC1.2 before the data pull-up.
  nextFrame = micros();
}

void loop() {
  handleSerialCommands();
  sampleCc();
  const uint8_t usbState = hUSBD_Device_CDC.dev_state;
  if (usbState == USBD_STATE_ADDRESSED || usbState == USBD_STATE_CONFIGURED || hUSBD_Device_CDC.dev_address) hostSeen = true;
  const bool charging = bcdFinished && (bcPort == BcPort::Charging || bcPort == BcPort::Dedicated);
  const bool suspended = usbSuspended || usbState == USBD_STATE_SUSPENDED;
  if (shutdownEvent) { outputsEnabled = false; shutdownEvent = false; } // ISR already drove SDB low.
  const uint8_t gcc = fault ? 0 : powerGcc(usbState == USBD_STATE_CONFIGURED,
                                         suspended, hostSeen, ccHigh, charging);
  applyGcc(gcc);
  if (fault || !gcc) {
    // Total STOP/suspend current and successful wake still require a hardware
    // measurement before any USB compliance claim.
    nextFrame = micros();
    delay(1);
    return;
  }
  const uint32_t now = micros();
  if (int32_t(now - nextFrame) < 0) return;
  if (uint32_t(now - nextFrame) > 100000) nextFrame = now; // Recover without a burst after a long stall.
  nextFrame += 1000000 / 60;
  frameRemainder += 1000000 % 60;
  if (frameRemainder >= 60) { ++nextFrame; frameRemainder -= 60; }
  if (displayPattern == DisplayPattern::Artwork) player.frame(columns);
  else diagnosticFrame(displayPattern, diagnosticTick++, columns);
  for (uint8_t driver = 0; driver < 4; ++driver) {
    uint8_t image[80];
    encodeDriver(columns, driver, image);
    if (!writeRegisters(driver, 0x01, image, sizeof image)) break;
  }
}
