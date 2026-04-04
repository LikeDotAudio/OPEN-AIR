// oaComEmber/Methods/oaEmberTree-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.1620.1

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyBytes, PyList};
use nom::{
    IResult,
    bytes::complete::take,
    number::complete::u8,
    error::Error,
};

#[pyclass]
struct EmberParser;

#[pymethods]
impl EmberParser {
    #[new]
    fn new() -> Self {
        EmberParser
    }

    fn parse_ber_payload<'py>(&self, py: Python<'py>, data: &'py [u8]) -> PyResult<Option<Bound<'py, PyDict>>> {
        match parse_ber_tlv(data) {
            Ok((_, tlv)) => {
                let dict = tlv.to_py_dict(py)?;
                Ok(Some(dict))
            }
            Err(_) => Ok(None),
        }
    }
}

#[derive(Debug)]
struct BerTlv<'a> {
    tag: u32,
    is_constructed: bool,
    class: u8,
    value: BerValue<'a>,
}

#[derive(Debug)]
enum BerValue<'a> {
    Primitive(&'a [u8]),
    Constructed(Vec<BerTlv<'a>>),
}

impl<'a> BerTlv<'a> {
    fn to_py_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("tag", self.tag)?;
        dict.set_item("is_constructed", self.is_constructed)?;
        dict.set_item("class", self.class)?;
        
        match &self.value {
            BerValue::Primitive(p) => {
                dict.set_item("value", PyBytes::new(py, p))?;
            }
            BerValue::Constructed(c) => {
                let list = PyList::empty(py);
                for item in c {
                    list.append(item.to_py_dict(py)?)?;
                }
                dict.set_item("value", list)?;
            }
        }
        Ok(dict)
    }
}

fn parse_tag(input: &[u8]) -> IResult<&[u8], (u32, bool, u8)> {
    let (input, first_byte) = u8(input)?;
    let class = (first_byte & 0xC0) >> 6;
    let is_constructed = (first_byte & 0x20) != 0;
    let mut tag = (first_byte & 0x1F) as u32;

    if tag == 0x1F {
        // High-tag-number form
        let mut input = input;
        tag = 0;
        loop {
            let (next_input, byte) = u8(input)?;
            input = next_input;
            tag = (tag << 7) | (byte & 0x7F) as u32;
            if (byte & 0x80) == 0 {
                break;
            }
        }
        Ok((input, (tag, is_constructed, class)))
    } else {
        Ok((input, (tag, is_constructed, class)))
    }
}

fn parse_length(input: &[u8]) -> IResult<&[u8], usize> {
    let (input, first_byte) = u8(input)?;
    if first_byte == 0x80 {
        // Indefinite length - not fully supported here for simplicity
        return Err(nom::Err::Error(Error::new(input, nom::error::ErrorKind::Tag)));
    }
    
    if (first_byte & 0x80) == 0 {
        // Short form
        Ok((input, first_byte as usize))
    } else {
        // Long form
        let n_bytes = (first_byte & 0x7F) as usize;
        let (mut input, length_bytes) = take(n_bytes)(input)?;
        let mut length = 0usize;
        for &b in length_bytes {
            length = (length << 8) | (b as usize);
        }
        Ok((input, length))
    }
}

fn parse_ber_tlv(input: &[u8]) -> IResult<&[u8], BerTlv> {
    let (input, (tag, is_constructed, class)) = parse_tag(input)?;
    let (input, length) = parse_length(input)?;
    let (input, value_bytes) = take(length)(input)?;

    if is_constructed {
        let mut children = Vec::new();
        let mut remaining = value_bytes;
        while !remaining.is_empty() {
            let (next_remaining, child) = parse_ber_tlv(remaining)?;
            remaining = next_remaining;
            children.push(child);
        }
        Ok((input, BerTlv {
            tag,
            is_constructed,
            class,
            value: BerValue::Constructed(children),
        }))
    } else {
        Ok((input, BerTlv {
            tag,
            is_constructed,
            class,
            value: BerValue::Primitive(value_bytes),
        }))
    }
}

#[pymodule]
fn oaembertree_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<EmberParser>()?;
    Ok(())
}
