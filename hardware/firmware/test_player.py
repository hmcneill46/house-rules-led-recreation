#!/usr/bin/env python3
"""Compile the portable player for the host and compare 60,000 scheduled frames."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
HOST_TEST = r'''
#include <cstdio>
#include <cassert>
#include "player.h"
int main() {
  assert(powerGcc(false,false,false,false,false)==8);
  assert(powerGcc(true,false,true,false,false)==64);
  assert(powerGcc(false,false,false,true,false)==64);
  assert(powerGcc(false,false,false,false,true)==64);
  assert(powerGcc(false,true,true,true,true)==0);
  assert(powerGcc(false,true,false,false,false)==0);
  assert(powerGcc(false,true,false,true,false)==64);
  assert(powerGcc(false,true,false,false,true)==64);
  uint8_t diagnostic[35];
  diagnosticFrame(DisplayPattern::AllOn,0,diagnostic);
  for(int x=0;x<35;x++)assert(diagnostic[x]==127);
  diagnosticFrame(DisplayPattern::Checkerboard,0,diagnostic);
  for(int x=0;x<35;x++)for(int y=0;y<7;y++)assert(bool(diagnostic[x]&(1<<y))==((x+y)%2==0));
  for(int pixel=0;pixel<245;pixel++) {
    diagnosticFrame(DisplayPattern::Walking,pixel*6,diagnostic);
    for(int x=0;x<35;x++)for(int y=0;y<7;y++)assert(bool(diagnostic[x]&(1<<y))==(x*7+y==pixel));
  }
  diagnosticFrame(DisplayPattern::Walking,245*6,diagnostic);
  assert(diagnostic[0]==1);for(int x=1;x<35;x++)assert(diagnostic[x]==0);
  HouseRulesPlayer p;
  for (int i=0;i<60000;i++) {
    uint8_t columns[35]; p.frame(columns);
    for (uint8_t driver=0;driver<4;driver++) {
      uint8_t encoded[80]; encodeDriver(columns,driver,encoded);
      for (uint8_t sw=0;sw<5;sw++) for(uint8_t cs=0;cs<16;cs++) {
        uint8_t module=driver*2+cs/7;
        bool expected=cs<14 && module<7 && (columns[module*5+sw] & (1<<(cs%7)));
        assert(encoded[sw*16+cs]==(expected?255:0));
      }
    }
    std::fwrite(columns,1,35,stdout);
  }
}
'''


def main():
    manifest = json.loads((HERE / "sequence_manifest.json").read_text())
    data = (HERE / "sequence_columns.bin").read_bytes()
    with tempfile.TemporaryDirectory(prefix="house-rules-player-") as tmp:
        temp = Path(tmp)
        shutil.copy2(HERE / "HouseRules/player.h", temp / "player.h")
        shutil.copy2(HERE / "generated_sequence.h", temp / "generated_sequence.h")
        (temp / "test.cpp").write_text(HOST_TEST)
        subprocess.run(["c++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-O2",
                        str(temp / "test.cpp"), "-o", str(temp / "test")], check=True)
        output = subprocess.check_output([str(temp / "test")])
    index = 0
    scroll = 0
    flash = 0
    visited_last = 0
    for frame in range(60000):
        command = manifest["commands"][index]
        if command["kind"] == "scrolling":
            scroll += 95
            offset = scroll // 120
        else:
            offset = 0
        length = max(0, min(35, command["length"] - offset))
        start = command["offset"] + offset
        expected = data[start:start + length].ljust(35, b"\0")
        actual = output[frame * 35:frame * 35 + 35]
        assert actual == expected, (frame, index)
        if command["kind"] == "flash":
            flash += 1
            done = flash >= command["flash_frames"]
        else:
            done = offset >= max(0, command["length"] - 35)
        if done:
            if index == len(manifest["commands"]) - 1:
                visited_last += 1
                assert command["next_index"] == 1
            index = command["next_index"]
            scroll = flash = 0
    assert visited_last >= 2
    print(f"60,000 C++ player frames match exported timing/content; {visited_last} complete traversals; diagnostics, power and driver-map assertions pass.")


if __name__ == "__main__":
    main()
