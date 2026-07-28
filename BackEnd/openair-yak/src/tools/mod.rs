//! Build-time tooling over the YAK command tables.
//!
//! These are the Rust ports of what used to be five Python scripts in
//! `BackEnd/openair-yak/tools/`. They are reports and generators over the
//! `Yak/<Family>/<Model>/commands.json` tree, not part of the running agent —
//! but they belong to the same crate as the tree they read, so they ship as
//! subcommands of the YAK binary rather than as a separate toolchain.
//!
//! Running `openair-yak` with no subcommand still starts the agent, which is
//! what `Deployment/openair.py` does.

pub mod crossref;
pub mod links;
pub mod list;
pub mod trees;
pub mod validate;

use std::path::{Path, PathBuf};

use serde_json::Value;

/// The four YAK verbs, in the order every report presents them.
pub const VERBS: [&str; 4] = ["set", "rig", "nab", "do"];

/// Locate the `Yak/` tree.
///
/// `YAK_REPO_PATH` wins, else walk up from the working directory until the tree
/// appears — so a tool works from `openair-yak/`, `BackEnd/`, or the repo root,
/// which is the same rule the agent itself uses.
pub fn yak_root() -> Option<PathBuf> {
    if let Ok(p) = std::env::var("YAK_REPO_PATH") {
        let p = PathBuf::from(p);
        if p.is_dir() {
            return Some(p);
        }
    }
    let mut dir = std::env::current_dir().ok()?;
    loop {
        for candidate in [
            dir.join("BackEnd/openair-yak/Yak"),
            dir.join("openair-yak/Yak"),
            dir.join("Yak"),
        ] {
            if candidate.is_dir() {
                return Some(candidate);
            }
        }
        if !dir.pop() {
            return None;
        }
    }
}

/// The repo root, derived from the located `Yak/` tree.
pub fn repo_root(yak: &Path) -> PathBuf {
    // <root>/BackEnd/openair-yak/Yak
    yak.ancestors().nth(3).unwrap_or(yak).to_path_buf()
}

/// Every `commands.json` in the tree, sorted by path.
///
/// Sorted because these tools generate files that are committed: an unstable
/// order would produce a diff of the filesystem's mood rather than of the edit.
pub fn tables(yak: &Path) -> Vec<(PathBuf, Value)> {
    let mut out = Vec::new();
    let Ok(families) = std::fs::read_dir(yak) else {
        return out;
    };
    let mut families: Vec<PathBuf> = families.flatten().map(|e| e.path()).collect();
    families.sort();
    for family in families {
        let Ok(models) = std::fs::read_dir(&family) else {
            continue;
        };
        let mut models: Vec<PathBuf> = models.flatten().map(|e| e.path()).collect();
        models.sort();
        for model in models {
            let path = model.join("commands.json");
            if !path.is_file() {
                continue;
            }
            match read_json(&path) {
                Some(v) => out.push((path, v)),
                None => continue,
            }
        }
    }
    out
}

pub fn read_json(path: &Path) -> Option<Value> {
    let body = std::fs::read_to_string(path).ok()?;
    match serde_json::from_str(&body) {
        Ok(v) => Some(v),
        Err(e) => {
            println!("   ⚠️  unreadable {}: {e}", path.display());
            None
        }
    }
}

/// `Yak/`-relative path with forward slashes, which is how links are stored.
pub fn rel_to(yak: &Path, path: &Path) -> String {
    path.strip_prefix(yak)
        .unwrap_or(path)
        .to_string_lossy()
        .replace('\\', "/")
}

/// The commands of one verb block, in the order the file declares them.
///
/// File order, not sorted — and the distinction matters. The generators sort,
/// because their output is committed and an unstable order would produce a diff
/// of nothing. The validator does NOT, because its report groups findings by
/// first appearance, so sorting here would silently reorder the whole report.
pub fn verb_entries_in_file_order<'a>(table: &'a Value, verb: &str) -> Vec<(&'a String, &'a Value)> {
    table
        .get(verb)
        .and_then(|b| b.as_object())
        .map(|b| b.iter().collect())
        .unwrap_or_default()
}

/// The commands of one verb block, sorted by name. For generated artifacts.
pub fn verb_entries<'a>(table: &'a Value, verb: &str) -> Vec<(&'a String, &'a Value)> {
    let mut out = verb_entries_in_file_order(table, verb);
    out.sort_by(|a, b| a.0.cmp(b.0));
    out
}

pub fn str_field(v: &Value, key: &str) -> String {
    v.get(key).and_then(|x| x.as_str()).unwrap_or("").to_string()
}

/// The SCPI placeholders in a template, in first-appearance order.
pub fn placeholders(scpi: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    let bytes: Vec<char> = scpi.chars().collect();
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == '<' {
            let mut j = i + 1;
            let mut name = String::new();
            while j < bytes.len() && (bytes[j].is_alphanumeric() || bytes[j] == '_') {
                name.push(bytes[j]);
                j += 1;
            }
            if j < bytes.len() && bytes[j] == '>' && !name.is_empty() {
                if !out.contains(&name) {
                    out.push(name);
                }
                i = j + 1;
                continue;
            }
        }
        i += 1;
    }
    out
}

/// The first token of a statement — everything up to the first space or comma.
///
/// `INST:NSEL <chan>;OUTP ON` is two statements, and the node is EVERY one of
/// them, not the first. Cutting at the first space made every Power command that
/// selects a slot look like the same command.
pub fn statement_head(statement: &str) -> String {
    let s = statement.trim();
    match s.find([' ', ',', '\t', '\n']) {
        Some(i) => s[..i].to_string(),
        None => s.to_string(),
    }
}
