# timepass

Small generative-art toys in pure Python. No dependencies.

## `aquarium.py`

ASCII aquarium for your terminal. Fish swim and wrap around, bubbles rise,
the floor sands itself. Ctrl-C to quit.

```bash
python3 aquarium.py
```

## `flowfield.py`

Flow-field generative art. Particles ride a value-noise field and trace
curving ink lines into an SVG. Each run is unique (random seed + palette).

```bash
python3 flowfield.py   # writes flowfield.svg
```

## gallery

Sample outputs from `flowfield.py` (PNG + SVG).

![sample](gallery/art_1.png)
