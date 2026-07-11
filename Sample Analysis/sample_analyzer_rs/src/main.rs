//! oa_sample_analyzer — fast, parallel audio-sample analyzer.
//!
//! Walks a directory for WAV files and, across a pool of worker threads (30 by
//! default), computes for each: length, a pitch estimate (autocorrelation), and
//! a spectral "complexity" (centroid + spread). Streams one JSON line per file
//! to stdout so a GUI can graph progress live, then writes the aggregate
//! `sample_cloud_data.PEAK` (each record includes the file NAME and FOLDER).
//!
//! Usage: oa_sample_analyzer <dir> [--out <path>] [--workers <n>] [--max-len <s>]

use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;

use rayon::prelude::*;
use rustfft::{num_complex::Complex, FftPlanner};
use serde::Serialize;
use walkdir::WalkDir;

#[derive(Serialize, Clone)]
struct Peak {
    name: String,   // file name
    folder: String, // sub-folder relative to the scanned root ("" = root)
    sub: String,    // alias of `folder` (SoundCloud view compatibility)
    path: String,   // absolute path
    group: String,        // name-derived category (Kick, Snare, HiHat, … Other) — or "Loop" if >1 transient
    reason: String,       // why it's in `group` (matched keyword, or the loop rule)
    timbre: String,       // feature-derived class (Percussive/Tonal/Noise/Bass/Bright/Loop/Pad)
    length_class: String, // one-shot length tier: Short / Medium / Long (or "Loop")
    subgroup: String,     // group + length tier, e.g. "Bass Short" (or "Loop")
    audit: bool,          // generic "drum" tag, no specific type — flag for acoustic audit

    // --- time / envelope ---
    length: f64,       // seconds
    transients: usize, // onset count; >1 ⇒ a loop rather than a one-shot sample
    attack: f64,       // seconds from start to peak amplitude (small ⇒ percussive)
    rms: f64,          // overall loudness (linear RMS)
    crest: f64,        // peak / rms (high ⇒ spiky/transient, low ⇒ sustained)
    zcr: f64,          // zero-crossings per second (high ⇒ noisy/bright)

    // --- pitch / harmonicity ---
    pitch: f64,        // Hz (autocorrelation)
    harmonicity: f64,  // 0 = atonal/noise … 1 = strongly pitched
    sustain: f64,      // fraction of the file held above 50% of peak level
    sustained: bool,   // a single fundamental note sustained the whole file

    // --- spectrum ---
    complexity: f64,   // spectral spread (timbral richness)
    centroid: f64,     // spectral centroid Hz (brightness)
    rolloff: f64,      // 85%-energy roll-off Hz
    flatness: f64,     // spectral flatness 0 = tonal … 1 = noise-like
    low: f64,          // fraction of energy < 200 Hz
    mid: f64,          // fraction 200 Hz – 2 kHz
    high: f64,         // fraction > 2 kHz

    // --- raw file attributes ---
    sample_rate: u32,
    bit_depth: u16,
    channels: u16,

    // --- embedded metadata (ACID chunk, when present) ---
    bpm: f64,          // 0 if none
    root_note: i32,    // MIDI root note, -1 if none

    // --- unsupervised grouping (assigned after all files are analyzed) ---
    cluster: i32,      // K-Means cluster id, -1 until clustered
}

/// Normalize a file name into space-separated tokens for name matching:
/// lower-cased, every non-alphanumeric run becomes a space, and letter↔digit
/// boundaries are split (so "Tom2" → "tom 2", "OH_01" → "oh 01").
fn normalize_name(name: &str) -> String {
    let lower = name.to_lowercase();
    let mut out = String::with_capacity(lower.len() + 8);
    let mut prev = 0u8; // 0 = sep, 1 = alpha, 2 = digit
    for c in lower.chars() {
        let kind = if c.is_ascii_alphabetic() { 1 } else if c.is_ascii_digit() { 2 } else { 0 };
        if kind == 0 {
            if !out.ends_with(' ') {
                out.push(' ');
            }
        } else {
            if prev != 0 && prev != kind {
                out.push(' ');
            }
            out.push(c);
        }
        prev = kind;
    }
    out
}

/// Categorize a sample by its file name, tolerant of the many spelling /
/// abbreviation conventions for drum elements. Phrases are matched as
/// substrings of the normalized name; ABBREVIATIONS are matched as whole
/// tokens (so "bd" hits "BD_01" but not "bird"). Order = most specific first.
/// Returns (group, matched-token) — the second value explains *why*.
fn categorize(name: &str) -> (&'static str, &'static str) {
    let norm = normalize_name(name);
    let toks: Vec<&str> = norm.split_whitespace().collect();
    let tok = |t: &str| toks.iter().any(|x| *x == t);
    let ph = |p: &str| norm.contains(p);

    // "cym" anywhere ⇒ definitely a cymbal (highest priority).
    if norm.contains("cym") {
        return ("Cymbal", "cym");
    }

    // Each rule: (canonical group, phrases[], abbrev-tokens[]).
    const RULES: &[(&str, &[&str], &[&str])] = &[
        // Impulse responses (convolution / cabinet / reverb IRs) — checked early.
        ("IR", &["impulse response", "impulse", "convolution", "convol", "cabinet", "guitar cab", "reverb ir"], &["ir", "cab", "conv"]),
        // Kick before Bass so "bass drum" -> Kick, plain "bass" -> Bass.
        ("Kick", &["kick", "bass drum", "bassdrum"], &["bd", "kk", "kic", "kck"]),
        ("Snare", &["snare"], &["sd", "sn", "snr"]),
        // Hi-hat variants (closed/open/pedal).
        ("HiHat", &["hihat", "hi hat", "closed hat", "open hat", "pedal hat", "hat"], &["hh", "chh", "ohh", "ch", "oh", "ph"]),
        ("Ride", &["ride bell", "ride cymbal", "ride"], &["rd", "rdcym"]),
        ("Cymbal", &["crash cymbal", "splash cymbal", "cymbal", "crash", "splash"], &["cy", "cym", "crsh"]),
        ("Clap", &["handclap", "hand clap", "clap"], &["cp", "clp"]),
        ("Rim", &["rimshot", "rim shot", "cross stick", "crossstick", "rim"], &["rs", "rm"]),
        // Toms split high / mid / low, then generic.
        ("Tom Hi", &["high tom", "hi tom", "rack tom 1", "tom 1", "hitom"], &["ht", "hitom"]),
        ("Tom Mid", &["mid tom", "middle tom", "rack tom 2", "tom 2", "midtom"], &["mt", "midtom"]),
        ("Tom Lo", &["low tom", "floor tom", "tom 3", "lotom"], &["lt", "ft", "lotom"]),
        ("Tom", &["tom"], &["tm"]),
        ("Cowbell", &["cowbell", "cow bell"], &["cb", "cow", "cowb"]),
        ("Conga", &["conga", "tumba", "quinto"], &["cg", "con", "cng"]),
        ("Clave", &["claves", "clave"], &["cv", "clv"]),
        ("Shaker", &["shaker", "maracas", "cabasa"], &["shk", "sh"]),
        ("Perc", &["percussion", "auxiliary", "perc"], &["prc"]),
        ("Guitar", &["guitar", "gtr", "acoustic gt", "electric gt"], &["gtr", "gt"]),
        ("Strings", &["strings", "string", "violin", "viola", "cello", "orchestra", "ensemble", "pizz", "arco"], &[]),
        ("Bass", &["bass", "808", "sub bass"], &["sub"]),
        ("Vocal", &["vocal", "voice", "vox"], &["vx"]),
        ("FX", &["sound effect", "foley", "atmosphere", "atmos", "riser", "sweep", "noise",
                 "impact", "boom", "zap", "glitch", "drone", "whoosh", "reverse", "downlifter",
                 "uplifter", "riser", "sfx", "fx"], &["fx", "sfx"]),
        ("Loop", &["loop", "groove", "beat"], &["lp"]),
    ];

    for (cat, phrases, abbrevs) in RULES {
        if let Some(p) = phrases.iter().find(|p| ph(p)) {
            return (cat, p);
        }
        if let Some(a) = abbrevs.iter().find(|a| tok(a)) {
            return (cat, a);
        }
    }
    ("Other", "")
}

fn main() {
    // Per-file panics are caught below; keep their default messages off stderr.
    std::panic::set_hook(Box::new(|_| {}));

    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: oa_sample_analyzer <dir> [--out <path>] [--workers <n>] [--max-len <s>]");
        std::process::exit(2);
    }
    let root = PathBuf::from(&args[1]);
    let mut out: Option<PathBuf> = None;
    let mut workers = 30usize;
    let mut max_len = 10.0f64;
    let mut clusters = 8usize;
    let mut per_file = true;
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--out" => { out = args.get(i + 1).map(PathBuf::from); i += 2; }
            "--no-per-file" => { per_file = false; i += 1; }
            "--workers" => { workers = args.get(i + 1).and_then(|v| v.parse().ok()).unwrap_or(30); i += 2; }
            "--max-len" => { max_len = args.get(i + 1).and_then(|v| v.parse().ok()).unwrap_or(10.0); i += 2; }
            "--clusters" => { clusters = args.get(i + 1).and_then(|v| v.parse().ok()).unwrap_or(8); i += 2; }
            _ => { i += 1; }
        }
    }
    let out = out.unwrap_or_else(|| root.join("sample_cloud_data.PEAK"));

    // Discover WAV files.
    let files: Vec<PathBuf> = WalkDir::new(&root)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
        .map(|e| e.into_path())
        .filter(|p| p.extension().and_then(|x| x.to_str()).map(|x| x.eq_ignore_ascii_case("wav")).unwrap_or(false))
        .collect();

    let total = files.len();
    emit(&serde_json::json!({ "type": "start", "total": total, "workers": workers }));
    if total == 0 {
        emit(&serde_json::json!({ "type": "done", "count": 0, "out": out.to_string_lossy() }));
        return;
    }

    let done = AtomicUsize::new(0);
    let wrote = AtomicUsize::new(0);
    let failed = AtomicUsize::new(0);
    let stdout_lock = Mutex::new(());
    let pool = rayon::ThreadPoolBuilder::new().num_threads(workers.max(1)).build().unwrap();

    let results: Vec<Peak> = pool.install(|| {
        files
            .par_iter()
            .filter_map(|f| {
                // Catch any per-file panic so one bad sample can't abort the run.
                let res = std::panic::catch_unwind(std::panic::AssertUnwindSafe(
                    || analyze(f, &root, max_len),
                ))
                .unwrap_or(None);
                // Write the per-file sidecar immediately, so it appears during
                // the run and survives an interrupted/killed process.
                if per_file {
                    if let Some(p) = &res {
                        let peak_path = Path::new(&p.path).with_extension("PEAK");
                        match serde_json::to_string_pretty(p)
                            .map_err(|e| e.to_string())
                            .and_then(|js| std::fs::write(&peak_path, js).map_err(|e| e.to_string()))
                        {
                            Ok(_) => { wrote.fetch_add(1, Ordering::Relaxed); }
                            Err(_) => { failed.fetch_add(1, Ordering::Relaxed); }
                        }
                    }
                }
                let n = done.fetch_add(1, Ordering::Relaxed) + 1;
                // Stream progress / result (serialized to avoid interleaving).
                let _g = stdout_lock.lock().unwrap();
                match &res {
                    Some(p) => emit(&serde_json::json!({
                        "type": "result", "done": n, "total": total,
                        "name": p.name, "folder": p.folder, "group": p.group, "reason": p.reason,
                        "timbre": p.timbre, "length_class": p.length_class, "subgroup": p.subgroup,
                        "sustained": p.sustained, "sustain": p.sustain, "audit": p.audit,
                        "pitch": p.pitch, "complexity": p.complexity, "length": p.length,
                        "transients": p.transients, "centroid": p.centroid, "harmonicity": p.harmonicity,
                        "brightness": p.high, "attack": p.attack, "bpm": p.bpm,
                        "sample_rate": p.sample_rate, "bit_depth": p.bit_depth, "channels": p.channels
                    })),
                    None => emit(&serde_json::json!({
                        "type": "skip", "done": n, "total": total,
                        "name": f.file_name().and_then(|x| x.to_str()).unwrap_or("")
                    })),
                }
                res
            })
            .collect()
    });

    // ---- Blind K-Means grouping over the extracted feature space.
    let mut results = results;
    cluster_samples(&mut results, clusters);
    let mut cluster_counts = std::collections::BTreeMap::new();
    for p in &results {
        *cluster_counts.entry(p.cluster).or_insert(0usize) += 1;
    }
    emit(&serde_json::json!({ "type": "clusters", "k": clusters, "counts": cluster_counts }));

    // Sidecars were written incrementally during analysis (above). Rewrite each
    // now so the final cluster id is included too.
    if per_file {
        results.par_iter().for_each(|p| {
            let peak_path = Path::new(&p.path).with_extension("PEAK");
            if let Ok(js) = serde_json::to_string_pretty(p) {
                let _ = std::fs::write(&peak_path, js);
            }
        });
        emit(&serde_json::json!({
            "type": "per_file", "wrote": wrote.load(Ordering::Relaxed),
            "failed": failed.load(Ordering::Relaxed)
        }));
    }

    // Aggregate PEAK (used by the cloud / Groups / Examiner views).
    if let Ok(json) = serde_json::to_string(&results) {
        if let Ok(mut fh) = std::fs::File::create(&out) {
            let _ = fh.write_all(json.as_bytes());
        }
    }
    emit(&serde_json::json!({ "type": "done", "count": results.len(), "out": out.to_string_lossy(), "per_file": per_file }));
}

fn emit(v: &serde_json::Value) {
    println!("{}", v);
    let _ = std::io::stdout().flush();
}

/// Read a WAV as mono f32 samples. Returns (samples, sample_rate, bit_depth, channels).
fn read_wav_mono(path: &Path) -> Option<(Vec<f32>, u32, u16, u16)> {
    let mut reader = hound::WavReader::open(path).ok()?;
    let spec = reader.spec();
    let ch = spec.channels.max(1) as usize;
    let sr = spec.sample_rate;
    let bits = spec.bits_per_sample;

    let raw: Vec<f32> = match spec.sample_format {
        hound::SampleFormat::Float => reader.samples::<f32>().filter_map(|s| s.ok()).collect(),
        hound::SampleFormat::Int => {
            let div = match spec.bits_per_sample {
                8 => 128.0,
                16 => 32768.0,
                24 => 8_388_608.0,
                _ => 2_147_483_648.0,
            };
            reader.samples::<i32>().filter_map(|s| s.ok()).map(|s| s as f32 / div).collect()
        }
    };
    if raw.is_empty() {
        return None;
    }
    // Downmix to mono.
    let mono: Vec<f32> = if ch <= 1 {
        raw
    } else {
        raw.chunks(ch).map(|frame| frame.iter().copied().sum::<f32>() / ch as f32).collect()
    };
    Some((mono, sr, bits, ch as u16))
}

/// Read the ACID chunk (embedded loop metadata) if present: (bpm, root_note).
/// bpm = 0 and root_note = -1 when absent. Walks the RIFF chunk list without
/// loading the whole file.
fn read_acid(path: &Path) -> (f64, i32) {
    use std::io::{Read, Seek, SeekFrom};
    let none = (0.0, -1);
    let mut f = match std::fs::File::open(path) {
        Ok(f) => f,
        Err(_) => return none,
    };
    let mut hdr = [0u8; 12];
    if f.read_exact(&mut hdr).is_err() {
        return none;
    }
    if &hdr[0..4] != b"RIFF" || &hdr[8..12] != b"WAVE" {
        return none;
    }
    loop {
        let mut ch = [0u8; 8];
        if f.read_exact(&mut ch).is_err() {
            break;
        }
        let size = u32::from_le_bytes([ch[4], ch[5], ch[6], ch[7]]) as u64;
        if &ch[0..4] == b"acid" {
            let mut buf = vec![0u8; size.min(64) as usize];
            if f.read_exact(&mut buf).is_err() || buf.len() < 24 {
                break;
            }
            let flags = u32::from_le_bytes([buf[0], buf[1], buf[2], buf[3]]);
            let root = u16::from_le_bytes([buf[4], buf[5]]) as i32;
            let tempo = f32::from_le_bytes([buf[20], buf[21], buf[22], buf[23]]) as f64;
            let root_out = if flags & 0x2 != 0 { root } else { -1 };
            let bpm = if tempo.is_finite() && tempo > 0.0 && tempo < 400.0 { tempo } else { 0.0 };
            return (bpm, root_out);
        }
        // Skip this chunk's data (chunks are word-aligned).
        let skip = size + (size & 1);
        if f.seek(SeekFrom::Current(skip as i64)).is_err() {
            break;
        }
    }
    none
}

/// Count transients (attacks) by prominence peak-picking on the amplitude
/// envelope. A hit is a rise to a local peak that stands at least `PROM` above
/// the valley preceding it — so each re-attack in a loop counts, while a steady
/// sustain or low-frequency envelope ripple (no real dip-then-rise) does not.
/// A clean one-shot yields 1; a loop yields many.
fn count_transients(data: &[f32], sr: u32) -> usize {
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

/// Fraction of the file whose short-time RMS stays above 50 % of the peak
/// level — a proxy for "held/sustained the whole time" (≈1 for a drone/pad,
/// small for a percussive one-shot that decays quickly).
fn sustain_ratio(data: &[f32], sr: u32) -> f64 {
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

fn analyze(path: &Path, root: &Path, max_len: f64) -> Option<Peak> {
    let (data, sr, bit_depth, channels) = read_wav_mono(path)?;
    let sr_f = sr as f64;
    let length = data.len() as f64 / sr_f;
    if length > max_len {
        return None; // skip long files
    }

    // ---- Envelope / amplitude features.
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

    // ---- Pitch + harmonicity: autocorrelation over the middle chunk.
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

    // ---- Spectrum: centroid, spread (complexity), roll-off, flatness, bands.
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

    // ---- Transients: >1 attack ⇒ this is a loop/phrase, not a one-shot sample.
    let transients = count_transients(&data, sr);
    let sustain = sustain_ratio(&data, sr);

    // ---- Embedded ACID metadata (loop BPM / musical key), when present.
    let (bpm, root_note) = read_acid(path);

    let name = path.file_name().and_then(|x| x.to_str()).unwrap_or("").to_string();
    let parent = path.parent().unwrap_or(root);
    let folder = parent.strip_prefix(root).ok().map(|p| p.to_string_lossy().replace('\\', "/")).unwrap_or_default();
    // Loop if it has multiple transients OR carries a BPM (ACID) tag.
    let is_loop = transients > 1 || bpm > 0.0;
    // A single fundamental note held for the whole file (drone/pad/sustained tone).
    let sustained = harmonicity > 0.5 && !is_loop && sustain > 0.6;
    let (name_group, name_match) = categorize(&name);
    let (group, reason) = if is_loop {
        let why = if transients > 1 && bpm > 0.0 {
            format!("{} transients + {:.0} BPM tag → loop", transients, bpm)
        } else if transients > 1 {
            format!("{} transients (>1) → loop", transients)
        } else {
            format!("{:.0} BPM tag → loop", bpm)
        };
        ("Loop".to_string(), why)
    } else if name_match.is_empty() {
        (name_group.to_string(), "no naming keyword matched".to_string())
    } else {
        (name_group.to_string(), format!("name matched \"{}\"", name_match))
    };
    // Feature-derived timbre class — a blind, name-independent classification.
    let timbre = classify_timbre(transients, attack, crest, harmonicity, centroid, low, high).to_string();

    // Length tier: one-shots split Short / Medium / Long; loops are their own.
    let length_class = if is_loop {
        "Loop"
    } else if length < 0.5 {
        "Short"
    } else if length < 2.0 {
        "Medium"
    } else {
        "Long"
    }
    .to_string();
    let subgroup = if is_loop {
        "Loop".to_string()
    } else {
        format!("{} {}", group, length_class)
    };

    // A generic "drum" tag with no specific instrument matched ⇒ flag for a
    // second (acoustic) audit rather than trusting the vague name.
    let audit = !is_loop && group == "Other" && normalize_name(&name).contains("drum");
    let reason = if audit {
        "generic \"drum\" tag — flagged for acoustic audit".to_string()
    } else {
        reason
    };

    Some(Peak {
        name,
        folder: folder.clone(),
        sub: folder,
        path: path.to_string_lossy().to_string(),
        group,
        reason,
        timbre,
        length_class,
        subgroup,
        audit,
        length,
        transients,
        attack,
        rms,
        crest,
        zcr,
        pitch,
        harmonicity,
        sustain,
        sustained,
        complexity,
        centroid,
        rolloff,
        flatness,
        low,
        mid,
        high,
        sample_rate: sr,
        bit_depth,
        channels,
        bpm,
        root_note,
        cluster: -1,
    })
}

/// Blind K-Means++ clustering over the extracted feature space. Groups files
/// that "sound alike" without looking at their names — mirroring the linfa
/// K-Means idea but self-contained and deterministic (fixed seed, no rng dep).
/// Loops are clustered separately from one-shots (cluster ids offset by k) so
/// the two graphs get their own groupings.
fn cluster_samples(results: &mut [Peak], k: usize) {
    let idx_hits: Vec<usize> = (0..results.len()).filter(|&i| results[i].group != "Loop").collect();
    let idx_loops: Vec<usize> = (0..results.len()).filter(|&i| results[i].group == "Loop").collect();
    kmeans_assign(results, &idx_hits, k, 0);
    kmeans_assign(results, &idx_loops, k, k as i32);
}

fn feature_vec(p: &Peak) -> [f64; 9] {
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

fn sqdist(a: &[f64; 9], b: &[f64; 9]) -> f64 {
    let mut s = 0.0;
    for j in 0..9 {
        let d = a[j] - b[j];
        s += d * d;
    }
    s
}

fn kmeans_assign(results: &mut [Peak], idx: &[usize], k: usize, offset: i32) {
    let n = idx.len();
    if n == 0 {
        return;
    }
    let k = k.max(1).min(n);
    let d = 9;

    // Min-max normalize each feature column so no dimension dominates.
    let feats: Vec<[f64; 9]> = idx.iter().map(|&i| feature_vec(&results[i])).collect();
    let mut mn = [f64::INFINITY; 9];
    let mut mx = [f64::NEG_INFINITY; 9];
    for f in &feats {
        for j in 0..d {
            mn[j] = mn[j].min(f[j]);
            mx[j] = mx[j].max(f[j]);
        }
    }
    let norm: Vec<[f64; 9]> = feats
        .iter()
        .map(|f| {
            let mut o = [0.0; 9];
            for j in 0..d {
                let r = mx[j] - mn[j];
                o[j] = if r > 1e-12 { (f[j] - mn[j]) / r } else { 0.0 };
            }
            o
        })
        .collect();

    // Deterministic PRNG (xorshift) for K-Means++ seeding.
    let mut seed = 0x9E3779B97F4A7C15u64;
    let mut rnd = || {
        seed ^= seed << 13;
        seed ^= seed >> 7;
        seed ^= seed << 17;
        (seed >> 11) as f64 / ((1u64 << 53) as f64)
    };

    // K-Means++ init.
    let mut centers: Vec<[f64; 9]> = Vec::with_capacity(k);
    centers.push(norm[(rnd() * n as f64) as usize % n]);
    while centers.len() < k {
        let dists: Vec<f64> = norm
            .iter()
            .map(|x| centers.iter().map(|c| sqdist(x, c)).fold(f64::INFINITY, f64::min))
            .collect();
        let sum: f64 = dists.iter().sum();
        if sum <= 0.0 {
            centers.push(norm[centers.len() % n]);
            continue;
        }
        let mut target = rnd() * sum;
        let mut pick = 0;
        for (i, dd) in dists.iter().enumerate() {
            target -= dd;
            pick = i;
            if target <= 0.0 {
                break;
            }
        }
        centers.push(norm[pick]);
    }

    // Lloyd's iterations.
    let mut assign = vec![0usize; n];
    for _ in 0..40 {
        let mut changed = false;
        for (i, x) in norm.iter().enumerate() {
            let mut best = 0;
            let mut bd = f64::INFINITY;
            for (ci, c) in centers.iter().enumerate() {
                let dd = sqdist(x, c);
                if dd < bd {
                    bd = dd;
                    best = ci;
                }
            }
            if assign[i] != best {
                assign[i] = best;
                changed = true;
            }
        }
        let mut sums = vec![[0.0f64; 9]; k];
        let mut cnt = vec![0usize; k];
        for (i, x) in norm.iter().enumerate() {
            let a = assign[i];
            for j in 0..d {
                sums[a][j] += x[j];
            }
            cnt[a] += 1;
        }
        for ci in 0..k {
            if cnt[ci] > 0 {
                for j in 0..d {
                    centers[ci][j] = sums[ci][j] / cnt[ci] as f64;
                }
            }
        }
        if !changed {
            break;
        }
    }

    for (m, &i) in idx.iter().enumerate() {
        results[i].cluster = offset + assign[m] as i32;
    }
}

/// Blindly classify a one-shot by its extracted features (name-independent).
fn classify_timbre(
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

#[cfg(test)]
mod tests {
    use super::categorize;

    #[test]
    fn naming_conventions() {
        let cases: &[(&str, &str)] = &[
            ("Kick_01.wav", "Kick"), ("BD_808.wav", "Kick"), ("Bass Drum 3.wav", "Kick"),
            ("Kk-tight.wav", "Kick"),
            ("Snare_Acoustic.wav", "Snare"), ("SD_04.wav", "Snare"), ("Snr_rimmy.wav", "Snare"),
            ("HiHat_closed.wav", "HiHat"), ("HH_01.wav", "HiHat"), ("OH_open.wav", "HiHat"),
            ("CH_tight.wav", "HiHat"), ("Pedal Hat.wav", "HiHat"),
            ("Perc_shot.wav", "Perc"), ("PRC_02.wav", "Perc"),
            ("Clap_big.wav", "Clap"), ("CP_room.wav", "Clap"), ("Handclap.wav", "Clap"),
            ("Rimshot.wav", "Rim"), ("RS_dry.wav", "Rim"), ("Cross-stick.wav", "Rim"),
            ("Low Tom.wav", "Tom Lo"), ("FT_floor.wav", "Tom Lo"), ("Tom3.wav", "Tom Lo"),
            ("Mid Tom.wav", "Tom Mid"), ("Tom2.wav", "Tom Mid"),
            ("High Tom.wav", "Tom Hi"), ("HT_rack.wav", "Tom Hi"), ("Tom1.wav", "Tom Hi"),
            ("Crash Cymbal.wav", "Cymbal"), ("CY_splash.wav", "Cymbal"), ("Crsh.wav", "Cymbal"),
            ("OHCYM.wav", "Cymbal"), ("808_CYM.wav", "Cymbal"), ("Tom_cym_hit.wav", "Cymbal"),
            ("Hall_IR.wav", "IR"), ("guitar_cab.wav", "IR"), ("Impulse_room.wav", "IR"),
            ("Convolution 01.wav", "IR"),
            ("Ride Bell.wav", "Ride"), ("RD_ping.wav", "Ride"),
            ("Cowbell.wav", "Cowbell"), ("CB_hi.wav", "Cowbell"),
            ("Conga_open.wav", "Conga"), ("Tumba.wav", "Conga"), ("Quinto.wav", "Conga"),
            ("Claves.wav", "Clave"), ("CV_01.wav", "Clave"),
            ("Shaker.wav", "Shaker"), ("Maracas.wav", "Shaker"), ("Cabasa.wav", "Shaker"),
            ("FX_riser.wav", "FX"), ("SFX_boom.wav", "FX"), ("Foley_door.wav", "FX"),
            ("Sub_808.wav", "Bass"), ("Bassline.wav", "Bass"),
            ("Vox_chop.wav", "Vocal"), ("Vocal_ah.wav", "Vocal"),
            ("randomthing.wav", "Other"),
        ];
        for (name, want) in cases {
            let (got, why) = categorize(name);
            assert_eq!(got, *want, "categorize({:?}) = {:?} (why {:?}), want {:?}", name, got, why, want);
        }
    }
}
