// ============================================================================
//  Nulled - by Developer1XD
//  Star catalog: the "Null" black hole
//
//  Install: copy the whole "Nulled" folder into  SpaceEngine/addons/
//  Then search for "Null" (F3) in SpaceEngine.
// ============================================================================

Star "Null"
{
	RA          14 29 43.0      // right ascension (h m s)
	Dec        -62 40 46.0      // declination (deg ' ")
	Dist        42.0            // distance from Sol, light years

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
