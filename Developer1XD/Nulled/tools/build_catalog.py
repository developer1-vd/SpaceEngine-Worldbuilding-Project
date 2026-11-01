#!/usr/bin/env python3
"""Generate catalogs/planets/Null.sc for the Nulled SpaceEngine addon.

Run from the Nulled folder:   python3 tools/build_catalog.py
Orbital periods are computed from Kepler's 3rd law so the system is stable.
"""
import math
import random
from pathlib import Path

G = 6.674e-11
M_SUN = 1.989e30
M_EARTH = 5.972e24
AU = 1.496e11
YEAR = 365.25 * 86400
DAY = 86400

BH_MASS_SOL = 8.0          # must match catalogs/stars/Null.sc
TEX = "Null"               # textures/planets/Null/...

OUT = Path(__file__).resolve().parent.parent / "catalogs" / "planets" / "Null.sc"


def period_years(a_au, m_central_kg):
    a = a_au * AU
    return 2 * math.pi * math.sqrt(a ** 3 / (G * m_central_kg)) / YEAR


def period_days_km(a_km, m_central_kg):
    a = a_km * 1000
    return 2 * math.pi * math.sqrt(a ** 3 / (G * m_central_kg)) / DAY


def vec(v):
    return "(" + ", ".join(f"{x:.3f}" for x in v) + ")"


def rings(inner, outer, seed, front, back_thick, back_illum):
    r = random.Random(seed)
    return f"""
	Rings                                  // procedural rings
	{{
		InnerRadius     {inner}
		OuterRadius     {outer}
		EdgeRadius      {outer}
		MeanRadius      {(inner + outer) / 2:.0f}
		Thickness       0.6
		RocksMaxSize    20
		RocksSpacing    45
		DustDrawDist    40
		ChartRadius     40
		RotationPeriod  {r.uniform(8, 20):.2f}
		Brightness      1.0
		FrontBright     1.3
		BackBright      2.5
		Density         0.85
		Opacity         1.0
		SelfShadow      1.0
		PlanetShadow    1.0
		Hapke           0.4
		SpotBright      1.5
		SpotWidth       0.002
		Randomize       {vec([r.uniform(-1, 1) for _ in range(3)])}
		frequency       {r.uniform(3, 6):.2f}
		densityScale    1.5
		densityOffset   0.6
		densityPower    0.9
		colorContrast   1.6
		FrontColor      {vec(front)}
		BackThickColor  {vec(back_thick)}
		BackIllumColor  {vec(back_illum)}
	}}"""


def terra_surface(seed, diff=None, bump=None, bump_height=12.0, sea=0.5):
    """Procedural Earth-like surface; optional 4K textures on top."""
    r = random.Random(seed)
    maps = ""
    if diff:
        maps += f'\t\tDiffMap         "{TEX}/{diff}"\n'
    if bump:
        maps += f'\t\tBumpMap         "{TEX}/{bump}"\n\t\tBumpHeight      {bump_height}\n\t\tBumpOffset      {bump_height * sea:.2f}\n'
    return f"""
	Surface                                // procedural terrain (detail is added on top of textures)
	{{
{maps}		SurfStyle       {r.uniform(0, 1):.3f}
		Randomize       {vec([r.uniform(-1, 1) for _ in range(3)])}
		colorDistMagn   0.06
		colorDistFreq   500
		detailScale     30000
		seaLevel        {sea:.2f}
		snowLevel       0.85
		tropicLatitude  0.16
		icecapLatitude  0.82
		icecapHeight    0.4
		climatePole     0.95
		climateTropic   0.45
		climateEquator  0.65
		climateSteppeMin 0.4
		climateSteppeMax 0.6
		climateForestMin 0.6
		climateForestMax 0.9
		climateGrassMin 0.1
		climateGrassMax 0.4
		heightTempGrad  0.7
		beachWidth      0.0004
		mainFreq        {r.uniform(1.0, 2.2):.2f}
		terraceProb     0.5
		erosion         0.4
		montesMagn      {r.uniform(0.5, 0.9):.2f}
		montesFreq      450
		montesSpiky     0.95
		montesFraction  0.45
		hillsMagn       0.18
		hillsFreq       1000
		hillsFraction   0.4
		hills2Fraction  0.3
		dunesMagn       0.05
		dunesFreq       60
		dunesFraction   0.3
		riversMagn      60
		riversFreq      2.5
		riversSin       5
		riftsMagn       4
		riftsFreq       3
		riftsSin        5
		canyonsMagn     0.08
		canyonsFreq     120
		canyonsFraction 0.25
		cracksMagn      0.02
		cracksFreq      0.6
		cracksOctaves   2
		craterMagn      0.05
		craterFreq      25
		craterDensity   0.08
		craterOctaves   4
		volcanoMagn     0.15
		volcanoFreq     1.2
		volcanoDensity  0.2
		volcanoOctaves  2
		volcanoActivity 0.25
		volcanoFlows    0.6
		volcanoRadius   0.6
		volcanoTemp     1300
	}}"""


def ocean(color=(0.04, 0.22, 0.45)):
    return f"""
	NoOcean false
	Ocean                                  // animated 3D water (waves, reflections)
	{{
		Height          4.0
		Hapke           0.0
		SpotBright      3.0
		SpotWidth       0.25
		DayAmbient      0.07
		RoughnessBias   0.0
		RoughnessScale  1.0
		DiffColor       {vec(color)}
		Composition
		{{
			H2O         96.5
			NaCl        3.5
		}}
	}}"""


def terra_clouds(seed, diff=None, coverage=0.55):
    r = random.Random(seed)
    tex = f'\t\tDiffMap         "{TEX}/{diff}"\n' if diff else ""
    return f"""
	Clouds                                 // procedural, animated cloud layer
	{{
{tex}		Height          9
		Velocity        {r.uniform(40, 90):.1f}
		BumpHeight      3
		Hapke           0.2
		DayAmbient      0.7
		ModulateColor   (1.000, 1.000, 1.000, 1.000)
		mainFreq        1.0
		mainOctaves     10
		Coverage        {coverage:.2f}
		stripeZones     1.6
		stripeTwist     0.25
		stripeFluct     0.6
		cycloneMagn     {r.uniform(1.5, 3.0):.2f}
		cycloneFreq     0.6
		cycloneDensity  0.5
		cycloneOctaves  4
	}}"""


def earth_atmo(bright=10, hue=0.0):
    return f"""
	Atmosphere
	{{
		Model           "Earth"
		Height          100
		Density         1.0
		Pressure        1.0
		Greenhouse      33
		Bright          {bright}
		Opacity         1.0
		SkyLight        4
		Hue             {hue:.2f}
		Saturation      1.0
		Composition
		{{
			N2          78.08
			O2          20.95
			Ar          0.93
			CO2         0.04
		}}
	}}"""


def body(kind, name, parent, cls, mass_earth, radius_km, orbit, extra, rot_h, tilt):
    return f"""
{kind} "{name}"
{{
	ParentBody      "{parent}"
	Class           "{cls}"
	Mass            {mass_earth}        // Earth masses
	Radius          {radius_km}         // km
	RotationPeriod  {rot_h}             // hours
	Obliquity       {tilt}
{extra}

	Orbit
	{{
		RefPlane        "Equator"
{orbit}
	}}
}}
"""


def orbit_au(a_au, ecc, inc, m_central_kg):
    return (f"\t\tSemiMajorAxis   {a_au}          // AU\n"
            f"\t\tPeriod          {period_years(a_au, m_central_kg):.5f}     // years\n"
            f"\t\tEccentricity    {ecc}\n"
            f"\t\tInclination     {inc}")


def orbit_km(a_km, ecc, inc, m_central_kg, phase):
    return (f"\t\tSemiMajorAxis   {a_km / (AU / 1000):.8f}   // AU ({a_km:,.0f} km)\n"
            f"\t\tPeriod          {period_days_km(a_km, m_central_kg) / 365.25:.7f}   // years "
            f"({period_days_km(a_km, m_central_kg):.2f} days)\n"
            f"\t\tEccentricity    {ecc}\n"
            f"\t\tInclination     {inc}\n"
            f"\t\tMeanAnomaly     {phase:.1f}")


def main():
    random.seed(1337)
    m_bh = BH_MASS_SOL * M_SUN
    out = ["""// ============================================================================
//  Nulled - by Developer1XD
//  Planet catalog for the "Null" black hole system.
//  GENERATED by tools/build_catalog.py - edit that script, then re-run it.
//
//  Null (black hole, accretion disk)
//   |- Test1         earth-like world, 3D ocean, rings, clouds
//   |   '- TestAsteroid   Ganymede-sized moon
//   '- Test2         brown dwarf, rings, banded clouds
//       '- TestEarth1 ... TestEarth12   Earth-sized moons
// ============================================================================
"""]

    # ---------------- Test1: earth-like planet ----------------
    t1_mass, t1_radius = 1.15, 6650
    extra = (
        "\tAlbedoBond      0.30\n\tAlbedoGeom      0.37\n"
        "\tLife\n\t{\n\t\tClass  \"Organic\"\n\t\tType   \"Multicellular\"\n\t\tBiome  \"Marine/Terrestrial\"\n\t}"
        + terra_surface(11, diff="Test1_diff", bump="Test1_bump", bump_height=14.0, sea=0.5)
        + ocean()
        + terra_clouds(12, diff="Test1_clouds", coverage=0.5)
        + earth_atmo()
        + rings(10500, 21000, 13, (0.85, 0.80, 0.72), (0.92, 0.86, 0.76), (0.45, 0.62, 0.95))
    )
    out.append(body("Planet", "Test1", "Null", "Terra", t1_mass, t1_radius,
                    orbit_au(1.1, 0.02, 1.5, m_bh), extra, 23.4, 21.0))

    # TestAsteroid: Ganymede-sized moon of Test1 (R = 2634 km, M = 0.0248 Earth)
    extra = f"""
	AlbedoBond      0.25
	AlbedoGeom      0.40
	NoOcean         true
	Surface                                // procedural icy/rocky crust + 4K textures
	{{
		DiffMap         "{TEX}/TestAsteroid_diff"
		BumpMap         "{TEX}/TestAsteroid_bump"
		BumpHeight      10.0
		BumpOffset      5.0
		SurfStyle       0.72
		Randomize       (0.410, -0.770, 0.130)
		detailScale     20000
		mainFreq        1.6
		craterMagn      0.4
		craterFreq      40
		craterDensity   0.6
		craterOctaves   8
		cracksMagn      0.08
		cracksFreq      0.8
		cracksOctaves   3
		canyonsMagn     0.05
		canyonsFreq     80
		montesMagn      0.2
		hillsMagn       0.1
		erosion         0.1
		snowLevel       0.9
	}}"""
    out.append(body("Moon", "TestAsteroid", "Test1", "Selena", 0.0248, 2634,
                    orbit_km(240000, 0.01, 2.0, t1_mass * M_EARTH, 40.0), extra, 0, 0.2)
               .replace("RotationPeriod  0             // hours", "TidalLocked     true"))

    # ---------------- Test2: brown dwarf ----------------
    t2_mass, t2_radius = 12700, 64500        # ~40 Jupiter masses, ~0.9 R_Jupiter
    extra = f"""
	AlbedoBond      0.20
	AlbedoGeom      0.30
	TempMean        1100                   // hot, faintly glowing brown dwarf (T-type)
	Surface
	{{
		DiffMap         "{TEX}/Test2_diff"
		SurfStyle       0.85
		Randomize       (-0.620, 0.290, 0.880)
		colorDistMagn   0.2
		colorDistFreq   40
		mainFreq        1.0
	}}
	Clouds                                 // procedural banded storm layer
	{{
		Height          60
		Velocity        250
		BumpHeight      8
		Hapke           0.1
		DayAmbient      0.4
		ModulateColor   (0.820, 0.520, 0.360, 1.000)
		mainFreq        0.8
		mainOctaves     12
		Coverage        0.9
		stripeZones     9.0
		stripeTwist     1.4
		stripeFluct     0.8
		cycloneMagn     4.0
		cycloneFreq     0.4
		cycloneDensity  0.35
		cycloneOctaves  3
	}}
	Atmosphere
	{{
		Model           "Jupiter"
		Height          1500
		Density         2.0
		Pressure        1000
		Bright          8
		Opacity         1.0
		SkyLight        2
		Hue             0.04
		Saturation      1.3
		Composition
		{{
			H2          85.0
			He          14.5
			CH4         0.3
			H2O         0.1
			NH3         0.1
		}}
	}}""" + rings(95000, 240000, 21, (0.78, 0.62, 0.48), (0.86, 0.70, 0.55), (0.95, 0.55, 0.30))
    out.append(body("Planet", "Test2", "Null", "Jupiter", t2_mass, t2_radius,
                    orbit_au(5.2, 0.04, 3.0, m_bh), extra, 7.5, 12.0))

    # 12 Earth-sized moons, geometric spacing (well beyond mutual Hill radii, inside Test2's Hill sphere)
    m_t2 = t2_mass * M_EARTH
    for i in range(12):
        n = i + 1
        a_km = 520000 * 1.28 ** i
        r = random.Random(100 + n)
        sea = r.uniform(0.35, 0.65)
        water = (r.uniform(0.02, 0.08), r.uniform(0.15, 0.3), r.uniform(0.35, 0.55))
        extra = ("\tAlbedoBond      0.30\n\tAlbedoGeom      0.36"
                 + terra_surface(200 + n, sea=sea)
                 + ocean(water)
                 + terra_clouds(300 + n, coverage=r.uniform(0.35, 0.7))
                 + earth_atmo(bright=r.uniform(8, 12), hue=r.uniform(-0.05, 0.05)))
        out.append(body("Moon", f"TestEarth{n}", "Test2", "Terra", 1.0, 6371,
                        orbit_km(a_km, round(r.uniform(0.0, 0.03), 3), round(r.uniform(0, 4), 2),
                                 m_t2, r.uniform(0, 360)), extra, 0, round(r.uniform(0, 5), 1))
                   .replace("RotationPeriod  0             // hours", "TidalLocked     true"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(out))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
