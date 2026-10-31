#!/usr/bin/env python3
"""Execute the actual HardwareIO backend against a digital TLC59283 latch model.

Only the HardwareIO class is extracted from application.cpp and compiled with
fake GPIO/SPI primitives. This checks its real write/blank/latch ordering and
failure paths without pretending to simulate analog precharge or GPIO timing.
The independent model implements TI Rev.C p4: LAT is transparent while high;
falling LAT holds outputs and does not destroy the serial shift register.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
FW = HERE.parent


def main():
    path = FW / 'HouseRulesB2/application.cpp'
    source = path.read_text()
    start = source.index('class HardwareIO {')
    end = source.index('\nHardwareIO io;', start)
    backend = source[start:end]
    harness = r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include <initializer_list>
#include "board_contract_generated.h"
using namespace hrb2;
static bool pins[30]={};
static uint16_t shiftWords[4]={0xabcd,0xdead,0xcafe,0x1357},outputs[4]={};
static unsigned clocked=0,latPulses=0,latWaitUs=0,spiFrequency=0;
static int spi0=0,returnCount=8;
static const int GPIO_IN=0,GPIO_OUT=1,GPIO_FUNC_SPI=2,GPIO_FUNC_SIO=3;
static const int SPI_CPOL_0=0,SPI_CPHA_0=0,SPI_MSB_FIRST=1;
static void gpio_put(unsigned pin,bool value) {
  if (pin==PIN_LAT && value) { assert(pins[PIN_BLANK]); ++latPulses; }
  pins[pin]=value;
  if (pins[PIN_LAT]) std::memcpy(outputs,shiftWords,sizeof outputs);
}
static bool gpio_get(unsigned pin) { return pins[pin]; }
static void gpio_set_dir(unsigned,int) {}
static void gpio_set_function(unsigned,int) {}
static void gpio_disable_pulls(unsigned) {}
static void spi_deinit(int) {}
static void spi_init(int,unsigned frequency) { spiFrequency=frequency; }
static void spi_set_format(int,unsigned,int,int,int) {}
static void busy_wait_us_32(unsigned duration) {
  if (pins[PIN_LAT]) latWaitUs+=duration;
}
static void clockBit(unsigned bit) {
  for (unsigned device=0;device<4;++device) {
    unsigned carry=shiftWords[device]>>15;
    shiftWords[device]=uint16_t((shiftWords[device]<<1)|bit); bit=carry;
  }
  ++clocked;
  if (pins[PIN_LAT]) std::memcpy(outputs,shiftWords,sizeof outputs);
}
static size_t spi_write_blocking(int,const uint8_t *bytes,size_t count) {
  assert(pins[PIN_BLANK] && !pins[PIN_LAT]);
  assert(count==8);
  for (int i=0;i<returnCount;++i)
    for (int bit=7;bit>=0;--bit) clockBit((bytes[i]>>bit)&1);
  return returnCount;
}
BACKEND
int main() {
  HardwareIO io; const uint16_t clear[4]={};
  assert(!io.shiftAndLatch(clear)); // Unpowered/uninitialised must not latch.
  io.blankHigh(); assert(spiFrequency==8000000);
  unsigned rng=59283;
  for (unsigned transaction=0;transaction<1000;++transaction) {
    uint16_t desired[4];
    for (auto &word:desired) { rng=rng*1664525+1013904223; word=uint16_t(rng>>8); }
    const unsigned before=clocked,pulses=latPulses,wait=latWaitUs;
    assert(io.shiftAndLatch(desired));
    assert(clocked-before==64 && latPulses-pulses==1 && latWaitUs-wait>=1);
    assert(!pins[PIN_LAT] && pins[PIN_BLANK]);
    assert(!std::memcmp(outputs,desired,sizeof outputs));
    assert(!std::memcmp(shiftWords,desired,sizeof shiftWords)); // Non-destructive.
  }
  assert(io.shiftAndLatch(clear));
  for (auto word:outputs) assert(word==0);
  // A short SPI transfer must return false without exposing a partial latch.
  returnCount=6; const unsigned pulses=latPulses;
  const uint16_t ones[4]={65535,65535,65535,65535};
  assert(!io.shiftAndLatch(ones));
  assert(latPulses==pulses && !pins[PIN_LAT] && pins[PIN_BLANK]);
  for (auto word:outputs) assert(word==0);
  returnCount=8;
  io.blank(false); assert(!io.shiftAndLatch(clear));
  io.blankHiZ(); assert(!io.shiftAndLatch(clear));
  io.blankHigh(); io.signalsLow(); assert(!io.shiftAndLatch(clear));
  // Negative controls establish that the independent latch model is sensitive
  // to clocks during LAT-high and to an incomplete 63-clock clear.
  for (auto &word:shiftWords) word=0;
  gpio_put(PIN_BLANK,true); gpio_put(PIN_LAT,true); clockBit(1);
  assert(!std::memcmp(outputs,shiftWords,sizeof outputs));
  assert(outputs[0]==1); gpio_put(PIN_LAT,false);
  for (auto &word:shiftWords) word=65535;
  for (unsigned i=0;i<63;++i) clockBit(0);
  gpio_put(PIN_LAT,true); gpio_put(PIN_LAT,false);
  assert(outputs[0]==0 && outputs[1]==0 && outputs[2]==0 && outputs[3]==0x8000);
}
'''.replace('BACKEND', backend)
    with tempfile.TemporaryDirectory(prefix='house-rules-59283-transactions-') as tmp:
        cpp = Path(tmp) / 'test.cpp'
        exe = Path(tmp) / 'test'
        cpp.write_text(harness)
        command = ['c++', '-std=c++11', '-O2', '-Wall', '-Wextra', '-Werror',
                   '-Wno-misleading-indentation',
                   '-I' + str(FW / 'HouseRulesB2'), str(cpp), '-o', str(exe)]
        subprocess.run(command, check=True)
        subprocess.run([str(exe)], check=True)
    report = {
        'result': 'PASS', 'driver': 'TLC59283RGER',
        'source': 'https://www.ti.com/lit/ds/symlink/tlc59283.pdf',
        'source_section': 'Rev.C p4 LAT description; p8 digital timing limits (section5.7)',
        'actual_backend_source': 'HouseRulesB2/application.cpp class HardwareIO',
        'backend_source_sha256': hashlib.sha256(backend.encode()).hexdigest(),
        'complete_transactions': 1000, 'bits_per_transaction': 64,
        'SPI_Hz_requested': 8000000, 'LAT_high_wait_us_requested': 1,
        'checks': ['LAT low throughout each SPI write',
                   'Exactly64 clock bits then one latch pulse while BLANK high',
                   'All four output words match actual transmitted words',
                   'Level-sensitive latch preserves serial contents',
                   'Startup/shutdown all-zero write',
                   'Short SPI transfer never latches partial data',
                   'Unpowered, blank-low, HiZ and deinitialised SPI paths reject writes',
                   'Negative controls: LAT-high clocks propagate; 63-bit clear leaves stale data'],
        'limitations': ['Digital model plus actual C++ transaction backend only',
                        'No RP2040 peripheral or measured setup/hold/propagation timing',
                        'No precharge, PMOS, rail-transient, ghosting, current or thermal model']}
    (HERE / 'driver-transactions-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
