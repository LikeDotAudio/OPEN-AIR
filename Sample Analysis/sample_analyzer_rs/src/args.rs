//! Command-line configuration.
use std::path::PathBuf;

pub struct Config {
    pub root: PathBuf,
    pub out: PathBuf,
    pub workers: usize,
    pub max_len: f64,
    pub clusters: usize,
    pub per_file: bool,
}

impl Config {
    /// Parse the full argv (including argv[0]). Returns None when no directory
    /// argument was supplied (caller prints usage and exits).
    pub fn parse(args: Vec<String>) -> Option<Config> {
        if args.len() < 2 {
            return None;
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
        Some(Config { root, out, workers, max_len, clusters, per_file })
    }
}
