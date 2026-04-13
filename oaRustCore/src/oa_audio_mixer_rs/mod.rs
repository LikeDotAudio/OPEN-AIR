// oaAudioMixer/Core/oaAudioMixer_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.0010.1
//
// Description: Multi-platform Audio Mixer interface. Offloads volume control and
// device discovery to native Rust backends (CoreAudio, ALSA, WASAPI) to ensure
// nanosecond-latency during high-density SPLINKER interaction cycles.

use pyo3::prelude::*;
use pyo3::types::PyList;
use crate::oa_audio_mixer_rs::factory::get_os_manager;
use crate::oa_audio_mixer_rs::manager::AudioConnectionManager;

mod manager;
mod factory;

// Conditional compilation isolates platform-specific API complexities (WASAPI/ALSA/CoreAudio)
// from the unified Python-facing AudioMixer class.
#[cfg(target_os = "windows")] mod windows_backend;
#[cfg(target_os = "linux")] mod linux_backend;
#[cfg(target_os = "macos")] mod macos_backend;

#[pyclass]
struct AudioMixer { 
    // The manager is boxed to support polymorphic dispatch across different OS backends
    // without exposing raw C-pointers or platform-specific traits to the Python layer.
    manager: Box<dyn AudioConnectionManager> 
}

#[pymethods]
impl AudioMixer {
    #[new] 
    fn new() -> PyResult<Self> { 
        // The factory pattern ensures the correct low-level driver is initialized 
        // based on the host OS at runtime, maintaining a single codebase for the UI.
        Ok(AudioMixer { manager: get_os_manager() }) 
    }

    // Volume operations are mapped to f32 to align with standard floating-point audio scaling (0.0 to 1.0).
    fn get_master_volume(&self) -> PyResult<f32> { self.manager.get_master_volume().map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>) }
    fn set_master_volume(&mut self, level: f32) -> PyResult<()> { self.manager.set_master_volume(level).map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>) }
    fn set_device_volume(&mut self, identifier: String, level: f32) -> PyResult<()> { self.manager.set_device_volume(identifier, level).map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>) }
    fn set_app_volume(&mut self, identifier: u32, level: f32) -> PyResult<()> { self.manager.set_app_volume(identifier, level).map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>) }

    fn get_connected_software<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let applications = self.manager.get_connected_software().map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>)?;
        let application_list = PyList::empty_bound(py);
        for application in applications {
            let application_dictionary = pyo3::types::PyDict::new_bound(py);
            // Metadata is converted to a Python Dict to allow the GUI (oaGuiManager) to 
            // dynamically render per-application faders and status indicators.
            application_dictionary.set_item("name", application.name)?; 
            application_dictionary.set_item("pid", application.pid)?; 
            application_dictionary.set_item("driver", application.driver)?;
            application_dictionary.set_item("volume", application.volume)?; 
            application_dictionary.set_item("is_active", application.is_active)?;
            application_list.append(application_dictionary)?;
        }
        Ok(application_list)
    }

    fn get_available_devices<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        self.get_devices_list(py, self.manager.get_available_devices().map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>)?)
    }

    fn get_available_sources<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        self.get_devices_list(py, self.manager.get_available_sources().map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>)?)
    }
}

impl AudioMixer {
    // Utility for translating internal Rust device vectors into Python-accessible lists.
    // This separation ensures that raw backend data structures don't leak into public methods.
    fn get_devices_list<'py>(&self, py: Python<'py>, devices: Vec<crate::oa_audio_mixer_rs::manager::AudioDevice>) -> PyResult<Bound<'py, PyList>> {
        let device_list = PyList::empty_bound(py);
        for device in devices {
            let device_dictionary = pyo3::types::PyDict::new_bound(py);
            device_dictionary.set_item("name", device.name)?; 
            device_dictionary.set_item("description", device.description)?;
            device_dictionary.set_item("sample_rate", device.sample_rate)?; 
            device_dictionary.set_item("channels", device.channels)?;
            device_dictionary.set_item("volume", device.volume)?; 
            device_dictionary.set_item("is_default", device.is_default)?;
            device_list.append(device_dictionary)?;
        }
        Ok(device_list)
    }
}

#[pymodule] pub fn oaaudiomixer_rs(m: &Bound<'_, PyModule>) -> PyResult<()> { m.add_class::<AudioMixer>()?; Ok(()) }
