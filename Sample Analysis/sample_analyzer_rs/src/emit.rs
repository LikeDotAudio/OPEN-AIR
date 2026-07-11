use std::io::Write;

/// Print one JSON value as a line on stdout and flush (so a GUI reading the
/// pipe sees progress immediately).
pub fn emit(v: &serde_json::Value) {
    println!("{}", v);
    let _ = std::io::stdout().flush();
}
