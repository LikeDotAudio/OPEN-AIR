//! Per-device instrument panels — one control surface per discovered instrument.
//!
//! The Rust port of `build_instrument_panels.py`. The instrument panels used to
//! be a fixed display: one hand-placed DMM tab bound to no instrument in
//! particular, however many DMMs were actually on the bench. This bench has
//! eight 34401As, two loads and several scopes; it had one of each on screen.
//!
//! So the authored panels live in `Instruments/` — alongside each model's YAK
//! vocabulary, since a control surface and the commands behind it are two halves
//! of one declaration — and this stamps one
//! instance per discovered device into the frontend tree — eight DMMs become
//! eight tabs, each bound to its own VISA resource.
//!
//! An instrument type is TWO authored files and no folders:
//!
//! ```text
//! <Type>/<Type>.json     the instrument      — stamped once per device
//! <Type>/<Type>_N.json   N of the instrument — the block that repeats
//! ```
//!
//! The sub-tab structure a device panel used to get from nested template folders
//! now comes from the instrument file's top-level keys, so the tree the author
//! edits is flat and the tree the UI renders is not. That makes key ORDER
//! load-bearing throughout this module — see the `preserve_order` note in
//! Cargo.toml.
//!
//! Generated output is data: gitignored, and pruned when a device disappears.

use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::path::{Path, PathBuf};

use regex::Regex;
use serde_json::{json, Map, Value};

use crate::discovered::Collected;

/// Marker file identifying a generated device folder.
///
/// Pruning only ever deletes directories carrying this, so a hand-authored panel
/// dropped into the same tree survives — deleting someone's authored work
/// because it sat in a generated directory is not a recoverable mistake.
const STAMP: &str = ".generated-by-openair";

/// One discovered instrument, as the builder needs it.
#[derive(Clone, Debug)]
pub struct Device {
    pub dtype: String,
    pub model: String,
    pub resource: String,
    pub write_topic: String,
}

fn template_root(root: &Path) -> PathBuf {
    root.join("Instruments")
}

fn yak_root(root: &Path) -> PathBuf {
    // Same tree as the panels: an instrument's vocabulary and its control
    // surface are two halves of one declaration and now live together.
    root.join("Instruments")
}

/// Back into the tab the templates were evacuated from, so the Instruments tab
/// keeps its place in the UI — only its contents are now generated rather than
/// authored. `left_100` (not `left_50`) because an instrument gets the FULL tab
/// width: the right-hand half was retired, and a bench panel reads better across
/// the whole window than squeezed into a column. See
/// `WindowManager.parseSplitName` — `/^(left|right|top|bottom)_(\d+)$/`, the
/// number being percent of the parent.
fn out_root(root: &Path) -> PathBuf {
    root.join("FrontEnd")
        .join("Gui_Frames")
        .join("1_Instruments")
        .join("left_100")
}

/// `${name}`, and deliberately not `<name>`: panel templates carry SCPI
/// fragments (`"command_value": "VOLT <value>"`) and YAK's own command tables
/// use `<chan>`, `<n>`, `<slot>`. Two substitution passes run over this data —
/// this one at build time, YAK's at send time — and giving them the same
/// delimiter is how a slot number ends up where a voltage belongs.
fn token_re() -> &'static Regex {
    static RE: std::sync::OnceLock<Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| Regex::new(r"\$\{(\w+)\}").unwrap())
}

fn slot_re() -> &'static Regex {
    static RE: std::sync::OnceLock<Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| Regex::new(r"(?i)gpib\d+,(\d+),(\d+)").unwrap())
}

fn chassis_re() -> &'static Regex {
    static RE: std::sync::OnceLock<Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| Regex::new(r"(?i)(gpib\d+,\d+),\d+").unwrap())
}

// ── Instrument facts ─────────────────────────────────────────────────────────

/// What each model IS, from `Instruments/<Family>/<Model>/model.json`.
///
/// Channel counts and voltage/current ranges are properties of the instrument,
/// so they live with the SCPI vocabulary rather than in the panel. Before this
/// they lived nowhere machine-readable: the ranges were English in
/// `knownDevices.json` ("Module 8V / 16A (128W)") and the scope's channel count
/// was a description field reading "1, 2, 3, 4". Panels therefore shipped with
/// no clamps at all, and the 8V module and the 60V module got the same widget.
///
/// Keyed by model name, not by type — model names are unique across the YAK
/// tree, and a second type→directory table is a second thing to keep in sync.
/// The directory may carry a manufacturer prefix (`HP_8903B`), which is split
/// off so the key is the bare model.
fn load_capabilities(root: &Path) -> HashMap<String, Value> {
    let mut caps = HashMap::new();
    let yak = yak_root(root);
    let Ok(families) = std::fs::read_dir(&yak) else {
        return caps;
    };
    let mut families: Vec<_> = families.flatten().map(|e| e.path()).collect();
    families.sort();
    for family in families {
        let Ok(models) = std::fs::read_dir(&family) else {
            continue;
        };
        let mut models: Vec<_> = models.flatten().map(|e| e.path()).collect();
        models.sort();
        for model_dir in models {
            // `<Model>.gui` — what the instrument IS, named for it. Located by
            // extension: the folder may carry a manufacturer prefix (`HP_8903B`)
            // or an underscore in the model itself (`Porta_one`), so deriving
            // the filename from the directory would be wrong in both directions.
            let Some(path) = std::fs::read_dir(&model_dir).ok().and_then(|rd| {
                let mut hits: Vec<PathBuf> = rd
                    .flatten()
                    .map(|e| e.path())
                    .filter(|p| p.extension().map_or(false, |e| e == "gui"))
                    .collect();
                hits.sort();
                hits.into_iter().next()
            }) else {
                continue;
            };
            let Some(dir_name) = model_dir.file_name().and_then(|n| n.to_str()) else {
                continue;
            };
            // `HP_8903B` -> `8903B`; a bare `34401A` is unchanged.
            let key = dir_name.splitn(2, '_').last().unwrap_or(dir_name).to_string();
            if let Ok(body) = std::fs::read_to_string(&path) {
                if let Ok(value) = serde_json::from_str::<Value>(&body) {
                    caps.entry(key).or_insert(value);
                }
            }
        }
    }
    caps
}

/// An instrument that is wired to the bench but cannot be discovered.
pub struct Declared {
    pub dtype: String,
    pub model: String,
    pub manufacturer: String,
    pub notes: String,
    pub resource: String,
    pub listen_only: bool,
    /// SCPI to send the moment this instrument is declared, already resolved
    /// from the model's own vocabulary.
    pub on_connect: Vec<String>,
}

/// Where a model's two authored files live, by model name.
fn model_dir(root: &Path, model: &str) -> Option<PathBuf> {
    let families = std::fs::read_dir(yak_root(root)).ok()?;
    for family in families.flatten() {
        let Ok(models) = std::fs::read_dir(family.path()) else { continue };
        for dir in models.flatten() {
            let name = dir.file_name();
            let name = name.to_str().unwrap_or_default();
            // `HP_8903B` -> `8903B`, matching load_capabilities' key.
            if name.splitn(2, '_').last().unwrap_or(name) == model {
                return Some(dir.path());
            }
        }
    }
    None
}

/// One command's SCPI out of a model's YAK table, whichever verb holds it.
fn yak_scpi(root: &Path, model: &str, command: &str) -> Option<String> {
    let dir = model_dir(root, model)?;
    let path = dir.join(format!("{model}.yak"));
    let doc: Value = serde_json::from_str(&std::fs::read_to_string(path).ok()?).ok()?;
    for verb in ["do", "set", "rig", "nab"] {
        if let Some(s) = doc.get(verb).and_then(|v| v.get(command))
            .and_then(|c| c.get("scpi")).and_then(|s| s.as_str())
        {
            return Some(s.to_string());
        }
    }
    None
}

/// Instruments declared in their own capability sheet rather than found.
///
/// Discovery asks `*IDN?` and believes the answer. That is the right test for
/// almost everything, and useless for a switch matrix: the HP 3235 takes
/// commands and answers none of them, so a probe concludes it is absent while
/// it sits there routing audio. A scan can only ever find instruments that
/// talk.
///
/// So the sheet says so, next to everything else that is true of the model:
///
/// ```json
/// "declared": {
///   "resource": "TCPIP::44.44.44.222::gpib7,10::INSTR",
///   "listen_only": true
/// }
/// ```
///
/// One place, and the same file that already carries channel counts and
/// domains — an address is a fact about an installation the same way a channel
/// count is a fact about a model, and neither belongs in a panel.
pub fn declared_devices(root: &Path) -> Vec<Declared> {
    let mut out = Vec::new();
    for (model, caps) in load_capabilities(root) {
        let Some(d) = caps.get("declared") else { continue };
        let Some(resource) = d.get("resource").and_then(|r| r.as_str()) else {
            println!("[instrument-gui] {model} declares itself with no resource — skipped");
            continue;
        };
        let Some(dtype) = caps.get("type").and_then(|t| t.as_str()) else {
            println!("[instrument-gui] {model} is declared but names no type — skipped");
            continue;
        };
        // `on_connect` names COMMANDS, not SCPI: an installation fact belongs in
        // the sheet, but the words an instrument understands belong in its
        // vocabulary, and writing them twice is how the two drift apart.
        let on_connect = d
            .get("on_connect")
            .and_then(|v| v.as_array())
            .map(|names| {
                names.iter().filter_map(|n| n.as_str()).filter_map(|name| {
                    match yak_scpi(root, &model, name) {
                        Some(scpi) => Some(scpi),
                        None => {
                            println!("[instrument-gui] {model} names '{name}' on connect, \
                                      and its YAK table has no such command — skipped");
                            None
                        }
                    }
                }).collect()
            })
            .unwrap_or_default();

        out.push(Declared {
            dtype: dtype.to_string(),
            manufacturer: caps.get("manufacturer").and_then(|m| m.as_str())
                .unwrap_or("").to_string(),
            notes: caps.get("notes").and_then(|n| n.as_str()).unwrap_or("").to_string(),
            resource: resource.to_string(),
            listen_only: d.get("listen_only") == Some(&Value::Bool(true)),
            on_connect,
            model,
        });
    }
    // Stable order, so two runs stamp the same Dev index on the same box.
    out.sort_by(|a, b| (&a.dtype, &a.model).cmp(&(&b.dtype, &b.model)));
    out
}

/// Mainframe slot from a VISA resource, or None if the device isn't in one.
///
/// `TCPIP::44.44.44.111::gpib7,30,4::INSTR` — board 7, primary 30, SECONDARY 4.
/// The secondary address is the 66000A slot, and the only thing distinguishing
/// the eight modules that all answer at primary 30.
///
/// Three comma-parts is the test, and it has to be: the scope at `gpib7,6::INSTR`
/// has two, where the `6` is its own primary address. Reading that as a slot
/// would stamp `INST:NSEL 6` onto an instrument that has no slots.
fn slot_of(resource: &str) -> Option<u32> {
    slot_re()
        .captures(resource)
        .and_then(|c| c.get(2))
        .and_then(|m| m.as_str().parse().ok())
}

/// Key identifying the mainframe a device is plugged into.
///
/// The resource with the secondary address removed, so all eight modules at
/// `44.44.44.111::gpib7,30,*` share one key and group together, while a
/// standalone supply is its own chassis of one.
fn chassis_of(resource: &str) -> String {
    chassis_re().replace_all(resource, "$1").into_owned()
}

/// The instrument's host, for grouping things that share a bench but not a box.
///
/// The eight 34401As are eight separate meters at eight GPIB primary addresses
/// behind one gateway — no mainframe to group them by, yet a bank of eight is
/// exactly the view that bench wants. `by: "host"` in the manifest selects this
/// axis; `by: "chassis"` (the default) is for modules that really do plug into
/// the same frame.
fn host_of(resource: &str) -> String {
    resource
        .split("::")
        .nth(1)
        .unwrap_or(resource)
        .to_string()
}

/// Which devices a group view gathers, by the manifest's `by` axis.
///
/// `chassis` and `host` both ask where an instrument is PLUGGED IN, and answer
/// with a group of one for anything standing on its own. Two signal generators
/// at two addresses are exactly that — and "link both generators" is exactly
/// the view they need, so `type` gathers every instrument of the type wherever
/// it sits. The bench is the axis, not the box.
fn group_key(axis: &str, itype: &str, resource: &str) -> String {
    match axis {
        "host" => host_of(resource),
        "type" | "all" => itype.to_string(),
        _ => chassis_of(resource),
    }
}

/// Folder name for one device — this becomes its tab label.
///
/// Model alone is not identity: this bench has eight 34401As reporting serial
/// "0", so `34401A` would name all eight. The VISA resource is what actually
/// distinguishes them (host + GPIB address), so the address tail rides along:
/// `34401A_44-44-44-111_gpib7-4`. Ugly, and correct; a friendly name belongs in
/// a user-editable alias map, not in the identity that panels are keyed on.
fn device_slug(model: &str, resource: &str) -> String {
    let tail = resource.replace("TCPIP::", "").replace("::INSTR", "");
    let tail = Regex::new(r"[^A-Za-z0-9]+")
        .unwrap()
        .replace_all(&tail, "-")
        .trim_matches('-')
        .to_string();
    let slug = if tail.is_empty() {
        model.to_string()
    } else {
        format!("{model}_{tail}")
    };
    Regex::new(r"[^A-Za-z0-9_.-]+")
        .unwrap()
        .replace_all(&slug, "_")
        .into_owned()
}

// ── Template binding ─────────────────────────────────────────────────────────

/// Replace `${...}` through a copied template — in values AND in key names.
///
/// Key names matter as much as values: a panel's identity in the frontend tree
/// is its top-level key, so eight copies of one module template all named
/// `Power_Module_1` would be eight panels claiming to be the same panel. That
/// single differing line is the only thing the eight hand-maintained module
/// files ever encoded.
fn substitute(node: &Value, tokens: &BTreeMap<String, String>) -> Value {
    match node {
        Value::Object(map) => {
            let mut out = Map::new();
            for (k, v) in map {
                out.insert(expand_tokens(k, tokens), substitute(v, tokens));
            }
            Value::Object(out)
        }
        Value::Array(items) => Value::Array(items.iter().map(|v| substitute(v, tokens)).collect()),
        Value::String(s) => Value::String(expand_tokens(s, tokens)),
        other => other.clone(),
    }
}

/// One string's `${...}`, filled from `tokens`. An unknown token is left as
/// written, so a pass that does not know `n` yet hands `${n}` on intact to the
/// pass that does — which is what lets a channel strip survive `prepare` and be
/// repeated afterwards.
fn expand_tokens(s: &str, tokens: &BTreeMap<String, String>) -> String {
    token_re()
        .replace_all(s, |c: &regex::Captures| {
            tokens.get(&c[1]).cloned().unwrap_or_else(|| c[0].to_string())
        })
        .into_owned()
}

/// Resolve `"yak_domain": "volt"` against the model's capability sheet.
///
/// The template names the quantity; the model supplies units and limits. A
/// template cannot hardcode them and stay one template — this bench runs four
/// module models spanning 8V/16A to 60V/2.5A off the same panel.
/// How many `to` there are in one `from`, within a single quantity.
///
/// Conversion is defined only inside a family: Hz→MHz is arithmetic, Hz→dBm is
/// not, and `None` means "leave the number alone" rather than guess.
fn unit_ratio(from: &str, to: &str) -> Option<f64> {
    const FAMILIES: [&[(&str, f64)]; 4] = [
        &[("hz", 1.0), ("khz", 1e3), ("mhz", 1e6), ("ghz", 1e9)],
        &[("uv", 1e-6), ("mv", 1e-3), ("v", 1.0), ("kv", 1e3)],
        &[("ns", 1e-9), ("us", 1e-6), ("ms", 1e-3), ("s", 1.0)],
        &[("ua", 1e-6), ("ma", 1e-3), ("a", 1.0)],
    ];
    let f = from.trim().to_lowercase();
    let t = to.trim().to_lowercase();
    if f == t {
        return Some(1.0);
    }
    for fam in FAMILIES {
        let fv = fam.iter().find(|(u, _)| *u == f).map(|(_, v)| *v);
        let tv = fam.iter().find(|(u, _)| *u == t).map(|(_, v)| *v);
        if let (Some(a), Some(b)) = (fv, tv) {
            return Some(a / b);
        }
    }
    None
}

fn apply_domains(node: &mut Value, caps: &Value) -> usize {
    let mut resolved = 0;
    match node {
        Value::Object(map) => {
            if let Some(Value::String(key)) = map.get("yak_domain").cloned() {
                match caps.get("domains").and_then(|d| d.get(&key)) {
                    Some(Value::Object(spec)) => {
                        let entry = map
                            .entry("domain".to_string())
                            .or_insert_with(|| Value::Object(Map::new()));
                        if let Value::Object(existing) = entry {
                            // The model declares the limit in the INSTRUMENT's
                            // units; the widget displays in its own. Copying the
                            // numbers across verbatim clamped a MHz fader to
                            // 3000000000 — the right limit, three orders of
                            // magnitude wrong. Scale into the widget's units and
                            // leave its `units` alone; only fall back to the
                            // model's unit when the widget declares none.
                            let widget_unit = existing
                                .get("units")
                                .and_then(|u| u.as_str())
                                .map(|u| u.to_string());
                            let spec_unit = spec.get("units").and_then(|u| u.as_str()).map(|u| u.to_string());
                            let factor = match (&spec_unit, &widget_unit) {
                                (Some(f), Some(t)) => unit_ratio(f, t),
                                _ => None,
                            };
                            for (k, v) in spec {
                                if k == "units" && widget_unit.is_some() {
                                    continue;
                                }
                                let scaled = match (factor, v.as_f64()) {
                                    (Some(r), Some(n)) if k == "min" || k == "max" => {
                                        // Round to 12 significant figures: 100000 Hz / 1e6
                                        // is 0.09999999999999999 in binary floating point,
                                        // and a limit renders on screen.
                                        let scaled = n * r;
                                        let scaled = format!("{scaled:.12e}")
                                            .parse::<f64>()
                                            .unwrap_or(scaled);
                                        serde_json::Number::from_f64(scaled)
                                            .map(Value::Number)
                                            .unwrap_or_else(|| v.clone())
                                    }
                                    _ => v.clone(),
                                };
                                existing.insert(k.clone(), scaled);
                            }
                        }
                        resolved += 1;
                    }
                    // Silence here would look identical to a clamped widget.
                    _ => println!(
                        "[instrument-gui] no '{key}' domain for model {} — widget left unclamped",
                        caps.get("model").and_then(|m| m.as_str()).unwrap_or("?")
                    ),
                }
            }
            for (_, v) in map.iter_mut() {
                resolved += apply_domains(v, caps);
            }
        }
        Value::Array(items) => {
            for item in items {
                resolved += apply_domains(item, caps);
            }
        }
        _ => {}
    }
    resolved
}

/// Point display widgets at the device's SCPI reply topic.
///
/// A query is only half a readout: YAK sends `:READ?` to the Write topic, the
/// VISA daemon executes it and publishes the answer (retained) to `/Read`. A
/// widget marked `"yak_readout": true` gets `topic` set to that reply topic, so
/// the meter shows what the instrument said instead of a dash. Without this the
/// panel can command an instrument but never hear it.
///
/// The template cannot hardcode the topic — it is per device — which is why this
/// is a marker the builder resolves rather than a literal.
fn bind_readout(node: &mut Value, read_topic: &str) -> usize {
    let mut bound = 0;
    match node {
        Value::Object(map) => {
            if map.get("yak_readout") == Some(&Value::Bool(true)) {
                map.insert("topic".to_string(), Value::String(read_topic.to_string()));
                bound += 1;
            }
            // A HYDRATING control keeps its own topic — that is where the
            // operator's commands go — and gains a second, read-only source it
            // listens to for where the instrument actually is. Two topics, two
            // directions: `topic` is what this control says, `yak_hydrate_topic`
            // is what it is told. Stamped here for the same reason as the
            // readout: the template cannot know a per-device topic.
            if map.get("yak_hydrate") == Some(&Value::Bool(true)) {
                map.insert("yak_hydrate_topic".to_string(), Value::String(read_topic.to_string()));
                bound += 1;
            }
            // `yak_listen: "<command>/<field>"` names the reading this control
            // takes its value from. Bound by NAME, so it survives a reply gaining
            // a field — unlike an index into the joined string.
            // `yak_listen_all: {"<command>/<field>": "<expected>"}` — a control
            // whose state is DERIVED from several readings at once. High
            // Sensitivity is not a setting the instrument reports; it is the
            // combination preamp-on AND zero attenuation. Binding it to one
            // field would make it disagree with the two controls it shares
            // hardware with.
            if let Some(Value::Object(spec)) = map.get("yak_listen_all").cloned() {
                if let Some(dev_base) = read_topic.strip_suffix("/Read") {
                    let mut stamped = Map::new();
                    for (name, expected) in &spec {
                        stamped.insert(format!("{dev_base}/Reading/{name}"), expected.clone());
                    }
                    map.insert("yak_listen_all_topics".to_string(), Value::Object(stamped));
                    bound += 1;
                }
            }
            if let Some(Value::String(name)) = map.get("yak_listen") {
                if let Some(dev_base) = read_topic.strip_suffix("/Read") {
                    let topic = format!("{dev_base}/Reading/{name}");
                    map.insert("yak_listen_topic".to_string(), Value::String(topic));
                    bound += 1;
                }
            }
            // `yak_awaits: "<command>/<field>"` — the reading a polling loop
            // watches for to know its last request has landed. Same naming as
            // `yak_listen` and bound the same way; the difference is that
            // nothing DISPLAYS it. A loop that fires on a fixed timer either
            // undershoots the instrument or queues work behind it, and a scope
            // capture is 1.4 seconds of GPIB — a rate no author can guess and
            // the bus can simply report.
            if let Some(Value::String(name)) = map.get("yak_awaits") {
                if let Some(dev_base) = read_topic.strip_suffix("/Read") {
                    let topic = format!("{dev_base}/Reading/{name}");
                    map.insert("yak_awaits_topic".to_string(), Value::String(topic));
                    bound += 1;
                }
            }
            for (_, v) in map.iter_mut() {
                bound += bind_readout(v, read_topic);
            }
        }
        Value::Array(items) => {
            for item in items {
                bound += bind_readout(item, read_topic);
            }
        }
        _ => {}
    }
    bound
}

/// Recursively stamp device binding onto every `yak_handler` in a panel.
///
/// `target` is the topic the VISA daemon executes SCPI on; without it YAK
/// publishes every command to its global pub topic, which nothing subscribes to
/// — the reason the panels never actually drove an instrument. `model` narrows
/// YAK's SCPI lookup to this instrument's command table instead of "first
/// command of that name found in any model".
///
/// `params` are the constants this instance addresses itself with — `chan` for a
/// mainframe slot or a scope channel. The command table is per model, and four
/// of the eight modules here are 66104As, so the slot cannot live in the table:
/// it read `INST:NSEL 1` for every one of them. YAK substitutes these before the
/// widget value (`openair-yak/src/verbs/mod.rs`, `apply_params`).
fn bind_node(
    node: &mut Value,
    write_topic: &str,
    model: &str,
    params: &BTreeMap<String, String>,
) -> usize {
    let mut stamped = 0;
    match node {
        Value::Object(map) => {
            if let Some(Value::Object(handler)) = map.get_mut("yak_handler") {
                handler.insert("target".to_string(), Value::String(write_topic.to_string()));
                handler.insert("model".to_string(), Value::String(model.to_string()));
                if !params.is_empty() {
                    let mut p = Map::new();
                    for (k, v) in params {
                        p.insert(k.clone(), Value::String(v.clone()));
                    }
                    handler.insert("params".to_string(), Value::Object(p));
                }
                stamped += 1;
            }
            for (_, v) in map.iter_mut() {
                stamped += bind_node(v, write_topic, model, params);
            }
        }
        Value::Array(items) => {
            for item in items {
                stamped += bind_node(item, write_topic, model, params);
            }
        }
        _ => {}
    }
    stamped
}

/// Bind one panel document to one device: tokens, limits, topics, slot.
///
/// Every panel goes through here, whether it was stamped on its own or nested
/// into a group, so a module strip in the bank-of-8 is bound exactly as tightly
/// as the same strip on its own tab.
fn prepare(
    doc: &Value,
    dev: &Device,
    tokens: Option<&BTreeMap<String, String>>,
    caps_by_model: &HashMap<String, Value>,
) -> (Value, usize) {
    let slot = slot_of(&dev.resource);
    let empty = Value::Object(Map::new());
    let caps = caps_by_model.get(&dev.model).unwrap_or(&empty);

    let mut marks = tokens.cloned().unwrap_or_default();
    marks.entry("model".into()).or_insert_with(|| dev.model.clone());
    marks.entry("resource".into()).or_insert_with(|| dev.resource.clone());
    marks.entry("family".into()).or_insert_with(|| dev.dtype.clone());
    // The device's identity as a topic segment — the same string its folder is
    // named for. A panel needs it to address something ABOUT this instrument
    // that is not on this instrument: the LINK page and a module's own page are
    // two files, and "this module is excluded from the link" is one fact they
    // both have to see.
    marks
        .entry("slug".into())
        .or_insert_with(|| device_slug(&dev.model, &dev.resource));
    marks
        .entry("slot".into())
        .or_insert_with(|| slot.map(|s| s.to_string()).unwrap_or_else(|| "-".into()));

    let mut doc = substitute(doc, &marks);
    apply_domains(&mut doc, caps);

    // SCPI channel numbering is 1-based; the GPIB secondary address is 0-based.
    //
    // Both spellings of the index go out, because both are in use across the
    // vocabularies this binds: a mainframe addresses a slot as
    // `INST:NSEL <chan>`, the Rigol a channel as `:CHANnel<n>:SCALe`. They name
    // the same fact, and a strip that stands for one channel means the same
    // thing by either.
    let mut params = BTreeMap::new();
    if let Some(chan) = marks.get("chan") {
        params.insert("chan".to_string(), chan.clone());
        params.insert("n".to_string(), chan.clone());
    } else if let Some(s) = slot {
        params.insert("chan".to_string(), (s + 1).to_string());
        params.insert("n".to_string(), (s + 1).to_string());
    }

    let handlers = bind_node(&mut doc, &dev.write_topic, &dev.model, &params);

    // `/Read` is where the VISA daemon publishes what the instrument answered;
    // the Write topic is where commands go.
    if let Some(base) = dev.write_topic.strip_suffix("/Write") {
        bind_readout(&mut doc, &format!("{base}/Read"));
    }
    (doc, handlers)
}

/// How many analog channels this model declares, or None if it says nothing.
fn channel_count(caps: &HashMap<String, Value>, model: &str) -> Option<u64> {
    caps.get(model)
        .and_then(|c| c.get("channels"))
        .and_then(|c| c.as_u64())
        .filter(|n| *n > 0)
}

/// What one channel is called, and what colour it wears.
///
/// The colours are the scope's own: channel 1 yellow, 2 green, 3 blue, 4 purple,
/// which is how every four-channel instrument on this bench paints its screen.
/// They live here rather than in the panel because a panel authored once cannot
/// carry a different colour per copy — and a trace, the strip that drives it and
/// the row that measures it must all be the same colour or the tab stops reading
/// as one channel.
fn channel_tokens(i: u64) -> BTreeMap<String, String> {
    const COLORS: [&str; 4] = ["#FFD400", "#3DDC4A", "#3D9BFF", "#B06CFF"];
    let mut t = BTreeMap::new();
    t.insert("n".to_string(), i.to_string());
    t.insert("chan".to_string(), i.to_string());
    t.insert("label".to_string(), format!("CH{i}"));
    t.insert(
        "color".to_string(),
        COLORS[((i as usize).saturating_sub(1)) % COLORS.len()].to_string(),
    );
    t
}

/// Repeat every `${n}` thing in a tab, once per channel the model has.
///
/// `<Type>_N.json` repeats a block into a GROUP panel — the bank of eight, the
/// quads. A scope wants the same repetition INSIDE its own tabs: the amplitude
/// tab is one channel strip authored once and stamped four times for the
/// 4-channel Rigol, twice for a 54641D. Same convention, same tokens.
///
/// `${n}` marks the thing that repeats in the two places a panel can hold a
/// list — a BLOCK NAME, and an ARRAY ENTRY. The name is what makes N copies of a
/// strip N distinct widgets rather than one claiming to exist N times; the array
/// is how the DATASET graph names one series per channel, and it has no names to
/// carry the mark. Everything else is left alone.
///
/// Runs AFTER `prepare`, which leaves `${n}` alone because it holds no such
/// token. The copies therefore inherit the device's topics and model binding
/// already, and this adds only what differs between them: the channel each one
/// addresses.
///
/// A model that declares no channel count loses the marked block rather than
/// showing `${n}` on screen — an unexpanded token in a label is a widget that
/// lies about which channel it drives.
fn repeat_channels(doc: &mut Value, model: &str, channels: Option<u64>) {
    let Some(panel) = doc.as_object_mut().and_then(|o| o.values_mut().next()) else { return };
    if !marked(panel) {
        return;
    }
    let Some(n) = channels else {
        println!(
            "[instrument-gui] {model} declares no channel count in its .gui — \
             its per-channel controls are dropped"
        );
        // Fall through with zero copies rather than leaving `${n}` on screen.
        strip_marked(panel);
        return;
    };

    // Count-aware wording, so ONE authored label reads right on every scope:
    // GET BOTH TRACES on a two-channel 54641D, GET ALL 4 TRACES on the Rigol.
    let mut counts = BTreeMap::new();
    counts.insert("channels".to_string(), n.to_string());
    counts.insert(
        "all_traces".to_string(),
        if n == 2 { "BOTH TRACES".to_string() } else { format!("ALL {n} TRACES") },
    );
    *panel = substitute(panel, &counts);
    ask_every_channel(panel, n);

    if let Some(blocks) = panel.get_mut("blocks").and_then(|b| b.as_object_mut()) {
        let mut out = Map::new();
        for (name, block) in blocks.iter() {
            if !name.contains("${n}") {
                out.insert(name.clone(), block.clone());
                continue;
            }
            for (tokens, copy) in copies(block, n) {
                out.insert(expand_tokens(name, &tokens), copy);
            }
        }
        *blocks = out;
    }
    repeat_arrays(panel, n);
}

/// Turn `"per_channel": "waveform_${n}"` into one command and the rest as its
/// follow-ups — the GET ALL press.
///
/// It cannot be a single query. A scope selects its waveform source with a
/// WRITE, and on the DS1104Z a write standing between two chained queries takes
/// the second reply with it: `:WAV:SOUR CHAN1;:WAV:DATA?;:WAV:SOUR CHAN2;
/// :WAV:DATA?` answers with channel 1 alone. Four separate messages all answer —
/// 1.4 s for the set — so this fills `command` with the first channel and
/// `readback` with the others, which `dispatch_readback` already sends one at a
/// time (verbs/mod.rs).
///
/// Stamped rather than authored because the list is as long as the instrument
/// has channels, and the panel is written once for every scope on the bench.
fn ask_every_channel(node: &mut Value, channels: u64) {
    match node {
        Value::Object(map) => {
            if let Some(Value::Object(handler)) = map.get_mut("yak_handler") {
                if let Some(Value::String(template)) = handler.get("per_channel").cloned() {
                    let names: Vec<String> = (1..=channels)
                        .map(|i| expand_tokens(&template, &channel_tokens(i)))
                        .collect();
                    handler.insert("command".to_string(), Value::String(names[0].clone()));
                    handler.insert(
                        "readback".to_string(),
                        Value::String(names[1..].join(",")),
                    );
                    handler.remove("per_channel");
                }
            }
            for (_, v) in map.iter_mut() {
                ask_every_channel(v, channels);
            }
        }
        Value::Array(items) => {
            for item in items {
                ask_every_channel(item, channels);
            }
        }
        _ => {}
    }
}

/// One prepared copy per channel: tokens filled, handlers told their index.
fn copies(node: &Value, channels: u64) -> Vec<(BTreeMap<String, String>, Value)> {
    (1..=channels)
        .map(|i| {
            let tokens = channel_tokens(i);
            let mut copy = substitute(node, &tokens);
            stamp_channel(&mut copy, &i.to_string());
            (tokens, copy)
        })
        .collect()
}

/// Does `${n}` appear anywhere below here — in a key or in a string?
fn marked(node: &Value) -> bool {
    match node {
        Value::Object(map) => map
            .iter()
            .any(|(k, v)| k.contains("${n}") || marked(v)),
        Value::Array(items) => items.iter().any(marked),
        Value::String(s) => s.contains("${n}"),
        _ => false,
    }
}

/// Expand every marked ARRAY ENTRY into one entry per channel.
///
/// Marked BLOCKS are already gone by the time this runs and their copies carry
/// no `${n}`, so this only ever reaches lists that were authored per-channel —
/// the graph's `traces`, and the `sources` its axis picks the freshest of.
fn repeat_arrays(node: &mut Value, channels: u64) {
    match node {
        Value::Array(items) => {
            let mut out = Vec::with_capacity(items.len());
            for item in items.iter() {
                if marked(item) {
                    out.extend(copies(item, channels).into_iter().map(|(_, v)| v));
                } else {
                    out.push(item.clone());
                }
            }
            for item in out.iter_mut() {
                repeat_arrays(item, channels);
            }
            *items = out;
        }
        Value::Object(map) => {
            for (_, v) in map.iter_mut() {
                repeat_arrays(v, channels);
            }
        }
        _ => {}
    }
}

/// Drop every marked block and array entry, for a model with no channel count.
fn strip_marked(panel: &mut Value) {
    if let Some(blocks) = panel.get_mut("blocks").and_then(|b| b.as_object_mut()) {
        blocks.retain(|name, block| !name.contains("${n}") && !marked(block));
    }
    fn prune(node: &mut Value) {
        match node {
            Value::Array(items) => {
                items.retain(|i| !marked(i));
                for item in items.iter_mut() {
                    prune(item);
                }
            }
            Value::Object(map) => {
                for (_, v) in map.iter_mut() {
                    prune(v);
                }
            }
            _ => {}
        }
    }
    prune(panel);
}

/// Tell every handler in one repeated strip which channel it speaks for.
///
/// `prepare` already stamped `target`, `model` and the topics; only the index is
/// per-copy. Inserted into the existing `params` rather than replacing it, so a
/// slot stamped upstream is not lost.
fn stamp_channel(node: &mut Value, chan: &str) {
    match node {
        Value::Object(map) => {
            if let Some(Value::Object(handler)) = map.get_mut("yak_handler") {
                let params = handler
                    .entry("params".to_string())
                    .or_insert_with(|| Value::Object(Map::new()));
                if let Value::Object(p) = params {
                    p.insert("chan".to_string(), Value::String(chan.to_string()));
                    p.insert("n".to_string(), Value::String(chan.to_string()));
                }
            }
            for (_, v) in map.iter_mut() {
                stamp_channel(v, chan);
            }
        }
        Value::Array(items) => {
            for item in items {
                stamp_channel(item, chan);
            }
        }
        _ => {}
    }
}

// ── Files ────────────────────────────────────────────────────────────────────

/// Path of one of an instrument's two authored files.
fn template(root: &Path, itype: &str, suffix: &str) -> PathBuf {
    template_root(root)
        .join(itype)
        .join(format!("{itype}{suffix}.json"))
}

/// Load one authored panel, or None if it isn't one.
fn read_panel(path: &Path) -> Option<Value> {
    let body = std::fs::read_to_string(path).ok()?;
    match serde_json::from_str(&body) {
        Ok(v) => Some(v),
        Err(e) => {
            println!("[instrument-gui] skipping malformed {}: {e}", path.display());
            None
        }
    }
}

fn write_panel(path: &Path, doc: &Value) {
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    match serde_json::to_string_pretty(doc) {
        Ok(body) => {
            if let Err(e) = std::fs::write(path, body) {
                println!("[instrument-gui] could not write {}: {e}", path.display());
            }
        }
        Err(e) => println!("[instrument-gui] could not serialize {}: {e}", path.display()),
    }
}

/// `(repeating block, {deck name: deck block})` from `<Type>_N.json`.
///
/// The N file is an ordinary panel — one OcaBin — so it opens in the WYSIWYG
/// editor like anything else. Grouping unwraps it: the repeating block becomes
/// one field of a generated station block, which is the shape the hand-authored
/// `psu_four`/`psu_eight` had, only reached by composition instead of copy-paste.
///
/// The repeating block is the one carrying `${n}` in its NAME, because that is
/// already what makes N copies of it N distinct panels rather than one panel
/// claiming to exist N times. Every OTHER block is a header deck — a strip that
/// commands the whole group (`OUTP:ALL`) rather than one member — which a group
/// spec asks for by name. Power keeps both of its decks that way: the bank of
/// eight gets the logger, the quads get the master interlock, and neither needs
/// a folder of its own to live in.
fn unit_blocks(root: &Path, itype: &str) -> (Option<Value>, Map<String, Value>) {
    let Some(doc) = read_panel(&template(root, itype, "_N")) else {
        return (None, Map::new());
    };
    let Some(outer) = doc.as_object().and_then(|o| o.values().next()) else {
        return (None, Map::new());
    };
    let blocks = match outer.get("blocks").and_then(|b| b.as_object()) {
        Some(b) => b.clone(),
        None => Map::new(),
    };
    let unit = blocks
        .iter()
        .find(|(name, _)| name.contains("${n}"))
        .map(|(_, b)| b.clone());
    let decks: Map<String, Value> = blocks
        .into_iter()
        .filter(|(name, _)| !name.contains("${n}"))
        .collect();
    (unit, decks)
}

/// Stamp `<Type>.json` for one device, exploding its top-level keys to tabs.
///
/// A device panel's sub-tabs used to be authored as nested template folders —
/// `Spectrum/Instrument/{amplitude,bandwidth,frequency,markers,traces}/`, one
/// file each, five folders deep to hold five panels. The folders were the only
/// thing the author got out of that depth, and the frontend builds tabs from
/// folders anyway (`WindowManager.TabContainer`), so the keys can carry it:
///
/// ```text
/// {"amplitude": {...}, "bandwidth": {...}}  ->  0_amplitude/, 1_bandwidth/
/// ```
///
/// Key order is tab order, which is why the `<i>_` prefix goes on: TabContainer
/// sorts on it, and OaTopicMaker strips it back off, so the topic a widget
/// publishes on is unchanged by the numbering.
///
/// A key may instead hold a MAP of panels — the Router's `Coax` tab is two cards
/// stacked in one pane — which is the same either-a-node-or-a-map test
/// LoaderOrchestrator already makes on a file's own root. One key and one panel
/// means no sub-tab at all: the file lands straight in the device folder, as the
/// single-panel types (DMM, Load, LCR, …) have always rendered.
fn instantiate(
    root: &Path,
    itype: &str,
    out_dir: &Path,
    dev: &Device,
    caps: &HashMap<String, Value>,
) -> (usize, usize) {
    let path = template(root, itype, "");
    let Some(doc) = read_panel(&path) else {
        println!("[instrument-gui] template missing: {}", path.display());
        return (0, 0);
    };
    let Some(entries) = doc.as_object() else {
        return (0, 0);
    };

    let channels = channel_count(caps, &dev.model);

    if entries.len() == 1 {
        let (mut bound, handlers) = prepare(&doc, dev, None, caps);
        repeat_channels(&mut bound, &dev.model, channels);
        write_panel(&out_dir.join(format!("{itype}.json")), &bound);
        return (1, handlers);
    }

    let (mut panels, mut handlers) = (0, 0);
    for (i, (tab, node)) in entries.iter().enumerate() {
        // Either the value IS a panel, or it is a map of them.
        let stack: Map<String, Value> = if node.get("type").map(|t| t.is_string()) == Some(true) {
            let mut m = Map::new();
            m.insert(tab.clone(), node.clone());
            m
        } else {
            node.as_object().cloned().unwrap_or_default()
        };
        for (j, (name, panel)) in stack.iter().enumerate() {
            let mut one = Map::new();
            one.insert(name.clone(), panel.clone());
            let (mut bound, n) = prepare(&Value::Object(one), dev, None, caps);
            repeat_channels(&mut bound, &dev.model, channels);
            write_panel(
                &out_dir.join(format!("{i}_{tab}")).join(format!("{j}_{name}.json")),
                &bound,
            );
            handlers += n;
            panels += 1;
        }
    }
    (panels, handlers)
}

/// Where one device says "the link page must not drive me".
///
/// Outside the GUI panel tree on purpose: it belongs to the INSTRUMENT, not to
/// either page that shows it, and both pages are regenerated whenever the bench
/// changes. Nothing subscribes but LinkGang and the toggle itself — this is a
/// UI act that touches no instrument, which is the point of being able to drop
/// a module out of a link without first putting it back where it was.
fn link_veto_topic(itype: &str, dev: &Device) -> String {
    format!(
        "OpenAir/Gui/Link/{itype}/{}/exclude",
        device_slug(&dev.model, &dev.resource)
    )
}

/// Hand the link widget its members' veto topics.
///
/// `"link_veto": true` on a `_GuiLinkGang` node is a marker the builder
/// resolves, the same shape as `yak_readout` and `yak_listen`. It has to be
/// stamped rather than authored because the panel is written once and the
/// membership is whatever was discovered.
fn stamp_link_veto(node: &mut Value, veto: &Map<String, Value>) {
    match node {
        Value::Object(map) => {
            if map.get("link_veto") == Some(&Value::Bool(true)) {
                map.insert("link_veto_topics".to_string(), Value::Object(veto.clone()));
            }
            for (_, v) in map.iter_mut() {
                stamp_link_veto(v, veto);
            }
        }
        Value::Array(items) => {
            for item in items {
                stamp_link_veto(item, veto);
            }
        }
        _ => {}
    }
}

/// What to call each bar in a bank graph.
///
/// A bank graph finds its rows on the bus, so all it can name them after is the
/// reading topic — `66104A/Dev3`, which says the model and a per-model counter
/// and nothing about WHICH MODULE. In a mainframe holding a 66101A, two 66102As
/// and four 66104As that is not an identity anyone at the rack can use.
///
/// The builder knows: the VISA secondary address IS the slot, and the channel
/// the module answers to is slot + 1 — the same number `prepare` stamps into
/// `INST:NSEL`. Keyed the way BankBars keys a row it has parsed off a topic.
///
/// Absent slots stay absent: a chassis with nothing in slot 3 numbers its
/// modules 1,2,3,5,6,7,8, because renumbering them 1-7 would put a name on a
/// bar that no longer matches the label on the hardware.
fn bank_names(members: &[(BTreeMap<String, String>, Device)]) -> Map<String, Value> {
    let mut out = Map::new();
    for (_tokens, dev) in members {
        let Some(base) = dev.write_topic.strip_suffix("/Write") else { continue };
        let mut segs = base.rsplit('/');
        let (Some(devid), Some(model)) = (segs.next(), segs.next()) else { continue };
        // A MODULE has a slot; a standalone instrument has an address. Naming
        // either one after its position in the discovery list would be a number
        // that looks like the rack's and is not: eight 34401As at GPIB 4, 11,
        // 12, 13 and 1, 2, 3, 5 would come out CH1..CH8 in whatever order the
        // scan happened to sort them, and CH4 would be the meter at gpib7,11.
        let label = match slot_of(&dev.resource) {
            Some(slot) => format!("CH{} · {}", slot + 1, dev.model),
            None => {
                let host = host_of(&dev.resource);
                let tail = host.rsplit('.').next().unwrap_or(&host).to_string();
                // The GPIB designator if there is one, else just the host.
                let addr = dev
                    .resource
                    .split("::")
                    .find(|s| s.to_lowercase().starts_with("gpib"))
                    .map(|s| s.to_string());
                match addr {
                    Some(a) => format!("{tail} · {a}"),
                    None => format!("{tail} · {}", dev.model),
                }
            }
        };
        out.insert(format!("{model}/{devid}"), Value::String(label));
    }
    out
}

/// `"bank_names": true` — same marker discipline as `link_veto` and
/// `yak_readout`: authored once, resolved against whatever was discovered.
fn stamp_bank_names(node: &mut Value, names: &Map<String, Value>) {
    match node {
        Value::Object(map) => {
            if map.get("bank_names") == Some(&Value::Bool(true)) {
                map.insert("names".to_string(), Value::Object(names.clone()));
            }
            for (_, v) in map.iter_mut() {
                stamp_bank_names(v, names);
            }
        }
        Value::Array(items) => {
            for item in items {
                stamp_bank_names(item, names);
            }
        }
        _ => {}
    }
}

/// Compose N bound copies of one unit template into a single group panel.
///
/// This is the whole point of the exercise. `psu_eight.json` was 1183 lines of
/// one module strip written out eight times; `psu_four.json` was the same strip
/// four times with a different header. Neither could be right about limits,
/// because a hand-authored file has one set of widgets and this chassis holds
/// four different module models — the 8V strip and the 60V strip were the same
/// strip. Composed here, each copy is bound to its own device, its own slot and
/// its own model's ranges.
///
/// `members` is `[(tokens, device)]` — the caller decides what repeats: sibling
/// modules across a mainframe, or channels within one instrument.
fn repeat_unit(
    root: &Path,
    itype: &str,
    spec: &Value,
    members: &[(BTreeMap<String, String>, Device)],
    station_id: &str,
    root_key: &str,
    caps: &HashMap<String, Value>,
) -> (Option<Value>, usize) {
    let (unit, decks) = unit_blocks(root, itype);
    let Some(unit) = unit else {
        println!(
            "[instrument-gui] {} has no ${{n}} block to repeat",
            template(root, itype, "_N").display()
        );
        return (None, 0);
    };

    let mut fields = Map::new();
    let mut handlers = 0;

    // Which unit stands for which device, as a topic the DEVICE owns.
    //
    // A link page and a module's own page are two files, so a control on one
    // cannot be named by the other — and "this module is excluded from the
    // link" has to be one fact, not two that can disagree. Keyed by the device
    // slug, it is a topic both pages can spell from what they already know: the
    // module page substitutes `${slug}` into its own toggle, and the link page
    // is told the whole table here.
    let veto: Map<String, Value> = members
        .iter()
        .map(|(tokens, dev)| {
            let idx = tokens.get("n").cloned().unwrap_or_default();
            (
                format!("Unit_{idx}"),
                Value::String(link_veto_topic(itype, dev)),
            )
        })
        .collect();

    if let Some(wanted_deck) = spec.get("header").and_then(|h| h.as_str()) {
        match decks.get(wanted_deck) {
            None => println!(
                "[instrument-gui] {itype}_N.json has no '{wanted_deck}' deck — {} built without its header",
                spec.get("name").and_then(|n| n.as_str()).unwrap_or("?")
            ),
            Some(block) => {
                // The header commands the whole group (`OUTP:ALL`), so it binds
                // to the first member — any of them reaches the mainframe.
                let (tokens, dev) = &members[0];
                let (mut bound, n) = prepare(block, dev, Some(tokens), caps);
                stamp_link_veto(&mut bound, &veto);
                // A bank graph is about every member, not the one the deck
                // happens to be bound to.
                stamp_bank_names(&mut bound, &bank_names(members));
                handlers += n;
                fields.insert(wanted_deck.to_string(), bound);
            }
        }
    }

    for (tokens, dev) in members {
        let (copy, n) = prepare(&unit, dev, Some(tokens), caps);
        handlers += n;
        let idx = tokens.get("n").cloned().unwrap_or_default();
        fields.insert(format!("Unit_{idx}"), copy);
    }

    let name = spec.get("name").and_then(|n| n.as_str()).unwrap_or("");
    let description = spec
        .get("description")
        .cloned()
        .unwrap_or_else(|| json!({ "En": name }));
    let columns = spec
        .get("columns")
        .cloned()
        .unwrap_or_else(|| json!(std::cmp::min(4, members.len())));

    let station = json!({
        "type": "OcaBlock",
        "description": description,
        "layout_columns": columns,
        "fields": Value::Object(fields),
    });
    let station_key = spec
        .get("station")
        .and_then(|s| s.as_str())
        .unwrap_or("Station");

    let doc = json!({
        root_key: {
            "type": "OcaBin",
            "id": station_id,
            "geometry": { "anchor": "NSEW" },
            "behavior": { "overflow_ns": "auto", "overflow_ew": "auto", "fluid_ew": true },
            "blocks": { station_key: station },
        }
    });
    (Some(doc), handlers)
}

/// Split into groups of `size`; `"all"` means one group of everything.
fn chunk<T: Clone>(items: &[T], size: &Value) -> Vec<Vec<T>> {
    if size.as_str() == Some("all") {
        return if items.is_empty() {
            vec![]
        } else {
            vec![items.to_vec()]
        };
    }
    let n = size.as_u64().unwrap_or(0) as usize;
    if n == 0 {
        return vec![];
    }
    items.chunks(n).map(|c| c.to_vec()).collect()
}

/// Emit the group views declared for one instrument type.
///
/// `over: "devices"` repeats across the instruments sharing a mainframe — the
/// bank of 8, the quads, the pairs. `over: "channels"` repeats within a single
/// instrument, once per channel its model declares, which is the same shape: two
/// 54641Ds and a 4-channel Rigol are three devices whose panels differ only in
/// how many identical channel strips they carry.
fn build_group_panels(
    root: &Path,
    itype: &str,
    spec: &Value,
    tab: &str,
    devices: &[Device],
    caps: &HashMap<String, Value>,
) -> (usize, usize, BTreeSet<String>) {
    let (mut written, mut built) = (0, 0);
    let mut wanted = BTreeSet::new();

    let groups = spec.get("groups").and_then(|g| g.as_array()).cloned().unwrap_or_default();
    for group in &groups {
        let gname = group.get("name").and_then(|n| n.as_str()).unwrap_or("");
        let mut instances: Vec<(String, Vec<(BTreeMap<String, String>, Device)>)> = Vec::new();

        if group.get("over").and_then(|o| o.as_str()) == Some("channels") {
            for dev in devices {
                let channels = caps
                    .get(&dev.model)
                    .and_then(|c| c.get("channels"))
                    .and_then(|c| c.as_u64());
                let Some(n) = channels.filter(|n| *n > 0) else {
                    println!(
                        "[instrument-gui] {} declares no channel count in its YAK model.json — {gname} skipped",
                        dev.model
                    );
                    continue;
                };
                let members = (1..=n).map(|i| (channel_tokens(i), dev.clone())).collect();
                instances.push((device_slug(&dev.model, &dev.resource), members));
            }
        } else {
            let axis = group.get("by").and_then(|b| b.as_str()).unwrap_or("chassis");
            let mut chassis: BTreeMap<String, Vec<Device>> = BTreeMap::new();
            for dev in devices {
                chassis
                    .entry(group_key(axis, itype, &dev.resource))
                    .or_default()
                    .push(dev.clone());
            }
            for (key, mut members) in chassis {
                // Slot order where there are slots, address order otherwise, so
                // a bank reads left-to-right the way the rack is wired rather
                // than in whatever order discovery happened to answer.
                members.sort_by(|a, b| {
                    (slot_of(&a.resource).unwrap_or(0), &a.resource)
                        .cmp(&(slot_of(&b.resource).unwrap_or(0), &b.resource))
                });
                if members.len() < 2 {
                    continue; // a "bank" of one is just the device's own panel
                }
                let size = group.get("size").cloned().unwrap_or_else(|| json!("all"));
                for (idx, part) in chunk(&members, &size).into_iter().enumerate() {
                    let tagged = part
                        .into_iter()
                        .enumerate()
                        .map(|(i, d)| {
                            let mut t = BTreeMap::new();
                            t.insert("n".to_string(), (i + 1).to_string());
                            t.insert("label".to_string(), d.model.clone());
                            (t, d)
                        })
                        .collect();
                    let slug = device_slug(gname, &key);
                    let name = if size.as_str() == Some("all") {
                        slug
                    } else {
                        format!("{slug}_{}", idx + 1)
                    };
                    instances.push((name, tagged));
                }
            }
        }

        for (slug, members) in instances {
            // Root key carries the slug: four pair-panels off one mainframe are
            // four panels, not one panel claiming to exist four times.
            let root_key = Regex::new(r"[^A-Za-z0-9]+")
                .unwrap()
                .replace_all(&slug, "_")
                .into_owned();
            let station_id = group
                .get("id")
                .and_then(|i| i.as_str())
                .unwrap_or("50.100.0.0");
            let (doc, handlers) =
                repeat_unit(root, itype, group, &members, station_id, &root_key, caps);
            let Some(doc) = doc else { continue };

            let out_dir = out_root(root).join(tab).join(gname).join(&slug);
            if out_dir.is_dir() {
                let _ = std::fs::remove_dir_all(&out_dir);
            }
            write_panel(&out_dir.join("group.json"), &doc);
            write_stamp(
                &out_dir,
                &json!({ "group": gname, "members": members.len() }),
            );
            wanted.insert(format!("{tab}/{gname}/{slug}"));
            written += 1;
            built += 1;
            println!(
                "[instrument-gui] {tab}/{gname}/{slug} — {} unit(s), {handlers} bound command(s)",
                members.len()
            );
        }
    }
    (written, built, wanted)
}

fn write_stamp(dir: &Path, body: &Value) {
    let _ = std::fs::create_dir_all(dir);
    if let Ok(text) = serde_json::to_string_pretty(body) {
        let _ = std::fs::write(dir.join(STAMP), text);
    }
}

/// Delete generated folders that no longer match a live device or group.
///
/// `wanted` holds paths relative to the output root. Matching on the stamp file
/// rather than on a fixed depth, because a device panel sits at `<tab>/<slug>`
/// and a group panel one level deeper at `<tab>/<group>/<slug>`. Only stamped
/// directories are removed — see `STAMP`.
fn prune(root: &Path, wanted: &BTreeSet<String>) {
    let out = out_root(root);
    if !out.is_dir() {
        return;
    }

    let mut stale = Vec::new();
    for entry in walkdir::WalkDir::new(&out).into_iter().flatten() {
        if !entry.file_type().is_dir() || !entry.path().join(STAMP).is_file() {
            continue;
        }
        let Ok(rel) = entry.path().strip_prefix(&out) else {
            continue;
        };
        let rel = rel.to_string_lossy().replace('\\', "/");
        if !wanted.contains(&rel) {
            stale.push((rel, entry.path().to_path_buf()));
        }
    }
    for (rel, path) in stale {
        let _ = std::fs::remove_dir_all(&path);
        println!("[instrument-gui] pruned {rel}");
    }

    // Empty tab/group folders go with them, so a type that vanished from the
    // bench does not leave a dead tab behind. Deepest-first, so a group folder
    // emptied by its own pruning is collected in the same pass.
    let mut dirs: Vec<PathBuf> = walkdir::WalkDir::new(&out)
        .into_iter()
        .flatten()
        .filter(|e| e.file_type().is_dir())
        .map(|e| e.path().to_path_buf())
        .collect();
    dirs.sort_by_key(|p| std::cmp::Reverse(p.components().count()));
    for dir in dirs {
        if dir == out {
            continue;
        }
        if std::fs::read_dir(&dir).map(|mut e| e.next().is_none()).unwrap_or(false) {
            let _ = std::fs::remove_dir(&dir);
        }
    }
}

/// One panel set per device. Returns `(panels_written, devices_built)`.
/// The bench roster: what is INSTALLED, as opposed to what answered today.
const ROSTER: &str = "BackEnd/Core/Database/bench.json";

fn roster_path(root: &Path) -> PathBuf {
    root.join(ROSTER)
}

/// Everything the bench has, whether or not this scan found it.
///
/// A SCAN THAT MISSES A DEVICE IS A FACT ABOUT THE SCAN.
///
/// The builder used to take the scan as the whole truth, and `prune` deleted
/// every folder not in it — so one pass where a GPIB gateway did not enumerate
/// took out eight multimeters, seven supply modules and two loads, panels and
/// all. Instruments are switched off, gateways answer slowly, and a bench does
/// not stop owning a meter because it was asleep at 3pm.
///
/// The roster also PINS the device index. `Dev<n>` is otherwise a per-model
/// counter over discovery order, so a scan that misses the meter at gpib7,4
/// renumbers every meter behind it: panels keep their topics and start reading
/// a different instrument. An index that moves is worse than one that is
/// occasionally absent.
///
/// A device found but not listed is APPENDED rather than argued with — the
/// record should learn from the bench, not need hand-editing every time
/// something new is plugged in. Existing rows are never rewritten, so aliases
/// and hand-set flags survive.
fn merge_roster(root: &Path, found: &[Device]) -> Vec<Device> {
    let path = roster_path(root);
    let mut doc = read_panel(&path).unwrap_or_else(|| json!({
        "schemaVersion": 1,
        "devices": [],
    }));

    let rows: Vec<Value> = doc
        .get("devices")
        .and_then(|d| d.as_array())
        .cloned()
        .unwrap_or_default();

    let by_resource: HashMap<String, Device> = found
        .iter()
        .map(|d| (d.resource.clone(), d.clone()))
        .collect();

    let mut out: Vec<Device> = Vec::new();
    let mut listed: BTreeSet<String> = BTreeSet::new();

    for row in &rows {
        let (Some(resource), Some(dtype), Some(model)) = (
            row.get("resource").and_then(|v| v.as_str()),
            row.get("type").and_then(|v| v.as_str()),
            row.get("model").and_then(|v| v.as_str()),
        ) else {
            println!("[instrument-gui] roster row without resource/type/model — skipped");
            continue;
        };
        listed.insert(resource.to_string());
        let dev = row.get("dev").and_then(|v| v.as_u64()).unwrap_or(0);

        // The instrument is the authority on what it IS; the roster is the
        // authority on where it sits and what to call its topic.
        let (dtype, model) = match by_resource.get(resource) {
            Some(live) if live.model != model => {
                println!("[instrument-gui] {resource} is listed as {model} but answered \
                          {} — using the instrument's answer", live.model);
                (live.dtype.clone(), live.model.clone())
            }
            Some(live) => (live.dtype.clone(), live.model.clone()),
            None => (dtype.to_string(), model.to_string()),
        };

        out.push(Device {
            dtype: dtype.replace(' ', "_"),
            model: model.replace(' ', "_"),
            resource: resource.to_string(),
            write_topic: format!(
                "OpenAir/System/Protocols/visa/Device/{}/{}/Dev{dev}/Write",
                dtype.replace(' ', "_"),
                model.replace(' ', "_")
            ),
        });
    }

    // Anything the scan turned up that the record has never seen.
    let mut appended = Vec::new();
    for d in found {
        if listed.contains(&d.resource) {
            continue;
        }
        out.push(d.clone());
        let dev = d
            .write_topic
            .rsplit('/')
            .nth(1)
            .and_then(|s| s.strip_prefix("Dev"))
            .and_then(|s| s.parse::<u64>().ok())
            .unwrap_or(0);
        appended.push(json!({
            "resource": d.resource,
            "type": d.dtype,
            "model": d.model,
            "dev": dev,
            "host": d.resource.split("::").nth(1).unwrap_or(""),
        }));
        println!("[instrument-gui] {} {} at {} is new — added to the bench roster",
                 d.dtype, d.model, d.resource);
    }

    if !appended.is_empty() {
        let mut all = rows;
        all.extend(appended);
        doc["devices"] = Value::Array(all);
        if let Some(parent) = path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        match serde_json::to_string_pretty(&doc) {
            Ok(text) => {
                let _ = std::fs::write(&path, text + "\n");
            }
            Err(e) => println!("[instrument-gui] could not write the roster: {e}"),
        }
    }

    if out.is_empty() {
        return found.to_vec();
    }
    println!("[instrument-gui] roster: {} instrument(s) known, {} answered this scan",
             out.len(), found.len());
    out
}

pub fn build(root: &Path, devices: &[Device]) -> (usize, usize) {
    // Build for the BENCH, not for the scan — see merge_roster.
    let devices = &merge_roster(root, devices)[..];
    let manifest_path = template_root(root).join("manifest.json");
    let Some(manifest) = read_panel(&manifest_path) else {
        println!("[instrument-gui] no manifest at {}", manifest_path.display());
        return (0, 0);
    };
    let caps = load_capabilities(root);

    let mut wanted = BTreeSet::new();
    let (mut written, mut built) = (0, 0);
    let mut by_type: BTreeMap<String, Vec<Device>> = BTreeMap::new();

    for dev in devices {
        by_type.entry(dev.dtype.clone()).or_default().push(dev.clone());
        let Some(spec) = manifest.get(&dev.dtype) else {
            // A discovered type with no authored template (VNA, Counter, DAQ,
            // SMU today). A silent skip would read as a broken build.
            println!(
                "[instrument-gui] no template for type '{}' — {} skipped",
                dev.dtype, dev.model
            );
            continue;
        };
        let tab = spec.get("tab").and_then(|t| t.as_str()).unwrap_or("");
        let slug = device_slug(&dev.model, &dev.resource);
        let out_dir = out_root(root).join(tab).join(&slug);
        // Rewrite rather than merge: a stale panel from a previous template is
        // worse than a missing one, and the folder is generated data.
        if out_dir.is_dir() {
            let _ = std::fs::remove_dir_all(&out_dir);
        }
        let (panels, handlers) = instantiate(root, &dev.dtype, &out_dir, dev, &caps);
        if panels == 0 {
            continue;
        }
        write_stamp(
            &out_dir,
            &json!({
                "type": dev.dtype,
                "model": dev.model,
                "resource": dev.resource,
                "write_topic": dev.write_topic,
            }),
        );
        wanted.insert(format!("{tab}/{slug}"));
        written += panels;
        built += 1;
        println!("[instrument-gui] {tab}/{slug} — {panels} panel(s), {handlers} bound command(s)");
    }

    // Group views come after the per-device pass because they are about the
    // bench rather than about one instrument — which modules share a mainframe,
    // how many channels a scope has. Nothing to build until every device is in.
    for (dtype, group_devices) in &by_type {
        let Some(spec) = manifest.get(dtype) else { continue };
        if spec.get("groups").and_then(|g| g.as_array()).map(|g| g.is_empty()) != Some(false) {
            continue;
        }
        let tab = spec.get("tab").and_then(|t| t.as_str()).unwrap_or("");
        let (gw, gb, gwanted) = build_group_panels(root, dtype, spec, tab, group_devices, &caps);
        written += gw;
        built += gb;
        wanted.extend(gwanted);
    }

    // KEEP THE OLD STATE when this pass built nothing.
    //
    // An empty `wanted` set does not mean every instrument on the bench
    // vanished — on a fresh boot it means the discovery mirror had not filled
    // yet. Pruning on that reading deleted every device panel and rebuilt it
    // seconds later once the scan landed: churn on every restart, and a window
    // where the operator's panels are simply gone.
    //
    // A device that has genuinely disappeared is pruned by the next pass that
    // builds something — the pass that can actually tell the difference between
    // "gone" and "not known yet".
    if wanted.is_empty() {
        println!("[instrument-gui] nothing discovered yet — keeping the panels already on disk");
    } else {
        prune(root, &wanted);
    }
    (written, built)
}

/// Adapt the discovery mirror's `collected` map to `build`'s device list.
///
/// VISA categories ARE the knowledge-base type (DMM, Spectrum, …), so the
/// category name selects the template. `_topic_prefix` is recorded by the
/// collector because the device's Write topic cannot be reconstructed from the
/// row fields alone — the Dev index appears in none of them.
pub fn devices_from_collected(root: &Path, collected: &Collected) -> Vec<Device> {
    let manifest = read_panel(&template_root(root).join("manifest.json"));
    let mut devices = Vec::new();
    for (category, blocks) in collected {
        if manifest.as_ref().and_then(|m| m.get(category)).is_none() {
            continue;
        }
        for fields in blocks.values() {
            let Some(prefix) = fields.get("_topic_prefix") else {
                continue;
            };
            devices.push(Device {
                dtype: category.clone(),
                model: fields.get("model").cloned().unwrap_or_else(|| "unknown".into()),
                resource: fields.get("resource").cloned().unwrap_or_default(),
                write_topic: format!("{prefix}/Write"),
            });
        }
    }
    devices
}

#[cfg(test)]
mod tests {
    use super::*;

    fn dev(model: &str, resource: &str) -> Device {
        Device {
            dtype: "Power".into(),
            model: model.into(),
            resource: resource.into(),
            write_topic: "OpenAir/System/Protocols/visa/Device/Power/66104A/Dev0/Write".into(),
        }
    }

    #[test]
    fn a_secondary_address_is_a_slot_but_a_primary_one_is_not() {
        // board 7, primary 30, SECONDARY 4 -> slot 4.
        assert_eq!(slot_of("TCPIP::44.44.44.111::gpib7,30,4::INSTR"), Some(4));
        // The scope's `6` is its own primary address, not a slot. Reading it as
        // one would stamp INST:NSEL 6 onto an instrument that has no slots.
        assert_eq!(slot_of("TCPIP::44.44.44.111::gpib7,6::INSTR"), None);
        assert_eq!(slot_of("TCPIP::44.44.44.66::INSTR"), None);
    }

    #[test]
    fn modules_of_one_mainframe_share_a_chassis_key() {
        let a = chassis_of("TCPIP::44.44.44.111::gpib7,30,0::INSTR");
        let h = chassis_of("TCPIP::44.44.44.111::gpib7,30,7::INSTR");
        assert_eq!(a, h);
        // A standalone instrument is its own chassis of one.
        assert_ne!(a, chassis_of("TCPIP::44.44.44.111::gpib7,6::INSTR"));
        // Eight meters behind one gateway group by host instead.
        assert_eq!(host_of("TCPIP::44.44.44.111::gpib7,4::INSTR"), "44.44.44.111");
    }


    #[test]
    fn the_roster_keeps_a_bench_that_a_scan_missed() {
        let tmp = std::env::temp_dir().join(format!("oa-roster-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&tmp);
        std::fs::create_dir_all(tmp.join("BackEnd/Core/Database")).unwrap();
        std::fs::write(
            tmp.join(ROSTER),
            serde_json::to_string_pretty(&json!({
                "schemaVersion": 1,
                "devices": [
                    // Two meters the bench owns. Only one answers today.
                    {"resource": "TCPIP::1.1.1.1::gpib7,4::INSTR",  "type": "DMM", "model": "34401A", "dev": 0},
                    {"resource": "TCPIP::1.1.1.1::gpib7,11::INSTR", "type": "DMM", "model": "34401A", "dev": 1},
                ]
            })).unwrap(),
        ).unwrap();

        let live = vec![Device {
            dtype: "DMM".into(),
            model: "34401A".into(),
            resource: "TCPIP::1.1.1.1::gpib7,11::INSTR".into(),
            // A scan that found only this one would have called it Dev0.
            write_topic: "OpenAir/System/Protocols/visa/Device/DMM/34401A/Dev0/Write".into(),
        }];

        let merged = merge_roster(&tmp, &live);

        // The meter that stayed silent is still on the bench.
        assert_eq!(merged.len(), 2, "a scan missing a device must not drop it");
        let quiet = merged.iter().find(|d| d.resource.ends_with("gpib7,4::INSTR")).unwrap();
        assert!(quiet.write_topic.ends_with("/Dev0/Write"));

        // And the one that answered keeps the index the roster pinned, NOT the
        // one this scan would have handed it — otherwise every panel bound to
        // Dev1 would quietly start reading Dev0's meter.
        let loud = merged.iter().find(|d| d.resource.ends_with("gpib7,11::INSTR")).unwrap();
        assert!(loud.write_topic.ends_with("/Dev1/Write"),
                "pinned index lost: {}", loud.write_topic);

        // A device nobody listed is adopted, and written down.
        let newcomer = vec![Device {
            dtype: "Load".into(), model: "6060B".into(),
            resource: "TCPIP::1.1.1.1::gpib7,22::INSTR".into(),
            write_topic: "OpenAir/System/Protocols/visa/Device/Load/6060B/Dev0/Write".into(),
        }];
        let merged = merge_roster(&tmp, &newcomer);
        assert_eq!(merged.len(), 3);
        let saved: Value = serde_json::from_str(
            &std::fs::read_to_string(tmp.join(ROSTER)).unwrap()).unwrap();
        let rows = saved["devices"].as_array().unwrap();
        assert_eq!(rows.len(), 3, "a newly found instrument is recorded");
        assert!(rows.iter().any(|r| r["model"] == json!("6060B")));

        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn a_bank_bar_is_named_for_its_slot_not_its_model_counter() {
        let mk = |model: &str, slot: u32, devn: u32| {
            let mut t = BTreeMap::new();
            t.insert("n".to_string(), (devn + 1).to_string());
            (t, Device {
                dtype: "Power".into(),
                model: model.into(),
                resource: format!("TCPIP::44.44.44.111::gpib7,30,{slot}::INSTR"),
                write_topic: format!(
                    "OpenAir/System/Protocols/visa/Device/Power/{model}/Dev{devn}/Write"
                ),
            })
        };
        // One mainframe, three models, and slot 3 empty.
        let members = vec![mk("66101A", 0, 0), mk("66102A", 1, 0), mk("66102A", 2, 1),
                           mk("66104A", 4, 0), mk("66104A", 7, 3)];
        let names = bank_names(&members);
        // Keyed as BankBars parses a reading topic: "<model>/<dev>".
        assert_eq!(names["66101A/Dev0"], json!("CH1 · 66101A"));
        // Two 66102As both counted from Dev0 by model — the slot tells them apart.
        assert_eq!(names["66102A/Dev0"], json!("CH2 · 66102A"));
        assert_eq!(names["66102A/Dev1"], json!("CH3 · 66102A"));
        // The empty slot is not closed up: nothing is called CH4 here.
        assert_eq!(names["66104A/Dev0"], json!("CH5 · 66104A"));
        assert_eq!(names["66104A/Dev3"], json!("CH8 · 66104A"));
        assert!(!names.values().any(|v| v == &json!("CH4 · 66104A")));

        // A STANDALONE instrument has no slot, so it is named for the address
        // it answers at. Eight meters on two gateways, and the label is the one
        // written on the front of each: gpib7,11 is gpib7,11 wherever it sorts.
        let meter = |host: &str, gpib: &str, devn: u32| {
            (BTreeMap::new(), Device {
                dtype: "DMM".into(),
                model: "34401A".into(),
                resource: format!("TCPIP::{host}::{gpib}::INSTR"),
                write_topic: format!(
                    "OpenAir/System/Protocols/visa/Device/DMM/34401A/Dev{devn}/Write"
                ),
            })
        };
        let meters = vec![meter("44.44.44.111", "gpib7,4", 0),
                          meter("44.44.44.111", "gpib7,11", 1),
                          meter("44.44.44.222", "gpib7,1", 4)];
        let m = bank_names(&meters);
        assert_eq!(m["34401A/Dev0"], json!("111 · gpib7,4"));
        assert_eq!(m["34401A/Dev1"], json!("111 · gpib7,11"));
        // Same GPIB number, different gateway — the host tail keeps them apart.
        assert_eq!(m["34401A/Dev4"], json!("222 · gpib7,1"));
        assert!(!m.values().any(|v| v.as_str().unwrap_or("").starts_with("CH")));
    }

    #[test]
    fn two_generators_at_two_addresses_group_by_type() {
        let a = "TCPIP::44.44.44.162::INSTR";
        let b = "TCPIP::44.44.44.33::INSTR";
        // Neither shares a box nor a gateway, so both of the older axes put
        // each one in a group of one — and a group of one is dropped.
        assert_ne!(group_key("chassis", "Generator", a), group_key("chassis", "Generator", b));
        assert_ne!(group_key("host", "Generator", a), group_key("host", "Generator", b));
        // The LINK page is a view over the bench, and there they meet.
        assert_eq!(group_key("type", "Generator", a), group_key("type", "Generator", b));
        // …but only with instruments of their own type.
        assert_ne!(group_key("type", "Generator", a), group_key("type", "DMM", b));
    }

    #[test]
    fn the_slug_distinguishes_identical_models() {
        // This bench has eight 34401As all reporting serial "0", so the model
        // alone would name all eight the same thing.
        let a = device_slug("34401A", "TCPIP::44.44.44.111::gpib7,4::INSTR");
        let b = device_slug("34401A", "TCPIP::44.44.44.111::gpib7,11::INSTR");
        assert_ne!(a, b);
        // Everything non-alphanumeric in the resource tail collapses to a dash;
        // only the model/tail join is an underscore. (The Python docstring
        // renders this as `34401A_44-44-44-111_gpib7-4`, which its own code does
        // not produce — the generated folders on disk carry the dash.)
        assert_eq!(a, "34401A_44-44-44-111-gpib7-4");
        // No resource at all falls back to the bare model.
        assert_eq!(device_slug("N9340B", ""), "N9340B");
    }

    #[test]
    fn substitution_rewrites_key_names_as_well_as_values() {
        // The key is the panel's identity in the frontend tree, so eight copies
        // named `PSU_Module_${n}` must become eight DIFFERENT names.
        let mut tokens = BTreeMap::new();
        tokens.insert("n".to_string(), "3".to_string());
        let doc = json!({ "PSU_Module_${n}": { "label": "Module ${n}" } });
        let out = substitute(&doc, &tokens);
        assert!(out.get("PSU_Module_3").is_some());
        assert_eq!(out["PSU_Module_3"]["label"], "Module 3");

        // An unknown token is left alone rather than blanked — a `<value>` SCPI
        // placeholder must survive to YAK's own substitution pass.
        let out = substitute(&json!({"cmd": "VOLT ${unknown}"}), &tokens);
        assert_eq!(out["cmd"], "VOLT ${unknown}");
    }

    #[test]
    fn every_handler_gets_its_target_model_and_slot() {
        let mut caps = HashMap::new();
        caps.insert("66104A".to_string(), json!({ "model": "66104A" }));
        let doc = json!({
            "Panel": { "fields": { "v": { "yak_handler": { "verb": "set" } } } }
        });
        let (bound, handlers) = prepare(
            &doc,
            &dev("66104A", "TCPIP::44.44.44.111::gpib7,30,4::INSTR"),
            None,
            &caps,
        );
        assert_eq!(handlers, 1);
        let h = &bound["Panel"]["fields"]["v"]["yak_handler"];
        assert_eq!(h["model"], "66104A");
        assert!(h["target"].as_str().unwrap().ends_with("/Write"));
        // SCPI channels are 1-based, the GPIB secondary address is 0-based —
        // slot 4 addresses itself as channel 5.
        assert_eq!(h["params"]["chan"], "5");
    }

    #[test]
    fn a_marked_block_becomes_one_strip_per_channel() {
        // The scope's amplitude tab is ONE channel strip in the panel file. The
        // 4-channel Rigol must get four of them, each driving its own channel.
        let mut doc = json!({ "AMPLITUDE": { "blocks": {
            "Trigger": { "label": "Trigger" },
            "Channel_${n}": {
                "label": "${label}",
                "fields": { "scale": {
                    "color": "${color}",
                    "yak_handler": { "command": "Set_Channel_Scale" },
                } },
            },
        }}});
        repeat_channels(&mut doc, "DS1104Z", Some(4));
        let blocks = &doc["AMPLITUDE"]["blocks"];

        for i in 1..=4 {
            let strip = &blocks[format!("Channel_{i}")];
            assert_eq!(strip["label"], format!("CH{i}"));
            // The index is what turns `:CHANnel<n>:SCALe` into this channel's
            // knob; without it all four strips drive channel one.
            let params = &strip["fields"]["scale"]["yak_handler"]["params"];
            assert_eq!(params["n"], i.to_string());
            assert_eq!(params["chan"], i.to_string());
        }
        // Distinct colours, and the unmarked block untouched.
        assert_ne!(blocks["Channel_1"]["fields"]["scale"]["color"],
                   blocks["Channel_2"]["fields"]["scale"]["color"]);
        assert_eq!(blocks["Trigger"]["label"], "Trigger");
        assert!(blocks.get("Channel_${n}").is_none());
    }

    #[test]
    fn a_marked_array_entry_repeats_too_and_a_two_channel_scope_gets_two() {
        // The DATASET graph names one series per channel, and an array entry has
        // no key to carry the mark — so the mark is inside it.
        let mut doc = json!({ "DATASET": { "blocks": { "G": { "fields": { "g": {
            "traces": [{ "id": "CH${n}", "yak_listen": "waveform_${n}/samples" }],
        }}}}}});
        repeat_channels(&mut doc, "54641D", Some(2));
        let traces = doc["DATASET"]["blocks"]["G"]["fields"]["g"]["traces"]
            .as_array()
            .expect("still an array");
        assert_eq!(traces.len(), 2);
        assert_eq!(traces[0]["yak_listen"], "waveform_1/samples");
        assert_eq!(traces[1]["id"], "CH2");
    }

    #[test]
    fn a_model_with_no_channel_count_loses_the_strip_rather_than_showing_a_token() {
        // `${n}` left on screen is a widget that lies about which channel it
        // drives, and a knob that writes `:CHANnel${n}:SCALe` writes nothing.
        let mut doc = json!({ "AMPLITUDE": { "blocks": {
            "Trigger": { "label": "Trigger" },
            "Channel_${n}": { "label": "${label}" },
        }}});
        repeat_channels(&mut doc, "TBS2000B", None);
        let blocks = &doc["AMPLITUDE"]["blocks"];
        assert!(blocks.get("Trigger").is_some());
        assert_eq!(blocks.as_object().unwrap().len(), 1);
    }

    #[test]
    fn an_instrument_that_never_answers_is_declared_rather_than_discovered() {
        // The HP 3235 matrix takes commands and answers none, so `*IDN?` gets
        // nothing and no scan can see it. Its sheet says where it is instead,
        // and names the command that puts it in a known state — resolved
        // through the model's OWN vocabulary, so the address lives in the sheet
        // and the words live in the YAK table.
        let tmp = std::env::temp_dir().join(format!("oa-declared-{}", std::process::id()));
        let dir = tmp.join("Instruments").join("Router").join("3235");
        std::fs::create_dir_all(&dir).unwrap();
        std::fs::write(dir.join("3235.gui"), r#"{
            "model": "3235", "type": "Router", "manufacturer": "HP",
            "declared": {
                "resource": "TCPIP::44.44.44.222::gpib7,10::INSTR",
                "listen_only": true,
                "on_connect": ["Open_All", "No_Such_Command"]
            }
        }"#).unwrap();
        std::fs::write(dir.join("3235.yak"),
            r#"{"do": {"Open_All": {"scpi": "OPEN 000-999"}}}"#).unwrap();

        let found = declared_devices(&tmp);
        assert_eq!(found.len(), 1);
        assert_eq!(found[0].resource, "TCPIP::44.44.44.222::gpib7,10::INSTR");
        assert_eq!(found[0].dtype, "Router");
        assert!(found[0].listen_only, "the heartbeat must know not to probe it");
        // The real command resolved; the fictional one was dropped with a
        // complaint rather than sent as its own name.
        assert_eq!(found[0].on_connect, vec!["OPEN 000-999".to_string()]);

        // A sheet with no resource is a declaration of nothing.
        std::fs::write(dir.join("3235.gui"),
            r#"{"model": "3235", "type": "Router", "declared": {"listen_only": true}}"#).unwrap();
        assert!(declared_devices(&tmp).is_empty());
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn a_readout_widget_is_pointed_at_the_reply_topic() {
        let caps = HashMap::new();
        let doc = json!({ "P": { "fields": { "m": { "yak_readout": true } } } });
        let (bound, _) = prepare(&doc, &dev("66104A", ""), None, &caps);
        assert_eq!(
            bound["P"]["fields"]["m"]["topic"],
            "OpenAir/System/Protocols/visa/Device/Power/66104A/Dev0/Read"
        );
    }

    #[test]
    fn domains_come_from_the_model_not_the_template() {
        // The 8V module and the 60V module share one template; only the model's
        // capability sheet can tell the widgets apart.
        let mut caps = HashMap::new();
        caps.insert(
            "66104A".to_string(),
            json!({ "model": "66104A", "domains": { "volt": { "min": 0, "max": 60 } } }),
        );
        let doc = json!({ "P": { "fields": { "v": { "yak_domain": "volt" } } } });
        let (bound, _) = prepare(&doc, &dev("66104A", ""), None, &caps);
        assert_eq!(bound["P"]["fields"]["v"]["domain"]["max"], 60);
    }

    #[test]
    fn chunking_splits_banks_and_all_means_one_group() {
        let items = vec![1, 2, 3, 4, 5];
        assert_eq!(chunk(&items, &json!("all")), vec![vec![1, 2, 3, 4, 5]]);
        assert_eq!(chunk(&items, &json!(2)), vec![vec![1, 2], vec![3, 4], vec![5]]);
        let empty: Vec<i32> = vec![];
        assert!(chunk(&empty, &json!("all")).is_empty());
    }

    #[test]
    fn template_key_order_becomes_tab_order() {
        // Alphabetically `amplitude` precedes `bandwidth`, so this test only
        // means anything because serde_json is built with preserve_order: the
        // point is that the AUTHORED order wins, whatever it is.
        let doc: Value =
            serde_json::from_str(r#"{"zulu": {"type": "OcaBin"}, "alpha": {"type": "OcaBin"}}"#)
                .unwrap();
        let keys: Vec<&String> = doc.as_object().unwrap().keys().collect();
        assert_eq!(keys, vec!["zulu", "alpha"], "key order was not preserved");
    }
}
