use std::path::Path;

/// Read the ACID chunk (embedded loop metadata) if present: (bpm, root_note).
/// bpm = 0 and root_note = -1 when absent. Walks the RIFF chunk list without
/// loading the whole file.
pub fn read_acid(path: &Path) -> (f64, i32) {
    use std::io::{Read, Seek, SeekFrom};
    let none = (0.0, -1);
    let mut f = match std::fs::File::open(path) {
        Ok(f) => f,
        Err(_) => return none,
    };
    let mut hdr = [0u8; 12];
    if f.read_exact(&mut hdr).is_err() {
        return none;
    }
    if &hdr[0..4] != b"RIFF" || &hdr[8..12] != b"WAVE" {
        return none;
    }
    loop {
        let mut ch = [0u8; 8];
        if f.read_exact(&mut ch).is_err() {
            break;
        }
        let size = u32::from_le_bytes([ch[4], ch[5], ch[6], ch[7]]) as u64;
        if &ch[0..4] == b"acid" {
            let mut buf = vec![0u8; size.min(64) as usize];
            if f.read_exact(&mut buf).is_err() || buf.len() < 24 {
                break;
            }
            let flags = u32::from_le_bytes([buf[0], buf[1], buf[2], buf[3]]);
            let root = u16::from_le_bytes([buf[4], buf[5]]) as i32;
            let tempo = f32::from_le_bytes([buf[20], buf[21], buf[22], buf[23]]) as f64;
            let root_out = if flags & 0x2 != 0 { root } else { -1 };
            let bpm = if tempo.is_finite() && tempo > 0.0 && tempo < 400.0 { tempo } else { 0.0 };
            return (bpm, root_out);
        }
        // Skip this chunk's data (chunks are word-aligned).
        let skip = size + (size & 1);
        if f.seek(SeekFrom::Current(skip as i64)).is_err() {
            break;
        }
    }
    none
}
