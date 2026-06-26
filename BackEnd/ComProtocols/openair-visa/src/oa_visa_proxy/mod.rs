use pyo3::prelude::*;
use pyo3::exceptions::PyException;
use crate::oa_visa_resource_manager::ResourceManager;

pub struct CommandInfo {
    command: String,
    query: bool,
    correlation_id: String,
}

#[pyclass]
pub struct VisaProxy {
    sender: Option<std::sync::mpsc::Sender<Option<CommandInfo>>>,
}

#[pymethods]
impl VisaProxy {
    #[new]
    pub fn new() -> Self {
        VisaProxy { sender: None }
    }

    pub fn set_instrument_instance(&mut self, resource_name: &str, callback: PyObject) -> PyResult<()> {
        let rm = ResourceManager {};
        let mut inst = rm.open_resource(resource_name)?;

        let (tx, rx) = std::sync::mpsc::channel::<Option<CommandInfo>>();
        self.sender = Some(tx);

        std::thread::spawn(move || {
            for msg in rx {
                match msg {
                    Some(info) => {
                        if info.query {
                            let result = inst.query(&info.command);
                            Python::with_gil(|py| {
                                match result {
                                    Ok(res) => {
                                        let _ = callback.call1(py, (res, info.command, info.correlation_id, true));
                                    },
                                    Err(e) => {
                                        let _ = callback.call1(py, (e.to_string(), info.command, info.correlation_id, false));
                                    }
                                }
                            });
                        } else {
                            let result = inst.write(&info.command);
                            Python::with_gil(|py| {
                                if let Err(e) = result {
                                    let _ = callback.call1(py, (e.to_string(), info.command, info.correlation_id, false));
                                }
                            });
                        }
                    }
                    None => break,
                }
            }
        });
        Ok(())
    }

    #[pyo3(signature = (command, query=false, correlation_id="N/A".to_string()))]
    pub fn enqueue_command(&self, command: String, query: bool, correlation_id: String) -> PyResult<()> {
        if let Some(tx) = &self.sender {
            tx.send(Some(CommandInfo { command, query, correlation_id }))
                .map_err(|_| PyException::new_err("Failed to enqueue command"))?;
        } else {
            return Err(PyException::new_err("Proxy not initialized with an instrument"));
        }
        Ok(())
    }

    pub fn shutdown(&self) -> PyResult<()> {
        if let Some(tx) = &self.sender {
            let _ = tx.send(None);
        }
        Ok(())
    }
}
