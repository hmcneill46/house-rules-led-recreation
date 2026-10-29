// House Rules test tool, NOT a manufacturing PCB or a fit guarantee.
// Millimetres. Print at 100% scale. The PCB's finished holes are 0.9 mm.
// Default 1.0 mm PRINT holes allow printer clearance and do not prove 0.9 fit.
part = "plate"; // plate, scale, both
print_hole_diameter = 1.0;
plate_thickness = 1.0;
$fn = 32;

assert(print_hole_diameter > 0 && print_hole_diameter < 2.0);
assert(plate_thickness > 0);

module pin_fit_plate() {
    difference() {
        cube([88.4,17.3,plate_thickness]);
        for (m=[0:6], side=[-1,1], row=[0:5])
            translate([6.1+12.7*m+side*3.81,
                       8.65-6.35+2.54*row,-0.1])
                cylinder(d=print_hole_diameter,h=plate_thickness+0.2);
    }
}

module external_scale_coupon() {
    // Separate 50.00 x 10.00 coupon checks slicer X and Y scaling with calipers.
    cube([50,10,plate_thickness]);
}

if (part == "scale") external_scale_coupon();
else if (part == "both") {
    pin_fit_plate();
    translate([19.2,22.3,0]) external_scale_coupon();
}
else pin_fit_plate();
