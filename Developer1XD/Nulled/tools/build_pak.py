#!/usr/bin/env python3
"""Build a SpaceEngine .pak release of the Nulled addon.

Run from the Nulled folder:
    python3 tools/build_pak.py                          # -> dist/
    python3 tools/build_pak.py --version 2              # Nulled-v002.pak
    python3 tools/build_pak.py --install "C:/Games/SpaceEngine"   # also install it

Follows the rules in the SpaceEngine manual ("Making addons > Introduction"):
  * a .pak is a zip archive renamed to .pak; only Deflate (or no) compression
  * its root holds the standard folders (catalogs/, scripts/, textures/ ...), no
    custom folders
  * .ogg music/sounds can NOT go inside a pak -> they ship loose next to it
  * textures are stored uncompressed (they are already JPEG; faster loading)

Output:
  dist/Nulled/                    drop this folder into SpaceEngine/addons/
      Nulled-v001.pak             catalogs/ + scripts/ + textures/
      music/*.ogg                 black-hole sounds (must stay loose)
      tools/override_music.py     optional music override
      README.md
  dist/Nulled-v001.zip            the same folder zipped, for sharing
"""
import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
NAME = "Nulled"

PAK_FOLDERS = ["catalogs", "scripts", "textures"]          # standard SE subfolders
STORED = {".jpg", ".jpeg", ".png", ".dds", ".tif", ".tiff"}  # already compressed
LOOSE_FILES = ["README.md", "tools/override_music.py"]
SKIP = {".overrides.txt"}


def pak_files():
    for folder in PAK_FOLDERS:
        for p in sorted((ROOT / folder).rglob("*")):
            if p.is_file() and p.name not in SKIP and not p.name.startswith("."):
                if p.suffix.lower() == ".ogg":
                    sys.exit(f"{p}: .ogg files are not allowed inside a .pak")
                yield p


def music_files():
    # only Null's own tracks, never copies made by override_music.py
    return sorted((ROOT / "music").glob("Null - *.ogg"))


def check_textures():
    """Every DiffMap/BumpMap/... in the catalogs must exist in textures/planets/."""
    missing = []
    for sc in (ROOT / "catalogs").rglob("*.sc"):
        for ref in re.findall(r'^\s*\w+Map\s+"([^"]+)"', sc.read_text(), re.M):
            base = ROOT / "textures" / "planets" / ref
            if not any(base.with_suffix(ext).exists() for ext in (".jpg", ".png", ".dds", ".tif")):
                missing.append(f"{sc.name}: {ref}")
    if missing:
        sys.exit("missing textures referenced by catalogs:\n  " + "\n  ".join(missing))


def build(version):
    check_textures()
    tag = f"v{version:03d}"
    out = DIST / NAME
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    pak = out / f"{NAME}-{tag}.pak"
    n = 0
    with zipfile.ZipFile(pak, "w") as z:
        for p in pak_files():
            method = zipfile.ZIP_STORED if p.suffix.lower() in STORED else zipfile.ZIP_DEFLATED
            z.write(p, p.relative_to(ROOT).as_posix(), compress_type=method)
            n += 1
    print(f"  {pak.relative_to(ROOT)}  ({n} files, {pak.stat().st_size / 1e6:.1f} MB)")

    for p in music_files():
        dest = out / "music" / p.name
        dest.parent.mkdir(exist_ok=True)
        shutil.copy2(p, dest)
    print(f"  {NAME}/music/  ({len(music_files())} .ogg tracks, loose)")
    for rel in LOOSE_FILES:
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)

    # verify the pak: standard folders only, Deflate/Stored only, readable
    with zipfile.ZipFile(pak) as z:
        bad = z.testzip()
        if bad:
            sys.exit(f"corrupt entry in pak: {bad}")
        for info in z.infolist():
            top = info.filename.split("/", 1)[0]
            if top not in PAK_FOLDERS:
                sys.exit(f"non-standard top-level folder in pak: {info.filename}")
            if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                sys.exit(f"unsupported compression for {info.filename}")

    release = DIST / f"{NAME}-{tag}.zip"
    with zipfile.ZipFile(release, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(DIST).as_posix())
    print(f"  {release.relative_to(ROOT)}  ({release.stat().st_size / 1e6:.1f} MB)  <- share this")
    return out


def install(out, se_dir):
    addons = Path(se_dir) / "addons"
    if not addons.is_dir():
        sys.exit(f"not a SpaceEngine folder (no addons/): {se_dir}")
    dest = addons / NAME
    if dest.exists():
        loose = [f for f in PAK_FOLDERS if (dest / f).exists()]
        if loose:
            sys.exit(f"{dest} has loose {loose} folders (an unpacked install). Remove them "
                     "first so they don't clash with the .pak.")
        for old in dest.glob(f"{NAME}-v*.pak"):
            old.unlink()
    shutil.copytree(out, dest, dirs_exist_ok=True)
    print(f"installed to {dest}")


def main():
    ap = argparse.ArgumentParser(description="Build the Nulled .pak release")
    ap.add_argument("--version", type=int, default=1, help="release number (default 1 -> v001)")
    ap.add_argument("--install", metavar="SPACEENGINE_DIR", help="also install into <dir>/addons/Nulled")
    args = ap.parse_args()
    print(f"Building {NAME} v{args.version:03d}")
    out = build(args.version)
    if args.install:
        install(out, args.install)


if __name__ == "__main__":
    main()
