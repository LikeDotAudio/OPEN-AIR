#![allow(non_snake_case, unused_variables, dead_code, unused_imports, unused_mut, mismatched_lifetime_syntaxes)]
/**
 * Header: lib.rs
 * Purpose: lib.rs implementation.
 * Description: Logic and implementation for lib.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use nom::{
    bytes::complete::take,
    multi::count,
    number::complete::{be_u16, be_u32},
    IResult,
};
use serde_json::{json, Value};
use tokio::net::TcpStream;
use tokio::io::AsyncReadExt;
use tokio::sync::mpsc;
use std::sync::Arc;

#[derive(Debug, Clone)]
pub struct Aes70Event {
    pub address: String,
    pub value: Value,
}

pub struct Aes70Agent {
    pub target_ip: String,
    pub target_port: u16,
}

impl Aes70Agent {
    pub fn new(target_ip: String, target_port: u16) -> Self {
        Self {
            target_ip,
            target_port,
        }
    }

    /// Connects to an AES70 Device and reads OCP.1 packets.
    pub async fn start(&self, tx: mpsc::Sender<Aes70Event>) -> std::io::Result<()> {
        let addr = format!("{}:{}", self.target_ip, self.target_port);
        println!("🔊 [AES70 AGENT] Attempting TCP connection to {}", addr);

        let mut stream = TcpStream::connect(&addr).await?;
        println!("🔊 [AES70 AGENT] Connected to {}", addr);

        let mut buf = vec![0u8; 65535];
        loop {
            match stream.read(&mut buf).await {
                Ok(0) => {
                    println!("🔊❌ [AES70 AGENT] Connection closed by remote host");
                    break;
                }
                Ok(size) => {
                    let data = &buf[..size];
                    match parse_pdu(data) {
                        Ok((_, pdu)) => {
                            for message in pdu.messages {
                                let event = Aes70Event {
                                    address: format!("ONO/{}/Method/{}", message.target_ono, message.method_id),
                                    value: json!({
                                        "handle": message.handle,
                                        "parameters_len": message.parameters.len()
                                    }),
                                };
                                let _ = tx.send(event).await;
                            }
                        }
                        Err(e) => {
                            eprintln!("🔊⚙️❌ [AES70 AGENT] Failed to parse OCP.1 PDU: {:?}", e);
                        }
                    }
                }
                Err(e) => {
                    eprintln!("🔊⚙️❌ [AES70 AGENT] TCP Read error: {:?}", e);
                    break;
                }
            }
        }
        Ok(())
    }
}

// OCP.1 Parser Definitions
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

// Inline comment: Logic for parse_message
fn parse_message(input: &[u8]) -> IResult<&[u8], OcaMessage> {
    let (input, size) = be_u32(input)?;
    let (input, handle) = be_u32(input)?;
    let (input, target_ono) = be_u32(input)?;
    let (input, method_id) = be_u32(input)?;

    let param_size = if size > 16 { size - 16 } else { 0 };
    let (input, parameters) = take(param_size)(input)?;

    Ok((
        input,
        OcaMessage {
            size,
            handle,
            target_ono,
            method_id,
            parameters,
        },
    ))
}

// Inline comment: Logic for parse_pdu
fn parse_pdu(input: &[u8]) -> IResult<&[u8], OcaPdu> {
    let (input, version) = be_u16(input)?;
    let (input, size) = be_u32(input)?;
    let (input, message_count) = be_u16(input)?;

    let (input, messages) = count(parse_message, message_count as usize)(input)?;

    Ok((
        input,
        OcaPdu {
            version,
            size,
            message_count,
            messages,
        },
    ))
}

#[cfg(feature = "python")]
pub mod oa_aes70_core_rs;
