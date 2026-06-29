# AIFun

A few small generative-art toys written in **mostly pure Python** — standard
library only, apart from one optional GIF exporter. Throwaway weekend code that
turned out kind of pretty.

---

## 🐠 `aquarium.py` — terminal aquarium

An animated ASCII aquarium that runs right in your terminal. Fish made of
`><(((°>` swim left and right, wrap around the edges and flip direction,
randomly drift up and down, and change colour each lap. Bubbles spawn at the
bottom and wobble their way up to the surface. The top is a `~~~` waterline,
the bottom sands itself in with scattered `.`/`_` grains.

Everything scales to your terminal size — a wider window gets more fish.

```bash
python3 aquarium.py      # Ctrl-C to quit
```

**How it works**

- Each `Fish` carries its own direction, speed, colour and ASCII body, and
  re-randomises them whenever it swims off-screen.
- Each frame is composed into a character grid + a parallel colour grid, then
  flushed in one write using ANSI escape codes (`\033[H` to home the cursor,
  hidden cursor while running).
- ~8 frames/sec via `time.sleep(0.12)`. No curses, no external libs.

---

## 🌀 `flowfield.py` — flow-field generative art

Draws curving "ink" lines by releasing ~1400 particles into an invisible
**flow field** and letting them ride the currents. Every run is unique:
the noise field, the seed, and the colour palette are all randomised. Output
is a single self-contained **SVG** (vector, infinitely zoomable).

```bash
python3 flowfield.py      # writes flowfield.svg, prints the seed
```

**How it works**

- **Value noise from scratch** — a hashed integer lattice with quintic
  smoothing (Perlin's `6t⁵−15t⁴+10t³` fade, which kills the creasing you get
  from plain smoothstep). No `numpy`, no noise library.
- The noise value at each point becomes an **angle**; two octaves are summed
  to give a swirling field. Each particle repeatedly steps in the direction
  of the field, tracing a path until it leaves the canvas.
- A random **HSL palette** picks one hue family and varies lightness, so each
  piece is colour-coherent. Line width and opacity are jittered per stroke to
  build up depth.
- The print line reports the `seed` so a result you like can be reproduced.

**Tweakables** (top of the file): `N_PARTICLES`, `STEPS`, `STEP_LEN`, `GRID`
(field frequency), canvas `W`/`H`, and `MARGIN`.

---

## 🐦 `boids.py` — flocking simulation

Craig Reynolds' classic **boids**: each bird steers by just three local rules —
**separation** (don't crowd neighbours), **alignment** (match their heading),
**cohesion** (drift toward their centre) — and a swarm emerges with no leader
and no global plan. A minimum-speed rule keeps every bird cruising so the flock
never collapses into a stationary clump.

```bash
python3 boids.py          # -> boids.svg : one still, trails = the swarm's path
python3 boids.py --gif    # -> boids.gif : animation (needs Pillow)
```

![boids](boids.gif)

**How it works**

- Each `Boid` scans neighbours within a perception radius and accumulates the
  three steering vectors, each capped by `MAX_FORCE` so turns stay smooth.
- Separation is weighted highest and a `MIN_SPEED` floor stops the flock from
  stalling — the two fixes that turn a dead clump into a living swarm.
- The **SVG** mode traces each bird's full path into vector ink. The **GIF**
  mode draws fading per-bird tails frame by frame with Pillow.
- Soft walls near the canvas edge nudge birds back inward instead of hard
  bouncing, so the flock wanders the whole frame.

**Tweakables** (top of the file): `N_BOIDS`, `PERCEPTION`, `SEPARATION`,
`MAX_SPEED`/`MIN_SPEED`, `MAX_FORCE`, `TRAIL`.

---

## 🖼 gallery

Five sample renders from `flowfield.py`, each as both PNG (preview) and SVG
(source). They show the range of palettes the script produces — same code,
different seed.

| | | |
|---|---|---|
| ![](gallery/art_1.png) | ![](gallery/art_2.png) | ![](gallery/art_3.png) |
| ![](gallery/art_4.png) | ![](gallery/art_5.png) | |

---

## requirements

Python 3.6+ and nothing else — except `boids.py --gif`, which needs
[Pillow](https://pypi.org/project/Pillow/) (`pip install pillow`). Everything
else, including `boids.py`'s SVG mode, is pure standard library.
