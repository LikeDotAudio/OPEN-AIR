// oaAudioMixer/Core/oaAudioMixer_rs/src/lib.rs
use pyo3::prelude::*;
use pyo3::types::PyList;
use crate::factory::get_os_manager;
use crate::manager::AudioConnectionManager;

mod manager;
mod factory;

#[cfg(target_os = "windows")] mod windows_backend;
#[cfg(target_os = "linux")] mod linux_backend;
#[cfg(target_os = "macos")] mod macos_backend;

#[pyclass]
struct AudioMixer { manager: Box<dyn AudioConnectionManager> }

#[pymethods]
impl AudioMixer {
    #[new] fn new() -> PyResult<Self> { Ok(AudioMixer { manager: get_os_manager() }) }

    fn get_master_volume(&self) -> PyResult<f32> { self.manager.get_master_volume().map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>) }
    fn set_master_volume(&mut self, level: f32) -> PyResult<()> { self.manager.set_master_volume(level).map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>) }
    fn set_device_volume(&mut self, id: String, level: f32) -> PyResult<()> { self.manager.set_device_volume(id, level).map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>) }
    fn set_app_volume(&mut self, id: u32, level: f32) -> PyResult<()> { self.manager.set_app_volume(id, level).map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>) }

    fn get_connected_software<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let apps = self.manager.get_connected_software().map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>)?;
        let list = PyList::empty(py);
        for a in apps {
            let d = pyo3::types::PyDict::new(py);
            d.set_item("name", a.name)?; d.set_item("pid", a.pid)?; d.set_item("driver", a.driver)?;
            d.set_item("volume", a.volume)?; d.set_item("is_active", a.is_active)?;
            list.append(d)?;
        }
        Ok(list)
    }

    fn get_available_devices<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        self.get_devices_list(py, self.manager.get_available_devices().map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>)?)
    }

    fn get_available_sources<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        self.get_devices_list(py, self.manager.get_available_sources().map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>)?)
    }
}

impl AudioMixer {
    fn get_devices_list<'py>(&self, py: Python<'py>, devices: Vec<crate::manager::AudioDevice>) -> PyResult<Bound<'py, PyList>> {
        let list = PyList::empty(py);
        for d in devices {
            let dict = pyo3::types::PyDict::new(py);
            dict.set_item("name", d.name)?; dict.set_item("description", d.description)?;
            dict.set_item("sample_rate", d.sample_rate)?; dict.set_item("channels", d.channels)?;
            dict.set_item("volume", d.volume)?; dict.set_item("is_default", d.is_default)?;
            list.append(dict)?;
        }
        Ok(list)
    }
}

#[pymodule] fn oaaudiomixer_rs(m: &Bound<'_, PyModule>) -> PyResult<()> { m.add_class::<AudioMixer>()?; Ok(()) }
