//! Point each known device at its command table, where one exists.
//!
//! `Yak/knownDevices.json` says what an instrument IS — `*IDN?` gives a model,
//! this gives back a manufacturer, a type and a note. What it could not say is
//! whether YAK knows how to TALK to it, which is the next question anyone
//! reading the file has. So an entry with a table gains a path to it:
//!
//! ```json
//! "34401A": { "manufacturer": "…", "type": "DMM", "notes": "…",
//!             "commands": "DMM/34401A/commands.json" }
//! ```
//!
//! Paths are relative to the `Yak/` directory the file lives in, so the pair
//! moves together and neither has to know where the repo is checked out.
//!
//! Generated, not maintained. A hand-kept index of 181 entries against a tree
//! that gains tables one instrument at a time is a list that is wrong by the
//! second commit — `--check` in a hook is the difference between a stale link
//! and a lie. Only the populated models get the key; a `model.json`-only folder
//! gets none, because every one of the 181 has a `model.json` and a field that
//! is always present tells the reader nothing.

use std::collections::BTreeMap;
use std::path::Path;

use serde_json::{Map, Value};

/// The order a record's keys are written in. Not alphabetical, and not
/// negotiable: it is the order the file has always had, and rewriting all 181
/// records to satisfy a sort would bury the one link that actually changed.
const FIELD_ORDER: [&str; 4] = ["manufacturer", "type", "notes", "commands"];

/// `{model: path relative to Yak/}` for every `commands.json` that exists.
///
/// Keyed by the table's DECLARED model, not its folder name, so a folder renamed
/// without its contents (or the other way round) shows up as a mismatch instead
/// of silently linking the wrong instrument.
fn tables_on_disk(yak: &Path) -> BTreeMap<String, String> {
    let mut found = BTreeMap::new();
    for (path, table) in super::tables(yak) {
        let rel = super::rel_to(yak, &path);
        let folder = path
            .parent()
            .and_then(|p| p.file_name())
            .map(|f| f.to_string_lossy().to_string())
            .unwrap_or_default();
        let declared = table.get("model").and_then(|m| m.as_str());
        if let Some(d) = declared {
            if d != folder {
                println!("   ⚠️  {rel} declares model '{d}' but sits in '{folder}'");
            }
        }
        found.insert(declared.unwrap_or(&folder).to_string(), rel);
    }
    found
}

struct Rebuilt {
    known: Map<String, Value>,
    linked: Vec<String>,
    dropped: Vec<String>,
    orphans: Vec<String>,
}

fn rebuild(yak: &Path) -> Option<Rebuilt> {
    let known_path = yak.join("knownDevices.json");
    let known = super::read_json(&known_path)?;
    let known = known.as_object()?.clone();
    let tables = tables_on_disk(yak);

    let (mut linked, mut dropped, mut orphans) = (Vec::new(), Vec::new(), Vec::new());
    let mut out: Map<String, Value> = Map::new();

    // Sorted, because the file is written sorted; doing it here means the
    // insertion order below IS the output order.
    let mut models: Vec<&String> = known.keys().collect();
    models.sort();

    for model in models {
        let mut rec = known[model].as_object().cloned().unwrap_or_default();
        match tables.get(model) {
            Some(rel) => {
                if rec.get("commands").and_then(|c| c.as_str()) != Some(rel.as_str()) {
                    linked.push(model.clone());
                }
                rec.insert("commands".into(), Value::String(rel.clone()));
            }
            None => {
                // The table went away, or was never there. A link to nothing is
                // worse than no link: it reads as coverage.
                if rec.remove("commands").is_some() {
                    dropped.push(model.clone());
                }
            }
        }
        let mut ordered = Map::new();
        for key in FIELD_ORDER {
            if let Some(v) = rec.get(key) {
                ordered.insert(key.to_string(), v.clone());
            }
        }
        out.insert(model.clone(), Value::Object(ordered));
    }

    for model in tables.keys() {
        if !known.contains_key(model) {
            orphans.push(model.clone());
        }
    }

    Some(Rebuilt {
        known: out,
        linked,
        dropped,
        orphans,
    })
}

pub fn run(check: bool) -> i32 {
    let Some(yak) = super::yak_root() else {
        println!("❌ YAK tree not found; set YAK_REPO_PATH");
        return 1;
    };
    let known_path = yak.join("knownDevices.json");
    let Some(r) = rebuild(&yak) else {
        println!("❌ could not read {}", known_path.display());
        return 1;
    };

    let rendered = match serde_json::to_string_pretty(&Value::Object(r.known.clone())) {
        Ok(s) => format!("{s}\n"),
        Err(e) => {
            println!("❌ could not render knownDevices.json: {e}");
            return 1;
        }
    };

    if !r.orphans.is_empty() {
        // A table nothing can be discovered into: the VISA scan yields a model
        // string, and a model absent from knownDevices answers "Unknown
        // Instrument" no matter how complete its vocabulary is.
        let mut o = r.orphans.clone();
        o.sort();
        println!(
            "   ⚠️  {} command table(s) with no knownDevices entry — unreachable by discovery: {}",
            o.len(),
            o.join(", ")
        );
    }

    let current = std::fs::read_to_string(&known_path).unwrap_or_default();
    let have = r
        .known
        .values()
        .filter(|v| v.get("commands").is_some())
        .count();

    if check {
        if current != rendered {
            println!(
                "❌ knownDevices.json is stale — {} link(s) to add, {} to drop",
                r.linked.len(),
                r.dropped.len()
            );
            return 1;
        }
        println!(
            "✅ knownDevices.json is current ({have} of {} linked)",
            r.known.len()
        );
        return if r.orphans.is_empty() { 0 } else { 1 };
    }

    if let Err(e) = std::fs::write(&known_path, rendered) {
        println!("❌ could not write {}: {e}", known_path.display());
        return 1;
    }
    println!(
        "   ✅ {} known devices, {have} linked to a command table",
        r.known.len()
    );
    if !r.linked.is_empty() {
        let mut l = r.linked.clone();
        l.sort();
        println!("      + {}", l.join(", "));
    }
    if !r.dropped.is_empty() {
        let mut d = r.dropped.clone();
        d.sort();
        println!("      - dropped a dead link on {}", d.join(", "));
    }
    if r.orphans.is_empty() {
        0
    } else {
        1
    }
}
