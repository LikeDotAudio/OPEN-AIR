//! ROOT extraction — the musical note / key of a sample.
//!
//! FFTs the middle of the signal (Hann-windowed) and runs a Harmonic Product
//! Spectrum to lock onto the fundamental (which reinforces the true root and
//! suppresses octave/harmonic confusion), then maps the fundamental frequency
//! to an equal-tempered note name (e.g. "A3") with its cents deviation.
use rustfft::{num_complex::Complex, FftPlanner};

const NOTE_NAMES: [&str; 12] = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

pub struct Root {
    pub hz: f64,      // detected fundamental (0 = none)
    pub note: String, // e.g. "A3" ("" = none)
    pub cents: f64,   // deviation from the equal-tempered note (−50..+50)
}

impl Root {
    fn none() -> Root {
        Root { hz: 0.0, note: String::new(), cents: 0.0 }
    }
}

/// MIDI note number → name ("A4" = 69). Empty string when out of range.
pub fn midi_to_name(midi: i32) -> String {
    if !(0..=127).contains(&midi) {
        return String::new();
    }
    format!("{}{}", NOTE_NAMES[(midi % 12) as usize], midi / 12 - 1)
}

/// Frequency (Hz) → (midi, name, cents-off).
fn hz_to_note(hz: f64) -> (i32, String, f64) {
    if hz <= 0.0 {
        return (-1, String::new(), 0.0);
    }
    let midi_f = 69.0 + 12.0 * (hz / 440.0).log2();
    let midi = midi_f.round() as i32;
    if !(0..=127).contains(&midi) {
        return (-1, String::new(), 0.0);
    }
    let cents = (midi_f - midi as f64) * 100.0;
    (midi, midi_to_name(midi), cents)
}

/// Detect the ROOT note of a sample via FFT + Harmonic Product Spectrum.
pub fn extract_root(data: &[f32], sr_f: f64) -> Root {
    let n = data.len().min(65_536);
    if n < 1024 {
        return Root::none();
    }
    // Hann-windowed FFT over the middle of the signal (reduces spectral leakage).
    let start = (data.len().saturating_sub(n)) / 2;
    let mut buf: Vec<Complex<f32>> = (0..n)
        .map(|i| {
            let w = 0.5 - 0.5 * (2.0 * std::f32::consts::PI * i as f32 / (n as f32 - 1.0)).cos();
            Complex { re: data[start + i] * w, im: 0.0 }
        })
        .collect();
    FftPlanner::<f32>::new().plan_fft_forward(n).process(&mut buf);

    let half = n / 2;
    let mags: Vec<f64> = buf[..half].iter().map(|c| c.norm() as f64).collect();
    let bin_hz = sr_f / n as f64;

    // Harmonic Product Spectrum: multiply the spectrum by decimated copies of
    // itself so a bin only stays large when its harmonics are present too.
    const HARMONICS: usize = 5;
    let hps_len = half / HARMONICS;
    if hps_len < 8 {
        return Root::none();
    }
    // Search only a musical fundamental range (~30–1100 Hz).
    let lo = ((30.0 / bin_hz).floor() as usize).max(1);
    let hi = ((1100.0 / bin_hz).ceil() as usize).min(hps_len - 1);
    if hi <= lo {
        return Root::none();
    }
    let mut best_bin = 0usize;
    let mut best = 0.0f64;
    for k in lo..hi {
        let mut prod = mags[k];
        for h in 2..=HARMONICS {
            prod *= mags[k * h];
        }
        if prod > best {
            best = prod;
            best_bin = k;
        }
    }
    if best_bin == 0 || best <= 0.0 {
        return Root::none();
    }

    // Parabolic interpolation around the peak for a sub-bin frequency estimate.
    let f = if best_bin > 0 && best_bin + 1 < half {
        let (a, b, c) = (mags[best_bin - 1], mags[best_bin], mags[best_bin + 1]);
        let denom = a - 2.0 * b + c;
        let delta = if denom.abs() > 1e-12 { 0.5 * (a - c) / denom } else { 0.0 };
        (best_bin as f64 + delta.clamp(-0.5, 0.5)) * bin_hz
    } else {
        best_bin as f64 * bin_hz
    };

    let (midi, note, cents) = hz_to_note(f);
    if midi < 0 {
        return Root::none();
    }
    Root { hz: f, note, cents }
}
