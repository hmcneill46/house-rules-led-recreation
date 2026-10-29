#pragma once
#include <stdint.h>
#include <string.h>

namespace hrb2 {
constexpr uint16_t kPhaseUs = 500;
constexpr uint16_t kDeadtimeUs = 30;
constexpr uint16_t kFullOnUs = 470;
constexpr uint16_t kDimOnUs = 25;

struct Layout { uint8_t rows[49]; uint8_t gates[5]; };

inline bool validLayout(const Layout &layout) {
  uint64_t used = 0;
  for (uint8_t i=0;i<54;++i) {
    const uint8_t pin = i<49 ? layout.rows[i] : layout.gates[i-49];
    if (pin>=64 || (used & (uint64_t(1)<<pin))) return false;
    used |= uint64_t(1)<<pin;
  }
  return true;
}

// Global output n is U(n/16+1).OUT(n%16). TLC data bit 1 turns its sink on.
inline void encodePhase(const uint8_t frame[35], uint8_t phase,
                        const Layout &layout, uint16_t words[4]) {
  memset(words, 0, 4*sizeof(uint16_t));
  if (phase>=5 || !validLayout(layout)) return;
  const uint8_t gate=layout.gates[phase];
  words[gate/16] |= uint16_t(1U<<(gate%16));
  for (uint8_t module=0;module<7;++module) {
    const uint8_t column=frame[module*5+phase];
    for (uint8_t row=0;row<7;++row) if (column & (1U<<row)) {
      const uint8_t pin=layout.rows[module*7+row];
      words[pin/16] |= uint16_t(1U<<(pin%16));
    }
  }
}

struct EncodedFrame { uint16_t words[5][4]; };
inline void prepareFrame(const uint8_t frame[35],const Layout &layout,EncodedFrame &out) {
  for (uint8_t phase=0;phase<5;++phase) encodePhase(frame,phase,layout,out.words[phase]);
}

inline void serialBytes(const uint16_t words[4], uint8_t bytes[8]) {
  for (uint8_t i=0;i<4;++i) {
    const uint16_t word=words[3-i];
    bytes[i*2]=uint8_t(word>>8); bytes[i*2+1]=uint8_t(word);
  }
}

// One-core caller contract: queueFrame/setDuty/start/stop are protected against
// the timer ISR. IO must only latch while blank, and shift 64 bits in <30 us.
template<class IO> class ScanEngine {
 public:
  explicit ScanEngine(const Layout &layout): layout_(layout) { }
  // Production computes outside the IRQ critical section, then commits40bytes.
  void queuePrepared(const EncodedFrame &frame) { memcpy(&pending_,&frame,sizeof pending_); }
  void queueFrame(const uint8_t frame[35]) { EncodedFrame next; prepareFrame(frame,layout_,next); queuePrepared(next); }
  void setDuty(uint16_t onUs) { onUs_=onUs>kFullOnUs ? kFullOnUs : onUs; }
  bool start(uint64_t now) {
    if (fault_ || !validLayout(layout_)) { fault_=true; return false; }
    phase_=0; stage_=Stage::Boundary; deadline_=now; running_=true;
    return true;
  }
  void stop(IO &io) { io.blank(true); running_=false; }
  void failDark(IO &io) { stop(io); fault_=true; }
  bool faulted() const { return fault_; }
  bool running() const { return running_; }
  uint8_t phase() const { return phase_; }
  uint64_t deadline() const { return deadline_; }
  uint32_t frames() const { return frames_; }

  uint64_t alarm(uint64_t now, IO &io) {
    if (!running_) return 0;
    if (now<deadline_) return deadline_;
    // A missed complete phase latches dark instead of replaying stale columns.
    if (now-deadline_>=kPhaseUs) { failDark(io); return 0; }
    for (uint8_t transitions=0;transitions<3;++transitions) {
      if (stage_==Stage::Boundary) {
        io.blank(true);
        phaseStart_=now; // Actual turn-off time: never shorten physical deadtime.
        if (phase_==0) { memcpy(&active_,&pending_,sizeof active_); ++frames_; }
        uint16_t words[4]={0,0,0,0};
        phaseOnUs_=onUs_;
        if (phaseOnUs_) memcpy(words,active_.words[phase_],sizeof words);
        if (!io.shiftAndLatch(words)) { failDark(io); return 0; }
        if (phaseOnUs_) { stage_=Stage::Enable; deadline_=phaseStart_+kDeadtimeUs; }
        else advance();
        return deadline_;
      }
      if (stage_==Stage::Enable) {
        // An interrupt delayed beyond this phase's light window skips it.
        if (now>=phaseStart_+kDeadtimeUs+phaseOnUs_) {
          io.blank(true); advance(); return deadline_;
        }
        io.blank(false);
        stage_=Stage::Disable; deadline_=phaseStart_+kDeadtimeUs+phaseOnUs_;
        return deadline_;
      }
      io.blank(true);
      advance();
      if (now<deadline_) return deadline_;
      // Full brightness ends exactly at the next boundary; service both in one ISR.
    }
    failDark(io); return 0;
  }
 private:
  enum class Stage:uint8_t { Boundary, Enable, Disable };
  void advance() { phase_=uint8_t((phase_+1)%5); stage_=Stage::Boundary; deadline_=phaseStart_+kPhaseUs; }
  const Layout &layout_;
  EncodedFrame pending_={},active_={};
  uint16_t onUs_=0,phaseOnUs_=0;
  uint8_t phase_=0;
  Stage stage_=Stage::Boundary;
  uint64_t deadline_=0,phaseStart_=0;
  uint32_t frames_=0;
  bool running_=false,fault_=false;
};

class CcQualifier {
 public:
  bool update(uint32_t nowMs,uint16_t cc1RawMv,uint16_t cc2RawMv) {
    const bool a=cc1RawMv>=800 && cc1RawMv<=2200;
    const bool b=cc2RawMv>=800 && cc2RawMv<=2200;
    const uint8_t candidate=a!=b ? (a?1:2) : 0;
    if (!candidate) { candidate_=0; qualified_=false; return false; }
    if (candidate!=candidate_) { candidate_=candidate; since_=nowMs; qualified_=false; }
    if (uint32_t(nowMs-since_)>=100) qualified_=true;
    return qualified_;
  }
 private:
  uint32_t since_=0;
  uint8_t candidate_=0;
  bool qualified_=false;
};

// BQ24392 Table 2: HIGH/HiZ CHG_AL_N forbids charging regardless of DET.
// With GOOD_BAT permanently high, only AL_N=LOW and DET=HIGH grants
// charging current independently of USB configuration. AL_N=LOW/DET=LOW
// is the SDP/low-current state and needs the computer's USB power grant.
class Bc12Qualifier {
 public:
  enum class Grant:uint8_t { Unknown, Charging };
  Grant update(uint32_t nowMs,bool chargeDetected,bool allowanceN) {
    const Grant candidate=chargeDetected && !allowanceN ?
      Grant::Charging : Grant::Unknown;
    if (candidate==Grant::Unknown) {
      candidate_=grant_=Grant::Unknown; return grant_;
    }
    if (candidate!=candidate_) {
      candidate_=candidate; since_=nowMs; grant_=Grant::Unknown;
    }
    if (uint32_t(nowMs-since_)>=100) grant_=candidate_;
    return grant_;
  }
 private:
  uint32_t since_=0;
  Grant candidate_=Grant::Unknown,grant_=Grant::Unknown;
};

inline uint16_t allowedOnUs(bool configured,bool hostSuspended,bool hostSeen,
                            bool ccQualified,bool allowUnconfiguredDim,
                            bool bcQualified=false) {
  if (hostSuspended && hostSeen) return 0;
  if (configured || ccQualified || bcQualified) return kFullOnUs;
  return allowUnconfiguredDim ? kDimOnUs : 0;
}
} // namespace hrb2
