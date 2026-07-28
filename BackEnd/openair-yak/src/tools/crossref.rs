//! Cross-reference a type's panel controls against its YAK command vocabulary.
//!
//! Three questions, one report: which controls already carry a `yak_handler`,
//! which have a command sitting right there unbound (the work), and which
//! commands no control exposes.
//!
//! Advisory, not generative — it writes nothing. `--emit` prints handler stubs
//! for a human to paste and check.

use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

use serde_json::{json, Value};

use super::{str_field, tables, VERBS};

/// Which models a type's panels should be cross-referenced against.
///
/// A type can have several (the bench has two scope families and four PSU
/// modules), and a control counts as covered if ANY of them offers the command —
/// the panel is stamped per device, so each instance resolves against its own
/// model.
///
/// LCR and Distortion are listed even though 4263A and HP_8903B currently yield
/// zero commands: an explicit all-controls-unbacked row is the finding, silence
/// is not.
const TYPE_MODELS: [(&str, &[&str]); 9] = [
    ("DMM", &["34401A"]),
    ("Load", &["6060B"]),
    ("Power", &["66101A", "66102A", "66103A", "66104A"]),
    ("Generator", &["33210A", "33220A"]),
    ("Oscilloscope", &["54641D", "DS1104Z"]),
    ("Spectrum", &["N9340B", "N9342CN", "HPE4411A"]),
    ("Router", &["3235"]),
    ("LCR", &["4263A"]),
    ("Distortion", &["Porta_one", "HP_8903B"]),
];

/// Domain knowledge name similarity cannot supply. control name -> command name.
/// Deliberately small: only pairs a technician would call obvious, where the
/// words share no useful stem.
const ALIASES: [(&str, &[(&str, &str)]); 3] = [
    (
        "DMM",
        &[
            ("Mode_VDC", "Config_DC_Volts"),
            ("Mode_VAC", "Config_AC_Volts"),
            ("Mode_RES", "Measure_Resistance_2Wire"),
            ("Mode_FRES", "Config_Resistance_4Wire"),
            ("Mode_ADC", "Measure_DC_Current"),
            ("Primary_Readout", "Read_Next"),
            ("Trend_Graph", "Fetch_Existing"),
            ("DMM_MODEL", "Read_IDN"),
        ],
    ),
    (
        "Load",
        &[
            ("Master_Input_Switch", "Input_ON"),
            ("Set_Current", "Set_Current_Level"),
            ("Meter_Volts", "Measure_All"),
            ("Meter_Amps", "Measure_All"),
            ("Meter_Watts", "Measure_All"),
            ("DC_LOAD_MODEL", "IDN"),
        ],
    ),
    (
        "Power",
        &[
            ("Master_Output_Switch", "Output_ON"),
            ("Voltage_Fader", "Set_Voltage"),
            ("Current_Fader", "Set_Current"),
        ],
    ),
];

/// Widget types that display rather than command. They can still carry a handler
/// (a readout is a query), so they are reported — just never counted as missing.
const READOUT_TYPES: [&str; 6] = [
    "_GuiLabel",
    "_NeedleVUMeter",
    "_GuiGraph",
    "_TextInput",
    "_GuiValue",
    "_Value",
];

const SKIP_KEYS: [&str; 10] = [
    "label",
    "style",
    "cosmetics",
    "layout",
    "domain",
    "options",
    "description",
    "message_details",
    "behavior",
    "geometry",
];

// ── Python's difflib.SequenceMatcher.ratio(), reimplemented ──────────────────
//
// Reimplemented rather than swapped for an off-the-shelf edit distance, because
// the score it feeds is compared against fixed thresholds (30 to suggest at all,
// 55 and 100 to mark confidence). A different similarity measure would keep the
// same numbers meaning different things, and silently re-rank every suggestion.
//
// With no junk heuristic — the names here are far below difflib's 200-element
// autojunk threshold — `find_longest_match` reduces to the longest common
// contiguous run, preferring the earliest in `a` then the earliest in `b`.

fn longest_match(a: &[char], b: &[char], alo: usize, ahi: usize, blo: usize, bhi: usize) -> (usize, usize, usize) {
    let (mut besti, mut bestj, mut bestsize) = (alo, blo, 0usize);
    let mut j2len: BTreeMap<usize, usize> = BTreeMap::new();
    for i in alo..ahi {
        let mut newj2len: BTreeMap<usize, usize> = BTreeMap::new();
        for j in blo..bhi {
            if b[j] != a[i] {
                continue;
            }
            let k = if j > 0 { j2len.get(&(j - 1)).copied().unwrap_or(0) } else { 0 } + 1;
            newj2len.insert(j, k);
            if k > bestsize {
                besti = i + 1 - k;
                bestj = j + 1 - k;
                bestsize = k;
            }
        }
        j2len = newj2len;
    }
    (besti, bestj, bestsize)
}

fn matched_total(a: &[char], b: &[char], alo: usize, ahi: usize, blo: usize, bhi: usize) -> usize {
    let (i, j, k) = longest_match(a, b, alo, ahi, blo, bhi);
    if k == 0 {
        return 0;
    }
    k + matched_total(a, b, alo, i, blo, j) + matched_total(a, b, i + k, ahi, j + k, bhi)
}

/// `2 * M / T`, where M is the matched character count and T both lengths.
fn ratio(a: &str, b: &str) -> f64 {
    let a: Vec<char> = a.chars().collect();
    let b: Vec<char> = b.chars().collect();
    let t = a.len() + b.len();
    if t == 0 {
        return 1.0;
    }
    let m = matched_total(&a, &b, 0, a.len(), 0, b.len());
    2.0 * m as f64 / t as f64
}

// ── Reading the two sides ────────────────────────────────────────────────────

/// `{model: {command: scpi}}` from `Yak/<Family>/<Model>/commands.json`.
fn yak_vocabulary(yak: &Path) -> BTreeMap<String, Vec<(String, String)>> {
    let mut models: BTreeMap<String, Vec<(String, String)>> = BTreeMap::new();
    for (_, table) in tables(yak) {
        let model = str_field(&table, "model");
        if model.is_empty() {
            continue;
        }
        let entry = models.entry(model).or_default();
        for verb in VERBS {
            if let Some(block) = table.get(verb).and_then(|b| b.as_object()) {
                for (name, cmd) in block {
                    entry.push((name.clone(), str_field(cmd, "scpi")));
                }
            }
        }
    }
    models
}

/// `[(widget_name, widget_type, has_handler)]` for a type's per-device panel.
///
/// One file per type — `<Type>/<Type>.json`. The `<Type>_N.json` beside it is
/// deliberately not read: its widgets are the same controls again, repeated per
/// member, and counting them would report a type's coverage twice.
fn template_controls(templates: &Path, type_name: &str) -> Vec<(String, String, bool)> {
    let mut found = Vec::new();
    let mut seen = BTreeSet::new();

    fn walk(
        node: &Value,
        name: Option<&str>,
        found: &mut Vec<(String, String, bool)>,
        seen: &mut BTreeSet<String>,
    ) {
        match node {
            Value::Object(map) => {
                if let Some(wtype) = map.get("type").and_then(|t| t.as_str()) {
                    if wtype.starts_with('_') {
                        if let Some(n) = name {
                            if seen.insert(n.to_string()) {
                                // A readout is bound too: `yak_readout` makes the
                                // builder point the widget at the device's /Read
                                // topic, which is how a display widget
                                // participates. Counting it as unbound would
                                // report finished work.
                                let bound = map.get("yak_handler").map(|h| h.is_object())
                                    == Some(true)
                                    || map.get("yak_readout") == Some(&Value::Bool(true));
                                found.push((n.to_string(), wtype.to_string(), bound));
                            }
                        }
                    }
                }
                for (key, value) in map {
                    if SKIP_KEYS.contains(&key.as_str()) {
                        continue;
                    }
                    let next = if value.is_object() { Some(key.as_str()) } else { name };
                    walk(value, next, found, seen);
                }
            }
            Value::Array(items) => {
                for item in items {
                    walk(item, name, found, seen);
                }
            }
            _ => {}
        }
    }

    let path = templates.join(type_name).join(format!("{type_name}.json"));
    if let Some(doc) = super::read_json(&path) {
        walk(&doc, None, &mut found, &mut seen);
    }
    found
}

fn normalize(text: &str) -> String {
    text.to_lowercase()
        .chars()
        .filter(|c| c.is_ascii_alphanumeric())
        .collect()
}

fn tokens(text: &str) -> BTreeSet<String> {
    text.to_lowercase()
        .split(|c: char| !c.is_ascii_alphanumeric())
        .filter(|t| t.len() > 1)
        .map(String::from)
        .collect()
}

/// `(command, score, why)`. Score 100 = curated alias.
fn suggest(
    control: &str,
    commands: &[(String, (String, String))],
    type_name: &str,
) -> Option<(String, f64, String)> {
    if let Some((_, pairs)) = ALIASES.iter().find(|(t, _)| *t == type_name) {
        if let Some((_, alias)) = pairs.iter().find(|(c, _)| *c == control) {
            if commands.iter().any(|(name, _)| name == alias) {
                return Some((alias.to_string(), 100.0, "alias".to_string()));
            }
        }
    }

    let control_tokens = tokens(control);
    let normalized = normalize(control);
    let mut best: (Option<String>, f64, String) = (None, 0.0, String::new());
    for (command, _) in commands {
        let overlap: Vec<String> = control_tokens
            .intersection(&tokens(command))
            .cloned()
            .collect();
        // Token overlap carries the meaning ("Set_Current" vs
        // "Set_Current_Level"); the sequence ratio breaks ties between equally
        // overlapping candidates.
        let score = overlap.len() as f64 * 30.0 + ratio(&normalized, &normalize(command)) * 40.0;
        if score > best.1 {
            let why = if overlap.is_empty() {
                "similar".to_string()
            } else {
                overlap.join("+")
            };
            best = (Some(command.clone()), score, why);
        }
    }
    match best.0 {
        Some(c) if best.1 >= 30.0 => Some((c, best.1, best.2)),
        _ => None,
    }
}

struct Match {
    control: String,
    command: String,
    scpi: String,
    score: f64,
    why: String,
}

fn report(
    yak: &Path,
    templates: &Path,
    type_name: &str,
    vocab: &BTreeMap<String, Vec<(String, String)>>,
    verbose: bool,
) -> Vec<Match> {
    let _ = yak;
    let models: &[&str] = TYPE_MODELS
        .iter()
        .find(|(t, _)| *t == type_name)
        .map(|(_, m)| *m)
        .unwrap_or(&[]);

    // First model offering a command wins, which is `setdefault` semantics.
    let mut commands: Vec<(String, (String, String))> = Vec::new();
    let mut have: BTreeSet<String> = BTreeSet::new();
    for model in models {
        for (command, scpi) in vocab.get(*model).map(|v| v.as_slice()).unwrap_or(&[]) {
            if have.insert(command.clone()) {
                commands.push((command.clone(), (scpi.clone(), model.to_string())));
            }
        }
    }

    let controls = template_controls(templates, type_name);
    let bound = controls.iter().filter(|c| c.2).count();
    let unbound: Vec<&(String, String, bool)> = controls.iter().filter(|c| !c.2).collect();

    let mut matched: Vec<Match> = Vec::new();
    let mut orphan_controls: Vec<(String, String)> = Vec::new();
    for (name, wtype, _) in &unbound {
        match suggest(name, &commands, type_name) {
            Some((command, score, why)) => {
                let scpi = commands
                    .iter()
                    .find(|(c, _)| *c == command)
                    .map(|(_, (s, _))| s.clone())
                    .unwrap_or_default();
                matched.push(Match {
                    control: name.clone(),
                    command,
                    scpi,
                    score,
                    why,
                });
            }
            None => orphan_controls.push((name.clone(), wtype.clone())),
        }
    }

    let used: BTreeSet<&str> = matched.iter().map(|m| m.command.as_str()).collect();
    let unused: Vec<&(String, (String, String))> = {
        let mut v: Vec<&(String, (String, String))> = commands
            .iter()
            .filter(|(c, _)| !used.contains(c.as_str()))
            .collect();
        v.sort_by(|a, b| a.0.cmp(&b.0));
        v
    };

    let bar = "=".repeat(78);
    println!(
        "\n{bar}\n{type_name}  —  models: {}  ({} commands, {} widgets)\n{bar}",
        if models.is_empty() {
            "none".to_string()
        } else {
            models.join(", ")
        },
        commands.len(),
        controls.len()
    );
    println!("  BOUND        {bound:3}  already carry a yak_handler");
    println!(
        "  MATCH        {:3}  control + command exist, binding missing  <- the work",
        matched.len()
    );
    println!(
        "  CONTROL-ONLY {:3}  no command found (SCPI to author)",
        orphan_controls.len()
    );
    println!(
        "  COMMAND-ONLY {:3}  command exists, no control exposes it",
        unused.len()
    );

    if verbose {
        println!("\n  -- proposed bindings {}", "-".repeat(55));
        let mut sorted: Vec<&Match> = matched.iter().collect();
        sorted.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
        for m in sorted {
            let flag = if m.score >= 100.0 {
                "  "
            } else if m.score < 55.0 {
                "? "
            } else {
                "~ "
            };
            println!(
                "  {flag}{:30} -> {:32} {}",
                truncate(&m.control, 30),
                truncate(&m.command, 32),
                truncate(&m.scpi, 38)
            );
            if m.score < 100.0 {
                println!("      {:30}    (match: {}, score {:.0})", "", m.why, m.score);
            }
        }
        if !orphan_controls.is_empty() {
            println!("\n  -- controls with no command {}", "-".repeat(47));
            for (name, wtype) in &orphan_controls {
                let tag = if READOUT_TYPES.contains(&wtype.as_str()) {
                    "readout"
                } else {
                    "CONTROL"
                };
                println!("    [{tag}] {:34} {wtype}", truncate(name, 34));
            }
        }
        if !unused.is_empty() {
            println!("\n  -- unused commands {}", "-".repeat(56));
            for (command, (scpi, _)) in &unused {
                println!("    {:34} {}", truncate(command, 34), truncate(scpi, 40));
            }
        }
    }
    matched
}

fn truncate(s: &str, n: usize) -> String {
    s.chars().take(n).collect()
}

/// `yak_handler` blocks for the proposed bindings, ready to paste.
///
/// `target` and `model` are deliberately absent: the orchestrator's
/// `instruments.rs` stamps those per device, and a hardcoded one in the template
/// would point every instance at the same instrument.
fn emit_stubs(type_name: &str, matched: &[Match]) {
    println!("\n// yak_handler stubs for {type_name} — verb/converter need a human pass");
    let mut sorted: Vec<&Match> = matched.iter().collect();
    sorted.sort_by(|a, b| a.control.cmp(&b.control));
    for m in sorted {
        let placeholder = super::placeholders(&m.scpi).into_iter().next();
        let verb = if m.scpi.trim_end().ends_with('?') {
            "nab"
        } else if placeholder.is_some() {
            "set"
        } else {
            "do"
        };
        // Spaced separators, not serde_json's compact form. These lines exist to
        // be pasted into a hand-edited template, and `{"enable":true,...}` beside
        // authored JSON reads as machine output someone forgot to format.
        let quoted = |v: &str| json!(v).to_string();
        let mut parts = vec![
            "\"enable\": true".to_string(),
            format!("\"yak_type\": {}", quoted(verb)),
            format!("\"sub_path\": {}", quoted(type_name)),
            format!("\"command\": {}", quoted(&m.command)),
        ];
        if let Some(p) = placeholder {
            parts.push(format!("\"input_name\": {}", quoted(&p)));
            parts.push("\"converter\": \"\"".to_string());
        }
        println!(
            "  \"{}\": {{\"yak_handler\": {{{}}}}},",
            m.control,
            parts.join(", ")
        );
    }
}

pub fn run(type_name: Option<String>, verbose: bool, emit: bool) -> i32 {
    let Some(yak) = super::yak_root() else {
        println!("❌ YAK tree not found; set YAK_REPO_PATH");
        return 1;
    };
    let templates = super::repo_root(&yak).join("BackEnd").join("Instruments");
    let vocab = yak_vocabulary(&yak);

    // A type present in the manifest but missing from TYPE_MODELS is not
    // "clean" — it is unexamined. Say so loudly rather than omitting the row.
    if let Some(manifest) = super::read_json(&templates.join("manifest.json")) {
        if let Some(map) = manifest.as_object() {
            let listed: BTreeSet<&str> = TYPE_MODELS.iter().map(|(t, _)| *t).collect();
            let unlisted: Vec<&String> =
                map.keys().filter(|k| !listed.contains(k.as_str())).collect();
            if !unlisted.is_empty() {
                let mut u: Vec<&str> = unlisted.iter().map(|s| s.as_str()).collect();
                u.sort();
                println!(
                    "⚠️  manifest types with no models listed here (NOT analyzed): {}\n",
                    u.join(", ")
                );
            }
        }
    }

    // Commands whose model key is not a real model: the grandparent-is-the-model
    // rule mis-files anything nested deeper than <model>/<section>/file.json.
    // These are unreachable at runtime whenever YAK narrows a lookup by model,
    // so they are reported, not silently dropped.
    let real: BTreeSet<&str> = TYPE_MODELS.iter().flat_map(|(_, ms)| ms.iter().copied()).collect();
    let mut phantom: Vec<(&String, usize)> = vocab
        .iter()
        .filter(|(m, _)| !real.contains(m.as_str()))
        .map(|(m, c)| (m, c.len()))
        .collect();
    if !phantom.is_empty() {
        phantom.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(b.0)));
        let total: usize = phantom.iter().map(|(_, n)| n).sum();
        let detail: Vec<String> = phantom.iter().map(|(m, n)| format!("{m} ({n})")).collect();
        println!(
            "⚠️  {total} commands filed under non-model folders — unreachable by model-narrowed lookup: {}\n",
            detail.join(", ")
        );
    }

    let types: Vec<String> = match type_name {
        Some(t) => vec![t],
        None => TYPE_MODELS.iter().map(|(t, _)| t.to_string()).collect(),
    };
    for t in &types {
        let matched = report(&yak, &templates, t, &vocab, verbose || emit);
        if emit {
            emit_stubs(t, &matched);
        }
    }
    0
}

#[cfg(test)]
mod tests {
    use super::ratio;

    /// Values taken from Python's difflib on the same inputs. The thresholds
    /// this score feeds (30 / 55 / 100) are absolute, so a merely "similar"
    /// similarity measure would quietly re-rank every suggestion.
    #[test]
    fn ratio_matches_python_difflib() {
        let close = |a: f64, b: f64| (a - b).abs() < 1e-9;
        assert!(close(ratio("", ""), 1.0));
        assert!(close(ratio("abc", "abc"), 1.0));
        assert!(close(ratio("abc", "xyz"), 0.0));
        // difflib: SequenceMatcher(None, "setcurrent", "setcurrentlevel").ratio()
        assert!(
            close(ratio("setcurrent", "setcurrentlevel"), 0.8),
            "got {}",
            ratio("setcurrent", "setcurrentlevel")
        );
        // SequenceMatcher(None, "abcd", "bcde").ratio() -> 2*3/8
        assert!(close(ratio("abcd", "bcde"), 0.75), "got {}", ratio("abcd", "bcde"));
        // Order matters to the blocks but not to the total here.
        assert!(close(ratio("mastervoltage", "voltagemaster"), ratio("voltagemaster", "mastervoltage")));
    }

    #[test]
    fn ratio_uses_contiguous_blocks_not_bare_character_counts() {
        // Same characters, different arrangement: a set-based measure would call
        // these identical.
        assert!(ratio("abcdef", "fedcba") < 0.5);
    }
}
