use pyo3::prelude::*;
use crate::oa_visa_connect::Instrument;
use crate::oa_visa_scan_for_devices;
use crate::oa_visa_get_idn;

#[pyclass]
pub struct ResourceManager {}

#[pymethods]
impl ResourceManager {
    #[new]
    #[pyo3(signature = (_backend=None))]
    pub fn new(_backend: Option<&str>) -> PyResult<Self> {
        Ok(ResourceManager {})
    }

    pub fn list_resources(&self) -> PyResult<Vec<String>> {
        oa_visa_scan_for_devices::list_resources()
    }

    pub fn open_resource(&self, resource_name: &str) -> PyResult<Instrument> {
        crate::oa_visa_connect::open_resource(resource_name)
    }

    pub fn identify_device(&self, py: Python<'_>, resource_name: &str) -> PyResult<PyObject> {
        oa_visa_get_idn::identify_device(py, resource_name)
    }

    pub fn scan_and_catalog(&self, py: Python<'_>) -> PyResult<PyObject> {
        let resources = oa_visa_scan_for_devices::list_resources()?;
        let dict = pyo3::types::PyDict::new_bound(py);
        
        for (index, res) in resources.iter().enumerate() {
            let id = (index + 1).to_string();
            let entry = match oa_visa_get_idn::identify_device(py, res) {
                Ok(info) => info,
                Err(e) => {
                    let err_dict = pyo3::types::PyDict::new_bound(py);
                    let _ = err_dict.set_item("resource", res);
                    let _ = err_dict.set_item("status", "Unresponsive");
                    let _ = err_dict.set_item("notes", e.to_string());
                    err_dict.into()
                }
            };
            let _ = dict.set_item(id, entry);
        }
        
        Ok(dict.into())
    }

    pub fn publish_devices_mqtt(&self, py: Python<'_>, broker_ip: &str, port: u16, devices: Vec<PyObject>, base_topic: &str) -> PyResult<()> {
        let publisher = crate::oa_visa_mqtt::logic_mqtt_publisher::MqttPublisher::new(broker_ip, port);
        let mut publish_count = 0;
        let mut counts: std::collections::HashMap<(String, String), usize> = std::collections::HashMap::new();
        
        for info in devices {
            if let Ok(dict) = info.downcast_bound::<pyo3::types::PyDict>(py) {
                if let (Ok(Some(cat)), Ok(Some(model))) = (
                    dict.get_item("device_type"),
                    dict.get_item("model")
                ) {
                    let cat_str = cat.extract::<String>().unwrap_or_else(|_| "Unknown".to_string());
                    let model_str = model.extract::<String>().unwrap_or_else(|_| "Unknown".to_string());
                    
                    let key = (cat_str.clone(), model_str.clone());
                    let count = counts.entry(key).or_insert(0);
                    
                    // Convert PyDict to JSON string manually
                    let mut map = serde_json::Map::new();
                    let mut is_online = false;
                    for (k, v) in dict.iter() {
                        if let Ok(key) = k.extract::<String>() {
                            if let Ok(val) = v.extract::<String>() {
                                if key == "raw_idn" && !val.trim().is_empty() {
                                    is_online = true;
                                }
                                map.insert(key, serde_json::Value::String(val));
                            }
                        }
                    }
                    
                    if let Ok(duration) = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH) {
                        map.insert("last_online".to_string(), serde_json::Value::Number(duration.as_secs().into()));
                    }
                    map.insert("connected".to_string(), serde_json::Value::Number((if is_online { 1 } else { 0 }).into()));
                    
                    let topic = format!("{}/{}/{}/Dev{}", base_topic.trim_end_matches('/'), cat_str.replace(" ", "_"), model_str.replace(" ", "_"), count);
                    println!("   📡 Publishing attributes to: {}/*", topic);
                    
                    for (k, v) in &map {
                        let val_str = match v {
                            serde_json::Value::String(s) => s.clone(),
                            serde_json::Value::Number(n) => n.to_string(),
                            _ => v.to_string(),
                        };
                        publisher.publish_device_attribute(base_topic, &cat_str, &model_str, *count, k, &val_str);
                    }
                    
                    // Add mapping to DEVICE_MAP for the daemon
                    let topic_prefix = format!("{}/{}/{}/Dev{}", base_topic.trim_end_matches('/'), cat_str.replace(" ", "_"), model_str.replace(" ", "_"), count);
                    if let Some(res_val) = dict.get_item("resource").ok().flatten() {
                        if let Ok(res_str) = res_val.extract::<String>() {
                            crate::oa_visa_mqtt::logic_mqtt_listen::update_device_map(topic_prefix.clone(), res_str);
                        }
                    }
                    
                    // Create the Write and Read topics for this device
                    publisher.publish_raw(&format!("{}/Write", topic_prefix), "");
                    publisher.publish_raw(&format!("{}/Read", topic_prefix), "");
                    publish_count += 2;
                    
                    *count += 1;
                    publish_count += map.len();
                }
            }
        }
        
        // Wait for all messages to be sent
        if publish_count > 0 {
            publisher.flush(publish_count);
        }
        
        Ok(())
    }
}
