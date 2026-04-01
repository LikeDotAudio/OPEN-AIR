// oaComAES70/Methods/oaAES70Core-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.1520.2

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyBytes, PyList};
use nom::{
    IResult,
    number::complete::{be_u16, be_u32},
    bytes::complete::take,
    multi::count,
};

#[pyclass]
struct OcaParser;

#[pymethods]
impl OcaParser {
    #[new]
    fn new() -> Self {
        OcaParser
    }

    fn decode<'py>(&self, py: Python<'py>, data: &'py [u8]) -> PyResult<Option<Bound<'py, PyDict>>> {
        match parse_pdu(data) {
            Ok((_, pdu)) => {
                let dict = PyDict::new_bound(py);
                dict.set_item("version", pdu.version)?;
                dict.set_item("pdu_size", pdu.size)?;
                dict.set_item("message_count", pdu.message_count)?;
                
                let messages = PyList::empty_bound(py);
                for msg in pdu.messages {
                    let msg_dict = PyDict::new_bound(py);
                    msg_dict.set_item("size", msg.size)?;
                    msg_dict.set_item("handle", msg.handle)?;
                    msg_dict.set_item("target_ono", msg.target_ono)?;
                    msg_dict.set_item("method_id", msg.method_id)?;
                    msg_dict.set_item("parameters", PyBytes::new_bound(py, msg.parameters))?;
                    messages.append(msg_dict)?;
                }
                dict.set_item("messages", messages)?;
                
                Ok(Some(dict))
            }
            Err(_) => Ok(None),
        }
    }
}

struct OcaPdu<'a> {
    version: u16,
    size: u32,
    message_count: u16,
    messages: Vec<OcaMessage<'a>>,
}

struct OcaMessage<'a> {
    size: u32,
    handle: u32,
    target_ono: u32,
    method_id: u32,
    parameters: &'a [u8],
}

fn parse_message(input: &[u8]) -> IResult<&[u8], OcaMessage> {
    let (input, size) = be_u32(input)?;
    let (input, handle) = be_u32(input)?;
    let (input, target_ono) = be_u32(input)?;
    let (input, method_id) = be_u32(input)?;
    
    // Header is 16 bytes: size (4), handle (4), target_ono (4), method_id (4)
    let param_size = if size > 16 { size - 16 } else { 0 };
    let (input, parameters) = take(param_size)(input)?;
    
    Ok((input, OcaMessage {
        size,
        handle,
        target_ono,
        method_id,
        parameters,
    }))
}

fn parse_pdu(input: &[u8]) -> IResult<&[u8], OcaPdu> {
    let (input, version) = be_u16(input)?;
    let (input, size) = be_u32(input)?;
    let (input, message_count) = be_u16(input)?;
    
    let (input, messages) = count(parse_message, message_count as usize)(input)?;
    
    Ok((input, OcaPdu {
        version,
        size,
        message_count,
        messages,
    }))
}

#[pymodule]
fn oaaes70core_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<OcaParser>()?;
    Ok(())
}
