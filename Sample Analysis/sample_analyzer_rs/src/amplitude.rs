/// Time-domain envelope features from a single pass over the samples.
pub struct Amplitude {
    pub rms: f64,    // linear RMS loudness
    pub crest: f64,  // peak / rms (spiky ⇒ high, sustained ⇒ low)
    pub attack: f64, // seconds from start to the loudest sample
    pub zcr: f64,    // zero-crossings per second (bright/noisy ⇒ high)
}

/// Compute loudness (RMS), crest factor, attack time and zero-crossing rate.
pub fn amplitude_features(data: &[f32], sr_f: f64, length: f64) -> Amplitude {
    let mut peak_amp = 0.0f64;
    let mut peak_idx = 0usize;
    let mut sum_sq = 0.0f64;
    let mut zc = 0u64;
    let mut prev_sign = 0i8;
    for (i, &x) in data.iter().enumerate() {
        let ax = x.abs() as f64;
        if ax > peak_amp {
            peak_amp = ax;
            peak_idx = i;
        }
        sum_sq += (x as f64) * (x as f64);
        let sign = if x > 0.0 { 1 } else if x < 0.0 { -1 } else { 0 };
        if sign != 0 {
            if prev_sign != 0 && sign != prev_sign {
                zc += 1;
            }
            prev_sign = sign;
        }
    }
    let rms = (sum_sq / data.len().max(1) as f64).sqrt();
    let crest = if rms > 1e-9 { peak_amp / rms } else { 0.0 };
    let attack = peak_idx as f64 / sr_f; // time to reach the loudest point
    let zcr = zc as f64 / length.max(1e-6); // crossings per second
    Amplitude { rms, crest, attack, zcr }
}
