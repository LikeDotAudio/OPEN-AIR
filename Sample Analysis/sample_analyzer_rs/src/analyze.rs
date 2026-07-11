//! Analyze one WAV file into a `Peak` record. This orchestrates the individual
//! single-purpose feature extractors; each `let` is one well-scoped step.
use std::path::Path;

use crate::acid::read_acid;
use crate::amplitude::amplitude_features;
use crate::label::label_sample;
use crate::peak::Peak;
use crate::pitch::pitch_features;
use crate::root::{extract_root, midi_to_name};
use crate::spectrum::spectral_features;
use crate::sustain::sustain_ratio;
use crate::transients::count_transients;
use crate::wav::read_wav_mono;

pub fn analyze(path: &Path, root: &Path, max_len: f64) -> Option<Peak> {
    let (data, sr, bit_depth, channels) = read_wav_mono(path)?;
    let sr_f = sr as f64;
    let length = data.len() as f64 / sr_f;
    if length > max_len {
        return None; // skip long files
    }

    // Feature extraction — each helper does one thing.
    let amp = amplitude_features(&data, sr_f, length);
    let (pitch, harmonicity) = pitch_features(&data, sr_f);
    let spec = spectral_features(&data, sr_f)?; // None ⇒ too short to analyze
    let transients = count_transients(&data, sr);
    let sustain = sustain_ratio(&data, sr);
    let (bpm, root_note) = read_acid(path);

    // ROOT note (musical key). Prefer the embedded ACID root when present,
    // otherwise detect it from the spectrum (FFT + harmonic product spectrum).
    let fft_root = extract_root(&data, sr_f);
    let (root_name, root_hz, root_cents) = if root_note >= 0 {
        (midi_to_name(root_note), 0.0, 0.0)
    } else {
        (fft_root.note, fft_root.hz, fft_root.cents)
    };

    // Path → folder (relative to the scanned root).
    let name = path.file_name().and_then(|x| x.to_str()).unwrap_or("").to_string();
    let parent = path.parent().unwrap_or(root);
    let folder = parent
        .strip_prefix(root)
        .ok()
        .map(|p| p.to_string_lossy().replace('\\', "/"))
        .unwrap_or_default();

    // Taxonomy labels (group / subgroup / reason / timbre / length tier / audit).
    let l = label_sample(
        &folder, &name, length, transients, bpm, harmonicity, sustain,
        amp.attack, amp.crest, spec.centroid, spec.low, spec.high,
    );

    Some(Peak {
        name,
        folder: folder.clone(),
        sub: folder,
        path: path.to_string_lossy().to_string(),
        group: l.group,
        reason: l.reason,
        timbre: l.timbre,
        length_class: l.length_class,
        subgroup: l.subgroup,
        audit: l.audit,
        length,
        transients,
        attack: amp.attack,
        rms: amp.rms,
        crest: amp.crest,
        zcr: amp.zcr,
        pitch,
        harmonicity,
        sustain,
        sustained: l.sustained,
        complexity: spec.complexity,
        centroid: spec.centroid,
        rolloff: spec.rolloff,
        flatness: spec.flatness,
        low: spec.low,
        mid: spec.mid,
        high: spec.high,
        sample_rate: sr,
        bit_depth,
        channels,
        root: root_name,
        root_hz,
        root_cents,
        bpm,
        root_note,
        cluster: -1,
    })
}
