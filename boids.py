#!/usr/bin/env python3
"""Boids flocking. Each bird obeys three classic rules -- separation,
alignment, cohesion.

  python3 boids.py          -> boids.svg  (one still, trails = the swarm's
                                           swirling history; no deps)
  python3 boids.py --gif    -> boids.gif  (animation; needs Pillow)
"""
import math
import random
import sys

W, H = 1600, 1200
N_BOIDS = 220
STEPS = 1100         # simulation steps
TRAIL = 220          # how many recent points to draw per bird

MAX_SPEED = 5.0
MIN_SPEED = 3.0      # boids always cruise -- never stall into a clump
MAX_FORCE = 0.22     # steering cap per rule
PERCEPTION = 55.0    # neighbour radius for align/cohere (local flocks)
SEPARATION = 30.0    # personal-space radius
MARGIN = 110         # soft wall the flock is nudged away from
TURN = 0.6           # wall push strength

SEED = random.randint(0, 1 << 30)
random.seed(SEED)


def limit(vx, vy, m):
    d = math.hypot(vx, vy)
    if d > m and d > 0:
        vx, vy = vx / d * m, vy / d * m
    return vx, vy


class Boid:
    def __init__(self):
        self.x = random.uniform(MARGIN, W - MARGIN)
        self.y = random.uniform(MARGIN, H - MARGIN)
        a = random.uniform(0, math.tau)
        self.vx = math.cos(a) * MAX_SPEED
        self.vy = math.sin(a) * MAX_SPEED
        self.trail = [(self.x, self.y)]

    def flock(self, boids):
        # accumulate the three steering vectors over nearby boids
        ax = ay = cx = cy = sx = sy = 0.0
        n_align = n_coh = n_sep = 0
        for o in boids:
            if o is self:
                continue
            dx, dy = o.x - self.x, o.y - self.y
            d = math.hypot(dx, dy)
            if d == 0:
                continue
            if d < PERCEPTION:
                ax += o.vx; ay += o.vy            # alignment: match velocity
                cx += o.x;  cy += o.y             # cohesion: steer to centre
                n_align += 1; n_coh += 1
            if d < SEPARATION:
                sx -= dx / d; sy -= dy / d        # separation: push away
                n_sep += 1

        fx = fy = 0.0
        if n_align:
            ax, ay = limit(ax / n_align, ay / n_align, MAX_SPEED)
            ax, ay = limit(ax - self.vx, ay - self.vy, MAX_FORCE)
            fx += ax; fy += ay
        if n_coh:
            cx, cy = cx / n_coh - self.x, cy / n_coh - self.y
            cx, cy = limit(cx, cy, MAX_SPEED)
            cx, cy = limit(cx - self.vx, cy - self.vy, MAX_FORCE)
            fx += cx; fy += cy
        if n_sep:
            sx, sy = limit(sx, sy, MAX_SPEED)
            sx, sy = limit(sx - self.vx, sy - self.vy, MAX_FORCE)
            fx += sx * 1.5; fy += sy * 1.5        # weight separation higher

        # soft walls: steer back inside before hitting the edge
        if self.x < MARGIN:        fx += TURN
        elif self.x > W - MARGIN:  fx -= TURN
        if self.y < MARGIN:        fy += TURN
        elif self.y > H - MARGIN:  fy -= TURN

        self.vx += fx; self.vy += fy
        self.vx, self.vy = limit(self.vx, self.vy, MAX_SPEED)
        sp = math.hypot(self.vx, self.vy)          # keep them cruising
        if sp < MIN_SPEED and sp > 0:
            self.vx, self.vy = self.vx / sp * MIN_SPEED, self.vy / sp * MIN_SPEED

    def move(self):
        self.x += self.vx; self.y += self.vy
        self.trail.append((self.x, self.y))
        if len(self.trail) > TRAIL:
            self.trail.pop(0)


def palette():
    base = random.choice([(205, 70, 60), (15, 85, 62), (280, 55, 68),
                          (160, 60, 55), (45, 90, 60), (340, 70, 64)])
    hue, sat, lig = base
    return [
        f"hsl({(hue + random.randint(-22, 22)) % 360},"
        f"{max(25, min(95, sat + random.randint(-12, 12)))}%,"
        f"{max(25, min(85, lig + random.randint(-20, 20)))}%)"
        for _ in range(6)
    ]


def hsl_to_rgb(hsl):
    # parse "hsl(h,s%,l%)" -> (r,g,b) 0..255, for Pillow
    h, s, l = (float(v.strip(" %")) for v in hsl[4:-1].split(","))
    h /= 360; s /= 100; l /= 100
    if s == 0:
        v = int(l * 255); return (v, v, v)
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q

    def hue(t):
        t %= 1
        if t < 1 / 6: return p + (q - p) * 6 * t
        if t < 1 / 2: return q
        if t < 2 / 3: return p + (q - p) * (2 / 3 - t) * 6
        return p
    return tuple(int(hue(h + d) * 255) for d in (1 / 3, 0, -1 / 3))


def path_d(pts):
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for x, y in pts[1:]:
        d += f" L{x:.1f},{y:.1f}"
    return d


def make_flock():
    cols = palette()
    boids = [Boid() for _ in range(N_BOIDS)]
    for b in boids:
        b.col = random.choice(cols)
    return boids


def render_gif():
    from PIL import Image, ImageDraw

    GW, GH = 720, 540          # smaller canvas keeps the gif light
    FRAMES = 180
    GIF_TRAIL = 48             # short visible tail per bird (perf + size)
    scale_x, scale_y = GW / W, GH / H
    boids = make_flock()
    rgb = {c: hsl_to_rgb(c) for c in {b.col for b in boids}}
    frames = []

    for f in range(FRAMES):
        for b in boids:
            b.flock(boids)
        for b in boids:
            b.move()
        img = Image.new("RGB", (GW, GH), (18, 18, 18))
        d = ImageDraw.Draw(img, "RGBA")
        for b in boids:
            t = b.trail[-GIF_TRAIL:]
            if len(t) < 2:
                continue
            r, g, bl = rgb[b.col]
            n = len(t)
            pts = [(x * scale_x, y * scale_y) for x, y in t]
            # one polyline for the faint tail, brighter head segment on top
            d.line(pts, fill=(r, g, bl, 70), width=1, joint="curve")
            d.line(pts[-12:], fill=(r, g, bl, 170), width=1, joint="curve")
            hx, hy = pts[-1]
            d.ellipse([hx - 2, hy - 2, hx + 2, hy + 2], fill=(r, g, bl, 255))
        frames.append(img)
        if f % 30 == 0:
            print(f"  frame {f}/{FRAMES}")

    frames[0].save("boids.gif", save_all=True, append_images=frames[1:],
                   duration=50, loop=0, optimize=True)
    print(f"seed={SEED}  boids={N_BOIDS}  frames={FRAMES}  -> boids.gif")


def render_svg():
    boids = make_flock()
    for _ in range(STEPS):
        for b in boids:
            b.flock(boids)
        for b in boids:
            b.move()

    bg = "hsl(0,0%,7%)"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{bg}"/>',
        '<g fill="none" stroke-linecap="round" stroke-linejoin="round">',
    ]
    for b in boids:
        if len(b.trail) < 2:
            continue
        out.append(
            f'<path d="{path_d(b.trail)}" stroke="{b.col}" '
            f'stroke-width="1.1" opacity="0.45"/>'
        )
        # a brighter dot at the bird's head
        out.append(
            f'<circle cx="{b.x:.1f}" cy="{b.y:.1f}" r="2.6" '
            f'fill="{b.col}" opacity="0.95"/>'
        )
    out.append("</g></svg>")
    with open("boids.svg", "w") as f:
        f.write("\n".join(out))
    xs = [b.x for b in boids]; ys = [b.y for b in boids]
    print(f"seed={SEED}  boids={N_BOIDS}  steps={STEPS}  -> boids.svg")
    print(f"  spread x={max(xs)-min(xs):.0f}px y={max(ys)-min(ys):.0f}px "
          f"(canvas {W}x{H})")


if __name__ == "__main__":
    if "--gif" in sys.argv:
        render_gif()
    else:
        render_svg()
