//! Device identity derivation — guidelines D2, twin of
//! `contracts/src/identity.ts`, pinned by `vectors/identity.json`.
//! Priority: serial → protocol-native stable address → FNV-1a 64-bit hash of
//! `make|model|address`. Two agents deriving different IDs for one
//! instrument recreates the duplicate-34401A bug — so this is a contract.

/// FNV-1a 64-bit over UTF-8 bytes, lowercase hex (16 chars).
pub fn fnv1a64(input: &str) -> String {
    let mut hash: u64 = 0xcbf2_9ce4_8422_2325;
    for b in input.as_bytes() {
        hash ^= u64::from(*b);
        hash = hash.wrapping_mul(0x100_0000_01b3);
    }
    format!("{hash:016x}")
}

/// Replace anything outside the deviceId key charset with '-'.
/// NOTE: operates per Unicode scalar, matching the TS regex per-code-unit
/// behavior for all BMP input (vectors avoid astral-plane cases).
fn sanitize_key(value: &str) -> String {
    value
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || matches!(c, '.' | '_' | ':' | '-') {
                c
            } else {
                '-'
            }
        })
        .collect()
}

/// The D2 rule. Returns `{protocol}:{stableKey}`.
pub fn device_id_for(
    protocol: &str,
    serial: Option<&str>,
    address: Option<&str>,
    make: Option<&str>,
    model: Option<&str>,
) -> String {
    if let Some(s) = serial {
        let t = s.trim();
        if !t.is_empty() {
            return format!("{protocol}:{}", sanitize_key(t));
        }
    }
    if let Some(a) = address {
        let t = a.trim();
        if !t.is_empty() {
            return format!("{protocol}:{}", sanitize_key(t));
        }
    }
    let content = format!(
        "{}|{}|{}",
        make.unwrap_or(""),
        model.unwrap_or(""),
        address.unwrap_or("")
    );
    format!("{protocol}:{}", fnv1a64(&content))
}
