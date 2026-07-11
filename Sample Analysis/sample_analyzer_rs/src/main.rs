//! oa_sample_analyzer — fast, parallel audio-sample analyzer.
//!
//! Walks a directory for WAV files and, across a pool of worker threads (30 by
//! default), computes for each: length, a pitch estimate (autocorrelation), and
//! a spectral "complexity" (centroid + spread). Streams one JSON line per file
//! to stdout so a GUI can graph progress live, then writes the aggregate
//! `sample_cloud_data.PEAK` (each record includes the file NAME and FOLDER).
//!
//! Usage: oa_sample_analyzer <dir> [--out <path>] [--workers <n>] [--max-len <s>]
//!
//! The code is split one-purpose-per-module:
//!   peak         — the streamed/serialized record struct
//!   normalize    — file-name tokenizer for keyword matching
//!   categorize   — name/path → group + subgroup taxonomy (+ tests)
//!   wav / acid   — WAV decode (mono f32) and ACID loop metadata
//!   amplitude / pitch / spectrum / transients / sustain — feature extractors
//!   timbre / label — feature+name → timbre and taxonomy labels
//!   analyze      — orchestrates the extractors into one `Peak`
//!   feature_vec / sqdist / kmeans / cluster — blind K-Means grouping
//!   args / discover / sidecar / stream / emit / run — CLI + orchestration

mod acid;
mod amplitude;
mod analyze;
mod args;
mod categorize;
mod cluster;
mod discover;
mod emit;
mod feature_vec;
mod kmeans;
mod label;
mod normalize;
mod peak;
mod pitch;
mod root;
mod run;
mod sidecar;
mod spectrum;
mod sqdist;
mod stream;
mod sustain;
mod timbre;
mod transients;
mod wav;

fn main() {
    // Per-file panics are caught during the run; keep their default messages off stderr.
    std::panic::set_hook(Box::new(|_| {}));

    match args::Config::parse(std::env::args().collect()) {
        Some(cfg) => run::run(&cfg),
        None => {
            eprintln!("usage: oa_sample_analyzer <dir> [--out <path>] [--workers <n>] [--max-len <s>]");
            std::process::exit(2);
        }
    }
}
