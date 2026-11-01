#!/usr/bin/env python3
"""Replace ALL of SpaceEngine's music with Null's black-hole sounds - without touching
the game's own files.

SpaceEngine loads a file from an addon instead of data/ when it has the same relative
path and name. This script lists every track in <SpaceEngine>/data/music/ and puts a
same-named copy of one of Null's black-hole sounds in this addon's music/ folder, so
the game plays the black hole wherever it would have played its own music.

    python3 tools/override_music.py "C:/Games/SpaceEngine"            # override
    python3 tools/override_music.py "C:/Games/SpaceEngine" --undo     # restore

Run it on the Nulled folder that is INSTALLED in SpaceEngine/addons/ (or run it here
and copy the folder over afterwards). Run tools/fetch_black_hole_sounds.py first.
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUSIC = ROOT / "music"
MANIFEST = MUSIC / ".overrides.txt"
AUDIO = {".ogg", ".mp3", ".wav", ".flac"}

# The long ambient bed comes up most often; the raw sonifications are mixed in.
ROTATION = [
    "Null - Event Horizon (ambient).ogg",
    "Null - Perseus Black Hole.ogg",
    "Null - Event Horizon (ambient).ogg",
    "Null - M87 Radio.ogg",
    "Null - Event Horizon (ambient).ogg",
    "Null - M87 Composite.ogg",
    "Null - Event Horizon (ambient).ogg",
    "Null - M87 X-ray.ogg",
]


def undo():
    if not MANIFEST.exists():
        print("nothing to undo")
        return
    for rel in MANIFEST.read_text().splitlines():
        p = MUSIC / rel
        if p.exists():
            p.unlink()
            print(f"  removed music/{rel}")
            parent = p.parent
            while parent != MUSIC and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
    MANIFEST.unlink()
    print("SpaceEngine's own music is back.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spaceengine_dir", help="SpaceEngine installation folder (contains data/)")
    ap.add_argument("--undo", action="store_true", help="remove the overrides again")
    args = ap.parse_args()

    if args.undo:
        undo()
        return

    game_music = Path(args.spaceengine_dir) / "data" / "music"
    if not game_music.is_dir():
        sys.exit(f"not found: {game_music}  (pass the SpaceEngine installation folder)")
    sources = [MUSIC / n for n in ROTATION]
    missing = [s.name for s in sources if not s.exists()]
    if missing:
        sys.exit(f"missing {missing} - run tools/fetch_black_hole_sounds.py first")

    tracks = sorted(p for p in game_music.rglob("*") if p.suffix.lower() in AUDIO)
    if not tracks:
        sys.exit(f"no music files found in {game_music}")
    done = []
    for i, t in enumerate(tracks):
        rel = t.relative_to(game_music)
        if rel.suffix.lower() != ".ogg":
            print(f"  skip {rel} (only .ogg can be replaced by an .ogg)")
            continue
        dest = MUSIC / rel
        if dest.resolve() in {s.resolve() for s in sources}:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sources[i % len(sources)], dest)
        done.append(rel.as_posix())
        print(f"  music/{rel}  <-  {sources[i % len(sources)].name}")
    old = MANIFEST.read_text().splitlines() if MANIFEST.exists() else []
    MANIFEST.write_text("\n".join(sorted(set(old + done))) + "\n")
    print(f"Overrode {len(done)} SpaceEngine tracks. Restart SpaceEngine. Undo with --undo.")


if __name__ == "__main__":
    main()
