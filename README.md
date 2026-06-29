# AIFun

A couple of small generative-art toys written in **pure Python** — no `pip
install`, no dependencies, just the standard library. Throwaway weekend code
that turned out kind of pretty.

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

Python 3.6+. That's it.
