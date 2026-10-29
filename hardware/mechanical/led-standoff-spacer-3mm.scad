// Removable assembly tool. Print TWO. No rail stays inside the finished unit.
// Working bar:100 x1 x3 mm. Use the3 mm side to set the LED/PCB air gap.
// The supplied STL lies on that3 mm side for printing; turn it on edge to use.
print_orientation = true;
module spacer() {
    union() {
        translate([-8,0,0]) cube([100,1,3]);
        translate([-15,0,0]) cube([7,3,3]); // Handle outside the left LED edge.
    }
}
if (print_orientation) translate([15,3,0]) rotate([90,0,0]) spacer();
else spacer();
// Assembly: rail lower y=3.07 and13.23, centres3.57 and13.73.
// Set original z=6.3..9.3 in the enclosure stack, then pull left after soldering.
