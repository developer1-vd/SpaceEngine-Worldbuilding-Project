#!/usr/bin/env python3
"""Download real planetary imagery from NASA and convert it to 4K SpaceEngine textures.

Run from the Nulled folder:   python3 tools/fetch_web_textures.py [--size 4096] [--keep-downloads]

What gets replaced (all sources are NASA, public domain):
  Test1_diff.jpg          <- Test1's OWN invented continents, coloured with real terrain
                             colours sampled from NASA Blue Marble NG + NASA/GEBCO elevation
                             (forest, desert, tundra, ice, shallow/deep ocean). No Earth
                             continents end up on Test1.
  Test1_clouds.jpg        <- NASA Blue Marble cloud composite (shifted 180 deg in longitude)
  TestAsteroid_diff.jpg   <- NASA SVS CGI Moon Kit, LRO LROC colour mosaic
  TestAsteroid_bump.jpg   <- NASA SVS CGI Moon Kit, LRO LOLA elevation (LDEM)

Test1_bump.jpg stays the generated heightmap of Test1's invented continents.
Test2 (brown dwarf) keeps its generated texture - there is no photo of a brown dwarf's
surface; its look comes from SpaceEngine's procedural clouds on top.

If a download fails, the example texture for that file is left in place.
To go back to the examples: python3 tools/generate_example_textures.py
"""
import argparse
import shutil
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None  # NASA source maps are large (up to 21600x10800)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "textures" / "planets" / "Null"
CACHE = ROOT / ".download_cache"

EO = "https://eoimages.gsfc.nasa.gov/images/imagerecords"
SVS = "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720"

EARTH_COLOR = f"{EO}/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg"
EARTH_ELEV = f"{EO}/73000/73934/gebco_08_rev_elev_21600x10800.png"

SOURCES = {
    "Test1_diff.jpg": ((EARTH_COLOR, EARTH_ELEV), "palette"),
    "Test1_clouds.jpg": (f"{EO}/57000/57747/cloud_combined_8192.tif", "clouds"),
    "TestAsteroid_diff.jpg": (f"{SVS}/lroc_color_poles_4k.tif", "color"),
    "TestAsteroid_bump.jpg": (f"{SVS}/ldem_16_uint.tif", "height16"),
}


def download(url):
    CACHE.mkdir(exist_ok=True)
    dest = CACHE / url.rsplit("/", 1)[-1]
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  cached   {dest.name}")
        return dest
    print(f"  download {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        ctype = r.headers.get("Content-Type", "")
        if not ctype.startswith("image/"):
            raise RuntimeError(f"expected an image, got {ctype!r}")
        shutil.copyfileobj(r, f, 1 << 20)
    tmp.rename(dest)
    return dest


# ---------------------------------------------------------------------------
# Palette transfer: learn how real terrain is coloured on Earth as a function of
# (elevation, latitude, wetness), then paint Test1's own continents with it.
# ---------------------------------------------------------------------------
NE, NL, NQ = 24, 12, 12   # elevation bins, |latitude| bins, wetness/depth quantiles


def _fill_empty(lut, count):
    """Fill bins with no Earth samples from their nearest filled neighbours."""
    lut, count = lut.copy(), count.copy()
    while (count == 0).any():
        empty = count == 0
        acc = np.zeros_like(lut)
        n = np.zeros(count.shape, np.float32)
        for ax in range(count.ndim):
            for sh in (-1, 1):
                rolled_c = np.roll(count > 0, sh, ax)
                idx = [slice(None)] * count.ndim
                idx[ax] = 0 if sh == 1 else -1      # don't wrap around the edges
                rolled_c[tuple(idx)] = False
                acc += np.roll(lut, sh, ax) * rolled_c[..., None]
                n += rolled_c
        fill = empty & (n > 0)
        lut[fill] = acc[fill] / n[fill][:, None]
        count[fill] = 1
    return lut


def _rank01(a):
    """Map values to their percentile (0..1)."""
    order = np.argsort(a, kind="stable")
    r = np.empty(a.size, np.float32)
    r[order] = np.linspace(0, 1, a.size, dtype=np.float32)
    return r


def earth_palette(color_path, elev_path):
    W, H = 2700, 1350
    rgb = np.asarray(Image.open(color_path).convert("RGB").resize((W, H), Image.LANCZOS), np.float32) / 255
    elev = np.asarray(Image.open(elev_path).convert("L").resize((W, H), Image.BILINEAR), np.float32)
    alat = np.abs(np.linspace(90, -90, H, dtype=np.float32))[:, None].repeat(W, 1) / 90
    blueish = rgb[..., 2] > rgb[..., 0] + 0.06
    land = (elev > 0) & ~(blueish & (elev < 2))
    lbin = np.minimum((alat * NL).astype(int), NL - 1)

    # land: elevation percentile x latitude x wetness (greenness) quantile
    c, e, lb = rgb[land], _rank01(elev[land]), lbin[land]
    wet = c[:, 1] - 0.6 * c[:, 0] - 0.4 * c[:, 2]
    ebin = np.minimum((e * NE).astype(int), NE - 1)
    land_lut = np.zeros((NE, NL, NQ, 3), np.float32)
    land_n = np.zeros((NE, NL, NQ), np.float32)
    for i in range(NE):
        for j in range(NL):
            m = (ebin == i) & (lb == j)
            if m.sum() < NQ * 4:
                continue
            q = np.minimum((_rank01(wet[m]) * NQ).astype(int), NQ - 1)
            for k in range(NQ):
                land_lut[i, j, k] = c[m][q == k].mean(0)
                land_n[i, j, k] = 1
    land_lut = _fill_empty(land_lut, land_n)

    # ocean: latitude x brightness quantile (dark = deep)
    sea = ~land
    c, lb = rgb[sea], lbin[sea]
    ocean_lut = np.zeros((NL, NQ, 3), np.float32)
    ocean_n = np.zeros((NL, NQ), np.float32)
    for j in range(NL):
        m = lb == j
        if m.sum() < NQ * 4:
            continue
        q = np.minimum((_rank01(c[m].sum(1)) * NQ).astype(int), NQ - 1)
        for k in range(NQ):
            ocean_lut[j, k] = c[m][q == k].mean(0)
            ocean_n[j, k] = 1
    ocean_lut = _fill_empty(ocean_lut, ocean_n)
    return land_lut, ocean_lut


def _lookup(lut, coords):
    """Multilinear interpolation into lut[..., 3] at fractional bin coordinates."""
    out = 0
    dims = len(coords)
    base = [np.floor(c).astype(int) for c in coords]
    frac = [c - b for c, b in zip(coords, base)]
    for corner in range(1 << dims):
        wgt = 1
        idx = []
        for d in range(dims):
            bit = (corner >> d) & 1
            idx.append(np.clip(base[d] + bit, 0, lut.shape[d] - 1))
            wgt = wgt * (frac[d] if bit else 1 - frac[d])
        out = out + lut[tuple(idx)] * wgt[..., None]
    return out


def paint_test1(color_path, elev_path, size):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import generate_example_textures as gen

    print("  learning Earth's terrain palette ...")
    land_lut, ocean_lut = earth_palette(color_path, elev_path)
    print("  building Test1's own continents ...")
    P, lat = gen.sphere_coords(size, size // 2)
    h = gen.test1_height(P)
    moist = gen.test1_moisture(P)
    detail = gen.Noise3D(77).fbm(P, 40.0, 5)
    alat = np.abs(lat) / (np.pi / 2)
    alat = alat ** 2                               # more temperate: less ice than Earth
    lc = np.clip(alat * NL - 0.5, 0, NL - 1)

    img = np.zeros(h.shape + (3,), np.float32)
    land = h > 0.5
    e = _rank01(h[land]) * NE - 0.5
    q = np.clip(_rank01(moist[land]) + 0.15 * detail[land], 0, 1) * NQ - 0.5
    img[land] = _lookup(land_lut, [np.clip(e, 0, NE - 1), lc[land], np.clip(q, 0, NQ - 1)])
    depth = _rank01(h[~land])                       # 0 = deepest, 1 = coast
    img[~land] = _lookup(ocean_lut, [lc[~land], np.clip(depth * NQ - 0.5, 0, NQ - 1)])
    img *= (0.94 + 0.12 * detail)[..., None]       # fine-grained variation
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGB")


def convert(src, mode, size):
    w, h = size, size // 2
    if mode == "palette":
        return paint_test1(src[0], src[1], size)
    img = Image.open(src)
    if mode == "clouds":
        img = ImageOps.autocontrast(img.convert("L"), cutoff=0.5)
        a = np.asarray(img)
        img = Image.fromarray(np.roll(a, a.shape[1] // 2, axis=1))   # shift 180 deg
    elif mode == "height16":
        # 16-bit elevation -> stretch to full 8-bit range
        a = np.asarray(img, dtype=np.float32)
        lo, hi = np.percentile(a, [0.5, 99.5])
        a = np.clip((a - lo) / (hi - lo), 0, 1)
        img = Image.fromarray((a * 255).astype(np.uint8), "L")
    elif mode == "gray":
        img = img.convert("L")
        img = ImageOps.autocontrast(img, cutoff=0.5)
    else:
        img = img.convert("RGB")
    return img.resize((w, h), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=4096, help="output width (height = width/2)")
    ap.add_argument("--keep-downloads", action="store_true", help="keep the raw NASA files in .download_cache/")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    failed = []
    for name, (url, mode) in SOURCES.items():
        print(name)
        try:
            src = tuple(download(u) for u in url) if isinstance(url, tuple) else download(url)
            img = convert(src, mode, args.size)
            img.save(OUT / name, quality=92, optimize=True)
            print(f"  -> {OUT.relative_to(ROOT) / name}  {img.size[0]}x{img.size[1]}")
        except Exception as e:  # keep the example texture on any failure
            print(f"  !! failed ({e}); keeping the example texture")
            failed.append(name)

    if not args.keep_downloads:
        shutil.rmtree(CACHE, ignore_errors=True)
    print("done" + (f" - {len(failed)} kept as examples: {', '.join(failed)}" if failed else ""))
    sys.exit(1 if len(failed) == len(SOURCES) else 0)


if __name__ == "__main__":
    main()
