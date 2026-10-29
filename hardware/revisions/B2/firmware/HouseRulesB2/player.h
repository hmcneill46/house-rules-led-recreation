#pragma once
#include <stdint.h>
#include <string.h>
#include "generated_sequence.h"

enum class DisplayPattern : uint8_t { Artwork, Walking, AllOn, Checkerboard };

inline void diagnosticFrame(DisplayPattern pattern, uint32_t frame, uint8_t out[35]) {
  memset(out, 0, 35);
  switch (pattern) {
    case DisplayPattern::Walking: {
      const uint16_t pixel = (frame / 6) % 245; // 100 ms per dot at 60 fps.
      out[pixel / 7] = uint8_t(1U << (pixel % 7));
      break;
    }
    case DisplayPattern::AllOn: memset(out, 127, 35); break;
    case DisplayPattern::Checkerboard:
      for (uint8_t x = 0; x < 35; ++x) out[x] = x % 2 ? 0x2A : 0x55;
      break;
    case DisplayPattern::Artwork: break; // Caller uses HouseRulesPlayer instead.
  }
}

// Scheduler-independent 60 fps artwork player. Each call produces one frame.
class HouseRulesPlayer {
 public:
  void restart() { index_ = HR_INITIAL_COMMAND; scroll_ = 0; flash_ = 0; }
  uint16_t commandIndex() const { return index_; }
  void frame(uint8_t out[35]) {
    const HouseRulesCommand &cmd = hr_commands[index_];
    uint32_t offset = 0;
    if (cmd.kind == HR_KIND_SCROLLING) {
      scroll_ += HR_SCROLL_COLS_NUM * HR_FPS_DEN;
      offset = scroll_ / (HR_SCROLL_COLS_DEN * HR_FPS_NUM);
    }
    for (uint8_t x = 0; x < 35; ++x) {
      out[x] = offset + x < cmd.length ? hr_columns[cmd.offset + offset + x] : 0;
    }
    const bool done = cmd.kind == HR_KIND_FLASH
      ? ++flash_ >= cmd.flash_frames
      : offset >= (cmd.length > 35 ? cmd.length - 35 : 0);
    if (done) { index_ = cmd.next_index; scroll_ = 0; flash_ = 0; }
  }
 private:
  uint16_t index_ = HR_INITIAL_COMMAND;
  uint32_t scroll_ = 0;
  uint16_t flash_ = 0;
};

