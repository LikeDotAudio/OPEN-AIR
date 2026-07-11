use std::path::Path;

/// Read a WAV as mono f32 samples. Returns (samples, sample_rate, bit_depth, channels).
pub fn read_wav_mono(path: &Path) -> Option<(Vec<f32>, u32, u16, u16)> {
    let mut reader = hound::WavReader::open(path).ok()?;
    let spec = reader.spec();
    let ch = spec.channels.max(1) as usize;
    let sr = spec.sample_rate;
    let bits = spec.bits_per_sample;

    let raw: Vec<f32> = match spec.sample_format {
        hound::SampleFormat::Float => reader.samples::<f32>().filter_map(|s| s.ok()).collect(),
        hound::SampleFormat::Int => {
            let div = match spec.bits_per_sample {
                8 => 128.0,
                16 => 32768.0,
                24 => 8_388_608.0,
                _ => 2_147_483_648.0,
            };
            reader.samples::<i32>().filter_map(|s| s.ok()).map(|s| s as f32 / div).collect()
        }
    };
    if raw.is_empty() {
        return None;
    }
    // Downmix to mono.
    let mono: Vec<f32> = if ch <= 1 {
        raw
    } else {
        raw.chunks(ch).map(|frame| frame.iter().copied().sum::<f32>() / ch as f32).collect()
    };
    Some((mono, sr, bits, ch as u16))
}
