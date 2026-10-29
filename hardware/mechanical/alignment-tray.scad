// Temporary face-down soldering alignment tray; dimensions in millimetres.
// Seven LED modules sit in one uninterrupted pocket, with their pins upward.
pocket_length = 90.6;
pocket_width = 18.6;
floor_thickness = 1.2;
wall_thickness = 1.6;
wall_height = 3.0; // Height ABOVE the floor.

assert(pocket_length > 0 && pocket_width > 0);
assert(floor_thickness > 0 && wall_thickness > 0 && wall_height > 0);

difference() {
    cube([pocket_length + 2 * wall_thickness,
          pocket_width + 2 * wall_thickness,
          floor_thickness + wall_height]);
    translate([wall_thickness, wall_thickness, floor_thickness])
        cube([pocket_length, pocket_width, wall_height + 0.1]);
}
