use crate::peak::Peak;

/// The 9-D acoustic feature vector used for blind clustering (name-independent).
pub fn feature_vec(p: &Peak) -> [f64; 9] {
    [
        (1.0 + p.length).ln(),
        p.rms,
        p.zcr,
        p.centroid,
        p.harmonicity,
        p.low,
        p.high,
        p.crest,
        p.attack,
    ]
}
