/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaLogging/Core/oaAsyncSink_rs/mod.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260413.1400.1
//
// Description: High-performance asynchronous logging sink. Offloads 
// blocking I/O operations to a dedicated background thread using 
// crossbeam channels to ensure zero-latency log ingestion.

use pyo3::prelude::*;
use crossbeam_channel::{unbounded, Sender, Receiver};
use std::fs::OpenOptions;
use std::io::Write;
use std::thread;
use std::sync::Arc;
use once_cell::sync::Lazy;
use std::sync::Mutex;

struct LogMessage {
    file_path: String,
    content: String,
}

static LOG_CHANNEL: Lazy<(Sender<LogMessage>, Receiver<LogMessage>)> = Lazy::new(|| unbounded());

#[pyclass]
struct AsyncSink;

#[pymethods]
impl AsyncSink {
    #[new]
    fn new() -> Self {
        static START: Lazy<bool> = Lazy::new(|| {
            let receiver = LOG_CHANNEL.1.clone();
            thread::spawn(move || {
                while let Ok(message) = receiver.recv() {
                    if let Ok(mut file) = OpenOptions::new()
                        .create(true)
                        .append(true)
                        .open(&message.file_path) {
                        let _ = file.write_all(message.content.as_bytes());
                    }
                }
            });
            true
        });
        Lazy::force(&START);
        AsyncSink
    }

    fn write(&self, file_path: String, content: String) -> PyResult<()> {
        let _ = LOG_CHANNEL.0.send(LogMessage { file_path, content });
        Ok(())
    }
}

#[pymodule]
// Inline comment: Logic for oaasyncsink_rs
pub fn oaasyncsink_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<AsyncSink>()?;
    Ok(())
}
