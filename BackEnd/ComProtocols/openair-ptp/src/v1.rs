//! PTPv1 (IEEE 1588-2002) parsing.
//!
//! # Why this needs its own parser
//!
//! PTPv1 is not "PTPv2 with an older version number" — the header is a
//! different shape, and nothing but the transport is shared. It arrives on the
//! *same* multicast group and the *same* UDP ports as PTPv2, which is exactly
//! how a v1 device hides on a network someone believes is all v2.
//!
//! ```text
//! PTPv1 header (40 bytes)
//!   0..1    versionPTP = 1          <- the discriminator
//!   2..3    versionNetwork = 1
//!   4..19   subdomain (16-byte NUL/space padded name, e.g. "_DFLT")
//!   20      messageType  (1 = event, 2 = general)
//!   21      sourceCommunicationTechnology
//!   22..27  sourceUuid (6 bytes — a MAC, not a 64-bit clock identity)
//!   28..29  sourcePortId
//!   30..31  sequenceId
//!   32      control (0=Sync 1=Delay_Req 2=Follow_Up 3=Delay_Resp 4=Management)
//!   33      reserved
//!   34..35  flags
//!   36..39  reserved
//! ```
//!
//! Two differences matter when reading a mixed capture:
//!
//! * **Identity is a 6-byte UUID, not an 8-byte clock identity.** There is no
//!   `FF:FE` splice; the MAC is simply there. So a v1 and a v2 clock on the
//!   same physical device look like unrelated identifiers unless you know to
//!   splice one yourself.
//! * **`control`, not `messageType`, names the message.** Byte 20 only says
//!   event-vs-general. Reading byte 20 as if it were v2's messageType — an easy
//!   mistake given both are "the message type field" — turns every v1 Sync into
//!   a Delay_Req.

/// PTPv1 message kinds, from the `control` field at byte 32.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum V1MessageType {
    Sync,
    DelayReq,
    FollowUp,
    DelayResp,
    Management,
    Other(u8),
}

impl V1MessageType {
    fn from_control(c: u8) -> Self {
        match c {
            0 => Self::Sync,
            1 => Self::DelayReq,
            2 => Self::FollowUp,
            3 => Self::DelayResp,
            4 => Self::Management,
            n => Self::Other(n),
        }
    }

    pub fn label(&self) -> &'static str {
        match self {
            Self::Sync => "Sync",
            Self::DelayReq => "Delay_Req",
            Self::FollowUp => "Follow_Up",
            Self::DelayResp => "Delay_Resp",
            Self::Management => "Management",
            Self::Other(_) => "Unknown",
        }
    }
}

/// A parsed PTPv1 message.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct V1Message {
    pub message_type: V1MessageType,
    /// `_DFLT`, `_ALT1`… — v1's equivalent of a domain, as a name.
    pub subdomain: String,
    /// 6-byte source UUID. This is a MAC address.
    pub source_uuid: [u8; 6],
    pub source_port_id: u16,
    pub sequence_id: u16,
    /// True for event messages (Sync, Delay_Req), which are timestamped.
    pub is_event: bool,
    pub flags: u16,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum V1ParseError {
    TooShort(usize),
    /// `versionPTP` is not 1.
    NotVersion1(u16),
}

/// Is this payload PTPv1?
///
/// Checked before v2 parsing when a datagram arrives on the shared ports.
pub fn is_v1(payload: &[u8]) -> bool {
    payload.len() >= 2 && u16::from_be_bytes([payload[0], payload[1]]) == 1
}

/// Format a v1 source UUID.
pub fn format_uuid(uuid: &[u8; 6]) -> String {
    format!(
        "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}",
        uuid[0], uuid[1], uuid[2], uuid[3], uuid[4], uuid[5]
    )
}

/// Splice a v1 UUID into the EUI-64 form a v2 clock identity would use.
///
/// A device running both stacks presents a 6-byte UUID to v1 and an 8-byte
/// clock identity to v2, and they look unrelated. Since v2 identities are
/// conventionally the MAC with `FF:FE` in the middle, converting the v1 UUID
/// the same way is what lets one physical box be recognised as one clock in
/// both worlds — the exact problem of running v1 and v2 on one NIC.
///
/// This is a *convention*, not a guarantee, so callers should treat a match as
/// strong evidence rather than proof.
pub fn uuid_as_clock_identity(uuid: &[u8; 6]) -> [u8; 8] {
    [uuid[0], uuid[1], uuid[2], 0xFF, 0xFE, uuid[3], uuid[4], uuid[5]]
}

/// Parse a PTPv1 message from the UDP payload.
pub fn parse(payload: &[u8]) -> Result<V1Message, V1ParseError> {
    if payload.len() < 40 {
        return Err(V1ParseError::TooShort(payload.len()));
    }
    let version = u16::from_be_bytes([payload[0], payload[1]]);
    if version != 1 {
        return Err(V1ParseError::NotVersion1(version));
    }

    // The subdomain is a fixed 16-byte field padded with NULs; trailing
    // padding is not part of the name.
    let subdomain = payload[4..20]
        .iter()
        .take_while(|&&b| b != 0)
        .map(|&b| b as char)
        .collect::<String>()
        .trim()
        .to_string();

    let mut source_uuid = [0u8; 6];
    source_uuid.copy_from_slice(&payload[22..28]);

    Ok(V1Message {
        // Byte 32 (control), NOT byte 20, names the message.
        message_type: V1MessageType::from_control(payload[32]),
        subdomain,
        source_uuid,
        source_port_id: u16::from_be_bytes([payload[28], payload[29]]),
        sequence_id: u16::from_be_bytes([payload[30], payload[31]]),
        is_event: payload[20] == 1,
        flags: u16::from_be_bytes([payload[34], payload[35]]),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn v1_frame(control: u8, msg_type: u8, seq: u16, subdomain: &str) -> Vec<u8> {
        let mut p = vec![0u8; 44];
        p[0..2].copy_from_slice(&1u16.to_be_bytes()); // versionPTP = 1
        p[2..4].copy_from_slice(&1u16.to_be_bytes()); // versionNetwork = 1
        p[4..4 + subdomain.len()].copy_from_slice(subdomain.as_bytes());
        p[20] = msg_type;
        p[22..28].copy_from_slice(&[0x00, 0x0A, 0x92, 0x01, 0x56, 0xA3]);
        p[28..30].copy_from_slice(&1u16.to_be_bytes());
        p[30..32].copy_from_slice(&seq.to_be_bytes());
        p[32] = control;
        p
    }

    #[test]
    fn parses_a_v1_sync() {
        let m = parse(&v1_frame(0, 1, 900, "_DFLT")).unwrap();
        assert_eq!(m.message_type, V1MessageType::Sync);
        assert_eq!(m.subdomain, "_DFLT");
        assert_eq!(format_uuid(&m.source_uuid), "00:0A:92:01:56:A3");
        assert_eq!(m.sequence_id, 900);
        assert!(m.is_event);
    }

    /// The trap: byte 20 is event-vs-general, byte 32 names the message. If
    /// byte 20 were read as v2's messageType, this Sync (msg_type=1) would be
    /// reported as a Delay_Req.
    #[test]
    fn control_field_names_the_message_not_byte_20() {
        let sync = parse(&v1_frame(0, 1, 1, "_DFLT")).unwrap();
        assert_eq!(sync.message_type, V1MessageType::Sync);

        // Follow_Up is a general message (byte 20 = 2) with control = 2.
        let fu = parse(&v1_frame(2, 2, 1, "_DFLT")).unwrap();
        assert_eq!(fu.message_type, V1MessageType::FollowUp);
        assert!(!fu.is_event);
    }

    #[test]
    fn subdomain_padding_is_not_part_of_the_name() {
        let m = parse(&v1_frame(0, 1, 1, "_ALT1")).unwrap();
        assert_eq!(m.subdomain, "_ALT1");
        assert_eq!(m.subdomain.len(), 5, "NUL padding must be trimmed");
    }

    /// v1 and v2 share the wire, so version discrimination has to be exact.
    #[test]
    fn version_discrimination_is_exact() {
        assert!(is_v1(&v1_frame(0, 1, 1, "_DFLT")));

        // A PTPv2 header: byte 0 is messageType|transportSpecific, byte 1 is
        // the version. As a big-endian u16 that is nowhere near 1.
        let mut v2 = vec![0u8; 40];
        v2[0] = 0x1B; // gPTP Announce
        v2[1] = 0x02;
        assert!(!is_v1(&v2));
        assert_eq!(parse(&v2), Err(V1ParseError::NotVersion1(0x1B02)));
    }

    /// One physical device on both stacks must be recognisable as one clock.
    #[test]
    fn v1_uuid_maps_onto_the_v2_clock_identity_convention() {
        let uuid = [0x00, 0x0A, 0x92, 0x01, 0x56, 0xA3];
        let identity = uuid_as_clock_identity(&uuid);
        // The bench grandmaster, as PTPv2 would name it.
        assert_eq!(
            crate::message::format_clock_id(&identity),
            "00:0A:92:FF:FE:01:56:A3"
        );
        // ...and the round trip holds.
        assert_eq!(crate::message::clock_id_to_mac(&identity), Some(uuid));
    }

    #[test]
    fn short_payloads_are_refused() {
        assert_eq!(parse(&[0, 1, 0, 1]), Err(V1ParseError::TooShort(4)));
    }
}
