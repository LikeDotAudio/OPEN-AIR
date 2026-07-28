//! Regenerate `Yak/CommandList.csv` (and `.xlsx`) from the command tables.
//!
//! The sheet is a REPORT, not a source. Every row is derived from a
//! `Yak/<Family>/<Model>/commands.json` entry — edit the table, run this, never
//! the other way round.
//!
//! One row per command. The `Returns` / `Return type` / `Return unit` /
//! `Return fields` group is the declared shape of a NAB's reply — nothing parses
//! replies yet, so those columns are the spec the receiver will be built against
//! rather than a description of anything running.
//!
//! `Unverified` is the column the sheet did not have: a command swept out of a
//! manual and never sent to an instrument. That is most of the vocabulary, and a
//! sheet that stays quiet about it reads as 3600 working commands.
//!
//! `Arguments` and `Instance params` split the SCPI placeholders two ways, and
//! the split is the whole reason a panel author reads this file. Arguments come
//! from the operator through sibling `Input/*` widgets; instance params
//! (`<chan>`, `<slot>`) are stamped per panel by the orchestrator's
//! `instruments.rs` and substituted by `verbs::apply_params` BEFORE any widget
//! value goes in. A placeholder in neither column is a name nothing will ever
//! fill — the verb refuses to send rather than half-build the command, so it
//! shows up here as a table bug, not a runtime mystery.

use std::collections::BTreeSet;

use serde_json::Value;

use super::{placeholders, str_field, tables, verb_entries, VERBS};

const COLUMNS: [&str; 20] = [
    "Family",
    "Model",
    "Verb",
    "Command",
    "Description",
    "SCPI",
    "SCPI (short)",
    "Arguments",
    "Arg kind",
    "Arg values",
    "Instance params",
    "Group",
    "Subsystem",
    "Returns",
    "Return type",
    "Return unit",
    "Return fields",
    "SCPI statements",
    "Unverified",
    "File",
];

const WIDTHS: [f64; 20] = [
    12.0, 11.0, 10.0, 49.0, 60.0, 60.0, 44.0, 42.0, 11.0, 34.0, 17.0, 60.0, 18.0, 9.0, 14.0, 13.0,
    30.0, 17.0, 12.0, 36.0,
];

type Row = Vec<String>;

/// Flatten a `returns` object into the four reply columns.
///
/// A compound query — `MODE?;MEAS:VOLT?;MEAS:CURR?` — declares one `fields`
/// entry per value, and the columns stay parallel so row-wise they read as
/// tuples: field n's type is the nth entry of `Return type`. A field that never
/// got a type is written `?` rather than blank, because "unknown" and "the reply
/// carries no unit" are different facts and a blank cannot say which.
fn describe_returns(returns: Option<&Value>) -> (String, String, String, String) {
    let Some(r) = returns.and_then(|r| r.as_object()) else {
        return (String::new(), String::new(), String::new(), String::new());
    };
    if r.is_empty() {
        return (String::new(), String::new(), String::new(), String::new());
    }
    let count = r
        .get("count")
        .map(|c| match c {
            Value::Number(n) => n.to_string(),
            Value::String(s) => s.clone(),
            _ => String::new(),
        })
        .unwrap_or_default();
    let fields = r.get("fields").and_then(|f| f.as_array());
    match fields.filter(|f| !f.is_empty()) {
        None => (
            count,
            r.get("type").and_then(|t| t.as_str()).unwrap_or("").to_string(),
            r.get("unit").and_then(|u| u.as_str()).unwrap_or("").to_string(),
            String::new(),
        ),
        Some(fields) => {
            let pick = |key: &str, missing: &str| {
                fields
                    .iter()
                    .map(|f| f.get(key).and_then(|v| v.as_str()).unwrap_or(missing).to_string())
                    .collect::<Vec<_>>()
                    .join("; ")
            };
            (count, pick("type", "?"), pick("unit", ""), pick("name", ""))
        }
    }
}

/// Every command in the tree, as sheet rows, in a stable order.
///
/// Sorted by (family, model, verb, command) so a regeneration after an edit
/// produces a diff of the edit rather than of the dict order it happened to be
/// written in.
fn rows(yak: &std::path::Path) -> Vec<Row> {
    let mut out: Vec<Row> = Vec::new();
    for (path, table) in tables(yak) {
        let rel = super::rel_to(yak, &path);
        // The declared model wins over the directory. Filing a command under its
        // folder name is exactly the bug the table format was introduced to end.
        let family = table
            .get("family")
            .and_then(|f| f.as_str())
            .filter(|f| !f.is_empty())
            .unwrap_or_else(|| rel.split('/').next().unwrap_or(""))
            .to_string();
        let model = table
            .get("model")
            .and_then(|m| m.as_str())
            .filter(|m| !m.is_empty())
            .unwrap_or_else(|| rel.split('/').nth(1).unwrap_or(""))
            .to_string();

        for verb in VERBS {
            for (name, cmd) in verb_entries(&table, verb) {
                let scpi = str_field(cmd, "scpi");
                let args: Vec<String> = cmd
                    .get("args")
                    .and_then(|a| a.as_array())
                    .map(|a| a.iter().filter_map(|x| x.as_str()).map(String::from).collect())
                    .unwrap_or_default();
                // Anything in the template the operator does not supply is a
                // per-instance constant, in template order.
                let params: Vec<String> = placeholders(&scpi)
                    .into_iter()
                    .filter(|p| !args.contains(p))
                    .collect();
                let (count, rtype, runit, rfields) = describe_returns(cmd.get("returns"));
                let empty = Value::Object(Default::default());
                let arg = cmd.get("arg").unwrap_or(&empty);
                let arg_values: Vec<String> = arg
                    .get("values")
                    .and_then(|v| v.as_array())
                    .map(|v| v.iter().filter_map(|x| x.as_str()).map(String::from).collect())
                    .unwrap_or_default();

                out.push(vec![
                    family.clone(),
                    model.clone(),
                    verb.to_uppercase(),
                    name.clone(),
                    str_field(cmd, "description"),
                    scpi.clone(),
                    str_field(cmd, "scpiFast"),
                    args.join("; "),
                    arg.get("kind").and_then(|k| k.as_str()).unwrap_or("").to_string(),
                    // An enum's options are the widget: a selector cannot be
                    // authored from the SCPI string alone.
                    arg_values.join("; "),
                    params.join("; "),
                    str_field(cmd, "group"),
                    str_field(cmd, "subsystem"),
                    count,
                    rtype,
                    runit,
                    rfields,
                    scpi.split(';').filter(|s| !s.trim().is_empty()).count().to_string(),
                    if cmd.get("unverified").and_then(|u| u.as_bool()) == Some(true) {
                        "yes".to_string()
                    } else {
                        String::new()
                    },
                    rel.clone(),
                ]);
            }
        }
    }
    // (Family, Model, Verb, Command)
    out.sort_by(|a, b| (&a[0], &a[1], &a[2], &a[3]).cmp(&(&b[0], &b[1], &b[2], &b[3])));
    out
}

fn write_csv(data: &[Row], path: &std::path::Path) -> Result<(), String> {
    // CRLF, matching the file already committed. Python's csv module defaults to
    // the "excel" dialect, which terminates rows with \r\n; writing bare \n here
    // would rewrite all 3600 lines on the first run and bury every real edit.
    let mut w = csv::WriterBuilder::new()
        .terminator(csv::Terminator::CRLF)
        .from_path(path)
        .map_err(|e| e.to_string())?;
    w.write_record(COLUMNS).map_err(|e| e.to_string())?;
    for row in data {
        w.write_record(row).map_err(|e| e.to_string())?;
    }
    w.flush().map_err(|e| e.to_string())
}

/// Same rows, frozen header and an autofilter.
fn write_xlsx(data: &[Row], path: &std::path::Path) -> Result<(), String> {
    use rust_xlsxwriter::{Format, Workbook};

    let mut wb = Workbook::new();
    let ws = wb.add_worksheet();
    ws.set_name("CommandList").map_err(|e| e.to_string())?;

    let bold = Format::new().set_bold();
    for (i, col) in COLUMNS.iter().enumerate() {
        ws.write_string_with_format(0, i as u16, *col, &bold)
            .map_err(|e| e.to_string())?;
    }
    for (r, row) in data.iter().enumerate() {
        for (c, cell) in row.iter().enumerate() {
            ws.write_string(r as u32 + 1, c as u16, cell)
                .map_err(|e| e.to_string())?;
        }
    }
    ws.set_freeze_panes(1, 0).map_err(|e| e.to_string())?;
    ws.autofilter(0, 0, data.len() as u32, COLUMNS.len() as u16 - 1)
        .map_err(|e| e.to_string())?;
    for (i, width) in WIDTHS.iter().enumerate() {
        ws.set_column_width(i as u16, *width).map_err(|e| e.to_string())?;
    }
    wb.save(path).map_err(|e| e.to_string())
}

fn summarize(data: &[Row]) {
    let models: BTreeSet<(&str, &str)> = data.iter().map(|r| (r[0].as_str(), r[1].as_str())).collect();
    println!("   ✅ {} commands from {} models", data.len(), models.len());
    for verb in ["SET", "RIG", "NAB", "DO"] {
        let n = data.iter().filter(|r| r[2] == verb).count();
        println!("      {verb:<4} {n:5}");
    }
    let unverified = data.iter().filter(|r| !r[18].is_empty()).count();
    println!(
        "      unverified {unverified} ({}%)",
        unverified * 100 / data.len().max(1)
    );

    // A placeholder that is neither an argument nor an instance param can never
    // be filled: fill_placeholders refuses the command and the control is dead.
    // Cheap to check here, invisible everywhere else.
    let stamped: BTreeSet<&str> = ["chan", "slot"].into_iter().collect();
    let orphans: Vec<&Row> = data
        .iter()
        .filter(|r| {
            !r[10].is_empty() && r[10].split("; ").any(|p| !stamped.contains(p))
        })
        .collect();
    if !orphans.is_empty() {
        println!(
            "   ⚠️  {} commands need instance params beyond <chan>/<slot> — nothing stamps those, so they cannot send:",
            orphans.len()
        );
        for r in orphans.iter().take(10) {
            println!("      {}/{} {}: <{}>", r[0], r[1], r[3], r[10]);
        }
        if orphans.len() > 10 {
            println!("      … and {} more", orphans.len() - 10);
        }
    }
}

pub fn run(check: bool) -> i32 {
    let Some(yak) = super::yak_root() else {
        println!("❌ YAK tree not found; set YAK_REPO_PATH");
        return 1;
    };
    let csv_path = yak.join("CommandList.csv");
    let xlsx_path = yak.join("CommandList.xlsx");
    let data = rows(&yak);

    if check {
        let Ok(mut rdr) = csv::Reader::from_path(&csv_path) else {
            println!("   ❌ no CommandList.csv — run without --check");
            return 1;
        };
        let current: Vec<Row> = rdr
            .records()
            .filter_map(|r| r.ok())
            .map(|r| r.iter().map(|s| s.to_string()).collect())
            .collect();
        if current == data {
            println!("   ✅ CommandList.csv is current ({} commands)", data.len());
            return 0;
        }
        println!(
            "   ❌ CommandList.csv is stale: sheet has {} rows, the tables have {}",
            current.len(),
            data.len()
        );
        return 1;
    }

    if let Err(e) = write_csv(&data, &csv_path) {
        println!("   ❌ could not write CommandList.csv: {e}");
        return 1;
    }
    let wrote_xlsx = match write_xlsx(&data, &xlsx_path) {
        Ok(()) => true,
        Err(e) => {
            // The CSV is the artifact that matters; the workbook is a convenience.
            println!("   ⚠️  could not write the workbook ({e}) — wrote the CSV only");
            false
        }
    };
    let root = super::repo_root(&yak);
    let show = |p: &std::path::Path| {
        p.strip_prefix(&root).unwrap_or(p).to_string_lossy().to_string()
    };
    println!(
        "   ✅ wrote {}{}",
        show(&csv_path),
        if wrote_xlsx {
            format!(" and {}", show(&xlsx_path))
        } else {
            String::new()
        }
    );
    summarize(&data);
    0
}

#[cfg(test)]
mod tests {
    use super::describe_returns;
    use serde_json::json;

    #[test]
    fn a_chained_query_keeps_its_reply_columns_parallel() {
        // One fields entry per value, so field n's type is the nth entry of
        // `Return type` — the columns are read row-wise as tuples.
        let r = json!({
            "count": 3,
            "fields": [
                {"name": "mode", "type": "string"},
                {"name": "volts", "type": "float", "unit": "V"},
                {"name": "amps", "type": "float", "unit": "A"}
            ]
        });
        let (count, types, units, names) = describe_returns(Some(&r));
        assert_eq!(count, "3");
        assert_eq!(types, "string; float; float");
        assert_eq!(units, "; V; A");
        assert_eq!(names, "mode; volts; amps");
    }

    #[test]
    fn a_field_with_no_type_reads_as_unknown_not_blank() {
        // "unknown" and "the reply carries no unit" are different facts, and a
        // blank cannot say which.
        let r = json!({"count": 1, "fields": [{"name": "x"}]});
        let (_, types, units, _) = describe_returns(Some(&r));
        assert_eq!(types, "?");
        assert_eq!(units, "");
    }

    #[test]
    fn no_returns_block_gives_four_empty_columns() {
        assert_eq!(
            describe_returns(None),
            (String::new(), String::new(), String::new(), String::new())
        );
    }
}
