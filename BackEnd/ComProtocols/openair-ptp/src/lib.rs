#![allow(non_snake_case, unused_variables, dead_code, unused_imports)]
//! `openair-ptp` — PTP (IEEE 1588) discovery and live traffic monitoring.
//!
//! Watches all three clock protocols that can share one NIC — PTPv1
//! (1588-2002), PTPv2 (1588-2008) and gPTP (802.1AS) — decodes their messages,
//! and correlates them into the exchanges they actually form (Sync ↔ Follow_Up,
//! Delay_Req ↔ Delay_Resp, the three-legged peer-delay chain).
//!
//! * [`message`] — PTPv2 / gPTP parsing
//! * [`v1`] — PTPv1, which shares the wire but not the header layout
//! * [`net`] — capture across UDP (319/320) and raw Ethernet (0x88F7)
//! * [`flow`] — correlating messages into conversations
//! * [`monitor`] — the shared capture loop and clock table
//!
//! The `ptp-monitor` binary is the live view; [`run_listen_agent`] is the MQTT
//! agent. Both consume the same stream.
//!
//! # Legacy PyO3 shim
//!
//! The `oa_ptp_clock_rs` and `oa_ptp_parser_rs` modules predate this and remain
//! gated behind the non-default `python` feature. They are untouched, and the
//! Rust implementation above does not depend on them.
/**
 * Header: lib.rs
 * Purpose: lib.rs implementation.
 * Description: Logic and implementation for lib.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

pub mod flow;
pub mod message;
pub mod monitor;
pub mod net;
pub mod v1;

mod agent;
pub use agent::run_listen_agent;

#[cfg(feature = "python")]
pub mod oa_ptp_clock_rs;

#[cfg(feature = "python")]
pub mod oa_ptp_parser_rs;
