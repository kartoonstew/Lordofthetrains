// Bag End: Bilbo Baggins's hobbit hole under The Hill, Hobbiton.
//
// HO scale (1:87), modelled on the Hobbiton Movie Set (photos in refs/). The
// facade proportions are measured from those photos in units of the door
// diameter D; the hill and garden are compressed to fit the footprint.
// Print upright on the base, no supports. All dimensions in mm; z = 0 is the
// underside of the base. Heights in [Levels] are above the lane (base top).

include <../../../lib/ho.scad>
include <../../../lib/terrain.scad>

/* [Variant] */
// Hollow behind the round windows, open underneath, so LEDs can light them.
interior_light = false;
// Preview-only scale props (hobbit, wizard, track, oak). Never export with this on.
show_props = false;

/* [Scale] */
// Door diameter. The whole facade scales from this: 18 mm is about 1.57 m.
D = 18;

/* [Footprint] */
base_w = 135;
base_d = 97;
base_t = 2;
base_corner_r = 6;
wall_y = 11;            // front face of the dry-stone wall; the lane is in front of it

/* [Levels] */
garden_h = 6;           // garden at the top of the dry-stone wall
landing_h = 15;         // flagstone landing at the door
patio_h = 7;            // bench patio, lower right

/* [Layout] */
door_x = 54;
door_y = 46;            // facade line of the door bay
win_dx = 2.45 * D;      // window bay centre, right of the door
win_dy = 2;             // window bay is set back into the hill...
win_rise = 4.5;         // ...and sits higher on the bank
win_yaw = -5;
step_x = door_x + 1.5;
step_w = 8;

/* [Detail] */
groove_w = 0.4;
groove_d = 0.3;

/* [Hidden] */
$fn = 64;

// --- Proportions measured from refs/01, 02 and 03 (units of D) --------------
// Door bay: three facets; the side ones angle back into the hill.
// [centre half-width, side facet length, side angle, eave top at the ends,
//  at the inner posts, at the centre, floor drop toward the front, over this distance]
DOOR_BAY = [0.55 * D, 0.5 * D, 25, 21.0, 22.5, 26.2, 0, 1];
// Window bay: one flat facet, on a bank that falls away in front of it.
WIN_BAY = [0.6 * D, 0, 0, 16.5, 16.5, 22.5, -8, 18];

sill_h = 0.6;
door_cz = sill_h + D / 2;     // a full circle resting on the sill
door_recess = 2.2;
frame_w = 0.05 * D;           // grey timber ring lining the doorway
brick_w = 0.085 * D;          // brick arch: this at the sides...
brick_lift = 0.8;             // ...thicker at the crown
porthole_r = 0.115 * D;       // glass; brick ring outer is about 0.42 D across
porthole_cz = 13.7;           // about 0.75 D above the sill
win_r = 0.3 * D;              // big round window, refs/03 and 05
win_cz = 10.6;                // above the window bay floor

eave_p = 2.5;                 // eave projection; underside slopes at 45 degrees
eave_t = 1.2;                 // fascia depth
post_w = 1.1;
post_proud = 0.5;
bank_angle = 45;              // grass banks rising beside the dug-out bays

hill_h = landing_h + 1.75 * D;          // crest above the lane, refs/03
land_y = door_y - 7;                    // where the landing starts
rise = landing_h / 6;                   // six steps from the lane to the landing
tread = (land_y - wall_y) / 6;
oak_at = [door_x + 3, door_y + 15];     // trunk sits almost over the door
chimney_at = [door_x + 46, door_y + 24];

// --- Ground ------------------------------------------------------------------

// Garden: rises from the wall to the landing, and fades out at the side and back
// edges so the piece blends into a layout.
function garden(x, y) =
    min(ramp(x, 1, 17), ramp(base_w - x, 1, 17), ramp(base_d - y, 1, 17))
    * (garden_h + (landing_h - garden_h) * ramp(y, wall_y, land_y));

function hill(x, y) =
    let (m = ramp(x, door_x - 56, door_x - 8) * ramp(base_w - x, 3, 29)
           * ramp(y, door_y - 16, door_y + 4) * ramp(base_d - y, 3, 24))
    m * (hill_h + lump(x, y, [door_x + 2, door_y + 22], 18, 2.5)
                - lump(x, y, [door_x + 30, door_y + 30], 12, 2));

// --- Bays --------------------------------------------------------------------
// A bay is modelled in a local frame: centre facet on y = 0, wall at +y, the
// viewer at -y, z = 0 at the bay floor.

function bay_xo(b) = b[0] + b[1] * cos(b[2]);
function bay_yo(b) = b[1] * sin(b[2]);

DOOR_AT = [door_x, door_y, landing_h, 0];                         // [x, y, floor, yaw]
WIN_AT = [door_x + win_dx, door_y + win_dy, landing_h + win_rise, win_yaw];

// The hill dug out in front of a bay: the bay's floor straight ahead, grass
// banks rising to either side. Right beside the bay the bank comes up to the
// end of the eave and slopes down toward the front (refs/01, 03). Behind the
// eave line the hill is left alone.
function dig(b, at, x, y) =
    let (dx = x - at.x, dy = y - at.y,
         u = dx * cos(at[3]) + dy * sin(at[3]),
         v = -dx * sin(at[3]) + dy * cos(at[3]),
         ve = -eave_p - 0.4,
         du = max(0, abs(u) - bay_xo(b)),
         floor = at.z + b[6] * ramp(-v, -ve, b[7]),
         cheek_h = b[3] + 1)
    v >= ve ? 1e9
  : floor + tan(bank_angle) * du
          + cheek_h * ramp(du, 0, 5) * ramp(v, ve - cheek_h / tan(60), ve);

function ground(x, y) = max(0.6, smin(
    smax(garden(x, y), hill(x, y), 3),
    min(dig(DOOR_BAY, DOOR_AT, x, y), dig(WIN_BAY, WIN_AT, x, y)), 2));

// Top of the eave along the bay: an arch over the centre facet, sloping side eaves.
function eave_top(b, x) =
    let (ax = abs(x), c = b[0], xo = bay_xo(b))
    ax <= c ? b[4] + (b[5] - b[4]) * pow(max(0, 1 - pow(ax / c, 2)), 0.35)
            : b[3] + (b[4] - b[3]) * (xo - ax) / max(xo - c, 0.001);

// Where the eave's sloping underside meets the wall.
function eave_under(b, x) = eave_top(b, x) - eave_t - eave_p;

// Move to a point on a side facet: side = -1 or 1, t = 0 at the inner post, 1 at the end.
module on_side(b, side, t) {
    translate([side * (b[0] + t * b[1] * cos(b[2])), t * b[1] * sin(b[2]), 0])
        rotate([0, 0, side * b[2]]) children();
}

module bay_elevation(b, bottom, n = 60) {
    xo = bay_xo(b);
    polygon(concat([[-xo, bottom]], [for (i = [0:n]) let (x = -xo + 2 * xo * i / n) [x, eave_top(b, x)]], [[xo, bottom]]));
}

// Extrude a 2D (x, z) shape along y, from y0 to y1.
module y_extrude(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();

module ytube(r, y0, y1) translate([0, y0, 0]) rotate([-90, 0, 0]) cylinder(r = r, h = y1 - y0);

// The plastered wall mass behind the facets, up to the eave.
module bay_block(b) {
    xo = bay_xo(b);
    yo = bay_yo(b);
    intersection() {
        translate([0, 0, -8]) linear_extrude(80)
            polygon([[-xo, yo], [-b[0], 0], [b[0], 0], [xo, yo], [xo, yo + 14], [-xo, yo + 14]]);
        y_extrude(-1, yo + 15) offset(delta = 0.05) bay_elevation(b, -8);
    }
}

// Square up the dig: vertical faces from the bay floor to the eave, just in
// front of the eave line, where the heightfield can only manage a slope.
module bay_cut(b) {
    y_extrude(-eave_p - 2, bay_yo(b) + 0.01) bay_elevation(b, 0, 40);
}

// Eave: a curved fascia with a 45 degree underside, swept along each facet.
module eave_slice(z) {
    translate([0, 0, z]) rotate([90, 0, 90]) linear_extrude(0.01)
        polygon([[1, 0], [-eave_p, 0], [-eave_p, -eave_t], [1, -eave_t - eave_p - 1]]);
}

module bay_eave(b, n = 30) {
    c = b[0];
    for (i = [0 : n - 1]) hull() for (x = [-c + 2 * c * i / n, -c + 2 * c * (i + 1) / n])
        translate([x, 0, 0]) eave_slice(eave_top(b, x));
    if (b[1] > 0) for (side = [-1, 1], i = [0 : 9]) hull() for (t = [i / 10, (i + 1) / 10])
        on_side(b, side, t) eave_slice(eave_top(b, side * (b[0] + t * b[1] * cos(b[2]))));
}

module post(b, x, h0) {
    translate([-post_w / 2, -post_proud, h0]) cube([post_w, post_proud + 1, eave_under(b, x) - h0 + 0.6]);
}

module bay_posts(b, inner_from = -1) {
    c = b[0];
    for (side = [-1, 1]) {
        translate([side * c, 0, 0]) rotate([0, 0, side * b[2] / 2]) post(b, c, inner_from);
        if (b[1] > 0) on_side(b, side, 1) translate([-side * post_w / 2, 0, 0]) post(b, bay_xo(b), -1);
    }
}

// Annulus along y, clipped to z >= 0 so rings stop at the floor.
module ring(r0, r1, y0, y1, cz) {
    intersection() {
        translate([0, 0, cz]) difference() { ytube(r1, y0, y1); ytube(r0, y0 - 1, y1 + 1); }
        translate([-50, -10, 0]) cube([100, 20, 100]);
    }
}

// Brick arch round an opening: outer edge lifted so it is thicker at the crown.
module brick_arch(r0, w, cz) {
    intersection() {
        difference() {
            translate([0, 0, cz + brick_lift]) ytube(r0 + w, -0.45, 1);
            translate([0, 0, cz]) ytube(r0, -2, 2);
        }
        translate([-50, -10, 0]) cube([100, 20, 100]);
    }
}

module brick_joints(r0, w, cz, n) {
    for (a = [0 : 360 / n : 359]) translate([0, 0, cz]) rotate([0, a, 0])
        translate([r0 + 0.1, -1, -groove_w / 2]) cube([w + brick_lift + 1, 1 - 0.45 + 0.25, groove_w]);
}

// --- Door bay ----------------------------------------------------------------

module at_door_bay() translate([door_x, door_y, base_t + landing_h]) children();

module door_bay_body() {
    b = DOOR_BAY;
    color("#d9b65a") bay_block(b);
    color("#5a4632") { bay_eave(b); bay_posts(b, door_cz + 4); }
    color("#8a8478") ring(D / 2, D / 2 + frame_w, -0.5, 1, door_cz);
    color("#9c4a3a") brick_arch(D / 2 + frame_w, brick_w, door_cz);
    color("#9a9384") translate([-0.45 * D, -1.6, -0.5]) cube([0.9 * D, 2.1, sill_h + 0.5]);
    for (side = [-1, 1]) on_side(b, side, 0.5) {
        color("#2f7a55") ring(porthole_r, porthole_r + 0.5, -0.5, 1, porthole_cz);
        color("#9c4a3a") brick_arch(porthole_r + 0.5, 1.1, porthole_cz);
    }
}

module door_bay_cuts() {
    b = DOOR_BAY;
    color("#2f7a55") translate([0, 0, door_cz]) ytube(D / 2, -3, door_recess);
    color("#2f7a55") intersection() {
        for (x = [-D / 2 + 1.6 : 1.6 : D / 2]) translate([x - groove_w / 2, door_recess - 0.5, 0]) cube([groove_w, 0.85, 30]);
        translate([0, 0, door_cz]) ytube(D / 2 - 0.5, -5, 5);
    }
    color("#9c4a3a") brick_joints(D / 2 + frame_w, brick_w, door_cz, 36);
    for (side = [-1, 1]) on_side(b, side, 0.5) {
        color("#2a3040") translate([0, 0, porthole_cz]) ytube(porthole_r, -3, interior_light ? 7 : 0.8);
        color("#9c4a3a") brick_joints(porthole_r + 0.5, 1.1, porthole_cz, 14);
    }
}

module door_bay_trim() {
    b = DOOR_BAY;
    color("#c9a227") translate([0, door_recess, door_cz]) {
        ytube(1.0, -0.3, 0.1);
        translate([0, -0.9, 0]) sphere(r = 0.7, $fn = 24);
    }
    // Lantern under the eave, just left of centre. Its back touches the wall so
    // it prints standing on the facade rather than starting in mid-air.
    zs = eave_top(b, -1.4) - eave_t - (eave_p - 0.5);
    color("#4a4a45") translate([-1.4, -0.5, zs]) {
        translate([0, 0, -0.8]) cylinder(r = 0.3, h = 1.2, $fn = 12);
        translate([0, 0, -1.4]) cylinder(r1 = 0.95, r2 = 0.4, h = 0.6, $fn = 6);
        translate([0, 0, -3.0]) cylinder(r = 0.75, h = 1.6, $fn = 6);
        translate([0, 0, -3.6]) cylinder(r1 = 0.2, r2 = 0.75, h = 0.6, $fn = 6);
    }
}

// --- Window bay --------------------------------------------------------------

module at_win_bay() {
    translate([door_x + win_dx, door_y + win_dy, base_t + landing_h + win_rise])
        rotate([0, 0, win_yaw]) children();
}

module win_bay_body() {
    b = WIN_BAY;
    color("#d9b65a") bay_block(b);
    color("#5a4632") { bay_eave(b); bay_posts(b); }
    color("#5a4632") ring(win_r, win_r + 0.7, -0.5, 1, win_cz);
    color("#9c4a3a") brick_arch(win_r + 0.7, 1.2, win_cz);
}

module win_bay_cuts() {
    color("#2a3040") translate([0, 0, win_cz]) ytube(win_r, -3, interior_light ? 10 : 1.2);
    color("#9c4a3a") brick_joints(win_r + 0.7, 1.2, win_cz, 30);
}

// Leaded glazing: a square grid in the middle, a ring round it (refs/03, 05).
module win_bay_trim() {
    color("#5a4632") translate([0, 0, win_cz]) intersection() {
        ytube(win_r + 0.1, 0.2, 1.3);
        union() {
            for (v = [-1.8, 1.8]) {
                translate([v - 0.275, 0.2, -win_r]) cube([0.55, 1.1, 2 * win_r]);
                translate([-win_r, 0.2, v - 0.275]) cube([2 * win_r, 1.1, 0.55]);
            }
            difference() { ytube(4.4, 0.2, 1.3); ytube(3.9, 0, 2); }
        }
    }
}

// --- Garden ------------------------------------------------------------------

module steps_channel() {
    for (k = [0:5]) translate([step_x - step_w / 2 - 0.5, wall_y - 1 + k * tread, base_t + (k + 1) * rise])
        cube([step_w + 1, tread + 1, 80]);
}

module steps() {
    jit = rands(-0.5, 0.5, 18, 11);
    color("#9a9384") for (k = [0:5])
        translate([step_x + jit[3 * k], wall_y + k * tread, base_t - 0.01])
            rotate([0, 0, 2 * jit[3 * k + 1]])
                translate([-(step_w + jit[3 * k + 2]) / 2, -0.6, 0])
                    cube([step_w + jit[3 * k + 2], tread + 0.6, (k + 1) * rise + 0.01]);
}

// Irregular flagstones on the landing in front of the door.
module landing_stones() {
    jit = rands(-0.4, 0.4, 24, 21);
    color("#9a9384") for (r = [0:1], c = [0:2]) let (i = r * 3 + c)
        translate([door_x - 7 + c * 4.8 + jit[i], land_y + 0.3 + r * 3.3 + jit[i + 6] / 2, base_t + landing_h - 0.01])
            rotate([0, 0, 6 * jit[i + 12]]) cube([4.2 + jit[i + 18], 2.8, 0.3]);
}

module patio_cut() translate([door_x + 36, wall_y + 2, base_t + patio_h]) cube([26, 12, 80]);

module patio() {
    color("#9a9384") difference() {
        translate([door_x + 36, wall_y + 2, base_t - 0.01]) cube([26, 12, patio_h + 0.3]);
        for (x = [5.5, 11, 17.5, 22]) translate([door_x + 36 + x, wall_y + 1, base_t + patio_h + 0.05]) cube([groove_w, 14, 1]);
        translate([door_x + 35, wall_y + 8, base_t + patio_h + 0.05]) cube([28, groove_w, 1]);
    }
}

// Dry-stone retaining wall along the lane: random rubble below the turf line.
module wall_grooves() {
    heights = rands(1.3, 2.1, 5, 41);
    for (c = [0:3]) {
        z0 = sum_to(heights, c - 1);
        z1 = z0 + heights[c];
        lens = rands(2.2, 4.2, 60, 51 + c);
        for (j = [0:59]) let (xa = sum_to(lens, j - 1) - c * 1.3, xb = xa + lens[j],
                               top = min(ground(xa, wall_y), ground(xb, wall_y)) - 0.4)
            if (xb < base_w && xa > 0 && abs((xa + xb) / 2 - step_x) > step_w / 2 + 1) {
                if (z0 + 0.5 < top)
                    translate([xa - groove_w / 2, wall_y - 1, base_t + z0]) cube([groove_w, 1 + groove_d, min(z1, top) - z0]);
                if (z1 < top)
                    translate([xa, wall_y - 1, base_t + z1 - groove_w / 2]) cube([xb - xa, 1 + groove_d, groove_w]);
            }
    }
}

// Gate at the foot of the steps, with the party sign (refs/04, 05).
module gate() {
    gp = 1.4;
    xl = step_x - step_w / 2 - 0.4 - gp;
    xr = step_x + step_w / 2 + 0.4;
    y = wall_y - 2;
    color("#6b5238") translate([0, y, base_t - 0.01]) {
        for (x = [xl, xr]) translate([x, 0, 0]) {
            cube([gp, gp, 11]);
            translate([gp / 2, gp / 2, 11.6]) sphere(r = 0.9, $fn = 24);
        }
        translate([xl + gp, gp / 2 - 0.4, 0]) {
            w = xr - xl - gp;
            for (z = [0.8, 4.2, 7.4]) translate([0, 0, z]) cube([w, 0.8, 0.8]);
            for (x = [0, w - 0.8]) translate([x, 0, 0.8]) cube([0.8, 0.8, 7.4]);
            for (s = [0, 1]) hull() {
                translate([s * (w - 0.8), 0, 7.4]) cube([0.8, 0.8, 0.8]);
                translate([w / 2 - 0.4, 0, 9.6]) cube([0.8, 0.8, 0.8]);
            }
        }
    }
    color("#ece6d6") translate([step_x - 3.4, y + gp / 2 - 0.9, base_t + 2.6]) cube([6.8, 0.5, 3.4]);
}

// Barrel letterbox on a post beside the gate.
module letterbox() {
    x = step_x - step_w / 2 - 4.5;
    color("#6b5238") translate([x, wall_y - 2.6, base_t - 0.01]) {
        translate([-0.6, -0.6, 0]) cube([1.2, 1.2, 7]);
        translate([0, -1.6, 8]) rotate([-90, 0, 0]) cylinder(r = 1.3, h = 3.4, $fn = 24);
    }
}

// Low woven fence along the top of the wall, left of the gate.
module wattle() {
    xs = [for (x = [4 : 3.2 : step_x - step_w / 2 - 7]) x];
    y = wall_y + 1.4;
    color("#8a6e4b") {
        for (x = xs) translate([x - 0.4, y - 0.4, base_t + ground(x, y) - 2]) cube([0.8, 0.8, 6.5]);
        for (i = [0 : len(xs) - 2], h = [1.4, 2.8, 4.0]) hull()
            for (x = [xs[i], xs[i + 1]]) translate([x - 0.3, y - 0.3, base_t + ground(x, y) + h]) cube([0.6, 0.6, 0.6]);
    }
}

module flower_pots() {
    color("#c0623a") for (side = [-1, 1]) translate([door_x + side * 12.5, door_y - 3, base_t + landing_h - 0.01])
        difference() {
            cylinder(r1 = 1.7, r2 = 2.3, h = 3);
            translate([0, 0, 2.5]) cylinder(r = 1.8, h = 1);
        }
}

// Lamp post at the left of the landing (refs/07).
module lamp_post() {
    p = [door_x - 22, door_y - 14];
    color("#4a4a45") translate([p.x, p.y, base_t + ground(p.x, p.y) - 2]) {
        translate([-0.6, -0.6, 0]) cube([1.2, 1.2, 15]);
        translate([0, 0, 15]) cylinder(r = 1.1, h = 2, $fn = 6);
        translate([0, 0, 17]) cylinder(r1 = 1.5, r2 = 0.2, h = 1.2, $fn = 6);
    }
}

// Birdhouse on a pole in front of the window bay (refs/05).
module birdbox() {
    p = [door_x + 38, 27];
    color("#7a6248") translate([p.x, p.y, base_t + ground(p.x, p.y) - 4]) {
        translate([-0.6, -0.6, 0]) cube([1.2, 1.2, 18]);
        translate([0, 0, 17]) cylinder(r1 = 0.9, r2 = 1.4, h = 0.5, $fn = 6);
        translate([0, 0, 17.5]) cylinder(r = 1.4, h = 2.6, $fn = 6);
        translate([0, 0, 20.1]) cylinder(r1 = 1.9, r2 = 0.2, h = 1.7, $fn = 6);
    }
}

module bench() {
    l = 15;
    color("#9a7a52") translate([door_x + 46, wall_y + 9.5, base_t + patio_h + 0.3]) {
        for (x = [-l / 2, l / 2 - 1.2]) translate([x, -2, 0]) cube([1.2, 4, 5.2]);
        translate([-l / 2, -2.2, 4.4]) cube([l, 4.2, 0.8]);
        translate([-l / 2, 1.2, 5.2]) cube([l, 0.8, 3.8]);
    }
}

module planter() {
    color("#7a6248") translate([door_x + 56, wall_y + 6, base_t + patio_h + 0.3]) difference() {
        cube([4.5, 4.5, 3]);
        translate([0.6, 0.6, 2.4]) cube([3.3, 3.3, 1]);
    }
}

// --- On the hill ---------------------------------------------------------------

module chimney() {
    z = base_t + ground(chimney_at.x, chimney_at.y);
    s = 5.4;
    color("#9c4a3a") translate([chimney_at.x, chimney_at.y, z - 5]) difference() {
        union() {
            translate([-s / 2, -s / 2, 0]) cube([s, s, 14]);
            translate([0, 0, 14]) rotate([0, 0, 45]) cylinder(r1 = s / sqrt(2), r2 = s / sqrt(2) + 0.6, h = 0.6, $fn = 4);
            translate([-s / 2 - 0.6, -s / 2 - 0.6, 14.6]) cube([s + 1.2, s + 1.2, 0.8]);
            translate([-1.2, -1.2, 15.4]) cube([2.4, 2.4, 1.4]);
        }
        translate([0, 0, 15]) cylinder(r = 0.7, h = 3);
        for (zz = [6.2 : 1.7 : 13]) translate([-s, -s, zz]) difference() {
            cube([2 * s, 2 * s, groove_w]);
            translate([s / 2 + groove_d, s / 2 + groove_d, -1]) cube([s - 2 * groove_d, s - 2 * groove_d, 2]);
        }
    }
}

module oak_socket() {
    translate([oak_at.x, oak_at.y, base_t + ground(oak_at.x, oak_at.y) - 12]) cylinder(r = 1.65, h = 30);
}

// --- LED cavities (interior_light) -------------------------------------------
// Rooms behind the round windows, open to the underside. Gable roofs at 45
// degrees print without support.

// [half-width, front, back, eave height] in the bay's local frame.
DOOR_CAVITY = [bay_xo(DOOR_BAY) - 3, 4.5, 15, 12];
WIN_CAVITY = [WIN_BAY[0] - 3, 3.5, 14, 13];

function cavity_roof(c, v) = c[3] + min(v - c[1], c[2] - v);

module cavity(c, floor) {
    below = base_t + floor + 1;
    translate([0, 0, -below]) rotate([90, 0, 90]) linear_extrude(2 * c[0], center = true)
        polygon([[c[1], 0], [c[2], 0], [c[2], below + c[3]],
                 [(c[1] + c[2]) / 2, below + cavity_roof(c, (c[1] + c[2]) / 2)], [c[1], below + c[3]]]);
}

module light_cavities() {
    at_door_bay() cavity(DOOR_CAVITY, DOOR_AT.z);
    at_win_bay() cavity(WIN_CAVITY, WIN_AT.z);
}

// --- Checks --------------------------------------------------------------------

function to_world(at, u, v) = [at.x + u * cos(at[3]) - v * sin(at[3]), at.y + u * sin(at[3]) + v * cos(at[3])];

// Turf must cover the top of each bay's wall mass, not leave it poking out.
function bay_cover(b, at) = min([
    for (u = [-bay_xo(b) : 2 : bay_xo(b)], v = [bay_yo(b) + 2 : 3 : bay_yo(b) + 14])
        let (p = to_world(at, u, v)) ground(p.x, p.y) - (at.z + eave_top(b, u))]);
door_cover = bay_cover(DOOR_BAY, DOOR_AT);
win_cover = bay_cover(WIN_BAY, WIN_AT);
echo(door_cover = door_cover, win_cover = win_cover);
assert(door_cover >= 1, "hill too low over the door bay");
assert(win_cover >= 1, "hill too low over the window bay");

// The hill over each LED cavity must leave a printable shell.
function cavity_cover(c, at) = min([
    for (u = [-c[0] : 1 : c[0]], v = [c[1] : 1 : c[2]])
        let (p = to_world(at, u, v)) ground(p.x, p.y) - (at.z + cavity_roof(c, v))]);
if (interior_light) {
    covers = [cavity_cover(DOOR_CAVITY, DOOR_AT), cavity_cover(WIN_CAVITY, WIN_AT)];
    echo(cavity_cover = covers);
    assert(min(covers) >= 2, "hill too thin over an LED cavity");
}

// --- Assembly ------------------------------------------------------------------

module footprint() offset(r = base_corner_r) offset(delta = -base_corner_r) square([base_w, base_d]);

module base() {
    hull() {   // 0.4 mm chamfer on the bottom edge against elephant's foot
        linear_extrude(0.01) offset(delta = -0.4) footprint();
        translate([0, 0, 0.4]) linear_extrude(base_t - 0.4) footprint();
    }
}

module terrain() {
    intersection() {
        heightfield(function(x, y) base_t + ground(x, y), 0, wall_y, base_w, base_d, base_t - 0.5, 0.8);
        linear_extrude(200) footprint();
    }
}

module bag_end() {
    difference() {
        union() {
            difference() {
                union() { color("#a08c6a") base(); color("#6f8f3a") terrain(); }
                color("#6f8f3a") { at_door_bay() bay_cut(DOOR_BAY); at_win_bay() bay_cut(WIN_BAY); }
                color("#6f8f3a") steps_channel();
                color("#6f8f3a") patio_cut();
                color("#8a8070") wall_grooves();
            }
            at_door_bay() door_bay_body();
            at_win_bay() win_bay_body();
        }
        at_door_bay() door_bay_cuts();
        at_win_bay() win_bay_cuts();
        oak_socket();
        if (interior_light) light_cavities();
    }
    at_door_bay() door_bay_trim();
    at_win_bay() win_bay_trim();
    steps();
    landing_stones();
    patio();
    gate();
    letterbox();
    wattle();
    flower_pots();
    lamp_post();
    birdbox();
    bench();
    planter();
    chimney();
}

// The oak over Bag End: a short thick trunk, limbs spreading almost flat, and a
// broad low crown about 4.3 D across (refs/03, 10).
module oak() {
    limbs = [[15, 72, 30], [80, 76, 24], [150, 70, 34], [215, 74, 26], [285, 78, 30], [330, 68, 20]];
    color("#4f3f2e") {
        cylinder(h = 16, r1 = 3.6, r2 = 2.4);
        for (l = limbs) translate([0, 0, 13]) rotate([0, 0, l[0]]) rotate([0, l[1], 0]) cylinder(h = l[2], r1 = 1.5, r2 = 0.4);
    }
    blobs = rands(0, 1, 60, 3);
    color("#4c6e34") for (i = [0:19]) let (a = 360 * blobs[3 * i], d = 8 + 30 * blobs[3 * i + 1], r = 7 + 5 * blobs[3 * i + 2])
        translate([d * cos(a), d * sin(a) * 0.7, 22 + 8 * (1 - d / 38)]) scale([1, 1, 0.45]) sphere(r = r);
}

module props() {
    translate([door_x - 4, door_y - 5, base_t + landing_h]) ho_figure(HO_HOBBIT, body = "#7a6a3a");
    translate([step_x + 16, wall_y - 5, base_t]) ho_figure(ho(1.9), body = "#8d8f96", hat = true);
    translate([-10, -22, -1.6]) ho_track(base_w + 20);
    translate([oak_at.x, oak_at.y, base_t + ground(oak_at.x, oak_at.y) - 10]) oak();
}

bag_end();
if (show_props) props();
