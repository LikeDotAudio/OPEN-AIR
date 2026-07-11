/// Fraction of the file whose short-time RMS stays above 50 % of the peak
/// level — a proxy for "held/sustained the whole time" (≈1 for a drone/pad,
/// small for a percussive one-shot that decays quickly).
pub fn sustain_ratio(data: &[f32], sr: u32) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    let hop = (sr as usize / 60).max(1);
    let mut env: Vec<f32> = Vec::new();
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
    let peak = env.iter().cloned().fold(0.0f32, f32::max);
    if peak <= 0.0 || env.is_empty() {
        return 0.0;
    }
    let thr = peak * 0.5;
    let above = env.iter().filter(|&&e| e >= thr).count();
    above as f64 / env.len() as f64
}
