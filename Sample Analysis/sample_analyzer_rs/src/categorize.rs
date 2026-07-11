use crate::normalize::normalize_name;

/// Categorize a sample by its (full-path) name, tolerant of the many spelling /
/// abbreviation conventions for drum elements. Phrases are matched as substrings
/// of the normalized name; ABBREVIATIONS are matched as whole tokens (so "bd"
/// hits "BD_01" but not "bird"). Order = most specific first.
/// Returns (group, subgroup, matched-token). `subgroup` is a curated instrument
/// level under a broader group ("Conga" under "Perc", "Synth" under "Keyboards")
/// or "" when the group has no deeper level (then the length tier is used).
pub fn categorize(name: &str) -> (&'static str, &'static str, &'static str) {
    let norm = normalize_name(name);
    let toks: Vec<&str> = norm.split_whitespace().collect();
    let tok = |t: &str| toks.iter().any(|x| *x == t);
    let ph = |p: &str| norm.contains(p);

    // "cym" anywhere ⇒ definitely a cymbal (highest priority).
    if norm.contains("cym") {
        return ("Cymbal", "", "cym");
    }

    // Each rule: (group, subgroup, phrases[], abbrev-tokens[]). subgroup "" ⇒
    // no curated instrument level (the length tier fills the subgroup instead).
    // Order = most specific first.
    const RULES: &[(&str, &str, &[&str], &[&str])] = &[
        // Impulse responses (convolution / cabinet / reverb IRs) — checked early.
        ("IR", "", &["impulse response", "impulse", "convolution", "convol", "cabinet", "guitar cab", "reverb ir"], &["ir", "cab", "conv"]),
        // Kick before Bass so "bass drum" -> Kick, plain "bass" -> Bass.
        ("Kick", "", &["kick", "kik", "bass drum", "bassdrum"], &["bd", "kk", "kik", "kic", "kck"]),
        ("Snare", "", &["snare"], &["sd", "sn", "snr"]),
        // Hi-hat variants (closed/open/pedal).
        ("HiHat", "", &["hihat", "hi hat", "closed hat", "open hat", "pedal hat", "hat"], &["hh", "chh", "ohh", "ch", "oh", "ph"]),
        ("Ride", "", &["ride bell", "ride cymbal", "ride"], &["rd", "rdcym"]),
        ("Cymbal", "", &["crash cymbal", "splash cymbal", "cymbal", "crash", "splash"], &["cy", "cym", "crsh"]),
        ("Clap", "", &["handclap", "hand clap", "clap"], &["cp", "clp"]),
        ("Rim", "", &["rimshot", "rim shot", "cross stick", "crossstick", "rim"], &["rs", "rm"]),
        // Toms split high / mid / low, then generic.
        ("Tom Hi", "", &["high tom", "hi tom", "rack tom 1", "tom 1", "hitom"], &["ht", "hitom"]),
        ("Tom Mid", "", &["mid tom", "middle tom", "rack tom 2", "tom 2", "midtom"], &["mt", "midtom"]),
        ("Tom Lo", "", &["low tom", "floor tom", "tom 3", "lotom"], &["lt", "ft", "lotom"]),
        ("Tom", "", &["tom"], &["tm"]),
        // Auxiliary percussion — all under "Perc" with a curated subgroup.
        ("Perc", "Cowbell", &["cowbell", "cow bell"], &["cb", "cow", "cowb"]),
        ("Perc", "Conga", &["conga", "tumba", "quinto"], &["cg", "con", "cng"]),
        ("Perc", "Bongo", &["bongo"], &["bng"]),
        ("Perc", "Clave", &["claves", "clave"], &["cv", "clv"]),
        ("Perc", "Shaker", &["shaker", "maracas", "cabasa"], &["shk", "sh"]),
        ("Perc", "Block", &["woodblock", "wood block", "block"], &["wb"]),
        ("Perc", "", &["percussion", "auxiliary", "perc"], &["prc"]),
        ("Guitar", "", &["guitar", "gtr", "acoustic gt", "electric gt"], &["gtr", "gt"]),
        ("Strings", "", &["strings", "string", "violin", "viola", "cello", "orchestra", "ensemble", "pizz", "arco"], &[]),
        // 808 is a drum machine, NOT bass — so it is intentionally not a Bass keyword.
        ("Bass", "", &["bass", "sub bass"], &["sub"]),
        ("Vocal", "", &["vocal", "voice", "vox"], &["vx"]),
        // Keyboards — new group with curated subgroups (Electric Piano before
        // Piano so "epiano" doesn't fall through to plain Piano).
        ("Keyboards", "Electric Piano", &["electric piano", "rhodes", "wurlitzer", "wurli", "e-piano", "epiano"], &["ep"]),
        ("Keyboards", "Organ", &["organ", "hammond"], &["org"]),
        ("Keyboards", "Clav", &["clavinet", "clav"], &[]),
        ("Keyboards", "Piano", &["grand piano", "upright piano", "piano"], &["pno"]),
        ("Keyboards", "Synth", &["synthesizer", "synth"], &["syn"]),
        ("Keyboards", "", &["keyboard", "keys"], &["kb", "keyb"]),
        // Turntablism: scratches are their own group; DJ = turntable / decks.
        ("Scratch", "", &["scratches", "scratch"], &["scr"]),
        ("DJ", "", &["turntable", "deck"], &["dj"]),
        ("FX", "", &["sound effect", "foley", "atmosphere", "atmos", "riser", "sweep", "noise",
                 "impact", "boom", "zap", "glitch", "drone", "whoosh", "reverse", "downlifter",
                 "uplifter", "riser", "sfx", "fx"], &["fx", "sfx"]),
        ("Loops/Patterns", "", &["loop", "groove", "beat"], &["lp"]),
    ];

    for (cat, sub, phrases, abbrevs) in RULES {
        if let Some(p) = phrases.iter().find(|p| ph(p)) {
            return (cat, sub, p);
        }
        if let Some(a) = abbrevs.iter().find(|a| tok(a)) {
            return (cat, sub, a);
        }
    }
    ("Unclassified", "", "")
}

#[cfg(test)]
mod tests {
    use super::categorize;

    #[test]
    fn naming_conventions() {
        // (name, want_group, want_subgroup)
        let cases: &[(&str, &str, &str)] = &[
            ("Kick_01.wav", "Kick", ""), ("BD_808.wav", "Kick", ""), ("Bass Drum 3.wav", "Kick", ""),
            ("Kk-tight.wav", "Kick", ""), ("Kik_punchy.wav", "Kick", ""),
            ("Snare_Acoustic.wav", "Snare", ""), ("SD_04.wav", "Snare", ""), ("Snr_rimmy.wav", "Snare", ""),
            ("HiHat_closed.wav", "HiHat", ""), ("HH_01.wav", "HiHat", ""), ("OH_open.wav", "HiHat", ""),
            ("CH_tight.wav", "HiHat", ""), ("Pedal Hat.wav", "HiHat", ""), ("808_HH.wav", "HiHat", ""),
            ("Perc_shot.wav", "Perc", ""), ("PRC_02.wav", "Perc", ""),
            ("Clap_big.wav", "Clap", ""), ("CP_room.wav", "Clap", ""), ("Handclap.wav", "Clap", ""),
            ("Rimshot.wav", "Rim", ""), ("RS_dry.wav", "Rim", ""), ("Cross-stick.wav", "Rim", ""),
            ("Low Tom.wav", "Tom Lo", ""), ("FT_floor.wav", "Tom Lo", ""), ("Tom3.wav", "Tom Lo", ""),
            ("Mid Tom.wav", "Tom Mid", ""), ("Tom2.wav", "Tom Mid", ""),
            ("High Tom.wav", "Tom Hi", ""), ("HT_rack.wav", "Tom Hi", ""), ("Tom1.wav", "Tom Hi", ""),
            ("Crash Cymbal.wav", "Cymbal", ""), ("CY_splash.wav", "Cymbal", ""), ("Crsh.wav", "Cymbal", ""),
            ("OHCYM.wav", "Cymbal", ""), ("808_CYM.wav", "Cymbal", ""), ("Tom_cym_hit.wav", "Cymbal", ""),
            ("Hall_IR.wav", "IR", ""), ("guitar_cab.wav", "IR", ""), ("Impulse_room.wav", "IR", ""),
            ("Convolution 01.wav", "IR", ""),
            ("Ride Bell.wav", "Ride", ""), ("RD_ping.wav", "Ride", ""),
            // Auxiliary percussion — now Perc with a curated subgroup.
            ("Cowbell.wav", "Perc", "Cowbell"), ("CB_hi.wav", "Perc", "Cowbell"),
            ("Conga_open.wav", "Perc", "Conga"), ("Tumba.wav", "Perc", "Conga"), ("Quinto.wav", "Perc", "Conga"),
            ("Bongo_hi.wav", "Perc", "Bongo"),
            ("Claves.wav", "Perc", "Clave"), ("CV_01.wav", "Perc", "Clave"),
            ("Shaker.wav", "Perc", "Shaker"), ("Maracas.wav", "Perc", "Shaker"), ("Cabasa.wav", "Perc", "Shaker"),
            ("Woodblock.wav", "Perc", "Block"), ("Wood Block 2.wav", "Perc", "Block"),
            ("FX_riser.wav", "FX", ""), ("SFX_boom.wav", "FX", ""), ("Foley_door.wav", "FX", ""),
            ("Sub_808.wav", "Bass", ""), ("Bassline.wav", "Bass", ""),
            ("Vox_chop.wav", "Vocal", ""), ("Vocal_ah.wav", "Vocal", ""),
            // Keyboards — new group with curated subgroups.
            ("SynthLead.wav", "Keyboards", "Synth"), ("Analog Synth.wav", "Keyboards", "Synth"),
            ("Grand Piano C3.wav", "Keyboards", "Piano"), ("Rhodes_ep.wav", "Keyboards", "Electric Piano"),
            ("Hammond_organ.wav", "Keyboards", "Organ"), ("Clavinet.wav", "Keyboards", "Clav"),
            ("Keyboard_pad.wav", "Keyboards", ""),
            // Turntablism (Scratch is its own group) + DJ + Loops/Patterns.
            ("Scratch_01.wav", "Scratch", ""), ("Vinyl_scratches.wav", "Scratch", ""),
            ("DJ_scratch.wav", "Scratch", ""), ("Turntable_stop.wav", "DJ", ""), ("DJ_fx.wav", "DJ", ""),
            ("Beat_01.wav", "Loops/Patterns", ""), ("Groove.wav", "Loops/Patterns", ""), ("Loop_120.wav", "Loops/Patterns", ""),
            ("randomthing.wav", "Unclassified", ""),
        ];
        for (name, want_g, want_sg) in cases {
            let (got, sub, why) = categorize(name);
            assert_eq!(got, *want_g, "categorize({:?}) group = {:?} (why {:?}), want {:?}", name, got, why, want_g);
            assert_eq!(sub, *want_sg, "categorize({:?}) subgroup = {:?}, want {:?}", name, sub, want_sg);
        }
    }
}
