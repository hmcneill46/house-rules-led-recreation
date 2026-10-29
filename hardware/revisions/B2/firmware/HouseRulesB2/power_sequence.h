#pragma once
#include <stdint.h>

namespace hrb2 {
// IO supplies blankHigh/blankHiZ/signalsLow/enable/shiftAndLatch/waitUs.
// BLANK's external pull-up is on switched 3V3; HiZ avoids back-powering it.
template<class IO> class RailPower {
 public:
  explicit RailPower(IO &io,uint32_t settleUs=10000):io_(io),settleUs_(settleUs) {}
  void begin(uint64_t now) {
    if (state_!=State::Off || fault_) return;
    io_.signalsLow(); io_.blankHiZ(); io_.enable(true);
    readyAt_=now+settleUs_; state_=State::Ramping;
  }
  bool poll(uint64_t now) {
    if (state_==State::Ramping && now>=readyAt_) {
      io_.blankHigh(); const uint16_t zero[4]={0,0,0,0};
      if (!io_.shiftAndLatch(zero)) { fault_=true; off(); return false; }
      state_=State::Ready;
    }
    return state_==State::Ready;
  }
  void off() {
    if (state_==State::Off) return;
    if (state_==State::Ready) {
      io_.blankHigh(); const uint16_t zero[4]={0,0,0,0};
      // Clear the gate bits as well as row bits before removing either rail.
      if (!io_.shiftAndLatch(zero)) fault_=true;
      io_.waitUs(30);
    }
    // During ramp-up, never drive 3V3 logic into a rail below its final voltage.
    io_.signalsLow(); io_.blankHiZ(); io_.enable(false);
    state_=State::Off;
  }
  bool ready() const { return state_==State::Ready; }
  bool powered() const { return state_!=State::Off; }
  bool faulted() const { return fault_; }
 private:
  enum class State:uint8_t { Off,Ramping,Ready };
  IO &io_;
  uint32_t settleUs_;
  uint64_t readyAt_=0;
  State state_=State::Off;
  bool fault_=false;
};
} // namespace hrb2
