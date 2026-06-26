use pyo3::prelude::*;
use crate::oa_visa_mqtt::logic_mqtt_publisher::MqttPublisher;
use serde_json::json;
use crate::oa_visa_pyvisa_wrapper::execute_status_and_error;

#[pyfunction]
#[pyo3(signature = (resource_name, broker_ip, port, base_topic, category="Unknown", model="Unknown", count=0))]
pub fn oa_visa_error_check(
    py: Python<'_>,
    resource_name: &str,
    broker_ip: &str,
    port: u16,
    base_topic: &str,
    category: &str,
    model: &str,
    count: usize
) -> PyResult<String> {
    let (status_bit, error_msg) = execute_status_and_error(py, resource_name)?;
    
    let status_str = status_bit.trim();
    let error_str = error_msg.trim();
    
    let publisher = MqttPublisher::new(broker_ip, port);
    publisher.publish_device_attribute(base_topic, category, model, count, "status_bit", status_str);
    publisher.publish_device_attribute(base_topic, category, model, count, "error", error_str);
    publisher.flush(2);
    
    let payload = json!({
        "status_bit": status_str,
        "error": error_str
    });
    
    Ok(payload.to_string())
}
