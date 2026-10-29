// House Rules B2 / stock XIAO RP2040 Plus + Adafruit4090 / 29 Oct2026.
// mm; z=0 LED front. Prototype geometry: verify actual modules/wires/plug.
// Generated stock-module-values.scad is checked against ../stock-module-contract.json.
include <stock-module-values.scad>
view = "assembled"; // shell,lid,exploded,section,front-preview,interference,
                    // shell-lid-interference,electronics,fit-coupon,closure-coupon,
                    // closure-transition-interference,closure-detail
show_electronics = true;
show_wire_space = true;
fit_clearance = 0.22;
pcb_clearance = 0.20;
$fn = 40;
eps = 0.02;

main_w=88.4; main_h=17.3; main_t=1.6;
led_w=12.7; led_h=17.8; led_t=6.3; led_standoff=3.0;
module_pitch=12.7;
main_front_z=9.3; main_back_z=10.9; main_smd_h=2.0;
front_window_w=90.4; front_window_h=18.4;
window_w=90.4; window_h=19.4;
wall=1.6; total_depth=24.0; back_t=1.2; corner_radius=1.2;
lip_t=1.2; lip_depth=2.4; stop_clearance=0.15;
cx=main_w/2; cy=main_h/2;
window_x=cx-window_w/2;
front_window_x=cx-front_window_w/2;
front_window_y=cy-front_window_h/2;
window_y=front_window_y-(window_h-front_window_h);
outer_x=window_x-wall; outer_y=window_y-wall;
outer_w=window_w+2*wall; outer_h=window_h+2*wall;
back_inside_z=total_depth-back_t;

// Stock module z allowances include the wire/fillet space as separate volumes.
mcu_top_z=mcu_under_z+mcu_t;
usb_top_z=usb_under_z+usb_t;
usb_body_rear_z=usb_top_z+usb_top_h;
usb_face_y=usb_y+usb_h; // native Eagle X1 face is on PCB edge y13.97
usb_port_z=18.25; // allowance, actual purchased receptacle must be checked
port_relief_w=14.0; port_relief_h=6.5;
port_recess=outer_y+outer_h-usb_face_y;
main_stops_x=[3.0,30.0];
mcu_cap_x=38.3; mcu_cap_y=8.65; mcu_cap_front=14.1; mcu_cap_post_face=18.3;

assert(total_depth==24.0 && abs(outer_w-93.6)<.001);
assert(abs(outer_h-22.6)<.001);
assert(mcu_x>=-.25 && mcu_x+mcu_w<=88.65);
assert(mcu_y>=-.25 && mcu_y+mcu_h<=17.55+.001);
assert(usb_x>=-.25 && usb_x+usb_w<=88.65);
assert(usb_y>=-.25 && usb_y+usb_h<=17.55);
assert(mcu_under_z-mcu_under_allow-(main_back_z+main_smd_h)>=.5);
assert(usb_under_z-usb_under_allow-(main_back_z+main_smd_h)>=.49);
assert(back_inside_z-(mcu_top_z+mcu_top_h)>=2.0);
assert(back_inside_z-usb_body_rear_z>=2.0);
assert(back_inside_z-(usb_port_z+port_relief_h/2)>=1.2);
assert(screw_pilot_end_z<=total_depth-.8);
assert(abs(snap_r-fit_clearance-.20)<.001);
assert(wall-(snap_r+snap_pocket_clearance-fit_clearance)>=1.30-.001);
assert(snap_z-snap_r>max(usb_body_rear_z,mcu_top_z+mcu_top_h));
assert(snap_z+snap_r<back_inside_z);
for(x=snap_bottom_x)
 assert(x+snap_length/2+snap_end_clearance<usb_face_x-port_relief_w/2 ||
        x-snap_length/2-snap_end_clearance>usb_face_x+port_relief_w/2);

echo("B2 outer W/H/depth",outer_w,outer_h,total_depth);
echo("MCU PCB under/top,maximum upper",mcu_under_z,mcu_top_z,mcu_top_z+mcu_top_h);
echo("USB PCB under/top,maximum upper",usb_under_z,usb_top_z,usb_body_rear_z);
echo("USB face x/y/port-centre-z",usb_face_x,usb_face_y,usb_port_z);
echo("USB recess and closed-roof thickness",port_recess,back_inside_z-(usb_port_z+port_relief_h/2));
echo("MainSMD-to-MCU/USB wire clearances",mcu_under_z-mcu_under_allow-main_back_z-main_smd_h,usb_under_z-usb_under_allow-main_back_z-main_smd_h);
echo("Closure bead radius / nominal deflection / pocket residual wall",snap_r,snap_r-fit_clearance,wall-(snap_r+snap_pocket_clearance-fit_clearance));

module rounded_box(p,s,r) {
 translate(p) linear_extrude(height=s[2]) hull()
  for(x=[r,s[0]-r],y=[r,s[1]-r]) translate([x,y]) circle(r=r);
}
module port_well() {
 translate([usb_face_x-port_relief_w/2,usb_face_y-.25,
            usb_port_z-port_relief_h/2])
  cube([port_relief_w,outer_y+outer_h-usb_face_y+2,port_relief_h]);
}
module front_body_shoulders() {
 for(y=[front_window_y-eps,front_window_y+front_window_h-.5])
  translate([front_window_x,y,led_t]) cube([front_window_w,.5+eps,1.2]);
}
module main_front_rails() {
 translate([window_x,window_y-eps,main_front_z-1.2])
  cube([window_w,1.0-window_y+eps,1.2]);
 translate([window_x,main_h-1,main_front_z-1.2])
  cube([window_w,window_y+window_h-(main_h-1)+eps,1.2]);
}
module snap_cylinder(x,y,z,r,length) {
 translate([x-length/2,y,z]) rotate([0,90,0]) cylinder(h=length,r=r);
}
module closure_beads() {
 for(x=snap_top_x)
  snap_cylinder(x,window_y+fit_clearance,snap_z,snap_r,snap_length);
 for(x=snap_bottom_x)
  snap_cylinder(x,window_y+window_h-fit_clearance,snap_z,snap_r,snap_length);
}
module closure_pockets() {
 for(x=snap_top_x)
  snap_cylinder(x,window_y+fit_clearance,snap_z,snap_r+snap_pocket_clearance,
                snap_length+2*snap_end_clearance);
 for(x=snap_bottom_x)
  snap_cylinder(x,window_y+window_h-fit_clearance,snap_z,snap_r+snap_pocket_clearance,
                snap_length+2*snap_end_clearance);
}
module shell() {
 difference() {
  union() {
   difference() {
    rounded_box([outer_x,outer_y,0],[outer_w,outer_h,back_inside_z],corner_radius);
    rounded_box([front_window_x,front_window_y,-eps],
                [front_window_w,front_window_h,back_inside_z+2*eps],.3);
    rounded_box([window_x,window_y,led_t+1.2],
                [window_w,window_h,back_inside_z],.3);
   }
   front_body_shoulders(); main_front_rails();
   // MCU insertion is from the top edge while the lid is outside the shell.
   // The bottom stop lies beyond the main PCB edge and cannot snag that board.
   translate([mcu_x-.2,mcu_y+mcu_h+.15,mcu_under_z])
    cube([1.6,outer_y+outer_h-(mcu_y+mcu_h+.15),2.0]);
  }
  port_well();
  closure_pockets();
  translate([cx-4,outer_y-eps,back_inside_z-.9]) cube([8,wall+.4,1.0]);
 }
}
module stop_post(x,y,z_contact,w=2.8,d=1.2) {
 hull() {
  translate([x-w/2,y-d/2,z_contact]) cube([w,d,1.2]);
  translate([x-w/2,y-d/2,back_inside_z-.1]) cube([w,d,.2]);
 }
}
module mcu_channel(x_stem,x_ledge,y) {
 // A1.2 mm solid column and1.2 mm horizontal ledges; no thin snap clip.
 translate([x_stem,y,mcu_under_z-1.2])
  cube([1.2,1.8,back_inside_z-mcu_under_z+1.2+eps]);
 translate([x_ledge,y,mcu_under_z-1.2]) cube([2.5,1.8,1.2]);
 translate([x_ledge,y,mcu_top_z+pcb_clearance]) cube([2.5,1.8,1.2]);
}
module mcu_cradle() {
 // Right channels touch native-audited bare corner rims. The left cap is
 // removable, allowing a5 mm slide from the left without sweeping buttons.
 for(y=[.5,15.7]) {
  translate([mcu_x+mcu_w+.2,y,mcu_under_z-1.2])
   cube([1.2,1.2,back_inside_z-mcu_under_z+1.2+eps]);
  translate([mcu_x+mcu_w-1.1,y,mcu_under_z-1.2]) cube([2.5,1.2,1.2]);
  translate([mcu_x+mcu_w-1.1,y,mcu_top_z+.30]) cube([2.5,1.2,1.2]);
 }
 difference() {
  translate([mcu_cap_x,mcu_cap_y,mcu_cap_post_face])
   cylinder(h=back_inside_z-mcu_cap_post_face+eps,r=2.1);
  translate([mcu_cap_x,mcu_cap_y,mcu_cap_post_face-eps])
   cylinder(h=22.7-mcu_cap_post_face+eps,r=screw_pilot_d/2);
 }
}
module mcu_cap() {
 difference() {
  union() {
   translate([mcu_cap_x,mcu_cap_y,mcu_cap_front])
    cylinder(h=mcu_cap_post_face-mcu_cap_front,r=2.1);
   // Full spine stays0.7 mm outside the PCB and every native component.
   translate([mcu_cap_x-2.1,.5,mcu_cap_front])
    cube([4.2,16.4,mcu_cap_post_face-mcu_cap_front]);
   for(y=[.5,15.7]) {
    translate([mcu_cap_x,y,mcu_cap_front]) cube([mcu_x+1.1-mcu_cap_x,1.2,1.2]);
    translate([mcu_cap_x,y,mcu_top_z+.30]) cube([mcu_x+1.1-mcu_cap_x,1.2,1.2]);
   }
  }
  translate([mcu_cap_x,mcu_cap_y,mcu_cap_front-eps])
   cylinder(h=mcu_cap_post_face-mcu_cap_front+2*eps,r=1.1);
 }
}
module loom_anchor() {
 // Optional small tie passes beneath this2 mm bridge on the removable back.
 // A separate gentle main-board adhesive tack protects the SMT wire pads.
 difference() {
  translate([22,6,19.6]) cube([5,5.3,back_inside_z-19.6+eps]);
  translate([21.9,7.3,19.55]) cube([5.2,2.7,1.3]);
 }
}
module usb_posts() {
 for(p=usb_holes) translate([p[0],p[1],usb_top_z])
  cylinder(h=back_inside_z-usb_top_z+eps,r=2.1);
}
module screw_pilots() {
 for(p=usb_holes) translate([p[0],p[1],usb_top_z-eps])
  cylinder(h=screw_pilot_end_z-usb_top_z+eps,r=screw_pilot_d/2);
}
module lid() {
 difference() {
  union() {
   rounded_box([outer_x,outer_y,back_inside_z],[outer_w,outer_h,back_t],corner_radius);
   difference() {
    rounded_box([window_x+fit_clearance,window_y+fit_clearance,back_inside_z-lip_depth],
                [window_w-2*fit_clearance,window_h-2*fit_clearance,lip_depth+eps],.3);
    rounded_box([window_x+fit_clearance+lip_t,window_y+fit_clearance+lip_t,back_inside_z-lip_depth-eps],
                [window_w-2*(fit_clearance+lip_t),window_h-2*(fit_clearance+lip_t),lip_depth+3*eps],.2);
   }
   for(x=main_stops_x,y=[.65,16.65]) stop_post(x,y,main_back_z+stop_clearance);
   stop_post(64.6,.65,main_back_z+stop_clearance);
   stop_post(64.0,16.65,main_back_z+stop_clearance);
   stop_post(87.0,.65,main_back_z+stop_clearance);
   mcu_cradle(); usb_posts(); loom_anchor(); closure_beads();
  }
  screw_pilots(); port_well();
 }
}
module led_preview() {
 for(m=[0:6]) {
  x=6.1+module_pitch*m;
  color([.75,.73,.67]) translate([x-led_w/2,cy-led_h/2,0]) cube([led_w,led_h,led_t]);
  color([.015,.015,.018]) translate([x-led_w/2,cy-led_h/2,-.03]) cube([led_w,led_h,.04]);
  for(c=[0:4],r=[0:6]) color([.8,.8,.76])
   translate([x-5.08+2.54*c,cy-7.62+2.54*r,-.05]) cylinder(h=.03,r=.95);
  for(px=[-3.81,3.81],row=[0:5]) color([.65,.67,.68])
   translate([x+px,cy-6.35+2.54*row,led_t])
    cylinder(h=main_back_z+1-led_t,r=.25,$fn=12);
 }
}
module mcu_board(shrink=0) {
 rounded_box([mcu_x+shrink,mcu_y+shrink,mcu_under_z+shrink],
             [mcu_w-2*shrink,mcu_h-2*shrink,mcu_t-2*shrink],1.905);
}
module mcu_upper(shrink=0) {
 // Deliberately conservative body allowances. Bare end-edge support regions
 // are excluded, then separately audited against native module copper/pads.
 for(b=mcu_component_boxes) translate([b[0]+shrink,b[1]+shrink,mcu_top_z+shrink])
  cube([max(.001,b[2]-b[0]-2*shrink),max(.001,b[3]-b[1]-2*shrink),2.0-shrink]);
 translate([57.14726+shrink,4.214+shrink,mcu_top_z+shrink])
  cube([7.37-2*shrink,8.95-2*shrink,mcu_top_h-shrink]);
}
module mcu_lower_wires(shrink=0) {
 translate([mcu_x+1.3,mcu_y+.1,mcu_under_z-mcu_under_allow+shrink])
  cube([mcu_w-2.6,mcu_h-.2,mcu_under_allow-shrink]);
}
module usb_board(shrink=0) {
 difference() {
  rounded_box([usb_x+shrink,usb_y+shrink,usb_under_z+shrink],
              [usb_w-2*shrink,usb_h-2*shrink,usb_t-2*shrink],2.54);
  for(p=usb_holes) translate([p[0],p[1],usb_under_z-eps])
   cylinder(h=usb_t+2*eps,r=1.25);
 }
}
module usb_upper(shrink=0) {
 translate([usb_face_x-4.47+shrink,usb_face_y-7.35+shrink,usb_top_z+shrink])
  cube([8.94-2*shrink,7.35-2*shrink,usb_top_h-shrink]);
 // R1/R2 at the left edge are under1 mm; this allowance is1.2 mm.
 translate([usb_x+.8,usb_y+4.5,usb_top_z+shrink]) cube([2.5,4.0,1.2-shrink]);
}
module usb_lower_wires(shrink=0) {
 // All eight header pads, plus the maximum screw-head envelopes.
 translate([usb_x+.1,usb_y+1.2,usb_under_z-usb_under_allow+shrink])
  cube([usb_w-.2,2.7,usb_under_allow-shrink]);
 for(p=usb_holes) translate([p[0],p[1],usb_under_z-1.5+shrink])
  cylinder(h=1.5-shrink,r=2.0-shrink);
}
module electronics_preview() {
 led_preview();
 color([.02,.32,.15]) translate([0,0,main_front_z]) cube([main_w,main_h,main_t]);
 color([.06,.35,.52]) mcu_board();
 color([.16,.16,.18,.55]) mcu_upper();
 color([.04,.42,.28]) usb_board();
 color([.70,.72,.75]) difference() {
  usb_upper();
  translate([usb_face_x-4.15,usb_face_y-2.5,usb_port_z-1.25]) cube([8.3,2.6,2.5]);
 }
 color([.75,.65,.25]) for(p=mcu_pad_points)
  translate([p[0],p[1],mcu_under_z-.04]) cylinder(h=mcu_t+.08,r=.65);
 color([.75,.65,.25]) for(i=[0:7])
  translate([usb_x+1.27+i*2.54,usb_y+2.54,usb_under_z-.04])
   difference() { cylinder(h=usb_t+.08,r=.9);cylinder(h=usb_t+.1,r=.45); }
 color([.55,.57,.60]) translate([mcu_cap_x,mcu_cap_y,mcu_cap_front-1.5]) cylinder(h=1.5,r=2);
 color([.55,.57,.60]) for(p=usb_holes) {
  translate([p[0],p[1],usb_under_z-1.5]) cylinder(h=1.5,r=2);
  translate([p[0],p[1],usb_under_z]) cylinder(h=6,r=1);
 }
 if(show_wire_space) color([.95,.55,.15,.18])
  translate([8,2,14]) cube([28,13,6]);
}
module clearance_envelopes() {
 for(m=[0:6]) translate([6.1+module_pitch*m-led_w/2+eps,cy-led_h/2+eps,eps])
  cube([led_w-2*eps,led_h-2*eps,led_t-2*eps]);
 translate([eps,eps,main_front_z+eps]) cube([main_w-2*eps,main_h-2*eps,main_t-2*eps]);
 // Main rear component envelope excludes declared bare edge contact/pad bands.
 difference() {
  translate([.25,1.5,main_back_z+eps]) cube([main_w-.5,main_h-3.0,main_smd_h-eps]);
  translate([mcu_cap_x,mcu_cap_y,main_back_z+1.0]) cylinder(h=2,r=2.2);
 }
 mcu_board(eps);mcu_upper(eps);mcu_lower_wires(eps);
 translate([mcu_cap_x,mcu_cap_y,mcu_cap_front-1.5+eps]) cylinder(h=1.5-2*eps,r=2-eps);
 usb_board(eps);usb_upper(eps);usb_lower_wires(eps);
 for(m=[0:6],px=[-3.81,3.81],row=[0:5])
  translate([6.1+module_pitch*m+px,cy-6.35+2.54*row,led_t+eps])
   cylinder(h=main_back_z+1-led_t-2*eps,r=.25-eps,$fn=12);
}
module assembled() {
 color([.11,.11,.12]) shell();
 color([.12,.18,.28,.25]) lid();
 color([.30,.33,.38]) mcu_cap();
 if(show_electronics) electronics_preview();
}
module fit_coupon() {
 // A separate20 mm representative XIAO edge-channel fit sample.
 // Uses exactly the PCB thickness and channel ledges;not a case substitute.
 difference() {
  union() {
   cube([20,8,2]);
   translate([1,2,1.9]) cube([1.2,1.8,7]);
   translate([1,2,8]) cube([2.5,1.8,1.2]);
   translate([1,2,8-(mcu_t+.30)-1.2]) cube([2.5,1.8,1.2]);
  }
  translate([10,4,-eps]) cylinder(h=2+2*eps,r=screw_pilot_d/2);
 }
}
module closure_coupon() {
 // Two separate printable pieces. Same bead, pocket, wall and lip dimensions.
 // The shortened wall/sample boundary changes force; this only tests fit.
 coupon_wall_h=10.8;
 coupon_snap_z=coupon_wall_h-(back_inside_z-snap_z);
 difference() {
  union() {cube([24,wall,coupon_wall_h]);cube([24,5,1.2]);}
  snap_cylinder(12,wall+fit_clearance,coupon_snap_z,
                snap_r+snap_pocket_clearance,snap_length+2*snap_end_clearance);
 }
 translate([0,9,0]) union() {
  cube([24,6,back_t]);
  translate([0,wall+fit_clearance,back_t]) cube([24,lip_t,lip_depth]);
  snap_cylinder(12,wall+fit_clearance,back_t+back_inside_z-snap_z,snap_r,snap_length);
 }
}
if(view=="shell") shell();
else if(view=="lid") translate([0,0,total_depth]) mirror([0,0,1]) lid();
else if(view=="exploded") {
 color([.11,.11,.12]) shell();
 translate([0,0,10]) { color([.12,.18,.28,.4]) lid();color([.30,.33,.38]) mcu_cap(); if(show_electronics) {
   color([.06,.35,.52]) mcu_board();color([.04,.42,.28]) usb_board();
   color([.70,.72,.75]) usb_upper();color([.16,.16,.18,.6]) mcu_upper();
 }}
 led_preview();color([.02,.32,.15]) translate([0,0,main_front_z]) cube([main_w,main_h,main_t]);
}
else if(view=="section") intersection() {
 assembled();translate([37,outer_y-1,-1]) cube([54,outer_h+2,total_depth+2]);
}
else if(view=="front-preview") rotate([180,0,0]) assembled();
else if(view=="electronics") electronics_preview();
else if(view=="interference") intersection() {
 union(){shell();lid();mcu_cap();}clearance_envelopes();
}
else if(view=="shell-lid-interference") intersection() {
 shell();lid();translate([outer_x-1,outer_y-1,-1])
 cube([outer_w+2,outer_h+2,back_inside_z+1-eps]);
}
else if(view=="closure-transition-interference") intersection() {
 // Deliberately POSITIVE: rounded beads require shell flex before seating.
 // This is not a claim of an interference-free rigid insertion sweep.
 shell();translate([0,0,snap_transition_offset]) lid();
}
else if(view=="closure-detail") {
 color([.28,.28,.29]) intersection() {
  shell();translate([13,outer_y-.2,19.5]) cube([10,5,4]);
 }
 color([.12,.25,.48]) intersection() {
  translate([0,0,2.8]) lid();
  translate([13,outer_y-.2,22.3]) cube([10,5,4.5]);
 }
}
else if(view=="mcu-slide-interference") intersection() {
 lid();
 union() for(dx=[-5:.5:0]) translate([dx,0,0]) {mcu_board(eps);mcu_upper(eps);mcu_lower_wires(eps);}
}
else if(view=="mcu-cap") translate([-36.2,-.5,-mcu_cap_front]) mcu_cap();
else if(view=="fit-coupon") fit_coupon();
else if(view=="closure-coupon") closure_coupon();
else assembled();
