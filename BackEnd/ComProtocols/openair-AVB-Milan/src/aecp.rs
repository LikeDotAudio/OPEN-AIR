//! AECP — AVDECC Enumeration and Control Protocol, IEEE 1722.1 clause 9.
//!
//! # ⚠️ This module writes to devices
//!
//! Everything else in these discovery crates observes. This one sends a command
//! to a specific piece of hardware and changes its state. The scope is kept to
//! exactly one command — **IDENTIFY**, which blinks the device's front-panel
//! LED — because that is the operation whose entire purpose is "tell me which
//! physical box in the rack you are", and it is what Hive's Identify button
//! does.
//!
//! Nothing here sets stream formats, sampling rates, names, or connections.
//! Those are also `SET_*` commands over the same transport, and deliberately
//! absent: a discovery tool that can silently reconfigure a console is a
//! different and much more dangerous thing than one that can make it blink.
//!
//! # How identify works
//!
//! An AVDECC entity exposes a CONTROL descriptor of type IDENTIFY. Writing 255
//! to it starts the blink; writing 0 stops it. The descriptor's index normally
//! requires enumerating the device's descriptor tree — but ADP carries it
//! directly in `identify_control_index`, *provided* the entity sets the
//! `AEM_IDENTIFY_CONTROL_INDEX_VALID` capability bit. That shortcut is what
//! lets this crate identify a device without implementing enumeration.
//!
//! # Frame layout (AEM command)
//!
//! ```text
//!   0       subtype = 0x7B (AECP)
//!   1       sv(1) | version(3) | message_type(4)   0 = AEM_COMMAND, 1 = AEM_RESPONSE
//!   2..3    status(5) | control_data_length(11)
//!   4..11   target_entity_id
//!   12..19  controller_entity_id
//!   20..21  sequence_id
//!   22..23  u(1) | command_type(15)                0x0018 = SET_CONTROL
//!   24..25  descriptor_type                        0x001A = CONTROL
//!   26..27  descriptor_index
//!   28      control value (LINEAR_UINT8)           255 = on, 0 = off
//! ```

use crate::adp::ETHERTYPE_AVTP;

/// AVTP subtype for AECP.
pub const SUBTYPE_AECP: u8 = 0x7B;

/// `AEM_COMMAND` / `AEM_RESPONSE` message types.
pub const AEM_COMMAND: u8 = 0x00;
pub const AEM_RESPONSE: u8 = 0x01;

/// AEM command code for `SET_CONTROL`.
pub const CMD_SET_CONTROL: u16 = 0x0018;

/// AEM descriptor type for `CONTROL`.
pub const DESC_CONTROL: u16 = 0x001A;

/// IDENTIFY control values. The control is a `CONTROL_LINEAR_UINT8`, and these
/// are the only two values it takes.
pub const IDENTIFY_ON: u8 = 255;
pub const IDENTIFY_OFF: u8 = 0;

/// Bytes after the 12-byte common header in a `SET_CONTROL` with one uint8:
/// controller_entity_id(8) + sequence_id(2) + command_type(2) + descriptor(4) + value(1).
const SET_CONTROL_CDL: u16 = 17;

/// AEM status codes (§7.4). These are the useful diagnostics — a device that
/// refuses to identify usually says exactly why.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AemStatus {
    Success,
    NotImplemented,
    NoSuchDescriptor,
    EntityLocked,
    EntityAcquired,
    NotAuthenticated,
    AuthenticationDisabled,
    BadArguments,
    NoResources,
    InProgress,
    EntityMisbehaving,
    NotSupported,
    StreamIsRunning,
    Unknown(u8),
}

impl AemStatus {
    fn from_bits(bits: u8) -> Self {
        match bits {
            0 => Self::Success,
            1 => Self::NotImplemented,
            2 => Self::NoSuchDescriptor,
            3 => Self::EntityLocked,
            4 => Self::EntityAcquired,
            5 => Self::NotAuthenticated,
            6 => Self::AuthenticationDisabled,
            7 => Self::BadArguments,
            8 => Self::NoResources,
            9 => Self::InProgress,
            10 => Self::EntityMisbehaving,
            11 => Self::NotSupported,
            12 => Self::StreamIsRunning,
            n => Self::Unknown(n),
        }
    }

    /// Plain-language explanation aimed at whoever is standing at the rack.
    pub fn explain(&self) -> &'static str {
        match self {
            Self::Success => "success — the device should be blinking",
            Self::NotImplemented => "the device does not implement SET_CONTROL",
            Self::NoSuchDescriptor => {
                "no CONTROL descriptor at that index — the entity's identify_control_index may be wrong"
            }
            Self::EntityLocked => "another controller holds a lock on this entity",
            Self::EntityAcquired => "another controller has acquired this entity (Hive still open?)",
            Self::NotAuthenticated => "the device requires an authenticated controller",
            Self::AuthenticationDisabled => "authentication is disabled on the device",
            Self::BadArguments => "the device rejected the control value",
            Self::NoResources => "the device is out of resources",
            Self::InProgress => "in progress",
            Self::EntityMisbehaving => "the device reported an internal error",
            Self::NotSupported => "the command is not supported on this descriptor",
            Self::StreamIsRunning => "the stream is running and cannot be changed",
            Self::Unknown(_) => "unrecognised AEM status code",
        }
    }
}

/// A parsed AEM response.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AemResponse {
    pub status: AemStatus,
    pub target_entity_id: u64,
    pub controller_entity_id: u64,
    pub sequence_id: u16,
    pub command_type: u16,
}

/// Derive a controller entity ID from our own MAC.
///
/// A controller needs a unique 64-bit ID to put in its commands so responses
/// can be matched back. The convention is to build it from the interface MAC;
/// the low 16 bits distinguish multiple controllers on one host, and 0x0A15 is
/// simply this application's fixed marker.
pub fn controller_id_from_mac(mac: [u8; 6]) -> u64 {
    let mut bytes = [0u8; 8];
    bytes[..6].copy_from_slice(&mac);
    bytes[6] = 0x0A;
    bytes[7] = 0x15;
    u64::from_be_bytes(bytes)
}

/// Build an AEM `SET_CONTROL` frame that turns the IDENTIFY control on or off.
///
/// Addressed to the target's unicast MAC, not the AVDECC multicast group: this
/// is a command for one device, and broadcasting it would ask an entire rack to
/// blink at once.
#[allow(clippy::too_many_arguments)]
pub fn build_identify_frame(
    source_mac: [u8; 6],
    target_mac: [u8; 6],
    target_entity_id: u64,
    controller_entity_id: u64,
    sequence_id: u16,
    identify_control_index: u16,
    value: u8,
) -> Vec<u8> {
    let mut f = Vec::with_capacity(64);
    f.extend_from_slice(&target_mac);
    f.extend_from_slice(&source_mac);
    f.extend_from_slice(&ETHERTYPE_AVTP.to_be_bytes());

    f.push(SUBTYPE_AECP);
    f.push(AEM_COMMAND); // sv=0, version=0, message_type=AEM_COMMAND
    // status = 0 on a command; control_data_length is 11 bits across bytes 2-3.
    f.push(((SET_CONTROL_CDL >> 8) & 0x07) as u8);
    f.push((SET_CONTROL_CDL & 0xFF) as u8);
    f.extend_from_slice(&target_entity_id.to_be_bytes());
    f.extend_from_slice(&controller_entity_id.to_be_bytes());
    f.extend_from_slice(&sequence_id.to_be_bytes());
    f.extend_from_slice(&CMD_SET_CONTROL.to_be_bytes()); // u=0
    f.extend_from_slice(&DESC_CONTROL.to_be_bytes());
    f.extend_from_slice(&identify_control_index.to_be_bytes());
    f.push(value);

    // Pad to the 60-byte Ethernet minimum. Short frames are dropped by some
    // NICs before they ever reach the wire.
    if f.len() < 60 {
        f.resize(60, 0);
    }
    f
}

/// Parse an AEM response frame, if that is what this is.
///
/// Returns `None` for anything that is not an AEM response — including our own
/// outgoing commands, which the capture socket also sees.
pub fn parse_response(frame: &[u8]) -> Option<AemResponse> {
    if frame.len() < 14 {
        return None;
    }
    let mut offset = 12;
    let mut ethertype = u16::from_be_bytes([frame[offset], frame[offset + 1]]);
    if ethertype == 0x8100 || ethertype == 0x88A8 {
        if frame.len() < offset + 8 {
            return None;
        }
        offset += 4;
        ethertype = u16::from_be_bytes([frame[offset], frame[offset + 1]]);
    }
    offset += 2;
    if ethertype != ETHERTYPE_AVTP {
        return None;
    }

    let pdu = &frame[offset..];
    if pdu.len() < 24 || pdu[0] & 0x7F != SUBTYPE_AECP {
        return None;
    }
    if pdu[1] & 0x0F != AEM_RESPONSE {
        return None;
    }

    let be64 = |at: usize| -> u64 {
        let mut b = [0u8; 8];
        b.copy_from_slice(&pdu[at..at + 8]);
        u64::from_be_bytes(b)
    };

    Some(AemResponse {
        status: AemStatus::from_bits(pdu[2] >> 3),
        target_entity_id: be64(4),
        controller_entity_id: be64(12),
        sequence_id: u16::from_be_bytes([pdu[20], pdu[21]]),
        // The u bit is not part of the command code.
        command_type: u16::from_be_bytes([pdu[22], pdu[23]]) & 0x7FFF,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    const SRC: [u8; 6] = [0xA0, 0x36, 0x9F, 0x2A, 0xC7, 0x78];
    const DST: [u8; 6] = [0x00, 0x1B, 0x92, 0x0A, 0x1B, 0x2C];
    const TARGET: u64 = 0x001B_920A_1B2C_0001;

    fn identify_on() -> Vec<u8> {
        build_identify_frame(SRC, DST, TARGET, controller_id_from_mac(SRC), 7, 2, IDENTIFY_ON)
    }

    #[test]
    fn identify_command_has_the_right_shape() {
        let f = identify_on();
        assert!(f.len() >= 60, "must meet the Ethernet minimum");

        // Unicast to the device, NOT the AVDECC multicast group: broadcasting
        // an identify would light up every device in the rack.
        assert_eq!(&f[0..6], &DST);
        assert_ne!(&f[0..6], &crate::adp::AVDECC_MULTICAST_MAC);
        assert_eq!(&f[6..12], &SRC);
        assert_eq!(u16::from_be_bytes([f[12], f[13]]), ETHERTYPE_AVTP);

        let pdu = &f[14..];
        assert_eq!(pdu[0], SUBTYPE_AECP);
        assert_eq!(pdu[1] & 0x0F, AEM_COMMAND);
        assert_eq!(pdu[2] >> 3, 0, "status must be 0 on a command");
        let cdl = (((pdu[2] & 0x07) as u16) << 8) | pdu[3] as u16;
        assert_eq!(cdl, SET_CONTROL_CDL);
        assert_eq!(u64::from_be_bytes(pdu[4..12].try_into().unwrap()), TARGET);
        assert_eq!(u16::from_be_bytes([pdu[20], pdu[21]]), 7); // sequence_id
        assert_eq!(u16::from_be_bytes([pdu[22], pdu[23]]), CMD_SET_CONTROL);
        assert_eq!(u16::from_be_bytes([pdu[24], pdu[25]]), DESC_CONTROL);
        assert_eq!(u16::from_be_bytes([pdu[26], pdu[27]]), 2); // control index
        assert_eq!(pdu[28], IDENTIFY_ON);
    }

    /// Off differs from on in exactly one byte. If that ever stops being true,
    /// a failed cleanup would leave hardware blinking in a rack indefinitely.
    #[test]
    fn off_differs_from_on_only_in_the_value() {
        let on = identify_on();
        let off =
            build_identify_frame(SRC, DST, TARGET, controller_id_from_mac(SRC), 7, 2, IDENTIFY_OFF);
        let differing: Vec<usize> =
            (0..on.len()).filter(|&i| on[i] != off[i]).collect();
        assert_eq!(differing, vec![14 + 28]);
        assert_eq!(off[14 + 28], 0);
    }

    #[test]
    fn controller_id_derives_from_the_interface_mac() {
        let id = controller_id_from_mac(SRC);
        assert_eq!(crate::adp::format_id(id), "A0:36:9F:2A:C7:78:0A:15");
    }

    /// Build a response to our own command, as a device would.
    fn response_with_status(status: u8) -> Vec<u8> {
        let mut f = identify_on();
        f[14 + 1] = AEM_RESPONSE;
        f[14 + 2] = (status << 3) | (f[14 + 2] & 0x07);
        // Swap direction, as the device would.
        let (dst, src) = (SRC, DST);
        f[0..6].copy_from_slice(&dst);
        f[6..12].copy_from_slice(&src);
        f
    }

    #[test]
    fn parses_a_success_response() {
        let r = parse_response(&response_with_status(0)).unwrap();
        assert_eq!(r.status, AemStatus::Success);
        assert_eq!(r.target_entity_id, TARGET);
        assert_eq!(r.sequence_id, 7);
        assert_eq!(r.command_type, CMD_SET_CONTROL);
        assert_eq!(r.controller_entity_id, controller_id_from_mac(SRC));
    }

    /// The refusals an operator actually hits: Hive left open holding the
    /// entity, or a device without an identify control at that index.
    #[test]
    fn refusals_are_decoded_with_an_explanation() {
        let acquired = parse_response(&response_with_status(4)).unwrap();
        assert_eq!(acquired.status, AemStatus::EntityAcquired);
        assert!(acquired.status.explain().contains("acquired"));

        let no_desc = parse_response(&response_with_status(2)).unwrap();
        assert_eq!(no_desc.status, AemStatus::NoSuchDescriptor);
        assert!(no_desc.status.explain().contains("identify_control_index"));

        let locked = parse_response(&response_with_status(3)).unwrap();
        assert_eq!(locked.status, AemStatus::EntityLocked);
    }

    /// Our own outgoing command is visible on the capture socket. Treating it
    /// as a response would report a phantom success before the device replied.
    #[test]
    fn our_own_command_is_not_mistaken_for_a_response() {
        assert_eq!(parse_response(&identify_on()), None);
    }

    #[test]
    fn adp_and_stream_traffic_are_not_responses() {
        let mut adp_frame = vec![0u8; 82];
        adp_frame[12] = 0x22;
        adp_frame[13] = 0xF0;
        adp_frame[14] = crate::adp::SUBTYPE_ADP;
        assert_eq!(parse_response(&adp_frame), None);
    }
}
