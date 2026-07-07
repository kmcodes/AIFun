#!/usr/bin/env python3
"""Harmonograph. A Victorian drawing machine: two or three pendulums, each
swinging on its own axis and slowly dying down, drag a pen across paper. The
sum of decaying sine waves traces those hypnotic looping figures.

  python3 harmonograph.py        -> harmonograph.svg  (one still; no deps)
  python3 harmonograph.py --gif  -> harmonograph.gif  (pen draws live; Pillow)

Every run randomises the pendulum frequencies, phases, damping and palette,
and prints the seed so a result you like can be reproduced:

  python3 harmonograph.py --seed 123456
"""
import math
import random
import sys

W, H = 1400, 1400
MARGIN = 120
DURATION = 60.0      # seconds of (simulated) swinging
DT = 0.004           # time step -- smaller = smoother curve, bigger file
LINE_W = 1.1

# frequencies cluster near small integer ratios, but nudged slightly off so
# the figure precesses instead of closing into a dead-still loop.
BASE_FREQ = 2.0
DETUNE = 0.004       # how far a frequency may drift from a whole ratio


def rand_seed():
    return random.randint(0, 1 << 30)


class Pendulum:
    """One decaying sinusoid: amp * sin(2*pi*freq*t + phase) * e^(-damp*t)."""

    def __init__(self, amp, ratio):
        self.freq = BASE_FREQ * ratio + random.uniform(-DETUNE, DETUNE)
        self.phase = random.uniform(0, 2 * math.pi)
        self.amp = amp
        self.damp = random.uniform(0.003, 0.008)        # how fast it stalls

    def at(self, t):
        return (self.amp * math.sin(2 * math.pi * self.freq * t + self.phase)
                * math.exp(-self.damp * t))


def build_machine():
    """A pen tied to two pendulums per axis -- the classic lateral rig.

    X and Y ride *different* low ratios so the figure opens into a 2-D loop
    instead of collapsing onto a line (which happens when both axes share a
    ratio and drift into phase).
    """
    amp = (min(W, H) / 2 - MARGIN) / 2
    rx, ry = random.sample([1, 2, 3, 4], 2)             # distinct per axis
    # second pendulum per axis rides a neighbouring ratio -> beat patterns,
    # and can't silently cancel its partner.
    x1, x2 = Pendulum(amp, rx), Pendulum(amp * 0.6, rx + 1)
    y1, y2 = Pendulum(amp, ry), Pendulum(amp * 0.6, ry + 1)
    cx, cy = W / 2, H / 2

    def pen(t):
        return (cx + x1.at(t) + x2.at(t),
                cy + y1.at(t) + y2.at(t))

    return pen


def trace(pen):
    """Sample the pen path over the whole run. Returns list of (x, y)."""
    pts = []
    t = 0.0
    while t < DURATION:
        pts.append(pen(t))
        t += DT
    return pts


# ---- palette ---------------------------------------------------------------

def hsl(h, s, l):
    return f"hsl({h:.0f}, {s:.0f}%, {l:.0f}%)"


def palette():
    """A hue that drifts slowly along the curve -- ink shifting as it dries."""
    base = random.uniform(0, 360)
    spread = random.uniform(40, 120)
    sat = random.uniform(55, 80)
    light = random.uniform(45, 62)
    return base, spread, sat, light


# ---- SVG -------------------------------------------------------------------

def write_svg(pts, pal, path="harmonograph.svg"):
    base, spread, sat, light = pal
    bg = "#0d0d12"
    n = len(pts)
    # Draw in coloured segments so the hue can drift; group runs of a colour
    # into one polyline to keep the file reasonable.
    SEG = 400
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{bg}"/>',
        '<g fill="none" stroke-linecap="round" stroke-linejoin="round" '
        f'stroke-width="{LINE_W}" opacity="0.85">',
    ]
    i = 0
    while i < n - 1:
        j = min(i + SEG, n - 1)
        frac = i / n
        hue = (base + spread * math.sin(2 * math.pi * frac)) % 360
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts[i:j + 1])
        parts.append(f'<path d="{d}" stroke="{hsl(hue, sat, light)}"/>')
        i = j
    parts.append("</g></svg>")
    with open(path, "w") as f:
        f.write("\n".join(parts))
    return path


# ---- GIF (optional) --------------------------------------------------------

def write_gif(pts, pal, path="harmonograph.gif"):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        sys.exit("--gif needs Pillow:  pip install pillow")

    base, spread, sat, light = pal
    scale = 0.5
    w, h = int(W * scale), int(H * scale)
    frames = []
    FRAMES = 90
    per = len(pts) // FRAMES
    img = Image.new("RGB", (w, h), (13, 13, 18))
    draw = ImageDraw.Draw(img)

    def rgb(hue):
        import colorsys
        r, g, b = colorsys.hls_to_rgb(hue / 360, light / 100, sat / 100)
        return int(r * 255), int(g * 255), int(b * 255)

    drawn = 0
    for fi in range(FRAMES):
        end = min((fi + 1) * per, len(pts) - 1)
        for k in range(drawn, end):
            frac = k / len(pts)
            hue = (base + spread * math.sin(2 * math.pi * frac)) % 360
            x0, y0 = pts[k]
            x1, y1 = pts[k + 1]
            draw.line((x0 * scale, y0 * scale, x1 * scale, y1 * scale),
                      fill=rgb(hue), width=1)
        drawn = end
        frames.append(img.copy())

    frames += [frames[-1]] * 12   # hold on the finished figure
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=60, loop=0)
    return path


def main():
    args = sys.argv[1:]
    seed = rand_seed()
    if "--seed" in args:
        seed = int(args[args.index("--seed") + 1])
    random.seed(seed)

    pen = build_machine()
    pts = trace(pen)
    pal = palette()

    if "--gif" in args:
        out = write_gif(pts, pal)
    else:
        out = write_svg(pts, pal)

    print(f"wrote {out}   seed={seed}   points={len(pts)}")


if __name__ == "__main__":
    main()
