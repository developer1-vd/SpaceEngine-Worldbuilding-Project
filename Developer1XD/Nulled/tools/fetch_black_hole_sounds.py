#!/usr/bin/env python3
"""Download NASA's real black-hole sonifications and turn them into SpaceEngine music.

Run from the Nulled folder:   python3 tools/fetch_black_hole_sounds.py
Needs ffmpeg on PATH.

Sources (NASA Chandra X-ray Center, "A Universe of Sound"):
  * Perseus galaxy cluster black hole - real pressure waves (sound) travelling through
    the hot cluster gas, detected by Chandra and scaled up 57-58 octaves so humans
    can hear them.                     https://chandra.si.edu/sound/perseus.html
  * M87 black hole - Chandra X-ray + VLA radio data mapped to sound (composite,
    X-ray only, radio only).           https://chandra.si.edu/sound/m87.html
Credit: NASA/CXC/SAO/K.Arcand, SYSTEM Sounds (M. Russo, A. Santaguida).

Output (music/ of this addon, OGG Vorbis - the format SpaceEngine plays):
  Null - Perseus Black Hole.ogg         the raw Perseus sonification (34 s)
  Null - M87 Composite.ogg              M87 X-ray + radio (33 s)
  Null - M87 X-ray.ogg
  Null - M87 Radio.ogg
  Null - Event Horizon (ambient).ogg    ~6 min seamless ambient bed: the Perseus
                                        sound looped with long crossfades, M87 radio
                                        layered quietly underneath
"""
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "music"
BASE = "https://chandra.si.edu/sound/sounds"

TRACKS = {
    "perseus_sonification.mp4": "Null - Perseus Black Hole.ogg",
    "m87_all.mp4": "Null - M87 Composite.ogg",
    "m87_xray.mp4": "Null - M87 X-ray.ogg",
    "m87_radio.mp4": "Null - M87 Radio.ogg",
}
LOUDNORM = "loudnorm=I=-18:TP=-1.5:LRA=11"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def download(name, dest_dir):
    dest = dest_dir / name
    print(f"  download {BASE}/{name}")
    with urllib.request.urlopen(f"{BASE}/{name}", timeout=120) as r, open(dest, "wb") as f:
        if not r.headers.get("Content-Type", "").startswith(("video/", "audio/")):
            raise RuntimeError(f"unexpected content type {r.headers.get('Content-Type')!r}")
        shutil.copyfileobj(r, f, 1 << 20)
    return dest


def main():
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is required (https://ffmpeg.org/download.html)")
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for src, out in TRACKS.items():
            print(out)
            mp4 = download(src, tmp)
            # audio only -> stereo 44.1 kHz OGG Vorbis, loudness-normalised, short fades
            ffmpeg("-i", str(mp4), "-vn", "-ac", "2", "-ar", "44100",
                   "-af", f"{LOUDNORM},afade=t=in:d=1.5,areverse,afade=t=in:d=2,areverse",
                   "-c:a", "libvorbis", "-q:a", "6", str(OUT / out))

        print("Null - Event Horizon (ambient).ogg")
        perseus = OUT / TRACKS["perseus_sonification.mp4"]
        radio = OUT / TRACKS["m87_radio.mp4"]
        loops, xf = 12, 6        # 12 passes, 6 s crossfades -> ~5.6 min
        inputs, chain = [], ""
        for _ in range(loops):
            inputs += ["-i", str(perseus)]
        prev = "[0:a]"
        for i in range(1, loops):
            chain += f"{prev}[{i}:a]acrossfade=d={xf}:c1=qsin:c2=qsin[x{i}];"
            prev = f"[x{i}]"
        inputs += ["-stream_loop", "-1", "-i", str(radio)]
        chain += (f"[{loops}:a]volume=0.25,lowpass=f=900[bed];"
                  f"{prev}[bed]amix=inputs=2:duration=first:normalize=0,{LOUDNORM},"
                  f"afade=t=in:d=8,areverse,afade=t=in:d=10,areverse[out]")
        ffmpeg(*inputs, "-filter_complex", chain, "-map", "[out]",
               "-ac", "2", "-ar", "44100", "-c:a", "libvorbis", "-q:a", "6",
               str(OUT / "Null - Event Horizon (ambient).ogg"))
    for f in sorted(OUT.glob("*.ogg")):
        print(f"  {f.relative_to(ROOT)}  {f.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
