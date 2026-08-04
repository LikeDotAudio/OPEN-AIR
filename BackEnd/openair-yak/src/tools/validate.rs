//! Check the command tables against their own invariants.
//!
//! Written after a multi-step edit pass silently dropped ten hand-authored
//! commands: the tables are large enough now that a regression is invisible in a
//! diff, and "3646 loaded" reads the same whether or not the right 3646 are
//! there. Run it against git for the one check that needs a baseline:
//!
//! ```text
//! git stash && openair-yak check-tables --snapshot /tmp/before.json && git stash pop
//! openair-yak check-tables --against /tmp/before.json
//! ```

use std::collections::BTreeMap;
use std::path::Path;

use serde_json::Value;

use super::{statement_head, str_field, tables, verb_entries_in_file_order};

/// This tool's own verb order, which is NOT the generators' order.
///
/// The report groups findings by first appearance, so the order commands are
/// visited decides the order of every summary line. Sharing the generators'
/// `set, rig, nab, do` reshuffled the whole "by kind" section for no reason.
const VERBS: [&str; 4] = ["set", "do", "rig", "nab"];

const VOWELS: [char; 5] = ['A', 'E', 'I', 'O', 'U'];

/// One thing wrong: `(model, where, message)`.
type Finding = (String, String, String);

/// `VOLTage` -> `VOLT`, `LLINe1` -> `LLIN1`, `RESISTANCE` -> `RES`.
///
/// The trailing index has to survive: `CALCulate:LLINe1` addresses limit line 1,
/// and dropping the `1` turns it into a different command.
fn short_keyword(word: &str) -> String {
    if word.chars().any(|c| c.is_lowercase()) {
        let caps: String = word
            .chars()
            .filter(|c| c.is_uppercase() || c.is_numeric())
            .collect();
        if !caps.is_empty() {
            return caps;
        }
    }
    let letters: String = word.chars().filter(|c| c.is_alphabetic()).collect();
    // The Python slices the ORIGINAL word by the letter count, so this is the
    // remainder after that many characters, not "the non-letters".
    let trailing: String = word.chars().skip(letters.chars().count()).collect();
    let chars: Vec<char> = letters.chars().collect();
    if chars.len() <= 4 {
        return format!("{letters}{trailing}");
    }
    let take = if VOWELS.contains(&chars[3].to_ascii_uppercase()) {
        3
    } else {
        4
    };
    let base: String = chars[..take].iter().collect();
    format!("{base}{trailing}")
}

/// The `commands` links in knownDevices.json must resolve and be complete.
///
/// A dangling link reads as coverage, and a model with a table but no entry is
/// unreachable by discovery however complete its vocabulary is.
fn check_known_devices(yak: &Path, findings: &mut Vec<Finding>) {
    let known_path = yak.join("knownDevices.json");
    let Some(known) = super::read_json(&known_path) else {
        findings.push((
            "knownDevices".into(),
            known_path.display().to_string(),
            "unreadable".into(),
        ));
        return;
    };
    let Some(known) = known.as_object() else { return };

    let mut on_disk: BTreeMap<String, String> = BTreeMap::new();
    for (path, table) in tables(yak) {
        on_disk.insert(str_field(&table, "model"), super::rel_to(yak, &path));
    }

    for (model, rec) in known {
        let link = rec.get("commands").and_then(|c| c.as_str());
        match link {
            Some(link) if !yak.join(link).is_file() => findings.push((
                model.clone(),
                "knownDevices.commands".into(),
                format!("link points at nothing: {link}"),
            )),
            Some(link) if on_disk.get(model).map(|s| s.as_str()) != Some(link) => findings.push((
                model.clone(),
                "knownDevices.commands".into(),
                format!(
                    "link is {link}, table is at {}",
                    on_disk.get(model).cloned().unwrap_or_else(|| "None".into())
                ),
            )),
            None if on_disk.contains_key(model) => findings.push((
                model.clone(),
                "knownDevices.commands".into(),
                format!("has a table ({}) but no link", on_disk[model]),
            )),
            _ => {}
        }
    }
    for (model, rel) in &on_disk {
        if !known.contains_key(model) {
            findings.push((
                model.clone(),
                rel.clone(),
                "command table with no knownDevices entry — discovery cannot reach it".into(),
            ));
        }
    }
}

fn check(yak: &Path) -> (Vec<Finding>, BTreeMap<String, usize>) {
    let mut findings: Vec<Finding> = Vec::new();
    let mut counts: BTreeMap<String, usize> = BTreeMap::new();

    for (path, table) in tables(yak) {
        let model = table
            .get("model")
            .and_then(|m| m.as_str())
            .unwrap_or("?")
            .to_string();
        let folder = path
            .parent()
            .and_then(|p| p.file_name())
            .map(|f| f.to_string_lossy().to_string())
            .unwrap_or_default();
        let mut bad = |m: &str, w: String, msg: String| findings.push((m.to_string(), w, msg));

        if model != folder {
            bad(
                &model,
                path.display().to_string(),
                format!("declared model does not match its folder '{folder}'"),
            );
        }

        let mut seen_names: BTreeMap<String, String> = BTreeMap::new();
        let mut per_verb_scpi: BTreeMap<String, BTreeMap<String, String>> = BTreeMap::new();
        let mut n = 0;

        for verb in VERBS {
            for (name, e) in verb_entries_in_file_order(&table, verb) {
                n += 1;
                let where_ = format!("{verb}/{name}");
                if let Some(first) = seen_names.get(name) {
                    bad(
                        &model,
                        where_.clone(),
                        format!("name also used in '{first}' — repository.rs keeps the first and warns"),
                    );
                }
                seen_names.insert(name.clone(), verb.to_string());

                let scpi = e.get("scpi").and_then(|s| s.as_str()).unwrap_or("");
                if scpi.trim().is_empty() {
                    bad(&model, where_.clone(), "no scpi".into());
                    continue;
                }

                let head = scpi
                    .split(';')
                    .map(statement_head)
                    .collect::<Vec<_>>()
                    .join(";");
                let slot = per_verb_scpi.entry(verb.to_string()).or_default();
                if let Some(other) = slot.get(&head) {
                    bad(
                        &model,
                        where_.clone(),
                        format!("same SCPI node as '{other}' — one is an alias"),
                    );
                }
                slot.insert(head, name.clone());

                if str_field(e, "description").trim().is_empty() {
                    bad(&model, where_.clone(), "no description".into());
                }

                // A verb must match the shape of its template.
                let q = scpi.contains('?');
                if verb == "nab" && !q {
                    bad(&model, where_.clone(), "in nab but asks nothing".into());
                }
                if verb != "nab" && q {
                    bad(
                        &model,
                        where_.clone(),
                        "carries a '?' but is not in nab".into(),
                    );
                }

                let r = e.get("returns");
                if verb == "nab" {
                    match r.and_then(|r| r.as_object()) {
                        None => bad(&model, where_.clone(), "nab with no returns block".into()),
                        Some(r) => {
                            let want = scpi.matches('?').count() as u64;
                            let got = r.get("count").and_then(|c| c.as_u64());
                            if got != Some(want) {
                                bad(
                                    &model,
                                    where_.clone(),
                                    format!(
                                        "returns.count is {}, but the template asks {want} question(s)",
                                        got.map(|g| g.to_string()).unwrap_or_else(|| "None".into())
                                    ),
                                );
                            }
                            let fields = r.get("fields").and_then(|f| f.as_array());
                            if got.unwrap_or(0) > 1
                                && fields.map(|f| f.len() as u64) != Some(want)
                            {
                                bad(
                                    &model,
                                    where_.clone(),
                                    "chained query without one field per answer".into(),
                                );
                            }
                        }
                    }
                } else if r.is_some() && r != Some(&Value::Null) {
                    bad(
                        &model,
                        where_.clone(),
                        format!("{verb} should not carry a returns block"),
                    );
                }

                if verb == "set" || verb == "rig" {
                    match e.get("arg").and_then(|a| a.as_object()) {
                        None => bad(&model, where_.clone(), "set/rig with no arg block".into()),
                        Some(a) => {
                            let is_enum = a.get("kind").and_then(|k| k.as_str()) == Some("enum");
                            let has_values = a
                                .get("values")
                                .and_then(|v| v.as_array())
                                .map(|v| !v.is_empty())
                                .unwrap_or(false);
                            if is_enum && !has_values {
                                bad(
                                    &model,
                                    where_.clone(),
                                    "enum with no choice list — nothing can generate a legal value"
                                        .into(),
                                );
                            }
                            if let (Some(lo), Some(hi)) = (
                                a.get("min").and_then(|x| x.as_f64()),
                                a.get("max").and_then(|x| x.as_f64()),
                            ) {
                                if lo >= hi {
                                    bad(
                                        &model,
                                        where_.clone(),
                                        format!("min {} is not below max {}", fmt_num(lo), fmt_num(hi)),
                                    );
                                }
                            }
                        }
                    }
                }

                if let Some(fast) = e.get("scpiFast").and_then(|f| f.as_str()) {
                    if fast == scpi {
                        bad(
                            &model,
                            where_.clone(),
                            "scpiFast repeats scpi — drop the field".into(),
                        );
                    }
                    // Per STATEMENT: a chained template holds several, and
                    // checking only the first compared statement 1 against the
                    // whole chain.
                    for st in fast.split(';') {
                        let got = statement_head(st).trim_start_matches(':').to_string();
                        let expected: String = got
                            .split(':')
                            .map(|p| {
                                if p.is_empty() || p.contains('<') {
                                    p.to_string()
                                } else {
                                    short_keyword(p)
                                }
                            })
                            .collect::<Vec<_>>()
                            .join(":");
                        if expected.trim_end_matches('?') != got.trim_end_matches('?') {
                            bad(
                                &model,
                                where_.clone(),
                                "scpiFast is not the short form of its keywords".into(),
                            );
                            break;
                        }
                    }
                }
            }
        }
        counts.insert(model, n);
    }

    check_known_devices(yak, &mut findings);
    (findings, counts)
}

/// Render a JSON number the way Python's `str()` would, so messages match.
fn fmt_num(v: f64) -> String {
    if v.fract() == 0.0 && v.abs() < 1e15 {
        format!("{}", v as i64)
    } else {
        format!("{v}")
    }
}

pub fn run(strict: bool, snapshot: Option<String>, against: Option<String>) -> i32 {
    let Some(yak) = super::yak_root() else {
        println!("❌ YAK tree not found; set YAK_REPO_PATH");
        return 1;
    };
    let (findings, counts) = check(&yak);
    let total: usize = counts.values().sum();

    if let Some(path) = snapshot {
        let map: serde_json::Map<String, Value> = counts
            .iter()
            .map(|(k, v)| (k.clone(), Value::from(*v)))
            .collect();
        let body = serde_json::to_string_pretty(&Value::Object(map)).unwrap_or_default();
        if let Err(e) = std::fs::write(&path, body) {
            println!("❌ could not write {path}: {e}");
            return 1;
        }
        println!("snapshot: {total} commands across {} models", counts.len());
        return 0;
    }

    let mut lost_any = false;
    if let Some(path) = against {
        let Some(before) = super::read_json(Path::new(&path)).and_then(|v| v.as_object().cloned())
        else {
            println!("❌ could not read {path}");
            return 1;
        };
        let mut lost: Vec<(String, u64, u64)> = Vec::new();
        for (model, n) in &before {
            let b = n.as_u64().unwrap_or(0);
            let a = counts.get(model).copied().unwrap_or(0) as u64;
            if a < b {
                lost.push((model.clone(), b, a));
            }
        }
        lost.sort();
        for (m, b, a) in &lost {
            println!("❌ {m}: {b} -> {a} commands ({} lost)", b - a);
        }
        if !lost.is_empty() {
            return 1;
        }
        lost_any = false;
        println!("no model lost commands ({total} total)");
    }
    let _ = lost_any;

    // Counted the same two ways the Python did: the leading clause of each
    // message is its kind, which groups 3600 findings into a readable handful.
    //
    // Ties keep FIRST-SEEN order, not alphabetical — that is what
    // `collections.Counter.most_common` does, and with hundreds of kinds sharing
    // a count of 1 the tie-break decides most of the report's shape.
    let mut by_model: Vec<(&str, usize)> = Vec::new();
    let mut kinds: Vec<(String, usize)> = Vec::new();
    let bump = |list: &mut Vec<(String, usize)>, key: String| {
        match list.iter_mut().find(|(k, _)| *k == key) {
            Some((_, n)) => *n += 1,
            None => list.push((key, 1)),
        }
    };
    for (m, _w, msg) in &findings {
        match by_model.iter_mut().find(|(k, _)| *k == m.as_str()) {
            Some((_, n)) => *n += 1,
            None => by_model.push((m.as_str(), 1)),
        }
        let kind = msg
            .split(" —")
            .next()
            .unwrap_or(msg)
            .split(',')
            .next()
            .unwrap_or(msg)
            .to_string();
        bump(&mut kinds, kind);
    }

    println!(
        "{total} commands across {} models, {} finding(s)",
        counts.len(),
        findings.len()
    );
    if !findings.is_empty() {
        // Stable sort on count alone, so equal counts stay in first-seen order.
        kinds.sort_by(|a, b| b.1.cmp(&a.1));
        println!("\nby kind:");
        for (k, c) in &kinds {
            println!("   {c:>5}  {k}");
        }
        by_model.sort_by(|a, b| b.1.cmp(&a.1));
        let rendered: Vec<String> = by_model.iter().map(|(m, c)| format!("'{m}': {c}")).collect();
        println!("\nby model: {{{}}}", rendered.join(", "));
        println!("\nfirst 25:");
        for (m, w, msg) in findings.iter().take(25) {
            println!("   {m:<10} {w:<44} {msg}");
        }
    }

    if !findings.is_empty() && strict {
        1
    } else {
        0
    }
}

#[cfg(test)]
mod tests {
    use super::short_keyword;

    #[test]
    fn keywords_shorten_the_way_scpi_does() {
        // Mixed case: the capitals ARE the short form.
        assert_eq!(short_keyword("VOLTage"), "VOLT");
        assert_eq!(short_keyword("SENSe"), "SENS");
        // The trailing index has to survive — CALCulate:LLINe1 addresses limit
        // line 1, and dropping the 1 makes it a different command.
        assert_eq!(short_keyword("LLINe1"), "LLIN1");
        // All caps: truncate to 4, or 3 when the 4th letter is a vowel.
        assert_eq!(short_keyword("RESISTANCE"), "RES");
        assert_eq!(short_keyword("CURRENT"), "CURR");
        // Four or fewer letters are already short.
        assert_eq!(short_keyword("DC"), "DC");
        assert_eq!(short_keyword("MODE"), "MODE");
    }
}
