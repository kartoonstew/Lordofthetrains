// Terrain helpers: hills and mounds as printable solids.

// Solid whose top surface is z = f(x, y) over the rectangle [x0, x1] x [y0, y1],
// with a flat bottom at z0. f must stay above z0 everywhere; it is clamped to z0 + 0.01.
module heightfield(f, x0, y0, x1, y1, z0, step = 1) {
    nx = ceil((x1 - x0) / step);
    ny = ceil((y1 - y0) / step);
    sx = (x1 - x0) / nx;
    sy = (y1 - y0) / ny;
    n = (nx + 1) * (ny + 1);
    id = function(i, j) j * (nx + 1) + i;

    top = [for (j = [0:ny], i = [0:nx])
        let (x = x0 + i * sx, y = y0 + j * sy) [x, y, max(f(x, y), z0 + 0.01)]];
    bottom = [for (p = top) [p.x, p.y, z0]];

    // Faces wind clockwise as seen from outside.
    faces = concat(
        [for (j = [0:ny - 1], i = [0:nx - 1]) each [
            [id(i, j), id(i, j + 1), id(i + 1, j + 1)],
            [id(i, j), id(i + 1, j + 1), id(i + 1, j)]]],
        [for (j = [0:ny - 1], i = [0:nx - 1]) each [
            [n + id(i, j), n + id(i + 1, j + 1), n + id(i, j + 1)],
            [n + id(i, j), n + id(i + 1, j), n + id(i + 1, j + 1)]]],
        [for (i = [0:nx - 1]) [id(i, 0), id(i + 1, 0), n + id(i + 1, 0), n + id(i, 0)]],
        [for (i = [0:nx - 1]) [id(i + 1, ny), id(i, ny), n + id(i, ny), n + id(i + 1, ny)]],
        [for (j = [0:ny - 1]) [id(0, j + 1), id(0, j), n + id(0, j), n + id(0, j + 1)]],
        [for (j = [0:ny - 1]) [id(nx, j), id(nx, j + 1), n + id(nx, j + 1), n + id(nx, j)]]
    );
    polyhedron(concat(top, bottom), faces);
}

// 1 inside fraction p of the radius, easing to 0 at d = 1 with zero slope at both ends.
function plateau(d, p) =
    d <= p ? 1
  : d >= 1 ? 0
  : 0.5 + 0.5 * cos(180 * (d - p) / (1 - p));

// Superellipse distance: 1 on the boundary. e = 2 is an ellipse; larger is boxier.
function superellipse_dist(x, y, c, r, e) =
    pow(pow(abs(x - c.x) / r.x, e) + pow(abs(y - c.y) / r.y, e), 1 / e);

function lump(x, y, c, r, h) = h * exp(-(pow(x - c.x, 2) + pow(y - c.y, 2)) / (r * r));

// Cosine ease: 0 for t <= 0, 1 for t >= 1, zero slope at both ends.
function ease(t) = t <= 0 ? 0 : t >= 1 ? 1 : 0.5 - 0.5 * cos(180 * t);
// Ease from 0 at v = a to 1 at v = b.
function ramp(v, a, b) = ease((v - a) / (b - a));

// Smooth min/max: blend the crease where two surfaces meet over a width of about k.
function smin(a, b, k) = let (h = max(k - abs(a - b), 0) / k) min(a, b) - h * h * k / 4;
function smax(a, b, k) = -smin(-a, -b, k);

// Sum of v[0..i].
function sum_to(v, i) = i < 0 ? 0 : v[i] + sum_to(v, i - 1);
