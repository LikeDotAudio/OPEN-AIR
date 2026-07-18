//! Boundary time conversions — twin of `contracts/src/time.ts`, pinned by
//! `vectors/identity.json`. ISO-8601 UTC with milliseconds, byte-identical
//! to JavaScript's `Date.toISOString()`. No chrono — the crate rule is
//! serde + serde_json only, and this is 30 lines of civil-calendar math.

/// Unix seconds (int or float, as v40 emits) → `YYYY-MM-DDTHH:MM:SS.mmmZ`.
pub fn from_unix_seconds(seconds: f64) -> String {
    iso_from_unix_ms((seconds * 1000.0).round() as i64)
}

pub fn iso_from_unix_ms(ms: i64) -> String {
    let days = ms.div_euclid(86_400_000);
    let rem = ms.rem_euclid(86_400_000);
    let (y, m, d) = civil_from_days(days);
    let msec = rem % 1000;
    let sec = (rem / 1000) % 60;
    let min = (rem / 60_000) % 60;
    let hour = rem / 3_600_000;
    format!("{y:04}-{m:02}-{d:02}T{hour:02}:{min:02}:{sec:02}.{msec:03}Z")
}

/// Days since 1970-01-01 → (year, month, day). Howard Hinnant's algorithm.
fn civil_from_days(z: i64) -> (i64, u32, u32) {
    let z = z + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32;
    let m = (if mp < 10 { mp + 3 } else { mp - 9 }) as u32;
    (if m <= 2 { y + 1 } else { y }, m, d)
}
