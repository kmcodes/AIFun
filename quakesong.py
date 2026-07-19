#!/usr/bin/env python3
"""
quakesong.py -- listen to the Earth.

Fetches the last 24 hours of earthquakes from the USGS live feed and
sonifies them into a piece of music (stereo WAV), plus an SVG poster of
where every note came from.

The mapping:
    time of quake   -> position in the piece (24 h squeezed into ~72 s)
    magnitude       -> loudness, and how long the bell rings
    depth           -> pitch (shallow = high chime, 600 km deep = low toll)
    longitude       -> stereo pan (Pacific on the left, Europe mid-right)

Pitches snap to a pentatonic scale, so whatever the planet did today, it
comes out vaguely musical. Every run is a different piece -- the Earth
writes a new one every day.

    python3 quakesong.py                 # fetch, write quakesong.wav + .svg
    python3 quakesong.py --min-mag 4.5   # only the big ones
    python3 quakesong.py --seconds 120   # stretch the day over 2 minutes

Pure standard library: urllib, wave, math. No numpy, no pip.
"""

import argparse
import json
import math
import struct
import sys
import time
import urllib.request
import wave

FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

RATE = 44100

# A-minor pentatonic, four octaves, low -> high. Depth picks the degree:
# shallow crustal pops chime at the top, deep-focus quakes toll at the bottom.
PENTATONIC = [55.0 * 2 ** (octave + semi / 12)
              for octave in range(4) for semi in (0, 3, 5, 7, 10)]


def fetch_quakes(min_mag):
    with urllib.request.urlopen(FEED, timeout=15) as r:
        feed = json.loads(r.read().decode())
    quakes = []
    for f in feed["features"]:
        p, (lon, lat, depth) = f["properties"], f["geometry"]["coordinates"]
        if p["mag"] is None or p["mag"] < min_mag:
            continue
        quakes.append({
            "mag": p["mag"], "lon": lon, "lat": lat,
            "depth": max(0.0, depth), "t": p["time"] / 1000.0,
            "place": p["place"] or "somewhere",
        })
    quakes.sort(key=lambda q: q["t"])
    return quakes


def depth_to_freq(depth_km):
    # Depths are wildly skewed (most ~10 km, a few 600 km), so go log-scale:
    # 0..~700 km spans the whole scale, deeper = lower.
    x = math.log1p(depth_km) / math.log1p(700)          # 0..1
    idx = round((1 - x) * (len(PENTATONIC) - 1))
    return PENTATONIC[idx]


def bell(freq, seconds, amp):
    """Render one struck bell as a list of mono float samples.

    Three inharmonic partials, each an exponentially decaying sine. The
    sines come from a rotating complex phasor (z *= step), which keeps
    pure Python fast enough to render a few hundred of these.
    """
    n = int(seconds * RATE)
    out = [0.0] * n
    for partial, (ratio, gain) in enumerate(((1.0, 1.0), (2.76, 0.4), (5.40, 0.15))):
        w = 2 * math.pi * freq * ratio / RATE
        if w >= math.pi:                                # over Nyquist, skip
            continue
        step = complex(math.cos(w), math.sin(w))
        decay = math.exp(-(4.0 + 2.0 * partial) / (seconds * RATE))
        z, env = complex(1.0, 0.0), amp * gain
        for i in range(n):
            out[i] += z.imag * env
            z *= step
            env *= decay
    # a few ms of attack so it strikes instead of clicks
    a = min(int(0.004 * RATE), n)
    for i in range(a):
        out[i] *= i / a
    return out


def render(quakes, seconds):
    """Mix every quake into a stereo float buffer."""
    t0, t1 = quakes[0]["t"], quakes[-1]["t"]
    span = max(t1 - t0, 1.0)
    tail = 8.0
    total = int((seconds + tail) * RATE)
    left, right = [0.0] * total, [0.0] * total

    for q in quakes:
        freq = depth_to_freq(q["depth"])
        ring = 0.6 + (q["mag"] / 6.5) ** 2 * 7.0        # M2 rings 0.7s, M6.5 ~7.6s
        amp = 2.0 ** q["mag"]                           # normalized later
        theta = (q["lon"] + 180) / 360 * (math.pi / 2)  # equal-power pan
        note = bell(freq, ring, amp)
        if q["mag"] >= 5.5:                             # the big ones get a sub-octave toll
            low = bell(freq / 2, ring * 1.3, amp * 0.7)
            for i, s in enumerate(low):
                if i < len(note):
                    note[i] += s
                else:
                    note.append(s)
        start = int((q["t"] - t0) / span * seconds * RATE)
        gl, gr = math.cos(theta), math.sin(theta)
        for i, s in enumerate(note):
            j = start + i
            if j >= total:
                break
            left[j] += s * gl
            right[j] += s * gr

    peak = max(max(map(abs, left)), max(map(abs, right)), 1e-9)
    k = 0.85 / peak
    return [(l * k, r * k) for l, r in zip(left, right)]


def write_wav(path, frames):
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        data = bytearray()
        for l, r in frames:
            data += struct.pack("<hh", int(l * 32767), int(r * 32767))
        w.writeframes(bytes(data))


# ---------------------------------------------------------------- SVG poster

def depth_color(depth_km):
    # shallow amber -> deep violet, same log scale as the pitch mapping
    x = math.log1p(depth_km) / math.log1p(700)
    stops = [(255, 196, 84), (255, 122, 89), (196, 93, 152), (110, 84, 200)]
    x *= len(stops) - 1
    i = min(int(x), len(stops) - 2)
    f = x - i
    rgb = [round(a + (b - a) * f) for a, b in zip(stops[i], stops[i + 1])]
    return "rgb({},{},{})".format(*rgb)


def write_svg(path, quakes, seconds):
    W, H = 1200, 680
    mx, my, mw, mh = 60, 90, W - 120, 440               # map box
    t0 = quakes[0]["t"]
    span = max(quakes[-1]["t"] - t0, 1.0)

    def xy(lon, lat):
        return (mx + (lon + 180) / 360 * mw,
                my + (90 - lat) / 180 * mh)

    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}">'.format(W, H),
         '<rect width="{}" height="{}" fill="#0b0e1a"/>'.format(W, H)]

    # graticule
    for lon in range(-150, 180, 30):
        x, _ = xy(lon, 0)
        s.append('<line x1="{0:.0f}" y1="{1}" x2="{0:.0f}" y2="{2}" stroke="#1d2340" stroke-width="1"/>'
                 .format(x, my, my + mh))
    for lat in range(-60, 90, 30):
        _, y = xy(0, lat)
        s.append('<line x1="{1}" y1="{0:.0f}" x2="{2}" y2="{0:.0f}" stroke="#1d2340" stroke-width="1"/>'
                 .format(y, mx, mx + mw))
    s.append('<rect x="{}" y="{}" width="{}" height="{}" fill="none" stroke="#2a3155" stroke-width="1.5"/>'
             .format(mx, my, mw, mh))

    # quakes: ripple ring + core dot, sized by magnitude, coloured by depth
    for q in sorted(quakes, key=lambda q: -q["mag"]):
        x, y = xy(q["lon"], q["lat"])
        r = 2.5 + (q["mag"] / 7.0) ** 2 * 26
        c = depth_color(q["depth"])
        s.append('<circle cx="{:.1f}" cy="{:.1f}" r="{:.1f}" fill="none" stroke="{}" '
                 'stroke-width="1.2" opacity="0.45"/>'.format(x, y, r * 1.9, c))
        s.append('<circle cx="{:.1f}" cy="{:.1f}" r="{:.1f}" fill="{}" opacity="0.85"/>'
                 .format(x, y, r, c))

    # timeline: the score, one tick per note, where it lands in the piece
    ty = my + mh + 70
    s.append('<line x1="{0}" y1="{1}" x2="{2}" y2="{1}" stroke="#2a3155" stroke-width="1.5"/>'
             .format(mx, ty, mx + mw))
    for q in quakes:
        x = mx + (q["t"] - t0) / span * mw
        h = 4 + (q["mag"] / 7.0) ** 2 * 46
        s.append('<line x1="{0:.1f}" y1="{1:.1f}" x2="{0:.1f}" y2="{2:.1f}" stroke="{3}" '
                 'stroke-width="2" opacity="0.9"/>'.format(x, ty - h, ty, depth_color(q["depth"])))
    s.append('<text x="{}" y="{}" fill="#5b648c" font-family="monospace" font-size="13">0:00</text>'
             .format(mx, ty + 22))
    s.append('<text x="{}" y="{}" fill="#5b648c" font-family="monospace" font-size="13" '
             'text-anchor="end">{}:{:02d}</text>'.format(mx + mw, ty + 22, int(seconds) // 60, int(seconds) % 60))

    biggest = max(quakes, key=lambda q: q["mag"])
    day = time.strftime("%Y-%m-%d", time.gmtime(quakes[-1]["t"]))
    s.append('<text x="{}" y="46" fill="#e8ecff" font-family="monospace" font-size="26">'
             'QUAKESONG &#183; what the Earth played on {}</text>'.format(mx, day))
    s.append('<text x="{}" y="70" fill="#5b648c" font-family="monospace" font-size="14">'
             '{} earthquakes &#183; loudest: M{:.1f} {} &#183; shallow=amber deep=violet, size=magnitude</text>'
             .format(mx, len(quakes), biggest["mag"], biggest["place"].replace("&", "&amp;")))
    s.append("</svg>")
    with open(path, "w") as f:
        f.write("\n".join(s))


def main():
    ap = argparse.ArgumentParser(description="sonify the last 24 h of earthquakes")
    ap.add_argument("--min-mag", type=float, default=2.5, help="ignore quakes below this magnitude")
    ap.add_argument("--seconds", type=float, default=72.0, help="length of the piece")
    ap.add_argument("--out", default="quakesong", help="basename for .wav/.svg output")
    args = ap.parse_args()

    print("fetching last 24 h of earthquakes from USGS ...")
    quakes = fetch_quakes(args.min_mag)
    if len(quakes) < 2:
        sys.exit("not enough quakes above M{} today -- lower --min-mag".format(args.min_mag))

    biggest = max(quakes, key=lambda q: q["mag"])
    print("{} quakes, M{:.1f}..M{:.1f} -- loudest: {}".format(
        len(quakes), quakes and min(q["mag"] for q in quakes), biggest["mag"], biggest["place"]))

    print("rendering {} bells into {:.0f}s of audio ...".format(len(quakes), args.seconds))
    frames = render(quakes, args.seconds)
    write_wav(args.out + ".wav", frames)
    write_svg(args.out + ".svg", quakes, args.seconds)
    print("wrote {0}.wav and {0}.svg -- press play, that's the planet.".format(args.out))


if __name__ == "__main__":
    main()
