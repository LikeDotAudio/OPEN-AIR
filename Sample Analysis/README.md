# Sample Analysis

A self-contained audio-sample analyzer and file-management tool.

```
Sample Analysis/
├── run.sh                 # launcher: builds the Rust core if needed, opens the GUI
├── sample_analyzer_app.py # Python GUI (tabs below)
└── sample_analyzer_rs/    # Rust DSP core (fast, parallel)
    └── target/release/oa_sample_analyzer   # built binary
```

## Run

```bash
./run.sh
```

or directly:

```bash
python3 sample_analyzer_app.py
```

Requires: Python 3 with `numpy` + `matplotlib` (Tk backend), a Rust toolchain
(`cargo`) for the first build, and an audio player for previews
(`paplay`/`aplay`/`ffplay` on Linux, built-in on macOS/Windows).

## What it does

The Rust core walks a folder of WAV files across 30 threads and, per file,
extracts: length, pitch, harmonicity, spectral centroid / roll-off / flatness /
spread, low/mid/high band energy, RMS, crest, zero-crossing rate, attack time,
transient count, sample-rate / bit-depth / channels, and embedded ACID BPM +
root note. It then classifies each file by name (tolerant of abbreviations),
by feature-derived timbre, and by blind **K-Means** clustering. All measurements
are written as JSON to `sample_cloud_data.PEAK` **in the analyzed folder**, beside
the samples.

## Tabs

- **3D Cloud** — live interactive cloud (pitch × name-group depth × complexity,
  size = length). Scroll to zoom, Top/Front/Side/Iso views, drag to orbit.
  Show/hide any group; isolate a single group to remap its Y axis to any feature.
  Click a point to inspect its full record and play the sample.
- **Groups / CSV** — every group (by Name / Timbre / Cluster) with each file and
  the reason it's in the group; export to CSV.
- **PEAK Examiner** — open any `.PEAK` file, filter/search records, view full JSON.
- **Flatten / Rename** — batch-rename by folding the folder path into the file
  name (`A/B/C/D.wav` → `A-B-C-D.wav`), optionally flattening into one folder.
