#!/usr/bin/env bash
# Self-contained launcher for the Sample Analyzer.
# Builds the Rust core if needed, then starts the Python GUI.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BIN="$HERE/sample_analyzer_rs/target/release/oa_sample_analyzer"
if [ ! -x "$BIN" ]; then
    echo "Building Rust analyzer core (first run)…"
    ( cd "$HERE/sample_analyzer_rs" && cargo build --release )
fi

exec python3 "$HERE/sample_analyzer_app.py" "$@"
