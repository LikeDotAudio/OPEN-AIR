//! Turn a sample's path + extracted features into its taxonomy labels
//! (group / subgroup / reason / length tier / timbre / audit flag).
use crate::categorize::categorize;
use crate::normalize::normalize_name;
use crate::timbre::classify_timbre;

pub struct Labels {
    pub group: String,
    pub reason: String,
    pub timbre: String,
    pub length_class: String,
    pub subgroup: String,
    pub audit: bool,
    pub sustained: bool,
}

/// Assign the taxonomy for one sample. `folder` is relative to the scanned root;
/// it is combined with `name` so folder keywords ("…/Drums/…") count too.
#[allow(clippy::too_many_arguments)]
pub fn label_sample(
    folder: &str,
    name: &str,
    length: f64,
    transients: usize,
    bpm: f64,
    harmonicity: f64,
    sustain: f64,
    attack: f64,
    crest: f64,
    centroid: f64,
    low: f64,
    high: f64,
) -> Labels {
    // Loop if it has multiple transients OR carries a BPM (ACID) tag.
    let is_loop = transients > 1 || bpm > 0.0;
    // A single fundamental note held for the whole file (drone/pad/sustained tone).
    let sustained = harmonicity > 0.5 && !is_loop && sustain > 0.6;

    // Categorize on the FULL relative path (folder + file name), so keywords in
    // the folder structure help identify a file whose name alone is ambiguous.
    let full_name = format!("{} {}", folder.replace('/', " "), name);
    let (name_group, name_sub, name_match) = categorize(&full_name);
    let (group, reason) = if is_loop {
        let why = if transients > 1 && bpm > 0.0 {
            format!("{} transients + {:.0} BPM tag → loop", transients, bpm)
        } else if transients > 1 {
            format!("{} transients (>1) → loop", transients)
        } else {
            format!("{:.0} BPM tag → loop", bpm)
        };
        ("Loops/Patterns".to_string(), why)
    } else if name_match.is_empty() {
        (name_group.to_string(), "no naming keyword matched".to_string())
    } else {
        (name_group.to_string(), format!("path matched \"{}\"", name_match))
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

    // A generic "drum" tag with no specific instrument matched ⇒ flag for a
    // second (acoustic) audit rather than trusting the vague name. Uses the full
    // path so a "…/Drums/…" folder counts too.
    let audit = !is_loop && group == "Unclassified" && normalize_name(&full_name).contains("drum");

    // subgroup: loops split Beat/Groove/Loop by name; one-shots use the curated
    // instrument level, else a "Drum" audit tag, else the group + length tier.
    let subgroup = if is_loop {
        let n = normalize_name(&full_name);
        if n.contains("beat") { "Beat" } else if n.contains("groove") { "Groove" } else { "Loop" }.to_string()
    } else if !name_sub.is_empty() {
        name_sub.to_string()
    } else if audit {
        "Drum".to_string()
    } else {
        format!("{} {}", group, length_class)
    };

    let reason = if audit {
        "generic \"drum\" tag — flagged for acoustic audit".to_string()
    } else {
        reason
    };

    Labels { group, reason, timbre, length_class, subgroup, audit, sustained }
}
