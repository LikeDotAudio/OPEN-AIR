use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::time::{SystemTime, UNIX_EPOCH};

fn format_clock_id(raw: &[u8]) -> String {
    if raw.len() >= 10 {
        let hex_part = format!("{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}",
            raw[0], raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7]);
        let port = u16::from_be_bytes([raw[8], raw[9]]);
        format!("{} (Port {})", hex_part, port)
    } else {
        format!("{:?}", raw)
    }
}

fn get_message_type(m_id: u8) -> &'static str {
    match m_id {
        0 => "Sync",
        1 => "Delay_Req",
        2 => "Pdelay_Req",
        3 => "Pdelay_Resp",
        8 => "Follow_Up",
        9 => "Delay_Resp",
        10 => "Pdelay_Resp_Follow_Up",
        11 => "Announce",
        12 => "Signaling",
        13 => "Management",
        _ => "Unknown",
    }
}

#[pyfunction]
fn parse_packet(py: Python, payload: &[u8], src_ip: String, dst_ip: String, udp_port: u16) -> PyResult<Py<PyAny>> {
    let dict = PyDict::new(py);
    
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs_f64();
    dict.set_item("timestamp", now)?;
    dict.set_item("source_ip", src_ip)?;
    dict.set_item("dest_ip", dst_ip)?;
    dict.set_item("udp_port", udp_port)?;
    
    if payload.len() >= 34 {
        let m_id = payload[0] & 0x0F;
        let m_type = get_message_type(m_id);
        let domain = payload[4];
        let seq_id = u16::from_be_bytes([payload[30], payload[31]]);
        let port_id = &payload[20..30];
        
        let m_type_str = if m_type == "Unknown" {
            format!("Unknown ({})", m_id)
        } else {
            m_type.to_string()
        };

        dict.set_item("message_type", m_type_str)?;
        dict.set_item("domain", domain)?;
        dict.set_item("sequence_id", seq_id)?;
        dict.set_item("clock_identity", format_clock_id(port_id))?;
    } else {
        dict.set_item("message_type", "Unknown")?;
        dict.set_item("domain", 0)?;
        dict.set_item("sequence_id", 0)?;
        dict.set_item("clock_identity", "Unknown")?;
    }
    
    Ok(dict.into())
}

#[pymodule]
pub fn oaptpparser_rs(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_packet, m)?)?;
    Ok(())
}