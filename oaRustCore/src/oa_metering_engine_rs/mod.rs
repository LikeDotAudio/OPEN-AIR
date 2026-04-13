// oaGuiElements/Core/metering/oaMeteringEngine-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.1700.1

use pyo3::prelude::*;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Clone, Copy, Debug, PartialEq)]
enum MeterState {
    Idle,
    Tracking,
    Holding,
    Decaying,
}

#[pyclass]
struct BallisticsEngine {
    // Config values (cached for performance)
    min_val: f64,
    max_val: f64,
    hold_time: f64,
    dwell_time: f64,
    attack_ms: f64,
    release_ms: f64,
    fall_time: f64,
    peak_display: bool,
    peak_hold_time: f64,
    peak_display_fall_time: f64,
    show_peak_hold: bool,
    upper_range: f64,
    overload_fade_time: f64,

    // Runtime state
    current_value: f64,
    target_value: f64,
    peak_value: f64,
    state: MeterState,
    hold_start_time: f64,
    peak_hold_start_time: f64,
    overload_expiry: f64,
    overload_fade_factor: f64,
    is_running: bool,
}

#[pymethods]
impl BallisticsEngine {
    #[new]
    fn new(config: &Bound<'_, PyAny>) -> PyResult<Self> {
        let min_val: f64 = config.getattr("min_val")?.extract()?;
        let max_val: f64 = config.getattr("max_val")?.extract()?;
        let value_default: f64 = config.getattr("value_default")?.extract()?;
        
        Ok(BallisticsEngine {
            min_val,
            max_val,
            hold_time: config.getattr("hold_time")?.extract()?,
            dwell_time: config.getattr("dwell_time")?.extract()?,
            attack_ms: config.getattr("attack_ms")?.extract()?,
            release_ms: config.getattr("release_ms")?.extract()?,
            fall_time: config.getattr("fall_time")?.extract()?,
            peak_display: config.getattr("peak_display")?.extract()?,
            peak_hold_time: config.getattr("peak_hold_time")?.extract()?,
            peak_display_fall_time: config.getattr("peak_display_fall_time")?.extract()?,
            show_peak_hold: config.getattr("show_peak_hold")?.extract()?,
            upper_range: config.getattr("upper_range")?.extract()?,
            overload_fade_time: config.getattr("overload_fade_time")?.extract()?,

            current_value: value_default,
            target_value: value_default,
            peak_value: value_default,
            state: MeterState::Idle,
            hold_start_time: 0.0,
            peak_hold_start_time: 0.0,
            overload_expiry: 0.0,
            overload_fade_factor: 0.0,
            is_running: false,
        })
    }

    fn set_target(&mut self, value: f64) {
        self.target_value = value;
        self.state = MeterState::Tracking;
        self.is_running = true;
    }

    fn update(&mut self, dt_ms: f64) -> PyResult<(f64, f64, f64, bool, bool)> {
        let now_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs_f64() * 1000.0;
        
        let mut full_range = self.max_val - self.min_val;
        if full_range <= 0.0 { full_range = 1.0; }

        // 1. State Transitions & Target Selection
        if self.state == MeterState::Holding {
            let hold_dur = self.hold_time.max(self.dwell_time);
            if now_ms - self.hold_start_time >= hold_dur {
                self.state = MeterState::Decaying;
            }
        }

        let effective_target = match self.state {
            MeterState::Tracking => self.target_value,
            MeterState::Decaying => self.min_val,
            _ => self.current_value,
        };

        // 2. Main Bar Movement
        let diff = effective_target - self.current_value;
        let epsilon = full_range * 0.001;
        let mut reached_min = false;

        if diff.abs() < epsilon {
            self.current_value = effective_target;
            match self.state {
                MeterState::Tracking => {
                    self.state = MeterState::Holding;
                    self.hold_start_time = now_ms;
                }
                MeterState::Decaying => {
                    self.state = MeterState::Idle;
                    reached_min = true;
                }
                _ => {}
            }
        } else {
            let time_param = if diff > 0.0 {
                self.attack_ms
            } else if self.state == MeterState::Tracking {
                self.release_ms
            } else {
                self.fall_time
            };

            if time_param <= 0.0 {
                self.current_value = effective_target;
            } else {
                let step = (full_range / time_param) * dt_ms;
                if diff > 0.0 {
                    self.current_value = (self.current_value + step).min(effective_target);
                } else {
                    self.current_value = (self.current_value - step).max(effective_target);
                }
            }
        }

        // 3. Floating Peak Line
        if self.peak_display {
            if self.current_value > self.peak_value {
                self.peak_value = self.current_value;
                self.peak_hold_start_time = now_ms;
            } else {
                if now_ms - self.peak_hold_start_time >= self.peak_hold_time {
                    if self.peak_display_fall_time > 0.0 {
                        let p_step = (full_range / self.peak_display_fall_time) * dt_ms;
                        self.peak_value = (self.peak_value - p_step).max(self.min_val);
                    } else {
                        self.peak_value = self.current_value;
                    }
                }
            }
        }

        // 4. Overload LED
        if self.show_peak_hold {
            if self.current_value >= self.upper_range {
                self.overload_expiry = now_ms + self.peak_hold_time;
                self.overload_fade_factor = 1.0;
            } else if now_ms < self.overload_expiry {
                self.overload_fade_factor = 1.0;
            } else if now_ms < self.overload_expiry + self.overload_fade_time {
                if self.overload_fade_time > 0.0 {
                    let elapsed_fade = now_ms - self.overload_expiry;
                    self.overload_fade_factor = (1.0 - (elapsed_fade / self.overload_fade_time)).max(0.0);
                }
            } else {
                self.overload_fade_factor = 0.0;
            }
        }

        // 5. Activity Check
        let mut is_active = self.state != MeterState::Idle;
        if self.peak_display && (self.peak_value > self.current_value + epsilon) {
            is_active = true;
        }
        if self.overload_fade_factor > 0.0 {
            is_active = true;
        }

        self.is_running = is_active;
        Ok((self.current_value, self.peak_value, self.overload_fade_factor, self.is_running, reached_min))
    }

    #[getter]
    fn current_value(&self) -> f64 { self.current_value }

    #[getter]
    fn peak_value(&self) -> f64 { self.peak_value }

    #[getter]
    fn overload_fade_factor(&self) -> f64 { self.overload_fade_factor }
}

#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pymodule]
pub fn oameteringengine_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<BallisticsEngine>()?;
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
