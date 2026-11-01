# Nulled — a SpaceEngine addon by Developer1XD

A black hole system called **Null**, floating in intergalactic space just outside
the Andromeda Galaxy (M31) — ~2.58 million light years from Sol, ~133 000 ly from
M31's centre, out in its halo, beyond the visible disk. Search `M31` (F3) to see the galaxy, then `Null`.

```
Null                      8 M☉ Kerr black hole + accretion disk and jets
├── Test1                 earth-like world · 3D animated ocean · procedural land
│   │                     procedural rings · procedural clouds · atmosphere · life
│   └── TestAsteroid      Ganymede-sized moon (2634 km radius), cratered & grooved
└── Test2                 brown dwarf (~40 Jupiter masses) · procedural rings
    │                     banded procedural storm clouds
    ├── TestEarth1        ┐
    ├── TestEarth2        │ 12 Earth-sized moons (6371 km, 1 Earth mass),
    ├── …                 │ each with its own procedural surface, ocean,
    └── TestEarth12       ┘ clouds and atmosphere (different random seeds)
```

## Install

1. Copy the whole `Nulled` folder into `SpaceEngine/addons/`
   (so you get `SpaceEngine/addons/Nulled/catalogs/...`).
2. Start SpaceEngine, press **F3** and search for `Null`, `Test1`, `Test2`, `TestEarth7`, …

For the best look, set planet texture resolution / landscape quality to high in the
graphics settings — the textures are 4096×2048 (4K).

## Black hole → Earth (the "Null transit")

SpaceEngine has no portal/teleport feature, so flying into a black hole on its own
does nothing special. The addon ships a script that plays the transit for you:

`scripts/Null_EnterBlackHole.se` — flies you into Null's event horizon, drops you
on the surface of Earth's Moon, lifts you off it and flies you home to Earth.

Run it from SpaceEngine's script menu, or from the console (`~`) with the
`Run` command and the script name. The menu location differs a bit between
SpaceEngine versions.

## Textures (4K)

All textures live in `textures/planets/Null/` and are referenced by the catalogs.

| File | Example (generated) | Web version (NASA, public domain) |
|---|---|---|
| `Test1_diff.jpg` | procedural continents | **same invented continents**, painted with real terrain colours learned from Blue Marble NG + GEBCO elevation |
| `Test1_bump.jpg` | procedural heightmap | — (stays Test1's own heightmap) |
| `Test1_clouds.jpg` | procedural clouds | Blue Marble cloud composite (shifted 180°) |
| `TestAsteroid_diff.jpg` | procedural cratered crust | LRO LROC colour mosaic |
| `TestAsteroid_bump.jpg` | procedural craters/grooves | LRO LOLA elevation |
| `Test2_diff.jpg` | procedural banded atmosphere | — (stays generated) |

Test1 never gets Earth's continents: its land shapes are always its own, the web data
only supplies realistic colours (forest, desert, tundra, ice, shallow/deep water).

The 12 TestEarth moons are fully procedural (no textures), so every one is unique.
SpaceEngine adds procedural detail on top of the textured bodies when you get close.

```bash
# 1. offline example textures (what the addon starts with)
python3 tools/generate_example_textures.py
# 2. replace them with real imagery pulled from NASA (~130 MB download, cleaned up after)
python3 tools/fetch_web_textures.py
```

Both need Python 3 with `numpy` and `Pillow` (`pip install numpy pillow`).
`--size 8192` gives 8K textures if your GPU can take it.

Want Test1 / TestAsteroid fully procedural (SpaceEngine-generated) instead? Delete the `DiffMap` / `BumpMap`
lines for them in `catalogs/planets/Null.sc`.

## Editing the system

`catalogs/planets/Null.sc` is generated — change `tools/build_catalog.py` and run:

```bash
python3 tools/build_catalog.py
```

Orbital periods are computed with Kepler's third law; all moons sit outside their
planet's Roche limit and well inside its Hill sphere.

## Notes

* Lighting comes from the accretion disk (`Luminosity` in `catalogs/stars/Null.sc`).
  Raise it if the planets look too dark.
* Accretion disk keys can differ between SpaceEngine versions. If the disk doesn't
  show up, check the SpaceEngine log (`system/se.log`) for unknown keys.
