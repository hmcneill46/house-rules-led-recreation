// House Rules enclosure / engineering concept, 29 October 2026.
// Units: mm. PROTOTYPE STLs require print-fit and actual connector checks.
// Main PCB coordinates match circuit-spec.json: x right, y toward bottom edge.
// z=0 is the LED front face; positive z goes toward the removable rear cover.

view = "assembled"; // assembled, exploded, shell, lid, section, front-preview,
                    // interference, shell-lid-interference
show_electronics = true;
fit_clearance = 0.22; // Adjust after a printer/material fit coupon.
$fn = 32;
eps = 0.02;

main_w = 88.4;
main_h = 17.3;
main_t = 1.6;
led_w = 12.7;
led_h = 17.8;
led_t = 6.3;
led_standoff = 3.0;
module_pitch = 12.7;

daughter_w = 16.0;
daughter_h = 16.8;
daughter_t = 1.0;
daughter_xy = [72.15, 0.25];
daughter_gap = 3.5; // Main rear surface to daughter underside, not board centre.

usb_xy_local = [10.7, 13.7];
usb_w = 8.94;
usb_depth = 7.35;
usb_height = 3.31;
usb_front_offset = 3.675; // PCB-edge annotation is +3.1; mating face is +3.675.
usb_aperture_center_height = 1.73;

// Open front window clears the full reported approximately 90 x 18 LED group.
// The rear body shoulders support the plastic edges; no front lip covers dots.
front_window_w = 90.4;
front_window_h = 18.4;
window_w = 90.4;
window_h = 19.4; // Extra 1 mm is above the LEDs; USB wall stays in place.
wall = 1.6;
back_t = 1.2;
total_depth = 24.0; // Extra rear space for the vertical main JST wire bend.
corner_radius = 1.2;
lip_t = 1.2;
lip_depth = 2.4;
pcb_stop_clearance = 0.15;

cx = main_w / 2;
cy = main_h / 2;
window_x = cx - window_w / 2;
front_window_x = cx - front_window_w / 2;
front_window_y = cy - front_window_h / 2;
window_y = front_window_y - (window_h-front_window_h);
outer_x = window_x - wall;
outer_y = window_y - wall;
outer_w = window_w + 2 * wall;
outer_h = window_h + 2 * wall;

led_back_z = led_t;
main_front_z = led_t + led_standoff;
main_back_z = main_front_z + main_t;
daughter_under_z = main_back_z + daughter_gap;
daughter_rear_z = daughter_under_z + daughter_t;
usb_rear_z = daughter_rear_z + usb_height;
back_inside_z = total_depth - back_t;
usb_x = daughter_xy[0] + usb_xy_local[0];
usb_y = daughter_xy[1] + usb_xy_local[1];
usb_face_y = usb_y + usb_front_offset;
usb_port_z = daughter_rear_z + usb_aperture_center_height;

// Initial plug-overmould relief. Check the actual cable before finalising.
port_relief_w = 14.0;
port_relief_h = 6.5;
port_recess = outer_y + outer_h - usb_face_y;

assert(daughter_xy[0] >= -0.25 && daughter_xy[0] + daughter_w <= 88.65);
assert(daughter_xy[1] >= -0.25 && daughter_xy[1] + daughter_h <= 17.55);
assert(daughter_gap >= 3.5);
assert(back_inside_z - usb_rear_z >= 0.5);
assert(window_w >= 90.0 && window_h >= 18.0);
assert(fit_clearance > 0 && lip_t > 0);
assert(daughter_xy[1]-pcb_stop_clearance-(window_y+fit_clearance) >= 1.2,
       "Carrier top columns must be at least 1.2 mm thick");
assert(port_relief_h / 2 + usb_port_z < total_depth);
assert(total_depth-(usb_port_z+port_relief_h/2) >= 1.2,
       "Port well needs at least1.2 mm of material toward the rear");

echo("Outer case W/H/depth", outer_w, outer_h, total_depth);
echo("Main front/rear z", main_front_z, main_back_z);
echo("Daughter underside/rear z", daughter_under_z, daughter_rear_z);
echo("USB mating face x/y, rear z", usb_x, usb_face_y, usb_rear_z);
echo("USB recess from ordinary outer wall", port_recess);
echo("Back clearance above USB", back_inside_z - usb_rear_z);

module rounded_box(p, s, r) {
    translate(p)
        linear_extrude(height=s[2])
            hull()
                for (x=[r, s[0]-r], y=[r, s[1]-r])
                    translate([x,y]) circle(r=r);
}

module port_well() {
    // The larger well reaches the mating face, clearing the plug overmould.
    // At24 mm depth this leaves2.42 mm shell roof before the rear split.
    translate([usb_x-port_relief_w/2, usb_face_y-0.25,
               usb_port_z-port_relief_h/2])
        cube([port_relief_w, outer_y+outer_h-usb_face_y+2.0,
              port_relief_h]);
}

module front_body_shoulders() {
    // Contact the LED plastic rear rims only, outside every lead row.
    for (y=[front_window_y-eps, front_window_y+front_window_h-0.5])
        translate([front_window_x, y, led_back_z])
            cube([front_window_w, 0.5+eps, 1.2]);
}

module main_front_rails() {
    // Continuous insulating ledges under component-free front PCB edges.
    translate([window_x, window_y-eps, main_front_z-1.2])
        cube([window_w, 1.0-window_y+eps, 1.2]);
    translate([window_x, main_h-1.0, main_front_z-1.2])
        cube([window_w, window_y+window_h-(main_h-1.0)+eps, 1.2]);
}

module lid_carrier_cradle() {
    // The carrier slides into this cradle from the right while the lid is off.
    // Keeping these rails on the lid leaves the shell open for the already-
    // soldered main/LED assembly to enter from the rear without snagging.
    // Top columns are1.43 x3.0 with broad gussets in the extra rear air space;
    // lower-left pillar is1.2 x2.0 with a strengthened rear root.
    for (x=[74.5,86.6])
        translate([x-1.5, window_y+fit_clearance, daughter_under_z-1.2])
            cube([3.0, 1.0-window_y-fit_clearance, 1.2]);
    translate([70.8,14.0,daughter_under_z-1.2])
        cube([2.2,2.0,1.2]);

    // Edge columns connect the front tabs to the lid. They contact only the
    // bare board edges and carry connector loads through the printed back.
    for (x=[74.5,86.6])
        translate([x-1.5,window_y+fit_clearance,daughter_under_z-1.2])
            cube([3.0,daughter_xy[1]-pcb_stop_clearance-
                       (window_y+fit_clearance),
                  back_inside_z-daughter_under_z+1.2+eps]);
    for (x=[74.5,86.6])
        hull() {
            translate([x-1.5,window_y+fit_clearance,18.6])
                cube([3.0,1.43,0.2]);
            translate([x-1.5,window_y+fit_clearance,back_inside_z-0.2])
                cube([3.0,2.0-window_y-fit_clearance,0.4]);
        }
    // The lower-left side support avoids the JST housing and all components.
    translate([70.8,14.0,daughter_under_z-1.2])
        cube([1.2,2.0,back_inside_z-daughter_under_z+1.2+eps]);
    translate([70.8,14.0,daughter_rear_z+pcb_stop_clearance])
        cube([2.0,2.0,1.2]);
    hull() {
        translate([70.8,14.0,18.0]) cube([1.2,2.0,0.2]);
        translate([69.8,14.0,back_inside_z-0.2]) cube([2.2,2.0,0.4]);
    }
}

module carrier_right_fence() {
    // Captures sideways carrier movement after the lid enters the shell.
    // Main PCB ends at 88.4, so this cannot obstruct main-board insertion.
    // Nominal carrier edge clearance is 0.45 mm; the aperture allows this.
    // This is a 2.4 x 2.0 x 2.6 integral block extending through the wall,
    // rather than a thin freestanding clip; 0.8 projects into the cavity.
    translate([88.6,7.0,daughter_under_z])
        cube([outer_x+outer_w-88.6,2.0,2.6]);
}

module carrier_bottom_fence() {
    // Withdrawal loads go straight into this integral shell block. It starts
    // beyond the main PCB's 17.3 edge, keeping rear assembly insertion clear.
    // Carrier travel is limited to 0.45 before the top ledges can disengage.
    translate([73.0,17.5,daughter_under_z])
        cube([2.0,outer_y+outer_h-17.5,2.6]);
}

module shell() {
    difference() {
        union() {
            difference() {
                rounded_box([outer_x,outer_y,0],
                            [outer_w,outer_h,back_inside_z],corner_radius);
                rounded_box([front_window_x,front_window_y,-eps],
                            [front_window_w,front_window_h,
                             back_inside_z+2*eps],0.3);
                rounded_box([window_x,window_y,led_back_z+1.2],
                            [window_w,window_h,back_inside_z],0.3);
            }
            front_body_shoulders();
            main_front_rails();
            carrier_right_fence();
            carrier_bottom_fence();
        }
        port_well();
        // Pry recess for removing the friction-fit back; no PCB screw holes.
        translate([cx-4.0,outer_y-eps,back_inside_z-0.9])
            cube([8.0,wall+0.4,1.0]);
    }
}

module stop_post(x,y,z_contact,w=2.8,d=1.2) {
    // The contact end touches only the selected bare PCB perimeter.
    // A small gap avoids deliberate clamp force until printer fit is checked.
    hull() {
        translate([x-w/2,y-d/2,z_contact]) cube([w,d,1.2]);
        translate([x-w/2,y-d/2,back_inside_z-0.1]) cube([w,d,0.2]);
    }
}

module lid() {
    difference() {
        union() {
            rounded_box([outer_x,outer_y,back_inside_z],
                        [outer_w,outer_h,back_t],corner_radius);
            difference() {
                rounded_box([window_x+fit_clearance,
                             window_y+fit_clearance,
                             back_inside_z-lip_depth],
                            [window_w-2*fit_clearance,
                             window_h-2*fit_clearance,lip_depth+eps],0.3);
                rounded_box([window_x+fit_clearance+lip_t,
                             window_y+fit_clearance+lip_t,
                             back_inside_z-lip_depth-eps],
                            [window_w-2*(fit_clearance+lip_t),
                             window_h-2*(fit_clearance+lip_t),
                             lip_depth+3*eps],0.2);
            }
            // Main PCB stops avoid the right-hand carrier and all SMD parts.
            for (x=[3.0,35.0,53.0],y=[0.65,16.65])
                stop_post(x,y,main_back_z+pcb_stop_clearance);
            // Two top stops plus the lower-left broad roof retain the board.
            for (p=[[74.5,0.55],[86.6,0.55]])
                stop_post(p[0],p[1],daughter_rear_z+pcb_stop_clearance);
            lid_carrier_cradle();
        }
        port_well();
    }
}

module led_preview() {
    for (m=[0:6]) {
        x=6.1+module_pitch*m;
        color([0.75,0.73,0.67])
            translate([x-led_w/2,cy-led_h/2,0]) cube([led_w,led_h,led_t]);
        color([0.015,0.015,0.018])
            translate([x-led_w/2,cy-led_h/2,-0.03]) cube([led_w,led_h,0.04]);
        for (c=[0:4],r=[0:6])
            color([0.8,0.8,0.76])
                translate([x-5.08+2.54*c,cy-7.62+2.54*r,-0.05])
                    cylinder(h=0.03,r=0.95);
        // Illustrative lead envelopes. Actual PCB renders contain the pin model.
        for (px=[-3.81,3.81],row=[0:5])
            color([0.65,0.67,0.68])
                translate([x+px,cy-6.35+2.54*row,led_back_z])
                    cylinder(h=main_back_z+1.0-led_back_z,r=0.25);
    }
}

module electronics_preview() {
    led_preview();
    color([0.02,0.32,0.15])
        translate([0,0,main_front_z]) cube([main_w,main_h,main_t]);
    color([0.04,0.40,0.20])
        translate([daughter_xy[0],daughter_xy[1],daughter_under_z])
            cube([daughter_w,daughter_h,daughter_t]);
    color([0.68,0.7,0.73])
        difference() {
            translate([usb_x-usb_w/2,usb_y-usb_depth/2,daughter_rear_z])
                cube([usb_w,usb_depth,usb_height]);
            translate([usb_x-8.34/2,usb_face_y-2.5,
                       usb_port_z-2.56/2])
                cube([8.34,2.5+eps,2.56]);
        }
    // Mated JST carrier envelope; extra 2 mm housing extends left of header.
    color([0.9,0.9,0.85])
        translate([70.675,1.25,daughter_rear_z]) cube([6.25,8.0,2.95]);
    // Main vertical BM06B header plus plain SHR-06V-S mated housing.
    // It is left of the carrier, with wires bent toward the free left length.
    color([0.9,0.9,0.85])
        translate([67.1,8.2,main_back_z]) cube([2.9,8.0,6.3]);
    // Transparent free-space reservation for the 30-50 mm six-wire loop.
    // It is not an assertion that a particular purchased cable already fits.
    color([0.95,0.55,0.15,0.18])
        translate([54.0,2.0,14.0]) cube([13.0,13.0,4.7]);
}

module assembled() {
    color([0.1,0.1,0.11]) shell();
    color([0.12,0.18,0.28,0.30]) lid();
    if (show_electronics) electronics_preview();
}

module clearance_envelopes() {
    // Shrink intended contact faces by0.02 mm, so the collision test checks
    // positive-volume clashes instead of exporting coincident support planes.
    for (m=[0:6])
        translate([6.1+module_pitch*m-led_w/2+eps,cy-led_h/2+eps,eps])
            cube([led_w-2*eps,led_h-2*eps,led_t-2*eps]);
    translate([eps,eps,main_front_z+eps])
        cube([main_w-2*eps,main_h-2*eps,main_t-2*eps]);
    translate([daughter_xy[0]+eps,daughter_xy[1]+eps,daughter_under_z+eps])
        cube([daughter_w-2*eps,daughter_h-2*eps,daughter_t-2*eps]);
    translate([usb_x-usb_w/2+eps,usb_y-usb_depth/2+eps,daughter_rear_z+eps])
        cube([usb_w-2*eps,usb_depth-2*eps,usb_height-2*eps]);
    translate([70.675+eps,1.25+eps,daughter_rear_z+eps])
        cube([6.25-2*eps,8.0-2*eps,2.95-2*eps]);
    translate([67.1+eps,8.2+eps,main_back_z+eps])
        cube([2.9-2*eps,8.0-2*eps,6.3-2*eps]);
    for (m=[0:6],px=[-3.81,3.81],row=[0:5])
        translate([6.1+module_pitch*m+px,cy-6.35+2.54*row,led_back_z+eps])
            cylinder(h=main_back_z+1.0-led_back_z-2*eps,r=0.25-eps,$fn=12);
}

if (view == "shell") shell();
else if (view == "lid") translate([0,0,total_depth]) mirror([0,0,1]) lid();
else if (view == "exploded") {
    color([0.1,0.1,0.11]) shell();
    color([0.12,0.18,0.28]) translate([0,0,10]) lid();
    if (show_electronics) electronics_preview();
}
else if (view == "section")
    intersection() {
        assembled();
        translate([72.0,outer_y-1,-1]) cube([20,outer_h+2,total_depth+2]);
    }
else if (view == "front-preview") rotate([180,0,0]) assembled();
else if (view == "interference")
    intersection() {
        union() { shell(); lid(); }
        clearance_envelopes();
    }
else if (view == "shell-lid-interference")
    intersection() {
        shell(); lid();
        // Ignore the intended contact plane at the rear split.
        translate([outer_x-1,outer_y-1,-1])
            cube([outer_w+2,outer_h+2,back_inside_z+1-eps]);
    }
else assembled();
