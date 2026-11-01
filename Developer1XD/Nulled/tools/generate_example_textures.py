#!/usr/bin/env python3
"""Generate seamless 4K example textures for the Nulled addon (offline, no internet).

Run from the Nulled folder:   python3 tools/generate_example_textures.py [--size 4096]

Textures are equirectangular (width = 2 * height) and sampled from 3D noise on the
unit sphere, so they have no seam at the date line and no pinching at the poles.
Afterwards run tools/fetch_web_textures.py to replace them with real imagery.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "textures" / "planets" / "Null"


def sphere_coords(w, h):
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = np.pi / 2 - (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi
    lon, lat = np.meshgrid(lon, lat)
    c = np.cos(lat)
    return np.stack([c * np.cos(lon), c * np.sin(lon), np.sin(lat)]), lat


class Noise3D:
    """Vectorised 3D value noise with quintic interpolation."""

    def __init__(self, seed):
        rng = np.random.default_rng(seed)
        self.perm = np.concatenate([rng.permutation(256)] * 2).astype(np.int32)
        self.vals = rng.uniform(-1, 1, 256).astype(np.float32)

    def _h(self, x, y, z):
        p = self.perm
        return self.vals[p[p[p[x & 255] + (y & 255)] + (z & 255)]]

    def noise(self, P):
        x, y, z = P
        xi, yi, zi = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32), np.floor(z).astype(np.int32)
        xf, yf, zf = x - xi, y - yi, z - zi
        f = lambda t: t * t * t * (t * (t * 6 - 15) + 10)
        u, v, w = f(xf), f(yf), f(zf)
        lerp = lambda a, b, t: a + (b - a) * t
        x0 = lerp(self._h(xi, yi, zi), self._h(xi + 1, yi, zi), u)
        x1 = lerp(self._h(xi, yi + 1, zi), self._h(xi + 1, yi + 1, zi), u)
        x2 = lerp(self._h(xi, yi, zi + 1), self._h(xi + 1, yi, zi + 1), u)
        x3 = lerp(self._h(xi, yi + 1, zi + 1), self._h(xi + 1, yi + 1, zi + 1), u)
        return lerp(lerp(x0, x1, v), lerp(x2, x3, v), w)

    def fbm(self, P, freq=2.0, octaves=8, gain=0.5, ridged=False):
        total = np.zeros(P.shape[1:], np.float32)
        amp, norm = 1.0, 0.0
        for o in range(octaves):
            n = self.noise(P * freq + 17.31 * o)
            if ridged:
                n = 1 - np.abs(n)
                n = n * n
            total += amp * n
            norm += amp
            amp *= gain
            freq *= 2.03
        return total / norm


def norm01(a):
    a = a - a.min()
    return a / max(a.max(), 1e-9)


def save(arr, name, quality=92):
    OUT.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))
    path = OUT / name
    img.save(path, quality=quality, optimize=True)
    print(f"  {path.relative_to(OUT.parent.parent.parent)}  {img.size[0]}x{img.size[1]}")


def ramp(t, stops):
    """Colour ramp: stops = [(pos, (r,g,b)), ...] with pos ascending."""
    pos = np.array([s[0] for s in stops], np.float32)
    out = np.empty(t.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(t, pos, np.array([s[1][c] for s in stops], np.float32))
    return out


def test1_height(P):
    """Test1's own (invented) continents. 0..0.5 = sea floor, 0.5..1 = land."""
    n = Noise3D(11)
    warp = np.stack([n.fbm(P + 5.2, 1.5, 4), n.fbm(P + 1.3, 1.5, 4), n.fbm(P + 9.1, 1.5, 4)])
    cont = n.fbm(P + warp * 0.6, 1.2, 9)
    mountains = Noise3D(12).fbm(P, 4.0, 8, ridged=True)
    h = norm01(cont)
    land = np.clip((h - 0.5) / 0.5, 0, 1)
    return np.where(h > 0.5, 0.5 + land * 0.5 * (0.55 + 0.45 * mountains), h)


def test1_moisture(P):
    """0 = arid, 1 = wet. Drives deserts vs forests."""
    return norm01(Noise3D(13).fbm(P, 2.5, 6))


def test1(P, lat, size):
    print("Test1 (earth-like)")
    h = test1_height(P)
    save(h[..., None].repeat(3, -1), "Test1_bump.jpg")

    alat = np.abs(lat) / (np.pi / 2)
    moist = test1_moisture(P)
    sea = ramp(h / 0.5, [(0, (0.01, 0.04, 0.14)), (0.8, (0.03, 0.14, 0.35)), (0.97, (0.10, 0.42, 0.55)), (1, (0.55, 0.70, 0.60))])
    lh = (h - 0.5) / 0.5
    lush = ramp(lh, [(0, (0.76, 0.70, 0.50)), (0.03, (0.20, 0.42, 0.14)), (0.35, (0.12, 0.30, 0.10)),
                     (0.65, (0.42, 0.36, 0.25)), (0.85, (0.55, 0.52, 0.50)), (1, (0.95, 0.95, 0.97))])
    dry = ramp(lh, [(0, (0.80, 0.72, 0.50)), (0.3, (0.78, 0.58, 0.34)), (0.7, (0.55, 0.38, 0.25)), (1, (0.90, 0.88, 0.86))])
    desert = np.clip((0.55 - moist) * 3 * (1 - np.abs(alat - 0.28) * 2.5), 0, 1)[..., None]
    col = np.where((h > 0.5)[..., None], lush * (1 - desert) + dry * desert, sea)
    ice = np.clip((alat - 0.80 + 0.06 * Noise3D(14).fbm(P, 6, 5)) * 12, 0, 1)[..., None]
    col = col * (1 - ice) + np.array([0.93, 0.95, 0.98], np.float32) * ice
    save(col, "Test1_diff.jpg")

    c = Noise3D(15)
    cw = np.stack([c.fbm(P + 2.0, 2, 4), c.fbm(P + 4.0, 2, 4), c.fbm(P + 6.0, 2, 4)])
    cl = norm01(c.fbm(P + cw * 0.9, 2.5, 9))
    bands = 0.5 + 0.5 * np.cos(lat * 6)
    cl = np.clip((cl + 0.12 * bands - 0.50) * 3.2, 0, 1)
    save(cl[..., None].repeat(3, -1), "Test1_clouds.jpg")


def test_asteroid(P, lat, size):
    print("TestAsteroid (Ganymede-sized moon)")
    n = Noise3D(31)
    base = norm01(n.fbm(P, 2.0, 9))
    rng = np.random.default_rng(32)
    craters = np.zeros(P.shape[1:], np.float32)
    for r, count in [(0.25, 6), (0.12, 25), (0.06, 90), (0.03, 300)]:
        cs = rng.normal(size=(count, 3)).astype(np.float32)
        cs /= np.linalg.norm(cs, axis=1, keepdims=True)
        for cvec, rr in zip(cs, rng.uniform(0.5, 1.0, count) * r):
            d = np.arccos(np.clip(np.tensordot(cvec, P, 1), -1, 1)) / rr
            m = d < 1.6
            if not m.any():
                continue
            dm = d[m]
            craters[m] += np.where(dm < 1, dm * dm - 1, 0.25 * np.exp(-((dm - 1) * 6) ** 2)) * rr * 4
    grooves = Noise3D(33).fbm(P * np.array([1, 1, 3], np.float32)[:, None, None], 3, 6, ridged=True)
    h = norm01(base * 0.5 + craters * 0.8 + grooves * 0.25)
    save(h[..., None].repeat(3, -1), "TestAsteroid_bump.jpg")
    terr = norm01(Noise3D(34).fbm(P, 1.3, 5))
    dark, light = np.array([0.33, 0.30, 0.27], np.float32), np.array([0.78, 0.76, 0.74], np.float32)
    t = np.clip(terr * 1.4 - 0.2, 0, 1)[..., None]
    col = dark * (1 - t) + light * t
    col *= (0.75 + 0.45 * h)[..., None]
    frost = np.clip((np.abs(lat) / (np.pi / 2) - 0.7) * 4, 0, 1)[..., None]
    col = col * (1 - frost) + np.array([0.9, 0.92, 0.95], np.float32) * frost
    save(np.clip(col, 0, 1), "TestAsteroid_diff.jpg")


def test2(P, lat, size):
    print("Test2 (brown dwarf)")
    n = Noise3D(21)
    turb = n.fbm(P, 3.0, 8)
    swirl = Noise3D(22).fbm(P + turb[None] * 0.8, 6.0, 6)
    y = np.sin(lat) + 0.08 * turb + 0.03 * swirl
    bands = 0.5 + 0.5 * np.sin(y * 28 + 2 * np.sin(y * 7))
    fine = 0.5 + 0.5 * np.sin(y * 90 + swirl * 4)
    t = np.clip(bands * 0.75 + fine * 0.25, 0, 1)
    col = ramp(t, [(0, (0.22, 0.08, 0.05)), (0.35, (0.48, 0.20, 0.10)), (0.6, (0.72, 0.40, 0.20)),
                   (0.85, (0.88, 0.62, 0.38)), (1, (0.96, 0.80, 0.58))])
    # a great storm
    storm_c = np.array([np.cos(-0.35) * np.cos(1.0), np.cos(-0.35) * np.sin(1.0), np.sin(-0.35)], np.float32)
    d = np.arccos(np.clip(np.tensordot(storm_c, P, 1), -1, 1))
    s = np.clip(1 - d / 0.22, 0, 1) ** 1.5
    col = col * (1 - s[..., None]) + np.array([0.75, 0.25, 0.10], np.float32) * s[..., None]
    save(col, "Test2_diff.jpg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=4096, help="texture width (height = width/2)")
    args = ap.parse_args()
    w, h = args.size, args.size // 2
    print(f"Generating {w}x{h} example textures into {OUT}")
    P, lat = sphere_coords(w, h)
    test1(P, lat, w)
    test_asteroid(P, lat, w)
    test2(P, lat, w)
    print("done")


if __name__ == "__main__":
    main()
