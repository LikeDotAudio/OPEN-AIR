//! Orchestrate a full run: discover files, analyze them in parallel while
//! streaming progress, cluster, then write the sidecars + aggregate PEAK.
use std::io::Write;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;

use rayon::prelude::*;

use crate::analyze::analyze;
use crate::args::Config;
use crate::cluster::cluster_samples;
use crate::discover::discover_wavs;
use crate::emit::emit;
use crate::peak::Peak;
use crate::sidecar::write_sidecar;
use crate::stream::{emit_result, emit_skip};

pub fn run(cfg: &Config) {
    let files = discover_wavs(&cfg.root);
    let total = files.len();
    emit(&serde_json::json!({ "type": "start", "total": total, "workers": cfg.workers }));
    if total == 0 {
        emit(&serde_json::json!({ "type": "done", "count": 0, "out": cfg.out.to_string_lossy() }));
        return;
    }

    let done = AtomicUsize::new(0);
    let wrote = AtomicUsize::new(0);
    let failed = AtomicUsize::new(0);
    let stdout_lock = Mutex::new(());
    let pool = rayon::ThreadPoolBuilder::new().num_threads(cfg.workers.max(1)).build().unwrap();

    let mut results: Vec<Peak> = pool.install(|| {
        files
            .par_iter()
            .filter_map(|f| {
                // Catch any per-file panic so one bad sample can't abort the run.
                let res = std::panic::catch_unwind(std::panic::AssertUnwindSafe(
                    || analyze(f, &cfg.root, cfg.max_len),
                ))
                .unwrap_or(None);
                // Write the per-file sidecar immediately, so it appears during
                // the run and survives an interrupted/killed process.
                if cfg.per_file {
                    if let Some(p) = &res {
                        if write_sidecar(p) {
                            wrote.fetch_add(1, Ordering::Relaxed);
                        } else {
                            failed.fetch_add(1, Ordering::Relaxed);
                        }
                    }
                }
                let n = done.fetch_add(1, Ordering::Relaxed) + 1;
                // Stream progress / result (serialized to avoid interleaving).
                let _g = stdout_lock.lock().unwrap();
                match &res {
                    Some(p) => emit_result(p, n, total),
                    None => emit_skip(f.file_name().and_then(|x| x.to_str()).unwrap_or(""), n, total),
                }
                res
            })
            .collect()
    });

    // ---- Blind K-Means grouping over the extracted feature space.
    cluster_samples(&mut results, cfg.clusters);
    let mut cluster_counts = std::collections::BTreeMap::new();
    for p in &results {
        *cluster_counts.entry(p.cluster).or_insert(0usize) += 1;
    }
    emit(&serde_json::json!({ "type": "clusters", "k": cfg.clusters, "counts": cluster_counts }));

    // Sidecars were written incrementally during analysis (above). Rewrite each
    // now so the final cluster id is included too.
    if cfg.per_file {
        results.par_iter().for_each(|p| {
            write_sidecar(p);
        });
        emit(&serde_json::json!({
            "type": "per_file", "wrote": wrote.load(Ordering::Relaxed),
            "failed": failed.load(Ordering::Relaxed)
        }));
    }

    // Aggregate PEAK (used by the cloud / Groups / Examiner views).
    if let Ok(json) = serde_json::to_string(&results) {
        if let Ok(mut fh) = std::fs::File::create(&cfg.out) {
            let _ = fh.write_all(json.as_bytes());
        }
    }
    emit(&serde_json::json!({ "type": "done", "count": results.len(), "out": cfg.out.to_string_lossy(), "per_file": cfg.per_file }));
}
