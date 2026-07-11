/// Count transients (attacks) by prominence peak-picking on the amplitude
/// envelope. A hit is a rise to a local peak that stands at least `PROM` above
/// the valley preceding it — so each re-attack in a loop counts, while a steady
/// sustain or low-frequency envelope ripple (no real dip-then-rise) does not.
/// A clean one-shot yields 1; a loop yields many.
pub fn count_transients(data: &[f32], sr: u32) -> usize {
    if data.is_empty() {
        return 0;
    }
    let hop = (sr as usize / 60).max(1); // ~16 ms frames (averages out sub-100 Hz ripple)
    let mut env: Vec<f32> = Vec::with_capacity(data.len() / hop + 1);
    let mut i = 0;
    while i < data.len() {
        let end = (i + hop).min(data.len());
        let mut s = 0.0f32;
        for &x in &data[i..end] {
            s += x * x;
        }
        env.push((s / (end - i) as f32).sqrt());
        i += hop;
    }
    let n = env.len();
    if n < 3 {
        return if env.iter().any(|&e| e > 0.0) { 1 } else { 0 };
    }
    let emax = env.iter().cloned().fold(0.0f32, f32::max);
    if emax <= 0.0 {
        return 0;
    }

    // Normalize + 3-tap smoothing.
    let sm: Vec<f32> = (0..n)
        .map(|k| {
            let a = env[k.saturating_sub(1)];
            let b = env[k];
            let c = env[(k + 1).min(n - 1)];
            (a + b + c) / (3.0 * emax)
        })
        .collect();

    const PROM: f32 = 0.18;      // peak must rise this far above the preceding valley
    const MIN_LEVEL: f32 = 0.12; // and reach at least this loudness
    const EPS: f32 = 1e-4;

    let mut count = 0usize;
    let mut rising = false;
    let mut valley = sm[0];
    let mut peak = sm[0];
    for k in 1..n {
        if sm[k] > sm[k - 1] + EPS {
            if !rising {
                valley = sm[k - 1];
                rising = true;
            }
            peak = sm[k];
        } else if sm[k] < sm[k - 1] - EPS && rising {
            if peak - valley >= PROM && peak >= MIN_LEVEL {
                count += 1;
            }
            rising = false;
        }
    }
    count.max(1) // audible signal ⇒ at least one attack
}
