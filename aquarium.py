#!/usr/bin/env python3
"""ASCII aquarium. Fish swim, bubbles rise, seaweed sways. Ctrl-C to quit."""
import os
import random
import shutil
import sys
import time

# ---- fish art, facing right and left ----
FISH_RIGHT = [r"><(((°>", r"><>", r"><(((*>", r">=<>"]
FISH_LEFT = [r"<°)))><", r"<><", r"<*)))><", r"<>=<"]
COLORS = [31, 32, 33, 34, 35, 36, 91, 92, 93, 94, 95, 96]


def color(s, c):
    return f"\033[{c}m{s}\033[0m"


class Fish:
    def __init__(self, w, h):
        self.dir = random.choice((-1, 1))
        self.y = random.randint(1, h - 2)
        self.x = random.randint(0, w - 1)
        self.c = random.choice(COLORS)
        self.speed = random.choice((1, 1, 2))
        self.art()

    def art(self):
        self.body = random.choice(FISH_RIGHT if self.dir == 1 else FISH_LEFT)

    def step(self, w, h):
        self.x += self.dir * self.speed
        if random.random() < 0.02:           # occasional vertical drift
            self.y = max(1, min(h - 2, self.y + random.choice((-1, 1))))
        if self.x < -len(self.body) or self.x > w:   # wrap around, flip
            self.dir *= -1
            self.art()
            self.x = -len(self.body) if self.dir == 1 else w
            self.y = random.randint(1, h - 2)
            self.c = random.choice(COLORS)


class Bubble:
    def __init__(self, w, h):
        self.x = random.randint(0, w - 1)
        self.y = h - 1
        self.ch = random.choice("oO°.")

    def step(self):
        self.y -= 1
        if random.random() < 0.3:
            self.x += random.choice((-1, 1))


def draw(fish, bubbles, w, h):
    grid = [[" "] * w for _ in range(h)]
    style = [[None] * w for _ in range(h)]

    # surface line + sandy floor
    for x in range(w):
        grid[0][x] = "~"
        style[0][x] = 36
        grid[h - 1][x] = random.choice("..._") if random.random() < 0.15 else grid[h - 1][x]

    for b in bubbles:
        if 0 <= b.y < h and 0 <= b.x < w:
            grid[b.y][b.x] = b.ch
            style[b.y][b.x] = 36

    for f in fish:
        for i, ch in enumerate(f.body):
            x = f.x + i
            if 0 <= x < w and 0 <= f.y < h:
                grid[f.y][x] = ch
                style[f.y][x] = f.c

    out = []
    for y in range(h):
        row = []
        for x in range(w):
            ch, st = grid[y][x], style[y][x]
            row.append(color(ch, st) if st else ch)
        out.append("".join(row))
    sys.stdout.write("\033[H" + "\n".join(out))
    sys.stdout.flush()


def main():
    w, h = shutil.get_terminal_size((80, 24))
    h = max(10, h - 1)
    fish = [Fish(w, h) for _ in range(max(4, w // 12))]
    bubbles = []
    sys.stdout.write("\033[2J\033[?25l")   # clear + hide cursor
    try:
        while True:
            if random.random() < 0.25:
                bubbles.append(Bubble(w, h))
            for f in fish:
                f.step(w, h)
            for b in bubbles:
                b.step()
            bubbles = [b for b in bubbles if b.y > 0]
            draw(fish, bubbles, w, h)
            time.sleep(0.12)
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h\033[2J\033[H")   # restore cursor, clear
        print("fish swim away. bye 🐠")


if __name__ == "__main__":
    main()
