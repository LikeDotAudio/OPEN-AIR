/// Normalize a file name into space-separated tokens for name matching:
/// lower-cased, every non-alphanumeric run becomes a space, and letter↔digit
/// boundaries are split (so "Tom2" → "tom 2", "OH_01" → "oh 01").
pub fn normalize_name(name: &str) -> String {
    let lower = name.to_lowercase();
    let mut out = String::with_capacity(lower.len() + 8);
    let mut prev = 0u8; // 0 = sep, 1 = alpha, 2 = digit
    for c in lower.chars() {
        let kind = if c.is_ascii_alphabetic() { 1 } else if c.is_ascii_digit() { 2 } else { 0 };
        if kind == 0 {
            if !out.ends_with(' ') {
                out.push(' ');
            }
        } else {
            if prev != 0 && prev != kind {
                out.push(' ');
            }
            out.push(c);
        }
        prev = kind;
    }
    out
}
