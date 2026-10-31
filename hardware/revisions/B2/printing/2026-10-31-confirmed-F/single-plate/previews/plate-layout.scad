// Engineering preview of the actual STL placements. Supports are in the G-code, not shown here.
color([0.25,0.27,0.29]) translate([0,0,-1]) cube([220,220,0.6]);
color([0.68,0.70,0.72]) translate([62.6, 53.15, 0.0]) import("../../../../mechanical/enclosure-B2-PROTOTYPE-shell.stl");
color([0.68,0.70,0.72]) translate([62.6, 91.15, 0.0]) import("../../../../mechanical/enclosure-B2-PROTOTYPE-back.stl");
color([0.68,0.70,0.72]) translate([62.0, 124.0, 0.0]) import("../../models/B2-main-board-fit-1p6mm.stl");
color([0.68,0.70,0.72]) translate([60.0, 155.0, 0.0]) import("../../../../../../mechanical/pin-fit-scale-50mm.stl");
color([0.68,0.70,0.72]) translate([123.0, 151.0, 0.0]) import("../../../../mechanical/case-closure-fit-coupon.stl");
color([0.68,0.70,0.72]) translate([60.0, 179.0, 0.0]) import("../../../../mechanical/mcu-channel-fit-coupon.stl");
color([0.68,0.70,0.72]) translate([100.000000190735, 174.0, 5.72205e-07]) import("../../../../mechanical/mcu-retaining-cap.stl");
