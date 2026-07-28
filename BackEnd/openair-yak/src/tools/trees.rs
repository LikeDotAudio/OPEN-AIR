//! Render each command table as a browsable SCPI tree in Markdown.
//!
//! `commands.json` is the source; this is the view. A table of 600 flat command
//! names is unreadable, but the SCPI vocabulary is a tree by construction — so
//! nesting each command under its mnemonics turns the same data into something
//! a technician can scan.
//!
//! The generated block sits at the top of `commands_tree.md` between markers;
//! anything hand-written below is preserved.

use std::collections::BTreeMap;
use std::path::Path;

use serde_json::Value;

use super::{placeholders, str_field, tables, verb_entries, VERBS};

const BEGIN: &str = "<!-- BEGIN GENERATED — openair-yak build-trees -->";
/// Markers written before this tool became a subcommand. Recognised so a
/// regeneration REPLACES that block, instead of failing to find it and burying
/// the whole stale tree under "Notes carried over".
const LEGACY_BEGIN: [&str; 2] = [
    "<!-- BEGIN GENERATED — Deployment/build_yak_command_trees.py -->",
    "<!-- BEGIN GENERATED — BackEnd/openair-yak/tools/build_yak_command_trees.py -->",
];
const END: &str = "<!-- END GENERATED -->";
const CARRIED: &str = "## Notes carried over";

/// `:SENSe:VOLTage:DC:RANGe <range>` -> `(["SENSe","VOLTage","DC","RANGe"], "<range>")`.
///
/// The header is everything up to the first space; whatever follows is the
/// parameter, which may be a placeholder (`<range>`) or a literal the table
/// baked in (`OFF`). Both are worth showing — a literal is why `Auto_Zero_OFF`
/// and `Auto_Zero_ON` are two commands rather than one SET.
fn split_header(statement: &str) -> (Vec<String>, String) {
    let s = statement.trim();
    let (head, param) = match s.find(' ') {
        Some(i) => (&s[..i], s[i + 1..].trim()),
        None => (s, ""),
    };
    let path = head
        .trim_start_matches(':')
        .split(':')
        .filter(|m| !m.is_empty())
        .map(|m| m.to_string())
        .collect();
    (path, param.to_string())
}

/// The one-line summary that hangs off a leaf.
fn annotate(name: &str, verb: &str, cmd: &Value, statement_param: &str) -> String {
    let mut bits = vec![format!("**{}** `{name}`", verb.to_uppercase())];
    if !statement_param.is_empty() {
        bits.push(format!("`{statement_param}`"));
    }
    let args: Vec<String> = cmd
        .get("args")
        .and_then(|a| a.as_array())
        .map(|a| a.iter().filter_map(|x| x.as_str()).map(String::from).collect())
        .unwrap_or_default();
    if !args.is_empty() {
        let rendered: Vec<String> = args.iter().map(|a| format!("`{a}`")).collect();
        bits.push(format!("args: {}", rendered.join(", ")));
    }

    // `arg` types the value the operator supplies — a bool is a toggle, an enum
    // is a selector and its `values` ARE the options, a numeric wants a domain.
    let empty = Value::Object(Default::default());
    let arg = cmd.get("arg").unwrap_or(&empty);
    let values: Vec<String> = arg
        .get("values")
        .and_then(|v| v.as_array())
        .map(|v| v.iter().filter_map(|x| x.as_str()).map(String::from).collect())
        .unwrap_or_default();
    if !values.is_empty() {
        let kind = arg.get("kind").and_then(|k| k.as_str()).unwrap_or("enum");
        let rendered: Vec<String> = values.iter().map(|v| format!("`{v}`")).collect();
        bits.push(format!("{kind}: {}", rendered.join(" | ")));
    } else {
        let kind = arg.get("kind").and_then(|k| k.as_str()).unwrap_or("");
        if !kind.is_empty() && kind != "unknown" {
            let unit = arg.get("unit").and_then(|u| u.as_str()).unwrap_or("");
            if unit.is_empty() {
                bits.push(kind.to_string());
            } else {
                bits.push(format!("{kind} ({unit})"));
            }
        }
    }

    // Placeholders the operator does not supply are stamped per panel.
    let stamped: Vec<String> = placeholders(&str_field(cmd, "scpi"))
        .into_iter()
        .filter(|p| !args.contains(p))
        .collect();
    if !stamped.is_empty() {
        let rendered: Vec<String> = stamped.iter().map(|p| format!("`{p}`")).collect();
        bits.push(format!("per-instance: {}", rendered.join(", ")));
    }

    if let Some(returns) = cmd.get("returns").and_then(|r| r.as_object()) {
        if !returns.is_empty() {
            let fields = returns.get("fields").and_then(|f| f.as_array());
            match fields.filter(|f| !f.is_empty()) {
                Some(fields) => {
                    let names: Vec<&str> = fields
                        .iter()
                        .map(|f| f.get("name").and_then(|n| n.as_str()).unwrap_or("?"))
                        .collect();
                    bits.push(format!("→ {}", names.join(", ")));
                }
                None => {
                    let t = returns.get("type").and_then(|t| t.as_str()).unwrap_or("");
                    let u = returns.get("unit").and_then(|u| u.as_str()).unwrap_or("");
                    let rt = [t, u]
                        .iter()
                        .filter(|x| !x.is_empty())
                        .cloned()
                        .collect::<Vec<_>>()
                        .join(" ");
                    if rt.is_empty() {
                        let count = returns.get("count").and_then(|c| c.as_u64()).unwrap_or(1);
                        bits.push(format!("→ {count} value"));
                    } else {
                        bits.push(format!("→ {rt}"));
                    }
                }
            }
        }
    }
    if cmd.get("unverified").and_then(|u| u.as_bool()) == Some(true) {
        bits.push("†".to_string());
    }

    let mut line = bits.join(" · ");
    let desc = str_field(cmd, "description").trim().to_string();
    // The sweep gave whole subsystems the same description; it is noise once the
    // command name says the same thing.
    if !desc.is_empty() && desc.to_lowercase().replace(' ', "_") != name.to_lowercase() {
        line.push_str(&format!("<br>{desc}"));
    }
    line
}

/// One command as the tree holds it.
struct Leaf {
    mnemonic: String,
    name: String,
    verb: String,
    cmd: Value,
    param: String,
}

#[derive(Default)]
struct Node {
    leaves: Vec<Leaf>,
    children: BTreeMap<String, Node>,
}

/// Nest every single-statement command under its mnemonics.
///
/// `common` holds the `*IDN?` family, which has no path to nest under.
/// `compound` holds multi-statement commands, which belong to no single branch —
/// a NAB spanning three subsystems is exactly the thing a tree cannot draw.
#[allow(clippy::type_complexity)]
fn build_tree(table: &Value) -> (Node, Vec<(String, String, Value, String)>, Vec<(String, String, Value)>) {
    let mut tree = Node::default();
    let mut common = Vec::new();
    let mut compound = Vec::new();

    for verb in VERBS {
        for (name, cmd) in verb_entries(table, verb) {
            let scpi = str_field(cmd, "scpi");
            let statements: Vec<&str> = scpi.split(';').filter(|s| !s.trim().is_empty()).collect();
            if statements.len() > 1 {
                compound.push((name.clone(), verb.to_string(), cmd.clone()));
                continue;
            }
            let (path, param) = split_header(&scpi);
            if path.is_empty() {
                continue;
            }
            if path[0].starts_with('*') {
                common.push((name.clone(), verb.to_string(), cmd.clone(), param));
                continue;
            }
            let mut node = &mut tree;
            for mnemonic in &path[..path.len() - 1] {
                node = node.children.entry(mnemonic.clone()).or_default();
            }
            node.leaves.push(Leaf {
                mnemonic: path[path.len() - 1].clone(),
                name: name.clone(),
                verb: verb.to_string(),
                cmd: cmd.clone(),
                param,
            });
        }
    }
    (tree, common, compound)
}

fn render_tree(node: &Node, depth: usize) -> Vec<String> {
    let mut out = Vec::new();
    let pad = "  ".repeat(depth);
    for leaf in &node.leaves {
        out.push(format!(
            "{pad}- `{}` — {}",
            leaf.mnemonic,
            annotate(&leaf.name, &leaf.verb, &leaf.cmd, &leaf.param)
        ));
    }
    for (mnemonic, child) in &node.children {
        out.push(format!("{pad}- **`{mnemonic}`**"));
        out.extend(render_tree(child, depth + 1));
    }
    out
}

/// `<Family>/commands_tree.md` — prose written for a family, not a model.
///
/// Linked only when it actually names the model it would be claiming to
/// describe. `LCR/commands_tree.md` is byte-identical to `Load/commands_tree.md`
/// and explains the 6060B electronic load, so the 4263A gets no link and the
/// mis-file stays visible instead of being papered over by a pointer.
fn family_notes(yak: &Path, rel: &str, model: &str) -> Option<String> {
    let family = rel.split('/').next().unwrap_or("");
    let path = yak.join(family).join("commands_tree.md");
    let text = std::fs::read_to_string(&path).ok()?;
    // Prose about a module family names it once and wildcards the rest — the
    // Power notes cover 66103A as "6610xA" and never spell it out.
    if text.contains(model) {
        return Some("../commands_tree.md".to_string());
    }
    let chars: Vec<char> = model.chars().collect();
    for i in 0..chars.len() {
        let mut w: Vec<char> = chars.clone();
        w[i] = 'x';
        let wildcard: String = w.into_iter().collect();
        if text.contains(&wildcard) {
            return Some("../commands_tree.md".to_string());
        }
    }
    None
}

fn render(yak: &Path, rel: &str, table: &Value) -> String {
    let family = table
        .get("family")
        .and_then(|f| f.as_str())
        .unwrap_or_else(|| rel.split('/').next().unwrap_or(""))
        .to_string();
    let model = table
        .get("model")
        .and_then(|m| m.as_str())
        .unwrap_or_else(|| rel.split('/').nth(1).unwrap_or(""))
        .to_string();

    let counts: BTreeMap<&str, usize> = VERBS
        .iter()
        .map(|v| (*v, verb_entries(table, v).len()))
        .collect();
    let total: usize = counts.values().sum();
    let unverified: usize = VERBS
        .iter()
        .flat_map(|v| verb_entries(table, v))
        .filter(|(_, c)| c.get("unverified").and_then(|u| u.as_bool()) == Some(true))
        .count();

    let (tree, common, compound) = build_tree(table);

    let mut out: Vec<String> = vec![
        BEGIN.to_string(),
        String::new(),
        format!("# {family}/{model} — command tree"),
        String::new(),
        "Generated from `commands.json` by `openair-yak build-trees`. Edit the table, not this file."
            .to_string(),
        String::new(),
        format!(
            "**{total} commands** — SET {} · RIG {} · NAB {} · DO {}{}",
            counts["set"],
            counts["rig"],
            counts["nab"],
            counts["do"],
            if total > 0 {
                format!(" · {unverified} unverified ({}%)", unverified * 100 / total)
            } else {
                String::new()
            }
        ),
        String::new(),
        "`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.".to_string(),
        String::new(),
    ];

    if let Some(notes) = family_notes(yak, rel, &model) {
        out.push(format!(
            "Written notes for this family: [`{family}/commands_tree.md`]({notes})."
        ));
        out.push(String::new());
    }

    if !compound.is_empty() {
        out.extend([
            "## Compound commands".to_string(),
            String::new(),
            "Several statements in one message, so they hang off no single branch. Every statement after the first carries a leading colon — without it the parser reads it relative to the previous header's path and the instrument answers `-113`.".to_string(),
            String::new(),
        ]);
        let mut sorted = compound;
        sorted.sort_by(|a, b| a.0.cmp(&b.0).then(a.1.cmp(&b.1)));
        for (name, verb, cmd) in &sorted {
            out.push(format!("- {}", annotate(name, verb, cmd, "")));
            out.push(format!("  - `{}`", str_field(cmd, "scpi")));
        }
        out.push(String::new());
    }

    let rendered = render_tree(&tree, 0);
    if !rendered.is_empty() || !tree.leaves.is_empty() || !tree.children.is_empty() {
        out.push("## Tree".to_string());
        out.push(String::new());
        out.extend(rendered);
        out.push(String::new());
    }

    if !common.is_empty() {
        out.push("## Common commands (IEEE 488.2)".to_string());
        out.push(String::new());
        let mut sorted = common;
        sorted.sort_by(|a, b| a.0.cmp(&b.0).then(a.1.cmp(&b.1)));
        for (name, verb, cmd, param) in &sorted {
            out.push(format!(
                "- `{}` — {}",
                str_field(cmd, "scpi"),
                annotate(name, verb, cmd, param)
            ));
        }
        out.push(String::new());
    }

    out.push(END.to_string());
    out.join("\n")
}

/// Generated block on top, hand-written content preserved underneath.
fn merge(path: &Path, block: &str) -> String {
    let Ok(existing) = std::fs::read_to_string(path) else {
        return format!("{block}\n");
    };
    let mut markers = vec![BEGIN];
    markers.extend(LEGACY_BEGIN);
    for marker in markers {
        if let (Some(start), Some(end)) = (existing.find(marker), existing.find(END)) {
            if end >= start {
                let head = &existing[..start];
                let tail = &existing[end + END.len()..];
                return format!("{head}{block}{tail}");
            }
        }
    }
    // First run against a hand-written tree: keep every word of it.
    format!("{block}\n\n---\n\n{CARRIED}\n\n{}", existing.trim_start())
}

pub fn run(check: bool) -> i32 {
    let Some(yak) = super::yak_root() else {
        println!("❌ YAK tree not found; set YAK_REPO_PATH");
        return 1;
    };

    let mut stale = Vec::new();
    for (table_path, table) in tables(&yak) {
        let rel = super::rel_to(&yak, &table_path);
        let tree_path = table_path.with_file_name("commands_tree.md");
        let merged = merge(&tree_path, &render(&yak, &rel, &table));
        let current = std::fs::read_to_string(&tree_path).ok();
        if current.as_deref() == Some(merged.as_str()) {
            continue;
        }
        stale.push(super::rel_to(&yak, &tree_path));
        if !check {
            if let Err(e) = std::fs::write(&tree_path, &merged) {
                println!("   ⚠️  could not write {}: {e}", tree_path.display());
            }
        }
    }

    if check {
        if !stale.is_empty() {
            println!("   ❌ {} command tree(s) stale:", stale.len());
            for s in &stale {
                println!("      {s}");
            }
            return 1;
        }
        println!("   ✅ every command tree is current");
        return 0;
    }

    if stale.is_empty() {
        println!("   ✅ every command tree was already current");
    } else {
        println!("   ✅ rewrote {} command tree(s)", stale.len());
        for s in &stale {
            println!("      {s}");
        }
    }
    0
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn a_header_splits_into_mnemonics_and_its_parameter() {
        let (path, param) = split_header(":SENSe:VOLTage:DC:RANGe <range>");
        assert_eq!(path, vec!["SENSe", "VOLTage", "DC", "RANGe"]);
        assert_eq!(param, "<range>");
        // A literal baked into the table is a parameter too — it is why
        // Auto_Zero_OFF and Auto_Zero_ON are two commands rather than one SET.
        let (_, param) = split_header(":SENS:ZERO:AUTO OFF");
        assert_eq!(param, "OFF");
        let (path, param) = split_header("*IDN?");
        assert_eq!(path, vec!["*IDN?"]);
        assert!(param.is_empty());
    }

    #[test]
    fn compound_commands_are_kept_out_of_the_tree() {
        // A command spanning three subsystems hangs off no single branch.
        let table = json!({
            "set": {
                "Simple": {"scpi": ":VOLT <v>", "description": "d"},
                "Chained": {"scpi": ":INST:NSEL <chan>;:OUTP ON", "description": "d"}
            }
        });
        let (tree, common, compound) = build_tree(&table);
        assert_eq!(compound.len(), 1);
        assert_eq!(compound[0].0, "Chained");
        assert!(common.is_empty());
        assert!(tree.children.contains_key("VOLT") || !tree.leaves.is_empty());
    }

    #[test]
    fn star_commands_go_to_the_common_section() {
        let table = json!({ "nab": { "Read_IDN": {"scpi": "*IDN?", "returns": {"count": 1}} } });
        let (_, common, _) = build_tree(&table);
        assert_eq!(common.len(), 1);
        assert_eq!(common[0].0, "Read_IDN");
    }

    #[test]
    fn a_regeneration_replaces_a_legacy_marked_block() {
        // Trees generated before this became a subcommand carry the old marker.
        // Failing to find it would bury the stale tree under "Notes carried
        // over" instead of replacing it.
        let dir = std::env::temp_dir().join(format!("yak-trees-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("commands_tree.md");
        std::fs::write(
            &path,
            format!("{}\nOLD BODY\n{END}\n\nhand-written notes\n", LEGACY_BEGIN[0]),
        )
        .unwrap();

        let merged = merge(&path, "NEW BLOCK");
        std::fs::remove_dir_all(&dir).ok();
        assert!(merged.starts_with("NEW BLOCK"));
        assert!(merged.contains("hand-written notes"));
        assert!(!merged.contains("OLD BODY"));
        assert!(!merged.contains(CARRIED), "legacy block was not recognised");
    }
}
