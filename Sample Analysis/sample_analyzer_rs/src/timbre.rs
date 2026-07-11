/// Blindly classify a one-shot by its extracted features (name-independent).
pub fn classify_timbre(
    transients: usize,
    attack: f64,
    crest: f64,
    harmonicity: f64,
    _centroid: f64,
    low: f64,
    high: f64,
) -> &'static str {
    if transients > 1 {
        return "Loop";
    }
    if attack > 0.3 && crest < 4.0 {
        return "Pad"; // slow onset, sustained
    }
    if harmonicity > 0.45 {
        return if low > 0.6 { "Bass" } else { "Tonal" };
    }
    if high > 0.5 {
        return "Bright"; // hats / cymbals / noise-highs
    }
    if crest > 6.0 || attack < 0.02 {
        return "Percussive";
    }
    "Noise"
}
