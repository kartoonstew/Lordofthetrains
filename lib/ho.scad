// Shared HO scale (1:87) constants and preview-only scale props.
// All lengths are millimetres at model scale unless the name says otherwise.

HO_RATIO = 87;

function ho(meters) = meters * 1000 / HO_RATIO;
function ho_ft(feet) = ho(feet * 0.3048);

HO_GAUGE = 16.5;          // track gauge, between the rail heads
HO_PERSON = ho(1.75);     // ~20 mm
HO_HOBBIT = ho(1.07);     // ~12 mm, three and a half feet

// ---------------------------------------------------------------------------
// Preview props. Use them in renders to judge scale; never export them.

module ho_figure(height = HO_PERSON, body = "#6b5a45", hat = false) {
    color(body) cylinder(h = 0.84 * height, r1 = 0.14 * height, r2 = 0.10 * height, $fn = 24);
    color("#e2c4a4") translate([0, 0, 0.9 * height]) sphere(r = 0.08 * height, $fn = 24);
    if (hat) color("#7d7f86") translate([0, 0, 0.95 * height]) {
        cylinder(h = 0.02 * height, r = 0.16 * height, $fn = 24);
        cylinder(h = 0.3 * height, r1 = 0.08 * height, r2 = 0, $fn = 24);
    }
}

// Straight run of code 83 track along +x, centred on y = 0, sitting on z = 0.
module ho_track(length) {
    tie_pitch = ho_ft(1.8);
    color("#4a3b2f") for (x = [tie_pitch / 2 : tie_pitch : length])
        translate([x - 1.1, -15, 0]) cube([2.2, 30, 1.6]);
    color("#8c8c8c") for (side = [-1, 1])
        translate([0, side * (HO_GAUGE / 2 + 0.4) - 0.4, 1.6]) cube([length, 0.8, 2.1]);
}
