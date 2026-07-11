use rustfft::{num_complex::Complex, FftPlanner};

/// Frequency-domain features from a single FFT over the middle of the signal.
pub struct Spectrum {
    pub complexity: f64, // spectral spread (timbral richness)
    pub centroid: f64,   // spectral centroid Hz (brightness)
    pub rolloff: f64,    // 85%-energy roll-off Hz
    pub flatness: f64,   // 0 = tonal … 1 = noise-like
    pub low: f64,        // fraction of energy < 200 Hz
    pub mid: f64,        // fraction 200 Hz – 2 kHz
    pub high: f64,       // fraction > 2 kHz
}

/// Compute the spectral features. Returns None when the file is too short for
/// an FFT (<2 samples).
pub fn spectral_features(data: &[f32], sr_f: f64) -> Option<Spectrum> {
    // Guard tiny files: FFT needs ≥2 samples (data.len() may be 1).
    let n = data.len().min(262_144);
    if n < 2 {
        return None;
    }
    let start = (data.len().saturating_sub(n)) / 2;
    let mut buf: Vec<Complex<f32>> = data[start..start + n].iter().map(|&x| Complex { re: x, im: 0.0 }).collect();
    let mut planner = FftPlanner::<f32>::new();
    planner.plan_fft_forward(n).process(&mut buf);

    let half = n / 2;
    let bin_hz = sr_f / n as f64;
    let mut sum_mag = 0.0f64;
    let mut sum_fmag = 0.0f64;
    let mut sum_log = 0.0f64;
    let mut low = 0.0f64;
    let mut mid = 0.0f64;
    let mut high = 0.0f64;
    let mut mags: Vec<f64> = Vec::with_capacity(half);
    for k in 0..half {
        let m = buf[k].norm() as f64;
        let f = k as f64 * bin_hz;
        mags.push(m);
        sum_mag += m;
        sum_fmag += f * m;
        sum_log += (m + 1e-12).ln();
        if f < 200.0 {
            low += m;
        } else if f < 2000.0 {
            mid += m;
        } else {
            high += m;
        }
    }
    let (complexity, centroid, rolloff, flatness) = if sum_mag > 0.0 {
        let centroid = sum_fmag / sum_mag;
        let mut sum_var = 0.0f64;
        for (k, &m) in mags.iter().enumerate() {
            let f = k as f64 * bin_hz;
            sum_var += (f - centroid).powi(2) * m;
        }
        // 85% spectral roll-off.
        let target = sum_mag * 0.85;
        let mut cum = 0.0f64;
        let mut roll = 0.0f64;
        for (k, &m) in mags.iter().enumerate() {
            cum += m;
            if cum >= target {
                roll = k as f64 * bin_hz;
                break;
            }
        }
        // Spectral flatness = geo-mean / arith-mean.
        let arith = sum_mag / half.max(1) as f64;
        let geo = (sum_log / half.max(1) as f64).exp();
        let flat = if arith > 1e-12 { (geo / arith).clamp(0.0, 1.0) } else { 0.0 };
        ((sum_var / sum_mag).sqrt(), centroid, roll, flat)
    } else {
        (0.0, 0.0, 0.0, 0.0)
    };
    let (low, mid, high) = if sum_mag > 0.0 {
        (low / sum_mag, mid / sum_mag, high / sum_mag)
    } else {
        (0.0, 0.0, 0.0)
    };

    Some(Spectrum { complexity, centroid, rolloff, flatness, low, mid, high })
}
