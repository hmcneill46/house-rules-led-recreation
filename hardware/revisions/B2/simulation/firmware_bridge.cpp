// Host-execute the real firmware encoder and byte serializer. This bridge has
// no independent copy of its mapping and no emulated reverse encoder.
#include <cstdio>
#include <cstdint>
#include <cstring>
#include "board_contract_generated.h"
#include "player.h"

static void record(const uint8_t frame[35]) {
  std::fwrite(frame,1,35,stdout);
  for(uint8_t phase=0;phase<5;++phase) {
    uint16_t words[4];uint8_t bytes[8];
    hrb2::encodePhase(frame,phase,hrb2::kBoardLayout,words);
    hrb2::serialBytes(words,bytes);std::fwrite(bytes,1,8,stdout);
  }
}
int main() {
  std::fwrite("HRB2PIN1",1,8,stdout);
  uint8_t frame[35];
  for(unsigned pixel=0;pixel<245;++pixel) {
    std::memset(frame,0,35);frame[pixel/7]=uint8_t(1u<<(pixel%7));record(frame);
  }
  std::memset(frame,127,35);record(frame);
  for(unsigned x=0;x<35;++x)frame[x]=x%2?0x2a:0x55;
  record(frame);
  HouseRulesPlayer player;
  for(unsigned i=0;i<60000;++i){player.frame(frame);record(frame);}
  return std::ferror(stdout)?1:0;
}
