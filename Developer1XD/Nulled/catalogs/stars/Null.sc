// ============================================================================
//  Nulled - by Developer1XD
//  Star catalog: the "Null" black hole
//
//  Install: copy the whole "Nulled" folder into  SpaceEngine/addons/
//  Then search for "Null" (F3) in SpaceEngine.
// ============================================================================

Star "Null"
{
	// Located OUTSIDE the Andromeda Galaxy (M31), in intergalactic space.
	// M31's centre: RA 00 42 44.3, Dec +41 16 09, ~778 000 pc (~2.54 million ly).
	// Null sits ~2.6 deg off M31's disk (perpendicular to its major axis) and a bit
	// beyond it: ~40 700 pc (~133 000 ly) from M31's centre, out in the halo.
	RA          00 33 10.0      // right ascension (h m s)
	Dec        +43 30 00.0      // declination (deg ' ")
	Dist        790000          // distance from Sol, parsecs (~2.58 million ly)

	Class      "X"              // X = black hole
	MassSol     8.0             // 8 solar masses -> event horizon ~24 km
	KerrSpin    0.92            // fast-spinning (Kerr) black hole
	KerrCharge  0.0

	// The hot accretion disk is what lights up the planets of this system.
	Luminosity  0.6             // in Sun luminosities
	Teff        9000            // apparent colour temperature of the disk glow

	AccretionDisk
	{
		InnerRadius      3.0     // in event-horizon radii (ISCO for a Kerr hole is close in)
		OuterRadius      600.0   // in event-horizon radii
		Thickness        0.02
		Temperature      12000   // K at the inner edge
		Brightness       2.5
		Density          1.0
		TwistMagn        6.0     // spiral turbulence
		AngularVelocity  1.0     // animated rotation of the disk
		Jets             true
		JetLength        300.0
	}
}
