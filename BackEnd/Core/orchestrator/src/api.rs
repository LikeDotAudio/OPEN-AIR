/**
 * Header: api.rs
 * Purpose: api.rs implementation.
 * Description: Logic and implementation for api.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use axum::{
    extract::{Query, State},
    response::{IntoResponse, Json},
    routing::{get, post},
    Router, http::StatusCode,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::fs;
use std::path::{Path, PathBuf};
use ini::Ini;
use std::collections::HashSet;
use walkdir::WalkDir;

#[derive(Clone)]
pub struct ApiState {
    pub root_dir: PathBuf,
}

// Inline comment: Logic for router
pub fn router(state: ApiState) -> Router {
    Router::new()
        .route("/tree", get(get_tree))
        .route("/grabbag", get(get_grabbag))
        .route("/config", get(get_config))
        .route("/save", post(save_file))
        .with_state(state)
}

// Inline comment: Logic for get_directory_tree
fn get_directory_tree(path: &Path, base_path: &Path) -> Value {
    let name = path.file_name().unwrap_or_default().to_string_lossy().to_string();
    let mut children = Vec::new();
    
    if let Ok(entries) = fs::read_dir(path) {
        let mut entries: Vec<_> = entries.flatten().collect();
        entries.sort_by_key(|e| e.file_name());
        
        for entry in entries {
            let file_name = entry.file_name().to_string_lossy().to_string();
            if file_name.starts_with('.') || file_name.starts_with("__") {
                continue;
            }
            let full_path = entry.path();
            if full_path.is_dir() {
                children.push(get_directory_tree(&full_path, base_path));
            } else if file_name.ends_with(".json") {
                let content = fs::read_to_string(&full_path)
                    .and_then(|s| serde_json::from_str::<Value>(&s).map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e)))
                    .unwrap_or_else(|e| json!({"error": format!("Could not parse JSON: {}", e)}));
                
                let rel_path = full_path.strip_prefix(base_path).unwrap_or(&full_path).to_string_lossy().to_string();
                let rel_path_str = if !rel_path.starts_with('/') {
                    format!("/{}", rel_path)
                } else {
                    rel_path
                };
                
                children.push(json!({
                    "name": file_name,
                    "type": "file",
                    "content": content,
                    "path": rel_path_str
                }));
            }
        }
    }
    
    json!({
        "name": name,
        "type": "directory",
        "children": children
    })
}

// Inline comment: Logic for get_tree
async fn get_tree(State(state): State<ApiState>) -> impl IntoResponse {
    Json(build_tree(&state.root_dir))
}

/// The panel tree as `/api/tree` serves it.
pub fn build_tree(root: &Path) -> Value {
    let gui_frames = root.join("FrontEnd").join("Gui_Frames");
    get_directory_tree(&gui_frames, &gui_frames)
}

#[derive(Deserialize)]
struct ConfigQuery {
    proto: Option<String>,
}

// Inline comment: Logic for get_config
async fn get_config(State(state): State<ApiState>, Query(query): Query<ConfigQuery>) -> impl IntoResponse {
    if let Some(proto) = query.proto {
        if !proto.chars().all(|c| c.is_ascii_alphanumeric()) {
            return (StatusCode::BAD_REQUEST, Json(json!({"ok": false, "error": "Invalid protocol"})));
        }
        let ini_path = state.root_dir.join("BackEnd").join("ComProtocols").join(format!("openair-{}", proto.to_lowercase())).join("config.ini");
        if let Ok(conf) = Ini::load_from_file(&ini_path) {
            let mut config_map = serde_json::Map::new();
            for (sec, prop) in conf.iter() {
                let sec_name = sec.as_deref().unwrap_or("").to_string();
                let mut prop_map = serde_json::Map::new();
                for (k, v) in prop.iter() {
                    prop_map.insert(k.to_string(), json!(v));
                }
                config_map.insert(sec_name, json!(prop_map));
            }
            let rel = ini_path.strip_prefix(&state.root_dir).unwrap_or(&ini_path).to_string_lossy().to_string();
            return (StatusCode::OK, Json(json!({
                "ok": true,
                "proto": proto,
                "path": rel,
                "config": config_map
            })));
        }
        (StatusCode::NOT_FOUND, Json(json!({"ok": false, "error": "Not found"})))
    } else {
        (StatusCode::BAD_REQUEST, Json(json!({"ok": false, "error": "Missing proto param"})))
    }
}

#[derive(Deserialize)]
struct SavePayload {
    path: String,
    content: Value,
}

// Inline comment: Logic for strip_volatile
fn strip_volatile(val: &mut Value) {
    match val {
        Value::Object(map) => {
            map.remove("current_value");
            for v in map.values_mut() {
                strip_volatile(v);
            }
        }
        Value::Array(arr) => {
            for v in arr {
                strip_volatile(v);
            }
        }
        _ => {}
    }
}

// Inline comment: Logic for save_file
/// Resolve a caller-supplied relative path to an absolute path that is provably
/// inside `base`, or return `None`.
///
/// SECURITY: the previous implementation used `abs.starts_with(&base)` on an
/// **unnormalised** path. `Path::starts_with` compares path *components* and does
/// not resolve `..`, so `base/../../../tmp/x.json` literally begins with the
/// components of `base` and passed the check — the OS then resolved `..` at write
/// time and the file landed outside the tree. That made `POST /api/save` an
/// arbitrary-file-write. Verified by execution before this fix.
///
/// The rules now are structural rather than textual:
///   1. reject absolute paths and Windows-style prefixes outright,
///   2. reject any `..` component *before* touching the filesystem — no symlink
///      or TOCTOU trick can reintroduce it,
///   3. canonicalise the resolved **parent** and require it to sit inside the
///      canonicalised base, which also defeats symlinks pointing outward.
///
/// The `.json` suffix check remains, but as a secondary filter — never as the
/// control that keeps writes inside the tree.
fn resolve_within(base: &Path, rel: &str) -> Option<PathBuf> {
    use std::path::Component;

    let candidate = Path::new(rel);

    // (1) + (2): only plain names are allowed. This rejects `/etc/x`, `C:\…`,
    // and every form of `..` — including one hidden mid-path like `a/../../b`.
    if !candidate.components().all(|c| matches!(c, Component::Normal(_))) {
        return None;
    }

    let base_real = base.canonicalize().ok()?;
    let abs = base_real.join(candidate);

    // (3) The file may not exist yet, so canonicalise the parent directory that
    // will contain it. A symlinked parent pointing outside the tree fails here.
    let parent_real = abs.parent()?.canonicalize().ok()?;
    if !parent_real.starts_with(&base_real) {
        return None;
    }

    Some(parent_real.join(abs.file_name()?))
}

async fn save_file(State(state): State<ApiState>, Json(mut payload): Json<SavePayload>) -> impl IntoResponse {
    let clean_rel = payload.path.trim_start_matches('/');
    let gui_frames_dir = state.root_dir.join("FrontEnd").join("Gui_Frames");

    let abs_path = match resolve_within(&gui_frames_dir, clean_rel) {
        Some(p) if p.to_string_lossy().ends_with(".json") => p,
        _ => {
            eprintln!("   🚫 [API] Rejected save path: {:?}", payload.path);
            return (StatusCode::FORBIDDEN, Json(json!({"ok": false, "error": "Path outside Gui_Frames"})));
        }
    };

    let mut backup_name = None;
    if abs_path.exists() {
        let ts = chrono::Local::now().format("%Y%m%d_%H%M%S");
        let name = abs_path.file_name().unwrap().to_string_lossy();
        let backup_path = abs_path.with_file_name(format!("{}_{}.old", ts, name));
        if let Ok(_) = fs::copy(&abs_path, &backup_path) {
            backup_name = Some(backup_path.file_name().unwrap().to_string_lossy().to_string());
        }
    }
    
    strip_volatile(&mut payload.content);
    
    if let Ok(_) = fs::write(&abs_path, serde_json::to_string_pretty(&payload.content).unwrap()) {
        (StatusCode::OK, Json(json!({"ok": true, "saved": payload.path, "backup": backup_name})))
    } else {
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"ok": false, "error": "Write failed"})))
    }
}

// Inline comment: Logic for extract_readme_json
fn extract_readme_json(text: &str) -> Option<Value> {
    let re = regex::Regex::new(r"(?s)```json\s*\n(.*?)\n```").ok()?;
    if let Some(caps) = re.captures(text) {
        let json_str = caps.get(1)?.as_str();
        match serde_json::from_str(json_str) {
            Ok(val) => Some(val),
            Err(e) => {
                println!("Failed to parse JSON: {}", e);
                None
            }
        }
    } else {
        println!("Regex didn't match.");
        None
    }
}

// Inline comment: Logic for add_components
fn add_components(content: &Value, category: &str, relpath: &str, components: &mut Vec<Value>, legends: &mut serde_json::Map<String, Value>, seen: &mut HashSet<String>) {
    if let Value::Object(map) = content {
        for (key, schema) in map {
            if key == "_LEGEND" {
                if let Value::Object(lmap) = schema {
                    for (lk, lv) in lmap {
                        if let Value::Array(arr) = lv {
                            let bucket = legends.entry(lk.clone()).or_insert(json!([])).as_array_mut().unwrap();
                            for item in arr {
                                if !bucket.contains(item) {
                                    bucket.push(item.clone());
                                }
                            }
                        }
                    }
                }
                continue;
            }
            if key == "_README" {
                continue;
            }
            if let Value::Object(smap) = schema {
                if !smap.contains_key("type") { continue; }
                if seen.contains(key) { continue; }
                seen.insert(key.clone());
                
                components.push(json!({
                    "name": key,
                    "category": category,
                    "type": smap.get("type").unwrap_or(&json!("unknown")),
                    "schema": schema,
                    "path": relpath
                }));
            }
        }
    }
}

// Inline comment: Logic for get_grabbag
async fn get_grabbag(State(state): State<ApiState>) -> impl IntoResponse {
    Json(build_grabbag(&state.root_dir))
}

/// The widget grab-bag as `/api/grabbag` serves it.
pub fn build_grabbag(root: &Path) -> Value {
    let frontend = root.join("FrontEnd");
    let mut components = Vec::new();
    let mut legends = serde_json::Map::new();
    let mut seen = HashSet::new();
    
    // 1. libControl
    let lib_root = frontend.join("libControl");
    for entry in WalkDir::new(&lib_root).into_iter().filter_map(|e| e.ok()) {
        if entry.file_name().to_string_lossy().to_lowercase() == "readme.md" {
            if let Ok(text) = fs::read_to_string(entry.path()) {
                if let Some(content) = extract_readme_json(&text) {
                    let rel = entry.path().strip_prefix(&lib_root).unwrap();
                    let mut parts = rel.iter().map(|p| p.to_string_lossy().to_string()).collect::<Vec<_>>();
                    parts.pop();
                    let category = if parts.len() > 0 { parts[0].clone() } else { "structure".to_string() };
                    let path_str = entry.path().strip_prefix(&frontend).unwrap().to_string_lossy().to_string();
                    add_components(&content, &category, &path_str, &mut components, &mut legends, &mut seen);
                }
            }
        }
    }
    
    // 2. oaGuiElements
    let oag_root = frontend.join("..").join("oaGuiElements");
    if oag_root.exists() {
        for entry in WalkDir::new(&oag_root).into_iter().filter_map(|e| e.ok()) {
            if entry.file_name() == "sample.json" {
                if let Ok(text) = fs::read_to_string(entry.path()) {
                    if let Ok(content) = serde_json::from_str(&text) {
                        let rel = entry.path().strip_prefix(&oag_root).unwrap();
                        let mut parts = rel.iter().map(|p| p.to_string_lossy().to_string()).collect::<Vec<_>>();
                        parts.pop();
                        let meaningful: Vec<_> = parts.into_iter().filter(|p| p != "Core" && p != "Assets" && p != ".").collect();
                        let category = if !meaningful.is_empty() { meaningful[0].clone() } else { "General".to_string() };
                        let path_str = entry.path().strip_prefix(&oag_root).unwrap().to_string_lossy().to_string();
                        add_components(&content, &category, &path_str, &mut components, &mut legends, &mut seen);
                    }
                }
            }
        }
    }
    
    components.sort_by(|a, b| {
        let cat_a = a["category"].as_str().unwrap_or("").to_lowercase();
        let cat_b = b["category"].as_str().unwrap_or("").to_lowercase();
        match cat_a.cmp(&cat_b) {
            std::cmp::Ordering::Equal => {
                let name_a = a["name"].as_str().unwrap_or("").to_lowercase();
                let name_b = b["name"].as_str().unwrap_or("").to_lowercase();
                name_a.cmp(&name_b)
            },
            other => other,
        }
    });
    
    json!({
        "components": components,
        "legends": legends
    })
}

/// Write the static fallbacks the browser uses when the orchestrator is not
/// answering: `FrontEnd/api/tree.json` and `FrontEnd/api/grabbag`.
///
/// `index.html` fetches the live endpoints first and falls back to these, so a
/// snapshot that drifts is a UI that renders yesterday's panels with no error.
/// Regenerated on every panel build for exactly that reason — the Python script
/// this replaces had to be remembered and run by hand.
///
/// Compact separators, matching what is committed: this is a 2.5 MB file, and
/// pretty-printing it would triple the size of every diff that touches a panel.
pub fn write_static_snapshots(root: &Path) {
    let api_dir = root.join("FrontEnd").join("api");
    if let Err(e) = fs::create_dir_all(&api_dir) {
        println!("⚠️  [API] could not create {}: {e}", api_dir.display());
        return;
    }
    for (name, value) in [
        ("tree.json", build_tree(root)),
        ("grabbag", build_grabbag(root)),
    ] {
        match serde_json::to_string(&value) {
            Ok(body) => {
                if let Err(e) = fs::write(api_dir.join(name), ascii_escaped(&body)) {
                    println!("⚠️  [API] could not write {name}: {e}");
                }
            }
            Err(e) => println!("⚠️  [API] could not serialize {name}: {e}"),
        }
    }
}

/// Escape every non-ASCII character as `\uXXXX`, matching the escape convention
/// of the committed snapshots (Python's `json.dump` defaults to
/// `ensure_ascii=True`).
///
/// Cosmetic to any parser, and kept only so the artifact stays in the format it
/// has always had — greppable as ASCII, and diffable against older copies.
///
/// This does NOT make the output byte-identical to the Python's: serde_json
/// renders float exponents as `1e-6` where Python writes `1e-06`. Normalising
/// that would mean a blanket rewrite over 2.5 MB of embedded panel content to
/// fix a difference no consumer can observe, so it is left alone. The documents
/// are verified equal by parsing, not by comparing bytes.
///
/// Safe as a post-pass because JSON's structural characters are all ASCII, so
/// anything non-ASCII is necessarily inside a string literal.
fn ascii_escaped(json: &str) -> String {
    let mut out = String::with_capacity(json.len());
    for c in json.chars() {
        if c.is_ascii() {
            out.push(c);
        } else if (c as u32) <= 0xFFFF {
            out.push_str(&format!("\\u{:04x}", c as u32));
        } else {
            // Outside the BMP: Python emits a surrogate pair.
            let v = c as u32 - 0x1_0000;
            out.push_str(&format!(
                "\\u{:04x}\\u{:04x}",
                0xD800 + (v >> 10),
                0xDC00 + (v & 0x3FF)
            ));
        }
    }
    out
}

#[cfg(test)]
mod path_safety_tests {
    use super::resolve_within;
    use std::fs;

    /// Build a throwaway `base/` with a real subdirectory, plus a sibling
    /// `outside/` that traversal payloads try to reach.
    fn fixture(tag: &str) -> std::path::PathBuf {
        let root = std::env::temp_dir().join(format!("openair_path_test_{tag}"));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(root.join("base/sub")).unwrap();
        fs::create_dir_all(root.join("outside")).unwrap();
        root
    }

    #[test]
    fn accepts_paths_inside_the_tree() {
        let root = fixture("ok");
        let base = root.join("base");
        assert!(resolve_within(&base, "panel.json").is_some());
        assert!(resolve_within(&base, "sub/panel.json").is_some());
    }

    /// The regression this guard exists for. Every payload here passed the old
    /// `starts_with` check and wrote outside the tree.
    #[test]
    fn rejects_traversal() {
        let root = fixture("traversal");
        let base = root.join("base");
        for evil in [
            "../outside/pwned.json",
            "../../outside/pwned.json",
            "sub/../../outside/pwned.json",
            "./../outside/pwned.json",
            "sub/../sub/../../outside/pwned.json",
        ] {
            assert!(
                resolve_within(&base, evil).is_none(),
                "traversal payload was accepted: {evil}"
            );
        }
    }

    #[test]
    fn rejects_absolute_paths() {
        let root = fixture("absolute");
        let base = root.join("base");
        assert!(resolve_within(&base, "/etc/passwd.json").is_none());
        assert!(resolve_within(&base, "/tmp/pwned.json").is_none());
    }

    /// A parent that symlinks out of the tree must fail even though the path
    /// contains no `..` — this is why the parent is canonicalised.
    #[cfg(unix)]
    #[test]
    fn rejects_symlinked_parent() {
        let root = fixture("symlink");
        let base = root.join("base");
        std::os::unix::fs::symlink(root.join("outside"), base.join("escape")).unwrap();
        assert!(resolve_within(&base, "escape/pwned.json").is_none());
    }
}
