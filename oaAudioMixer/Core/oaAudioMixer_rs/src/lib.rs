// oaAudioMixer/Core/oaAudioMixer_rs/src/lib.rs
use pyo3::prelude::*;
use pyo3::types::PyList;
use crate::factory::get_os_manager;
use crate::manager::AudioConnectionManager;

mod manager;
mod factory;

#[cfg(target_os = "windows")]
mod windows_backend;

#[cfg(target_os = "linux")]
mod linux_backend;

#[cfg(target_os = "macos")]
mod macos_backend;

#[pyclass]
struct AudioMixer {
    manager: Box<dyn AudioConnectionManager>,
}

#[pymethods]
impl AudioMixer {
    #[new]
    fn new() -> PyResult<Self> {
        let manager = get_os_manager();
        Ok(AudioMixer { manager })
    }

    fn get_master_volume(&self) -> PyResult<f32> {
        self.manager.get_master_volume().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))
    }

    fn set_master_volume(&mut self, level: f32) -> PyResult<()> {
        self.manager.set_master_volume(level).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))
    }

    fn get_connected_software<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let apps = self.manager.get_connected_software().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;
        let py_list = PyList::empty(py);
        for app in apps {
            let app_dict = pyo3::types::PyDict::new(py);
            app_dict.set_item("name", app.name)?;
            app_dict.set_item("is_active", app.is_active)?;
            py_list.append(app_dict)?;
        }
        Ok(py_list)
    }
}

#[pymodule]
fn oaaudiomixer_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<AudioMixer>()?;
    Ok(())
}
