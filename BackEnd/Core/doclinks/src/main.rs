//! Fail if any Markdown file links to something that does not exist.
//!
//! Milestone 1 was credited "all internal links programmatically verified to
//! resolve." That check ran once, by hand, over README.md — and five links were
//! dead by the next day: two pointed at `Documents/Audits/2_Architecture_Diagrams.md`
//! when the file lives in `Documents/notes/`, and three broke when the executive
//! reviews moved into their own folder. A claim that is only true on the day it
//! is made is not a check. This is the check.
//!
//! ```text
//! openair-doclinks            # whole repo, from the working directory
//! openair-doclinks Documents  # a subtree
//! ```
//!
//! Exits 1 with a report if anything is dead.

use std::path::{Component, Path, PathBuf};

/// Directories that are not ours to police.
const SKIP_DIRS: [&str; 12] = [
    ".git",
    "node_modules",
    ".crawler",
    "target",
    "dist",
    "build",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "site-packages",
    ".cargo",
];

/// Vendored third-party sources. Their docs ship with dead links we did not
/// write and will not maintain; linting them would make the gate permanently red
/// and train everyone to ignore it. Matched against any path component.
const VENDORED: [&str; 4] = [
    "nmos-cpp-master",
    "nmos-testing-tool-master",
    "nmos-device-control-mock-main-master",
    "nmos-control-rusty-device-master",
];

/// Links we intentionally do not resolve on disk.
const EXTERNAL_PREFIXES: [&str; 6] = ["http://", "https://", "mailto:", "tel:", "#", "data:"];

fn is_external(target: &str) -> bool {
    EXTERNAL_PREFIXES.iter().any(|p| target.starts_with(p))
}

/// Every Markdown file under `root`, sorted, minus the trees we do not police.
fn markdown_files(root: &Path) -> Vec<PathBuf> {
    let mut out = Vec::new();
    let mut stack = vec![root.to_path_buf()];
    while let Some(dir) = stack.pop() {
        let Ok(entries) = std::fs::read_dir(&dir) else {
            continue;
        };
        for entry in entries.flatten() {
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().to_string();
            if path.is_dir() {
                if SKIP_DIRS.contains(&name.as_str()) || VENDORED.contains(&name.as_str()) {
                    continue;
                }
                stack.push(path);
            } else if name.ends_with(".md") {
                out.push(path);
            }
        }
    }
    out.sort();
    out
}

/// `[text](target)` — the target, minus any title and any `#fragment`.
///
/// Hand-rolled rather than a regex, to keep this crate dependency-free. Mirrors
/// `\[[^\]]*\]\(\s*([^)\s]+?)(?:\s+"[^"]*")?\s*\)`: no nested brackets in the
/// text, the target runs to the first space or `)`, and an optional quoted title
/// may follow it.
fn links_in(line: &str) -> Vec<String> {
    let chars: Vec<char> = line.chars().collect();
    let mut out = Vec::new();
    let mut i = 0;
    while i < chars.len() {
        if chars[i] != '[' {
            i += 1;
            continue;
        }
        // `[^\]]*\]` — the text runs to the first closing bracket.
        let Some(close) = (i + 1..chars.len()).find(|&j| chars[j] == ']') else {
            break;
        };
        if close + 1 >= chars.len() || chars[close + 1] != '(' {
            i += 1;
            continue;
        }
        let mut k = close + 2;
        while k < chars.len() && chars[k].is_whitespace() {
            k += 1;
        }
        let start = k;
        while k < chars.len() && chars[k] != ')' && !chars[k].is_whitespace() {
            k += 1;
        }
        if k == start {
            i += 1;
            continue;
        }
        let target: String = chars[start..k].iter().collect();
        // Optional `"title"` between the target and the closing paren.
        let mut p = k;
        while p < chars.len() && chars[p].is_whitespace() {
            p += 1;
        }
        if p < chars.len() && chars[p] == '"' {
            match (p + 1..chars.len()).find(|&j| chars[j] == '"') {
                Some(endq) => {
                    p = endq + 1;
                    while p < chars.len() && chars[p].is_whitespace() {
                        p += 1;
                    }
                }
                None => {
                    i += 1;
                    continue;
                }
            }
        }
        if p < chars.len() && chars[p] == ')' {
            out.push(target);
            i = p + 1;
        } else {
            i += 1;
        }
    }
    out
}

/// `%20` and friends: links are URL-encoded, paths are not.
fn percent_decode(s: &str) -> String {
    let bytes = s.as_bytes();
    let mut out: Vec<u8> = Vec::with_capacity(bytes.len());
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'%' && i + 2 < bytes.len() {
            let hex = std::str::from_utf8(&bytes[i + 1..i + 3]).ok();
            if let Some(v) = hex.and_then(|h| u8::from_str_radix(h, 16).ok()) {
                out.push(v);
                i += 3;
                continue;
            }
        }
        out.push(bytes[i]);
        i += 1;
    }
    String::from_utf8_lossy(&out).into_owned()
}

/// Normalise `..` and `.` without touching the filesystem.
///
/// `Path::canonicalize` cannot be used: it fails on paths that do not exist,
/// which is precisely the case being detected.
fn normalize(path: &Path) -> PathBuf {
    let mut out = PathBuf::new();
    for part in path.components() {
        match part {
            Component::ParentDir => {
                out.pop();
            }
            Component::CurDir => {}
            other => out.push(other.as_os_str()),
        }
    }
    out
}

fn check(files: &[PathBuf]) -> Vec<(PathBuf, usize, String)> {
    let mut dead = Vec::new();
    for md in files {
        let Ok(text) = std::fs::read_to_string(md) else {
            eprintln!("  ! could not read {}", md.display());
            continue;
        };
        let parent = md.parent().unwrap_or(Path::new("."));
        let mut in_fence = false;
        for (lineno, line) in text.lines().enumerate() {
            // Don't lint links inside fenced code blocks — they are examples.
            if line.trim_start().starts_with("```") {
                in_fence = !in_fence;
                continue;
            }
            if in_fence {
                continue;
            }
            for raw in links_in(line) {
                let target = raw.split('#').next().unwrap_or("").trim().to_string();
                if target.is_empty() || is_external(&target) {
                    continue;
                }
                let resolved = normalize(&parent.join(percent_decode(&target)));
                if !resolved.exists() {
                    dead.push((md.clone(), lineno + 1, target));
                }
            }
        }
    }
    dead
}

fn main() {
    let arg = std::env::args().nth(1);
    let root = match arg {
        Some(a) => PathBuf::from(a),
        None => std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")),
    };
    let root = root.canonicalize().unwrap_or(root);
    if !root.exists() {
        eprintln!("error: {} does not exist", root.display());
        std::process::exit(2);
    }

    let files = markdown_files(&root);
    let dead = check(&files);
    let cwd = std::env::current_dir().unwrap_or_default();

    if !dead.is_empty() {
        println!(
            "\n✗ {} dead link(s) across {} Markdown file(s):\n",
            dead.len(),
            files.len()
        );
        for (md, lineno, target) in &dead {
            let shown = md.strip_prefix(&cwd).unwrap_or(md);
            println!("  {}:{lineno}  ->  {target}", shown.display());
        }
        println!(
            "\nFix the path, or delete the link. If a file moved, search for other references to it before assuming this is the only one.\n"
        );
        std::process::exit(1);
    }

    println!(
        "✓ all internal Markdown links resolve ({} files checked)",
        files.len()
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn finds_the_target_and_ignores_the_title() {
        assert_eq!(links_in("see [docs](a/b.md)"), vec!["a/b.md"]);
        assert_eq!(links_in(r#"[x](a.md "a title")"#), vec!["a.md"]);
        assert_eq!(links_in("[a](one.md) and [b](two.md)"), vec!["one.md", "two.md"]);
        // An image is a link with a bang; the bracket scan finds it anyway.
        assert_eq!(links_in("![alt](img.png)"), vec!["img.png"]);
    }

    #[test]
    fn ignores_things_that_only_look_like_links() {
        assert!(links_in("a [bracketed] phrase").is_empty());
        assert!(links_in("[empty]()").is_empty());
        assert!(links_in("plain text").is_empty());
    }

    #[test]
    fn external_targets_are_never_resolved_on_disk() {
        for t in [
            "https://example.com",
            "http://example.com",
            "mailto:a@b.c",
            "#anchor",
            "data:x",
        ] {
            assert!(is_external(t), "{t} should be external");
        }
        assert!(!is_external("Documents/notes.md"));
    }

    #[test]
    fn percent_escapes_become_real_characters() {
        // Links are URL-encoded, the paths on disk are not.
        assert_eq!(percent_decode("2%20Plan%20of%20attack.md"), "2 Plan of attack.md");
        assert_eq!(percent_decode("plain.md"), "plain.md");
        // A stray percent is left alone rather than eating the next two chars.
        assert_eq!(percent_decode("100%.md"), "100%.md");
    }

    #[test]
    fn parent_segments_normalize_without_touching_the_disk() {
        // canonicalize() cannot be used here: it fails on the missing paths this
        // exists to find.
        assert_eq!(normalize(Path::new("a/b/../c.md")), PathBuf::from("a/c.md"));
        assert_eq!(normalize(Path::new("a/./b.md")), PathBuf::from("a/b.md"));
        assert_eq!(normalize(Path::new("a/b/../../c.md")), PathBuf::from("c.md"));
    }
}
