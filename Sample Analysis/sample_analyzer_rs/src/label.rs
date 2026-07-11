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
    // Categorize on the FULL relative path (folder + file name), so keywords in
    // the folder structure help identify a file whose name alone is ambiguous.
    let full_name = format!("{} {}", folder.replace('/', " "), name);
    let norm = normalize_name(&full_name);
    let (name_group, name_sub, name_match) = categorize(&full_name);

    // Loop detection. A BPM (ACID) tag is authoritative; a name that says
    // "loop/groove/beat" is a loop. Otherwise multiple transients only mean a
    // loop when the name gives NO drum/instrument hint — a named drum ("snr",
    // "kick", the word "drum", …) with no BPM stays a one-shot even if it
    // re-triggers (a roll/flam), rather than being mis-flagged as a loop.
    let name_says_loop = name_group == "Loops/Patterns";
    let has_drum_hint = !name_match.is_empty() || norm.contains("drum");
    let is_loop = bpm > 0.0 || name_says_loop || (transients > 1 && !has_drum_hint);
    // A single fundamental note held for the whole file (drone/pad/sustained tone).
    let sustained = harmonicity > 0.5 && !is_loop && sustain > 0.6;

    let (group, reason) = if is_loop {
        let why = if bpm > 0.0 && transients > 1 {
            format!("{} transients + {:.0} BPM tag → loop", transients, bpm)
        } else if bpm > 0.0 {
            format!("{:.0} BPM tag → loop", bpm)
        } else if name_says_loop {
            format!("name \"{}\" → loop", name_match)
        } else {
            format!("{} transients (>1), no drum/instrument name → loop", transients)
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
    let audit = !is_loop && group == "Unclassified" && norm.contains("drum");

    // subgroup: loops split Beat/Groove/Loop by name; one-shots use the curated
    // instrument level, else a "Drum" audit tag, else the group + length tier.
    let subgroup = if is_loop {
        // Instrument subgroups for loops (extend this list as needed), else the
        // Beat/Groove flavour, else a plain Loop.
        if norm.contains("guitar") { "Guitar" }
        else if norm.contains("beat") { "Beat" }
        else if norm.contains("groove") { "Groove" }
        else { "Loop" }.to_string()
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

#[cfg(test)]
mod tests {
    use super::label_sample;

    fn group_of(name: &str, transients: usize, bpm: f64) -> String {
        // Neutral feature values; only `name`, `transients`, `bpm` matter here.
        label_sample("", name, 0.5, transients, bpm, 0.0, 0.0, 0.01, 5.0, 1000.0, 0.3, 0.3).group
    }

    #[test]
    fn named_drum_without_bpm_is_not_a_loop() {
        // Named drums that re-trigger (roll/flam) but carry no BPM stay one-shots.
        assert_eq!(group_of("Snr_roll.wav", 5, 0.0), "Snare");
        assert_eq!(group_of("Kick_flam.wav", 3, 0.0), "Kick");
        // The generic word "drum" also blocks the transient→loop guess.
        assert_eq!(group_of("Drum_hit.wav", 4, 0.0), "Unclassified");
        // A real BPM (ACID) tag is authoritative → loop regardless of name.
        assert_eq!(group_of("Snare_thing.wav", 5, 120.0), "Loops/Patterns");
        // A name that literally says "loop" → loop.
        assert_eq!(group_of("Drum Loop.wav", 5, 0.0), "Loops/Patterns");
        // Unnamed, many transients, no BPM → loop (the transient fallback still works).
        assert_eq!(group_of("01.wav", 5, 0.0), "Loops/Patterns");
    }
}
