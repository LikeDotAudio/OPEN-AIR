use std::collections::HashMap;
use std::fs;
use std::path::Path;
use serde::Deserialize;
use log::error;

/// One command: the SCPI template plus the verb whose bucket it was declared in.
#[derive(Debug, Clone)]
pub struct Command {
    /// Long form — every keyword spelled out.
    pub scpi: String,
    /// Short form, where it differs. The 6060B programming manual: *"The short
    /// form provides the fastest program execution."* Absent when the long form
    /// is already short, so callers read `scpi_fast.unwrap_or(scpi)`.
    pub scpi_fast: Option<String>,
    /// "set" | "do" | "rig" | "nab" — which handler the table says owns this.
    pub verb: &'static str,
    /// How to read the reply apart, for a query that has one.
    ///
    /// A compound query — `:FREQ:STAR?;:FREQ:STOP?;:FREQ:CENT?;:FREQ:SPAN?` —
    /// comes back as one separator-joined string. `returns.fields` names each
    /// value and declares its unit, which is what lets a reply be published as
    /// individually addressable readings instead of a blob nobody can index
    /// safely. Absent for commands that answer nothing.
    pub returns: Option<Returns>,
}

/// The declared shape of a query's reply.
#[derive(Debug, Clone, Deserialize, Default)]
pub struct Returns {
    #[serde(default)]
    pub count: Option<serde_json::Value>,
    /// Defaults to ";" — the SCPI convention for chained replies.
    #[serde(default)]
    pub separator: Option<String>,
    #[serde(default)]
    pub fields: Vec<ReturnField>,
    /// Unit for a SINGLE-value reply, where there are no named fields.
    #[serde(default)]
    pub unit: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ReturnField {
    pub name: String,
    #[serde(default)]
    pub unit: Option<String>,
}

impl Command {
    /// The template to put on the wire, given whether speed was asked for.
    pub fn template(&self, prefer_fast: bool) -> &str {
        match (prefer_fast, &self.scpi_fast) {
            (true, Some(f)) => f,
            _ => &self.scpi,
        }
    }
}

/// `scpi` and `scpiFast` are read at runtime. `description`, `arg`, `returns`,
/// `group`, `args` and `subsystem` are in the file for the panel author, the
/// generated CommandList sheet and the test harness; serde skips what it is not
/// asked for.
#[derive(Debug, Deserialize)]
struct Entry {
    scpi: String,
    #[serde(default, rename = "scpiFast")]
    scpi_fast: Option<String>,
    #[serde(default)]
    returns: Option<Returns>,
}

/// `Instruments/<Family>/<Model>/commands.json` — the whole vocabulary for one
/// model, sitting beside the panel that drives it.
///
/// The model is DECLARED here rather than inferred from where the file sits.
/// It used to be read off the file's grandparent directory, so anything nested
/// one level deeper than `<Model>/<Subsystem>/` was filed under a folder name
/// ("_Legacy_Commands", "CHANnel") instead of a model — 391 commands reachable
/// only through get_scpi's search-every-model fallback.
#[derive(Debug, Deserialize)]
struct ModelTable {
    model: String,
    #[serde(default)]
    set: HashMap<String, Entry>,
    #[serde(default, rename = "do")]
    do_: HashMap<String, Entry>,
    #[serde(default)]
    rig: HashMap<String, Entry>,
    #[serde(default)]
    nab: HashMap<String, Entry>,
}

pub struct YakRepository {
    // Model Name -> (Command Name -> Command)
    pub models: HashMap<String, HashMap<String, Command>>,
}

impl YakRepository {
    pub fn new(root_path: &str) -> Self {
        let mut repo = YakRepository { models: HashMap::new() };
        eprintln!("   🔍 [YAK REPO] Scanning YAK repository at: {}", root_path);
        repo.scan_directory(Path::new(root_path));

        let total: usize = repo.models.values().map(|c| c.len()).sum();
        eprintln!("   ✅ [YAK REPO] Loaded {} models and {} total command definitions.",
                  repo.models.len(), total);
        repo
    }

    fn scan_directory(&mut self, path: &Path) {
        let entries = match fs::read_dir(path) {
            Ok(e) => e,
            Err(e) => {
                error!("Failed to read directory {:?}: {}", path, e);
                return;
            }
        };
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_dir() {
                self.scan_directory(&p);
            // `<Model>.yak` — the vocabulary, named for the instrument it
            // belongs to so a folder reads as a set: `34401A.gui` beside
            // `34401A.yak`. Matched by EXTENSION rather than by a fixed
            // filename, so the model in the name never has to agree with a
            // constant in here.
            } else if p.extension().map_or(false, |e| e == "yak") {
                self.load_table(&p);
            }
            // `model.json` beside it is the capability sheet — channel counts and
            // voltage/current ranges, read by the orchestrator's instruments.rs
            // to clamp widgets. What the model IS, not what it accepts.
        }
    }

    fn load_table(&mut self, path: &Path) {
        let text = match fs::read_to_string(path) {
            Ok(t) => t,
            Err(e) => {
                eprintln!("   ❌ [YAK REPO] {:?}: {}", path, e);
                return;
            }
        };
        let table: ModelTable = match serde_json::from_str(&text) {
            Ok(t) => t,
            Err(e) => {
                // Loud, because a table that fails to parse is a whole
                // instrument that silently stops responding to its panel.
                eprintln!("   ❌ [YAK REPO] malformed {:?}: {}", path, e);
                return;
            }
        };

        let bucket = self.models.entry(table.model.clone()).or_default();
        for (verb, commands) in [("set", table.set), ("do", table.do_),
                                 ("rig", table.rig), ("nab", table.nab)] {
            for (name, entry) in commands {
                // A name declared twice for one model is a table bug, not a
                // merge to resolve quietly: whichever won used to be decided by
                // directory walk order, and on the Power modules that was the
                // difference between addressing your slot and addressing slot 1.
                if let Some(prev) = bucket.get(&name) {
                    eprintln!("   ⚠️ [YAK REPO] {} declares '{}' twice ({} / {}) — keeping the first",
                              table.model, name, prev.verb, verb);
                    continue;
                }
                bucket.insert(name, Command {
                    scpi: entry.scpi,
                    scpi_fast: entry.scpi_fast,
                    verb,
                    returns: entry.returns,
                });
            }
        }
    }

    #[allow(dead_code)]
    pub fn get_scpi(&self, model_name: &str, command_name: &str) -> Option<String> {
        self.get_scpi_form(model_name, command_name, false)
    }

    /// `prefer_fast` picks the short-form spelling where the table carries one.
    /// Same command, same instrument, fewer bytes on a 1980s GPIB link.
    pub fn get_scpi_form(&self, model_name: &str, command_name: &str,
                         prefer_fast: bool) -> Option<String> {
        self.get(model_name, command_name)
            .map(|c| c.template(prefer_fast).to_string())
    }

    /// Which command produced this SCPI string.
    ///
    /// The VISA daemon reports the query it executed, not the name it was asked
    /// for, so attributing a reply means matching the text back to a template.
    /// Both spellings are checked because `prefer_short_scpi` decides which one
    /// actually went on the wire. Queries have no placeholders, so an exact
    /// match is sound here in a way it would not be for a parameterised set.
    pub fn command_for_scpi(&self, model_name: &str, scpi: &str) -> Option<&str> {
        let needle = scpi.trim();
        let bucket = self.models.get(model_name)?;
        bucket
            .iter()
            .find(|(_, c)| c.scpi.trim() == needle
                || c.scpi_fast.as_deref().map(|f| f.trim() == needle).unwrap_or(false))
            .map(|(name, _)| name.as_str())
    }

    pub fn get(&self, model_name: &str, command_name: &str) -> Option<&Command> {
        if let Some(cmd) = self.models.get(model_name).and_then(|c| c.get(command_name)) {
            return Some(cmd);
        }
        // Fallback: some other model happens to use the name. Kept for
        // hand-authored panels that name no model, but announced — with every
        // command now filed under the model that declares it, reaching this is
        // a sign the panel is bound to the wrong instrument, not a normal path.
        for (model, commands) in &self.models {
            if let Some(cmd) = commands.get(command_name) {
                eprintln!("   ⚠️ [YAK REPO] '{}' not found for model '{}' — falling back to {}'s",
                          command_name, model_name, model);
                return Some(cmd);
            }
        }
        None
    }
}
