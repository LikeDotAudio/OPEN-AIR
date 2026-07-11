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
    length: f64,
    pitch: f64,
    complexity: f64,
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: oa_sample_analyzer <dir> [--out <path>] [--workers <n>] [--max-len <s>]");
        std::process::exit(2);
    }
    let root = PathBuf::from(&args[1]);
    let mut out: Option<PathBuf> = None;
    let mut workers = 30usize;
    let mut max_len = 10.0f64;
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--out" => { out = args.get(i + 1).map(PathBuf::from); i += 2; }
            "--workers" => { workers = args.get(i + 1).and_then(|v| v.parse().ok()).unwrap_or(30); i += 2; }
            "--max-len" => { max_len = args.get(i + 1).and_then(|v| v.parse().ok()).unwrap_or(10.0); i += 2; }
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
    let stdout_lock = Mutex::new(());
    let pool = rayon::ThreadPoolBuilder::new().num_threads(workers.max(1)).build().unwrap();

    let results: Vec<Peak> = pool.install(|| {
        files
            .par_iter()
            .filter_map(|f| {
                let res = analyze(f, &root, max_len);
                let n = done.fetch_add(1, Ordering::Relaxed) + 1;
                // Stream progress / result (serialized to avoid interleaving).
                let _g = stdout_lock.lock().unwrap();
                match &res {
                    Some(p) => emit(&serde_json::json!({
                        "type": "result", "done": n, "total": total,
                        "name": p.name, "folder": p.folder,
                        "pitch": p.pitch, "complexity": p.complexity, "length": p.length
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

    if let Ok(json) = serde_json::to_string(&results) {
        if let Ok(mut fh) = std::fs::File::create(&out) {
            let _ = fh.write_all(json.as_bytes());
        }
    }
    emit(&serde_json::json!({ "type": "done", "count": results.len(), "out": out.to_string_lossy() }));
}

fn emit(v: &serde_json::Value) {
    println!("{}", v);
    let _ = std::io::stdout().flush();
}

/// Read a WAV as mono f32 samples. Returns (samples, sample_rate).
fn read_wav_mono(path: &Path) -> Option<(Vec<f32>, u32)> {
    let mut reader = hound::WavReader::open(path).ok()?;
    let spec = reader.spec();
    let ch = spec.channels.max(1) as usize;
    let sr = spec.sample_rate;

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
    Some((mono, sr))
}

fn analyze(path: &Path, root: &Path, max_len: f64) -> Option<Peak> {
    let (data, sr) = read_wav_mono(path)?;
    let sr_f = sr as f64;
    let length = data.len() as f64 / sr_f;
    if length > max_len {
        return None; // skip long files
    }

    // ---- Pitch: autocorrelation over the plausible lag range on the middle chunk.
    let min_lag = ((sr_f / 2000.0) as usize).max(1);
    let max_lag = (sr_f / 50.0) as usize;
    let mut pitch = 0.0;
    if data.len() > max_lag {
        let a = data.len() / 4;
        let b = (data.len() / 4) * 3;
        let chunk = &data[a..b];
        if chunk.len() > max_lag {
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
        }
    }

    // ---- Complexity: spectral centroid + spread over a windowed FFT.
    let n = data.len().min(262_144).max(2);
    let start = (data.len().saturating_sub(n)) / 2;
    let mut buf: Vec<Complex<f32>> = data[start..start + n].iter().map(|&x| Complex { re: x, im: 0.0 }).collect();
    let mut planner = FftPlanner::<f32>::new();
    planner.plan_fft_forward(n).process(&mut buf);

    let half = n / 2;
    let mut sum_mag = 0.0f64;
    let mut sum_fmag = 0.0f64;
    let mut mags: Vec<f64> = Vec::with_capacity(half);
    for k in 0..half {
        let m = buf[k].norm() as f64;
        let f = k as f64 * sr_f / n as f64;
        mags.push(m);
        sum_mag += m;
        sum_fmag += f * m;
    }
    let (pitch_out, complexity) = if sum_mag > 0.0 {
        let centroid = sum_fmag / sum_mag;
        let mut sum_var = 0.0f64;
        for (k, &m) in mags.iter().enumerate() {
            let f = k as f64 * sr_f / n as f64;
            sum_var += (f - centroid).powi(2) * m;
        }
        (pitch, (sum_var / sum_mag).sqrt())
    } else {
        (0.0, 0.0)
    };

    let name = path.file_name().and_then(|x| x.to_str()).unwrap_or("").to_string();
    let parent = path.parent().unwrap_or(root);
    let folder = parent.strip_prefix(root).ok().map(|p| p.to_string_lossy().replace('\\', "/")).unwrap_or_default();
    Some(Peak {
        name,
        folder: folder.clone(),
        sub: folder,
        path: path.to_string_lossy().to_string(),
        length,
        pitch: pitch_out,
        complexity,
    })
}
