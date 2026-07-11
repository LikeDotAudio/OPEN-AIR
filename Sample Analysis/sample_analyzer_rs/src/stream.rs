//! The streamed stdout protocol: one JSON line per analyzed (or skipped) file,
//! consumed live by the GUI.
use crate::emit::emit;
use crate::peak::Peak;

/// Emit the "result" line for one successfully analyzed file.
pub fn emit_result(p: &Peak, done: usize, total: usize) {
    emit(&serde_json::json!({
        "type": "result", "done": done, "total": total,
        "name": p.name, "folder": p.folder, "group": p.group, "reason": p.reason,
        "timbre": p.timbre, "length_class": p.length_class, "subgroup": p.subgroup,
        "sustained": p.sustained, "sustain": p.sustain, "audit": p.audit,
        "pitch": p.pitch, "complexity": p.complexity, "length": p.length,
        "transients": p.transients, "centroid": p.centroid, "harmonicity": p.harmonicity,
        "brightness": p.high, "attack": p.attack, "bpm": p.bpm,
        "root": p.root, "root_hz": p.root_hz, "root_cents": p.root_cents,
        "sample_rate": p.sample_rate, "bit_depth": p.bit_depth, "channels": p.channels
    }));
}

/// Emit the "skip" line for a file that could not be analyzed.
pub fn emit_skip(name: &str, done: usize, total: usize) {
    emit(&serde_json::json!({ "type": "skip", "done": done, "total": total, "name": name }));
}
