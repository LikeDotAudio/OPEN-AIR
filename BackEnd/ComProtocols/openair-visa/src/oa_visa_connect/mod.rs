use pyo3::prelude::*;
use pyo3::exceptions::PyException;
use std::io::{Read, Write};
use std::time::Duration;
use std::net::TcpStream;
use std::fs::{OpenOptions, File};

pub enum Connection {
    Tcp(TcpStream),
    Serial(File),
}

#[pyclass]
pub struct Instrument {
    pub conn: Connection,
    #[pyo3(get, set)]
    pub timeout: u32,
}

#[pymethods]
impl Instrument {
    pub fn query(&mut self, query_str: &str) -> PyResult<String> {
        self.write(query_str)?;
        std::thread::sleep(Duration::from_millis(50));
        self.read()
    }

    pub fn write(&mut self, command_str: &str) -> PyResult<()> {
        let command = format!("{}\n", command_str);
        match &mut self.conn {
            Connection::Tcp(stream) => {
                stream.set_write_timeout(Some(Duration::from_millis(self.timeout as u64))).unwrap_or(());
                stream.write_all(command.as_bytes()).map_err(|e| PyException::new_err(format!("Write failed: {:?}", e)))
            }
            Connection::Serial(file) => {
                file.write_all(command.as_bytes()).map_err(|e| PyException::new_err(format!("Write failed: {:?}", e)))
            }
        }
    }

    pub fn read(&mut self) -> PyResult<String> {
        let mut buf = vec![0; 4096];
        match &mut self.conn {
            Connection::Tcp(stream) => {
                stream.set_read_timeout(Some(Duration::from_millis(self.timeout as u64))).unwrap_or(());
                match stream.read(&mut buf) {
                    Ok(n) => {
                        let response = String::from_utf8_lossy(&buf[..n]).into_owned();
                        Ok(response.trim().to_string())
                    }
                    Err(e) => Err(PyException::new_err(format!("Read failed: {:?}", e))),
                }
            }
            Connection::Serial(file) => {
                match file.read(&mut buf) {
                    Ok(n) => {
                        let response = String::from_utf8_lossy(&buf[..n]).into_owned();
                        Ok(response.trim().to_string())
                    }
                    Err(e) => Err(PyException::new_err(format!("Read failed: {:?}", e))),
                }
            }
        }
    }

    pub fn close(&mut self) -> PyResult<()> {
        Ok(())
    }
}

pub fn open_resource(resource_name: &str) -> PyResult<Instrument> {
    if resource_name.starts_with("TCPIP") {
        let parts: Vec<&str> = resource_name.split("::").collect();
        if parts.len() >= 2 {
            let ip = parts[1];
            let mut port = 5025; // Default LXI port
            
            if parts.len() > 2 {
                let p2 = parts[2].to_lowercase();
                if p2.starts_with("gpib") {
                    if let Some(comma_idx) = p2.find(',') {
                        let addr_str = &p2[comma_idx + 1..];
                        let primary_addr = addr_str.split(',').next().unwrap_or("0");
                        if let Ok(addr) = primary_addr.parse::<u16>() {
                            port = 5000 + addr; // Common mapping for LAN/GPIB gateways
                        }
                    }
                } else if let Ok(p) = p2.parse::<u16>() {
                    port = p;
                }
            }
            
            let addr = format!("{}:{}", ip, port);
            let stream = TcpStream::connect_timeout(&addr.parse().unwrap(), Duration::from_secs(2))
                .map_err(|e| PyException::new_err(format!("Failed to connect TCP on port {}: {:?}", port, e)))?;
            Ok(Instrument { conn: Connection::Tcp(stream), timeout: 5000 })
        } else {
            Err(PyException::new_err("Invalid TCPIP resource format"))
        }
    } else if resource_name.starts_with("ASRL") {
        let path = resource_name.strip_prefix("ASRL").unwrap_or(resource_name);
        let path = path.strip_suffix("::INSTR").unwrap_or(path);
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .open(path)
            .map_err(|e| PyException::new_err(format!("Failed to open serial port: {:?}", e)))?;
        Ok(Instrument { conn: Connection::Serial(file), timeout: 5000 })
    } else {
        Err(PyException::new_err(format!("Unsupported resource type: {}", resource_name)))
    }
}
