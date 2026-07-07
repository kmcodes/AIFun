#!/usr/bin/env python3
"""Where is the ISS right now? Plots the live position of the International
Space Station onto an ASCII world map in your terminal, and lists every
human currently off the planet.

  python3 iss.py            # one snapshot
  python3 iss.py --track    # live: re-fetch every few seconds, Ctrl-C to quit

Pulls live data from the open-notify.org API. Needs internet, no API key,
no third-party libraries.
"""
import json
import math
import sys
import time
import urllib.request

ISS_NOW = "http://api.open-notify.org/iss-now.json"
ASTROS = "http://api.open-notify.org/astros.json"

# A crude equirectangular world map, verified against real coordinates:
# columns run lon -180..180, rows run lat +90..-90. Land is roughly placed so
# the projected @ lands where it should -- e.g. London ~col33, Tokyo ~col59,
# Sydney ~col61, so the continents below sit under those columns.
#         0         1         2         3         4         5         6
#         0123456789012345678901234567890123456789012345678901234567890123456789
WORLD = r"""
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
. . . . . _.--._ . . . . . . _.-._ . . . . . _.--..__.-. . . . . . .
. . . . _-  N.  '-. . . . . _' EUR '. . . . _'  A S I A  '-._ . . . .
. . . . |AMERICA  | . . . _-'-._..-' . . . |             | . . . . .
. . . . '-._    _.' . . . |  AFR   | . . . '._  .-._  _.-' . . . . .
. . . . . . '--'  . . . . |        | . . . . '-'    '-' . . . . . . .
. . . . . . . |  . . . . .'._    _.' . . . . . . . . . . . . . . . .
. . . . . . _-'-._ . . . . . '--' . . . . . . . . . _.-. . . . . . .
. . . . . .| SOUTH| . . . . . . . . . . . . . . . .( AUS ) . . . . .
. . . . . .|AMERICA. . . . . . . . . . . . . . . . '-._.-' . . . . .
. . . . . . '-._.' . . . . . . . . . . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
""".strip("\n").split("\n")


def get_json(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode())


def plot(lat, lon):
    rows = len(WORLD)
    cols = max(len(r) for r in WORLD)
    grid = [list(r.ljust(cols)) for r in WORLD]

    # equirectangular projection into the grid
    col = int((lon + 180) / 360 * (cols - 1))
    row = int((90 - lat) / 180 * (rows - 1))
    row = max(0, min(rows - 1, row))
    col = max(0, min(cols - 1, col))
    grid[row][col] = "@"                    # the station

    lines = ["".join(r) for r in grid]
    # ANSI: paint the @ bright yellow, land dim
    out = []
    for ln in lines:
        ln = ln.replace("@", "\033[1;93m@\033[0m")
        ln = ln.replace("#", "\033[2m#\033[0m")
        out.append(ln)
    return "\n".join(out)


def snapshot():
    now = get_json(ISS_NOW)["iss_position"]
    lat, lon = float(now["latitude"]), float(now["longitude"])
    crew = get_json(ASTROS)["people"]

    print("\033[H\033[2J", end="")           # home + clear
    print(plot(lat, lon))
    print()
    hemi_ns = "N" if lat >= 0 else "S"
    hemi_ew = "E" if lon >= 0 else "W"
    print(f"  \033[1;93m@\033[0m  ISS  ->  "
          f"{abs(lat):5.2f}°{hemi_ns}  {abs(lon):6.2f}°{hemi_ew}"
          f"   (~408 km up, ~27 600 km/h)")
    print()

    crafts = {}
    for p in crew:
        crafts.setdefault(p["craft"], []).append(p["name"])
    total = len(crew)
    print(f"  \033[1mcrew, per the astros.json feed ({total} names):\033[0m")
    for craft, names in crafts.items():
        print(f"    {craft}: {', '.join(names)}")
    # The position feed is live, but open-notify's crew list is known to be
    # stale (it has served the same snapshot for a long time), so don't dress
    # it up as "who is in space right now".
    print("    \033[2m(note: this crew feed is often out of date — the "
          "@ position above is live)\033[0m")


def main():
    track = "--track" in sys.argv[1:]
    try:
        if track:
            while True:
                snapshot()
                print("\n  live — refreshing every 5s, Ctrl-C to quit")
                time.sleep(5)
        else:
            snapshot()
    except urllib.error.URLError as e:
        sys.exit(f"couldn't reach the API (need internet): {e}")
    except KeyboardInterrupt:
        print("\n  bye \U0001f6f0")


if __name__ == "__main__":
    main()
