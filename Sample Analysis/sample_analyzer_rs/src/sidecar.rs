use std::path::Path;

use crate::peak::Peak;

/// Write a per-file `<sample>.PEAK` sidecar next to the audio file. Returns true
/// on success. Used both for the incremental write during analysis and the
/// rewrite afterwards (once the cluster id is known).
pub fn write_sidecar(p: &Peak) -> bool {
    let peak_path = Path::new(&p.path).with_extension("PEAK");
    serde_json::to_string_pretty(p)
        .ok()
        .and_then(|js| std::fs::write(&peak_path, js).ok())
        .is_some()
}
