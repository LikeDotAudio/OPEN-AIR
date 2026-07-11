//! The per-file analysis record: streamed to the GUI (one JSON line each) and
//! written to the aggregate `sample_cloud_data.PEAK` / per-file sidecars.
use serde::Serialize;

#[derive(Serialize, Clone)]
pub struct Peak {
    pub name: String,   // file name
    pub folder: String, // sub-folder relative to the scanned root ("" = root)
    pub sub: String,    // alias of `folder` (SoundCloud view compatibility)
    pub path: String,   // absolute path
    pub group: String,        // path-derived category (Kick, Snare, Perc, Keyboards, DJ, … Unclassified) — or "Loops/Patterns" if >1 transient
    pub reason: String,       // why it's in `group` (matched keyword, or the loop rule)
    pub timbre: String,       // feature-derived class (Percussive/Tonal/Noise/Bass/Bright/Loop/Pad)
    pub length_class: String, // one-shot length tier: Short / Medium / Long (or "Loop")
    pub subgroup: String,     // curated instrument level (Perc→Conga, Keyboards→Synth), a "Drum" audit tag, or "group + length tier"
    pub audit: bool,          // generic "drum" tag, no specific type — flag for acoustic audit

    // --- time / envelope ---
    pub length: f64,       // seconds
    pub transients: usize, // onset count; >1 ⇒ a loop rather than a one-shot sample
    pub attack: f64,       // seconds from start to peak amplitude (small ⇒ percussive)
    pub rms: f64,          // overall loudness (linear RMS)
    pub crest: f64,        // peak / rms (high ⇒ spiky/transient, low ⇒ sustained)
    pub zcr: f64,          // zero-crossings per second (high ⇒ noisy/bright)

    // --- pitch / harmonicity ---
    pub pitch: f64,        // Hz (autocorrelation)
    pub harmonicity: f64,  // 0 = atonal/noise … 1 = strongly pitched
    pub sustain: f64,      // fraction of the file held above 50% of peak level
    pub sustained: bool,   // a single fundamental note sustained the whole file

    // --- spectrum ---
    pub complexity: f64,   // spectral spread (timbral richness)
    pub centroid: f64,     // spectral centroid Hz (brightness)
    pub rolloff: f64,      // 85%-energy roll-off Hz
    pub flatness: f64,     // spectral flatness 0 = tonal … 1 = noise-like
    pub low: f64,          // fraction of energy < 200 Hz
    pub mid: f64,          // fraction 200 Hz – 2 kHz
    pub high: f64,         // fraction > 2 kHz

    // --- raw file attributes ---
    pub sample_rate: u32,
    pub bit_depth: u16,
    pub channels: u16,

    // --- musical ROOT (note / key), FFT-derived (ACID takes precedence) ---
    pub root: String,      // note name, e.g. "A3" ("" if unpitched/none)
    pub root_hz: f64,      // detected fundamental Hz (0 if none)
    pub root_cents: f64,   // cents off the equal-tempered note (−50..+50)

    // --- embedded metadata (ACID chunk, when present) ---
    pub bpm: f64,          // 0 if none
    pub root_note: i32,    // MIDI root note, -1 if none

    // --- unsupervised grouping (assigned after all files are analyzed) ---
    pub cluster: i32,      // K-Means cluster id, -1 until clustered
}
