#!/usr/bin/env python3
"""Download real planetary imagery from NASA and convert it to 4K SpaceEngine textures.

Run from the Nulled folder:   python3 tools/fetch_web_textures.py [--size 4096] [--keep-downloads]

What gets replaced (all sources are NASA, public domain):
  Test1_diff.jpg          <- NASA Blue Marble Next Generation, topography + bathymetry (Dec 2004)
  Test1_bump.jpg          <- NASA / GEBCO combined elevation map
  Test1_clouds.jpg        <- NASA Blue Marble cloud composite
  TestAsteroid_diff.jpg   <- NASA SVS CGI Moon Kit, LRO LROC colour mosaic
  TestAsteroid_bump.jpg   <- NASA SVS CGI Moon Kit, LRO LOLA elevation (LDEM)

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

SOURCES = {
    "Test1_diff.jpg": (f"{EO}/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg", "color"),
    "Test1_bump.jpg": (f"{EO}/73000/73934/gebco_08_rev_elev_21600x10800.png", "gray"),
    "Test1_clouds.jpg": (f"{EO}/57000/57747/cloud_combined_8192.tif", "gray"),
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


def convert(src, mode, size):
    w, h = size, size // 2
    img = Image.open(src)
    if mode == "height16":
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
            img = convert(download(url), mode, args.size)
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
