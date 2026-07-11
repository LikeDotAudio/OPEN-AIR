/// Estimate pitch (Hz) and harmonicity (0 = noise … 1 = strongly pitched) by
/// autocorrelation over the middle half of the signal. Returns (0.0, 0.0) when
/// the file is too short to analyze.
pub fn pitch_features(data: &[f32], sr_f: f64) -> (f64, f64) {
    let min_lag = ((sr_f / 2000.0) as usize).max(1);
    let max_lag = (sr_f / 50.0) as usize;
    let mut pitch = 0.0;
    let mut harmonicity = 0.0f64;
    if data.len() > max_lag {
        let a = data.len() / 4;
        let b = (data.len() / 4) * 3;
        let chunk = &data[a..b];
        if chunk.len() > max_lag {
            let zero_lag: f64 = chunk.iter().map(|&v| (v as f64) * (v as f64)).sum();
            let mut best = f64::MIN;
            let mut best_lag = 0usize;
            for lag in min_lag..max_lag {
                let mut s = 0.0f64;
                let n = chunk.len() - lag;
                for k in 0..n {
                    s += chunk[k] as f64 * chunk[k + lag] as f64;
                }
                if s > best {
                    best = s;
                    best_lag = lag;
                }
            }
            if best_lag > 0 {
                pitch = sr_f / best_lag as f64;
            }
            if zero_lag > 1e-12 {
                harmonicity = (best / zero_lag).clamp(0.0, 1.0);
            }
        }
    }
    (pitch, harmonicity)
}
