#!/usr/bin/env python3
"""Flow-field generative art. Particles ride a pseudo-noise field, trace
curving ink lines. Each run unique. Writes flowfield.svg."""
import math
import random
import sys

W, H = 1200, 1600
N_PARTICLES = 1400
STEPS = 220
STEP_LEN = 4.0
MARGIN = 60

# ---- value-noise: hashed lattice + smooth interp. no deps. ----
SEED = random.randint(0, 1 << 30)
GRID = 0.0035   # field frequency


def _hash(ix, iy):
    h = (ix * 374761393 + iy * 668265263 + SEED * 2654435761) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return (h & 0xFFFF) / 0xFFFF


def _smooth(t):
    # quintic (Perlin's "fade"): 6t^5-15t^4+10t^3. zero 1st+2nd deriv at
    # corners -> no creasing artifacts that smoothstep (3t^2-2t^3) leaves.
    return t * t * t * (t * (t * 6 - 15) + 10)


def noise(x, y):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    sx, sy = _smooth(fx), _smooth(fy)
    a = _hash(ix, iy)
    b = _hash(ix + 1, iy)
    c = _hash(ix, iy + 1)
    d = _hash(ix + 1, iy + 1)
    top = a + (b - a) * sx
    bot = c + (d - c) * sx
    return top + (bot - top) * sy


def angle_at(x, y):
    # two octaves of noise -> swirling field, 0..2pi*~2.5
    n = noise(x * GRID, y * GRID) + 0.5 * noise(x * GRID * 2.3, y * GRID * 2.3)
    return n * math.pi * 2.5


# ---- palette: pick a random hue family, vary lightness ----
def palette():
    base = random.choice([(15, 90, 75), (200, 70, 60), (280, 60, 70),
                          (340, 75, 65), (45, 85, 60), (160, 55, 55)])
    hue, sat, lig = base
    cols = []
    for _ in range(6):
        h = (hue + random.randint(-25, 25)) % 360
        s = max(20, min(95, sat + random.randint(-15, 15)))
        l = max(20, min(85, lig + random.randint(-25, 25)))
        cols.append(f"hsl({h},{s}%,{l}%)")
    return cols


def trace(x, y):
    pts = [(x, y)]
    for _ in range(STEPS):
        a = angle_at(x, y)
        x += math.cos(a) * STEP_LEN
        y += math.sin(a) * STEP_LEN
        if not (MARGIN < x < W - MARGIN and MARGIN < y < H - MARGIN):
            break
        pts.append((x, y))
    return pts


def path_d(pts):
    if len(pts) < 2:
        return ""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for x, y in pts[1:]:
        d += f" L{x:.1f},{y:.1f}"
    return d


def main():
    cols = palette()
    bg = "hsl(0,0%,8%)"
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{bg}"/>',
        '<g fill="none" stroke-linecap="round">',
    ]
    drawn = 0
    for _ in range(N_PARTICLES):
        x = random.uniform(MARGIN, W - MARGIN)
        y = random.uniform(MARGIN, H - MARGIN)
        pts = trace(x, y)
        if len(pts) < 8:
            continue
        c = random.choice(cols)
        sw = random.choice([0.6, 0.9, 1.2, 1.8])
        op = round(random.uniform(0.25, 0.7), 2)
        lines.append(
            f'<path d="{path_d(pts)}" stroke="{c}" '
            f'stroke-width="{sw}" opacity="{op}"/>'
        )
        drawn += 1
    lines.append("</g></svg>")
    with open("flowfield.svg", "w") as f:
        f.write("\n".join(lines))
    print(f"seed={SEED}  lines={drawn}  -> flowfield.svg")


if __name__ == "__main__":
    main()
