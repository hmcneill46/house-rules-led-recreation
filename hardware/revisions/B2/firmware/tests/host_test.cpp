#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
#include <string>
#include "board_contract_generated.h"
#include "power_sequence.h"
#include "player.h"
using namespace hrb2;
struct Event {std::string kind; uint64_t time; uint16_t words[4];};
struct IO {
  uint64_t now=0; bool isBlank=true,powered=true,fail=false,hiz=false;
  std::vector<Event> events;
  void event(const char *kind) { Event e={kind,now,{0,0,0,0}}; events.push_back(e); }
  void blank(bool b) {isBlank=b;event(b?"blank":"light");}
  bool shiftAndLatch(const uint16_t w[4]) {assert(isBlank);event("latch");memcpy(events.back().words,w,8);return !fail;}
  void signalsLow(){event("signals-low");}
  void blankHiZ(){hiz=true;isBlank=true;event("blank-hiz");}
  void blankHigh(){hiz=false;isBlank=true;event("blank-high");}
  void enable(bool b){powered=b;event(b?"enable":"disable");}
  void waitUs(uint32_t us){event("wait");now+=us;}
};
static bool bit(const uint16_t words[4],unsigned n){return words[n/16]&(1u<<(n%16));}
static void verifyWords(const uint8_t frame[35],unsigned phase,const uint16_t words[4]) {
  bool expected[64]={false};expected[kBoardLayout.gates[phase]]=true;
  for(unsigned m=0;m<7;++m)for(unsigned r=0;r<7;++r)
    expected[kBoardLayout.rows[m*7+r]]=frame[m*5+phase]&(1u<<r);
  for(unsigned n=0;n<64;++n)assert(bit(words,n)==expected[n]);
}
static void mapping() {
  assert(validLayout(kBoardLayout));
  Layout invalid=kBoardLayout;invalid.rows[1]=invalid.rows[0];assert(!validLayout(invalid));
  invalid=kBoardLayout;invalid.gates[4]=64;assert(!validLayout(invalid));
  uint8_t frame[35]={0};uint16_t words[4];
  for(unsigned pixel=0;pixel<245;++pixel) {
    memset(frame,0,35);frame[pixel/7]=1u<<(pixel%7);
    for(unsigned p=0;p<5;++p){encodePhase(frame,p,kBoardLayout,words);verifyWords(frame,p,words);}
  }
  unsigned rng=0x12345678;
  for(unsigned i=0;i<1000;++i){for(auto &c:frame){rng=rng*1664525+1013904223;c=(rng>>16)&127;}
    for(unsigned p=0;p<5;++p){encodePhase(frame,p,kBoardLayout,words);verifyWords(frame,p,words);}}
  const uint16_t ordered[4]={0x1234,0x5678,0x9abc,0xdef0};uint8_t bytes[8];
  const uint8_t want[8]={0xde,0xf0,0x9a,0xbc,0x56,0x78,0x12,0x34};serialBytes(ordered,bytes);assert(!memcmp(bytes,want,8));
  encodePhase(frame,5,kBoardLayout,words);for(auto w:words)assert(!w);
}
static void timedScan(unsigned duty) {
  IO io;ScanEngine<IO> scan(kBoardLayout);uint8_t frame[35];memset(frame,127,35);
  scan.queueFrame(frame);scan.setDuty(duty);assert(scan.start(100));
  uint64_t next=100;
  while(next<100+200000){io.now=next;next=scan.alarm(next,io);assert(next>io.now);}
  assert(!scan.faulted());assert(scan.frames()==80);
  uint64_t lastBoundary=0,lastLight=0;unsigned latches=0,lights=0;
  bool isLit=false;
  for(const auto &e:io.events){
    if(e.kind=="latch") { if(latches)assert(e.time-lastBoundary==500);lastBoundary=e.time;
      verifyWords(frame,latches%5,e.words);++latches; }
    if(e.kind=="light"){assert(e.time-lastBoundary==30);lastLight=e.time;isLit=true;++lights;}
    if(e.kind=="blank"&&isLit){assert(e.time-lastLight==duty);isLit=false;}
  }
  assert(latches==400);assert(lights==400);
  io.now=next;scan.stop(io);assert(io.isBlank&&!scan.running());
}
static void bufferAndFaults() {
  IO io;ScanEngine<IO> s(kBoardLayout);uint8_t a[35],b[35];memset(a,1,35);memset(b,64,35);
  s.queueFrame(a);s.setDuty(25);s.start(0);
  uint64_t t=0;bool queued=false;
  while(t<=2500){io.now=t;t=s.alarm(t,io);if(!queued){s.queueFrame(b);queued=true;}}
  unsigned n=0;for(auto &e:io.events)if(e.kind=="latch"){verifyWords(n<5?a:b,n%5,e.words);++n;}assert(n==6);
  // A late enable beyond a dim light window must never flash a stale column.
  IO late;ScanEngine<IO> l(kBoardLayout);l.setDuty(25);l.start(0);assert(l.alarm(0,late)==30);
  late.now=70;assert(l.alarm(70,late)==500);assert(late.isBlank);
  for(auto &e:late.events)assert(e.kind!="light");
  // An alarm delayed by a complete phase permanently latches dark.
  late.now=1000;assert(l.alarm(1000,late)==0);assert(l.faulted()&&late.isBlank);assert(!l.start(1001));
  IO failed;failed.fail=true;ScanEngine<IO> f(kBoardLayout);f.setDuty(470);f.start(0);
  assert(f.alarm(0,failed)==0&&f.faulted()&&failed.isBlank);
  Layout bad=kBoardLayout;bad.gates[0]=bad.rows[0];ScanEngine<IO> invalid(bad);assert(!invalid.start(0)&&invalid.faulted());
  // A zero-duty scan leaves all 64 outputs off; high requested duty clamps safely.
  IO zero;ScanEngine<IO> z(kBoardLayout);z.queueFrame(a);z.start(0);z.alarm(0,zero);
  for(auto w:zero.events.back().words)assert(!w);assert(zero.isBlank);
  IO clamp;ScanEngine<IO> c(kBoardLayout);c.setDuty(65535);c.start(0);c.alarm(0,clamp);clamp.now=30;
  assert(c.alarm(30,clamp)==500);
}
static void qualification() {
  CcQualifier c;assert(!c.update(0,1000,0));assert(!c.update(99,1000,0));assert(c.update(100,1000,0));
  assert(!c.update(101,1000,1000));assert(!c.update(102,0,1000));assert(c.update(202,0,1000));
  assert(!c.update(203,0,799));assert(!c.update(204,2201,0));assert(!c.update(205,800,0));assert(c.update(305,800,0));
  CcQualifier wrap;assert(!wrap.update(0xfffffff0,1000,0));assert(wrap.update(84,1000,0));
  assert(allowedOnUs(false,false,false,false,true)==25);
  assert(allowedOnUs(false,false,false,false,false)==0);
  assert(allowedOnUs(true,false,true,false,true)==470);
  assert(allowedOnUs(false,false,false,true,true)==470);
  assert(allowedOnUs(true,true,true,true,true)==0);
  assert(allowedOnUs(false,true,true,true,true)==0); // Reset then suspend before enumeration.
  assert(allowedOnUs(false,true,false,true,true)==470); // No host ever reset/mounted: charger idle.
  Bc12Qualifier bc;
  using Grant=Bc12Qualifier::Grant;
  assert(bc.update(0,false,true)==Grant::Unknown); // Open/reset outputs.
  assert(bc.update(1,false,false)==Grant::Unknown); // No charger grant.
  assert(bc.update(2,true,true)==Grant::Unknown); // AL high forbids charging even with DET high.
  assert(bc.update(102,true,true)==Grant::Unknown);
  assert(bc.update(103,true,false)==Grant::Unknown);
  assert(bc.update(202,true,false)==Grant::Unknown);
  assert(bc.update(203,true,false)==Grant::Charging);
  assert(bc.update(204,false,false)==Grant::Unknown); // Withdraw immediately.
  assert(bc.update(205,true,false)==Grant::Unknown);
  assert(bc.update(305,true,false)==Grant::Charging);
  assert(bc.update(306,true,true)==Grant::Unknown); // AL withdrawal is immediate too.
  Bc12Qualifier bcWrap;
  assert(bcWrap.update(0xfffffff0,true,false)==Grant::Unknown);
  assert(bcWrap.update(84,true,false)==Grant::Charging);
  // Exhaustive source/suspend policy: a real host suspend overrides every grant.
  for (unsigned mask=0;mask<64;++mask) {
    const bool configured=mask&1,suspended=mask&2,seen=mask&4;
    const bool cc=mask&8,dim=mask&16,charger=mask&32;
    const uint16_t expected=suspended&&seen ? 0 :
      configured||cc||charger ? kFullOnUs : dim ? kDimOnUs : 0;
    assert(allowedOnUs(configured,suspended,seen,cc,dim,charger)==expected);
  }
}
static void power() {
  IO io;io.powered=false;RailPower<IO> p(io);p.begin(100);
  assert(io.events.size()==3&&io.events[0].kind=="signals-low"&&io.events[1].kind=="blank-hiz"&&io.events[2].kind=="enable");
  assert(!p.poll(10099));io.now=10100;assert(p.poll(10100));assert(p.ready()&&!io.hiz&&io.isBlank);
  for(auto w:io.events.back().words)assert(!w);
  io.events.clear();p.off();assert(!p.powered()&&!io.powered&&io.hiz);
  const char *want[]={"blank-high","latch","wait","signals-low","blank-hiz","disable"};
  assert(io.events.size()==6);for(unsigned i=0;i<6;++i)assert(io.events[i].kind==want[i]);
  assert(io.events.back().time-io.events.front().time==30);
  io.events.clear();p.begin(20000);p.off();
  for(auto &e:io.events)assert(e.kind!="blank-high"&&e.kind!="latch");assert(!p.powered());
  IO failed;RailPower<IO> f(failed);f.begin(0);failed.fail=true;
  assert(!f.poll(10000)&&f.faulted()&&!f.powered());auto n=failed.events.size();f.begin(20000);assert(failed.events.size()==n);
}
static void diagnostics() {
  uint8_t d[35];diagnosticFrame(DisplayPattern::AllOn,0,d);for(auto c:d)assert(c==127);
  diagnosticFrame(DisplayPattern::Checkerboard,0,d);for(unsigned x=0;x<35;++x)for(unsigned y=0;y<7;++y)assert(bool(d[x]&(1u<<y))==((x+y)%2==0));
  for(unsigned pixel=0;pixel<245;++pixel){diagnosticFrame(DisplayPattern::Walking,pixel*6,d);for(unsigned x=0;x<35;++x)for(unsigned y=0;y<7;++y)assert(bool(d[x]&(1u<<y))==(x*7+y==pixel));}
}
int main(){mapping();timedScan(470);timedScan(25);bufferAndFaults();qualification();power();diagnostics();
  HouseRulesPlayer p;for(unsigned i=0;i<60000;++i){uint8_t frame[35];p.frame(frame);std::fwrite(frame,1,35,stdout);}
}
