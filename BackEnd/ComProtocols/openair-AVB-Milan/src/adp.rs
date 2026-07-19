//! ADP — the AVDECC Discovery Protocol, IEEE 1722.1 clause 6.
//!
//! An AVB entity announces itself by emitting an ADPDU inside an IEEE 1722
//! (AVTP) frame sent to the reserved multicast MAC `91:E0:F0:01:00:00`. There
//! is no IP header anywhere in this path — the frame is the announcement, and
//! everything below parses raw Ethernet.
//!
//! # Frame layout
//!
//! ```text
//! Ethernet: | dst 6 | src 6 | [802.1Q tag 4] | ethertype 0x22F0 |
//! AVTP common control header (12 bytes):
//!   0       subtype = 0x7A (ADP)
//!   1       sv(1) | version(3) | message_type(4)
//!   2..3    valid_time(5) | control_data_length(11)
//!   4..11   entity_id
//! ADPDU body (56 bytes):
//!   12..19  entity_model_id
//!   20..23  entity_capabilities
//!   24..25  talker_stream_sources     26..27  talker_capabilities
//!   28..29  listener_stream_sinks     30..31  listener_capabilities
//!   32..35  controller_capabilities
//!   36..39  available_index
//!   40..47  gptp_grandmaster_id
//!   48      gptp_domain_number        49      reserved
//!   50..51  current_configuration_index
//!   52..53  identify_control_index    54..55  interface_index
//!   56..63  association_id            64..67  reserved
//! ```
//!
//! # What ADP does and does not tell you
//!
//! ADP is the *announcement* only. It carries the entity's ID, its capability
//! bitfields, and its gPTP grandmaster — enough to say "this device exists,
//! it talks AVB, and here is the clock it follows". It does **not** carry
//! channel counts, stream names, or the descriptor tree; those come from
//! AEM enumeration (AECP READ_DESCRIPTOR), which is a request/response
//! conversation with the device, not a broadcast.
//!
//! This module deliberately stops at ADP. Enumeration is a separate, larger
//! job, and a discovery agent that claimed channel counts it never asked for
//! would be inventing them.

/// Reserved multicast MAC for all AVDECC discovery and control traffic.
pub const AVDECC_MULTICAST_MAC: [u8; 6] = [0x91, 0xE0, 0xF0, 0x01, 0x00, 0x00];

/// IEEE 1722 (AVTP) EtherType. Stream data and control share it.
pub const ETHERTYPE_AVTP: u16 = 0x22F0;

/// AVTP subtype for ADP. Stream payloads use other subtypes on the same
/// EtherType, which is why the subtype check exists.
pub const SUBTYPE_ADP: u8 = 0x7A;

/// Total ADPDU size: 12-byte common header + 56-byte body.
pub const ADPDU_LEN: usize = 68;

/// ADP message types (1722.1 §6.2.1.5).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MessageType {
    /// Periodic "I am here" heartbeat.
    EntityAvailable,
    /// Clean shutdown — the entity is leaving the network.
    EntityDeparting,
    /// A controller asking who is out there.
    EntityDiscover,
    /// Reserved / unknown value, kept rather than coerced.
    Other(u8),
}

impl MessageType {
    fn from_bits(bits: u8) -> Self {
        match bits {
            0 => Self::EntityAvailable,
            1 => Self::EntityDeparting,
            2 => Self::EntityDiscover,
            n => Self::Other(n),
        }
    }
}

/// One decoded ADP announcement.
#[derive(Debug, Clone, PartialEq)]
pub struct AdpEntity {
    pub message_type: MessageType,
    /// Source MAC from the Ethernet header — the authoritative address of the
    /// announcing device. Not derived from `entity_id`: the common convention
    /// of embedding the MAC in the entity ID is a convention, not a guarantee.
    pub source_mac: [u8; 6],
    /// Unique 64-bit entity identifier.
    pub entity_id: u64,
    /// Identifies the device's AEM descriptor model — same model id means same
    /// descriptor tree, which is how a controller caches enumeration results.
    pub entity_model_id: u64,
    pub entity_capabilities: u32,
    /// Number of stream sources this entity can transmit.
    pub talker_stream_sources: u16,
    pub talker_capabilities: u16,
    /// Number of stream sinks this entity can receive.
    pub listener_stream_sinks: u16,
    pub listener_capabilities: u16,
    pub controller_capabilities: u32,
    /// Increments whenever the entity's state changes — a jump means the
    /// device changed configuration and any cached enumeration is stale.
    pub available_index: u32,
    /// The gPTP grandmaster this entity is locked to. Two entities showing
    /// different grandmasters are not on the same clock and cannot stream to
    /// each other, which makes this the single most diagnostic field in ADP.
    pub gptp_grandmaster_id: u64,
    pub gptp_domain_number: u8,
    pub current_configuration_index: u16,
    pub identify_control_index: u16,
    pub interface_index: u16,
    pub association_id: u64,
    /// Seconds this announcement stays valid (`valid_time` × 2).
    pub valid_time_secs: u16,
}

/// Why a frame was not an ADP announcement.
///
/// Distinct variants because "too short" is a truncation worth logging while
/// "not AVTP" is simply every other frame on the wire.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AdpError {
    /// Frame shorter than an Ethernet header.
    TooShort,
    /// EtherType is not 0x22F0.
    NotAvtp,
    /// AVTP frame, but a subtype other than ADP — stream data, ACMP, AECP.
    NotAdp(u8),
    /// ADP subtype but the body is truncated.
    ShortAdpdu(usize),
}

/// Parse a raw Ethernet frame as an ADP announcement.
///
/// Handles an optional 802.1Q tag: AVB control frames are sometimes
/// priority-tagged, and the kernel only strips the tag when the NIC offloads
/// it, so both forms reach us in practice.
pub fn parse_frame(frame: &[u8]) -> Result<AdpEntity, AdpError> {
    if frame.len() < 14 {
        return Err(AdpError::TooShort);
    }

    let mut source_mac = [0u8; 6];
    source_mac.copy_from_slice(&frame[6..12]);

    let mut offset = 12;
    let mut ethertype = u16::from_be_bytes([frame[offset], frame[offset + 1]]);
    if ethertype == 0x8100 || ethertype == 0x88A8 {
        // 802.1Q / 802.1ad tag: 4 bytes, then the real EtherType.
        if frame.len() < offset + 8 {
            return Err(AdpError::TooShort);
        }
        offset += 4;
        ethertype = u16::from_be_bytes([frame[offset], frame[offset + 1]]);
    }
    offset += 2;

    if ethertype != ETHERTYPE_AVTP {
        return Err(AdpError::NotAvtp);
    }

    let pdu = &frame[offset..];
    if pdu.is_empty() {
        return Err(AdpError::TooShort);
    }
    let subtype = pdu[0] & 0x7F;
    if subtype != SUBTYPE_ADP {
        return Err(AdpError::NotAdp(subtype));
    }
    if pdu.len() < ADPDU_LEN {
        return Err(AdpError::ShortAdpdu(pdu.len()));
    }

    let be64 = |at: usize| -> u64 {
        let mut b = [0u8; 8];
        b.copy_from_slice(&pdu[at..at + 8]);
        u64::from_be_bytes(b)
    };
    let be32 = |at: usize| -> u32 {
        u32::from_be_bytes([pdu[at], pdu[at + 1], pdu[at + 2], pdu[at + 3]])
    };
    let be16 = |at: usize| -> u16 { u16::from_be_bytes([pdu[at], pdu[at + 1]]) };

    Ok(AdpEntity {
        message_type: MessageType::from_bits(pdu[1] & 0x0F),
        source_mac,
        entity_id: be64(4),
        entity_model_id: be64(12),
        entity_capabilities: be32(20),
        talker_stream_sources: be16(24),
        talker_capabilities: be16(26),
        listener_stream_sinks: be16(28),
        listener_capabilities: be16(30),
        controller_capabilities: be32(32),
        available_index: be32(36),
        gptp_grandmaster_id: be64(40),
        gptp_domain_number: pdu[48],
        current_configuration_index: be16(50),
        identify_control_index: be16(52),
        interface_index: be16(54),
        association_id: be64(56),
        // valid_time is the top 5 bits of byte 2, in units of 2 seconds.
        valid_time_secs: ((pdu[2] >> 3) as u16) * 2,
    })
}

/// Format a 64-bit AVDECC identifier the way controllers display it.
pub fn format_id(id: u64) -> String {
    let b = id.to_be_bytes();
    format!(
        "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}",
        b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7]
    )
}

/// Format a MAC address.
pub fn format_mac(mac: &[u8; 6]) -> String {
    format!(
        "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}",
        mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]
    )
}

/// The OUI (first three octets) of a MAC, as hex.
///
/// Returned as raw hex rather than a vendor name on purpose: mapping OUIs to
/// manufacturers requires the IEEE registry, and guessing a vendor from memory
/// would put an invented brand name on an engineer's screen.
pub fn format_oui(mac: &[u8; 6]) -> String {
    format!("{:02X}:{:02X}:{:02X}", mac[0], mac[1], mac[2])
}

/// Entity capability flags (1722.1 §6.2.1.8), most-significant first.
const ENTITY_CAPS: [(u32, &str); 18] = [
    (0x0002_0000, "ENTITY_NOT_READY"),
    (0x0001_0000, "GENERAL_CONTROLLER_IGNORE"),
    (0x0000_8000, "AEM_INTERFACE_INDEX_VALID"),
    (0x0000_4000, "AEM_IDENTIFY_CONTROL_INDEX_VALID"),
    (0x0000_2000, "AEM_PERSISTENT_ACQUIRE_SUPPORTED"),
    (0x0000_1000, "AEM_AUTHENTICATION_REQUIRED"),
    (0x0000_0800, "AEM_AUTHENTICATION_SUPPORTED"),
    (0x0000_0400, "GPTP_SUPPORTED"),
    (0x0000_0200, "CLASS_B_SUPPORTED"),
    (0x0000_0100, "CLASS_A_SUPPORTED"),
    (0x0000_0080, "VENDOR_UNIQUE_SUPPORTED"),
    (0x0000_0040, "ASSOCIATION_ID_VALID"),
    (0x0000_0020, "ASSOCIATION_ID_SUPPORTED"),
    (0x0000_0010, "LEGACY_AVC"),
    (0x0000_0008, "AEM_SUPPORTED"),
    (0x0000_0004, "GATEWAY_ENTITY"),
    (0x0000_0002, "ADDRESS_ACCESS_SUPPORTED"),
    (0x0000_0001, "EFU_MODE"),
];

/// Talker capability flags (§6.2.1.10). Listener flags use the same bit
/// positions with SINK in place of SOURCE.
const TALKER_CAPS: [(u16, &str); 8] = [
    (0x8000, "IMPLEMENTED"),
    (0x0040, "VIDEO_SOURCE"),
    (0x0020, "AUDIO_SOURCE"),
    (0x0010, "MIDI_SOURCE"),
    (0x0008, "SMPTE_SOURCE"),
    (0x0004, "MEDIA_CLOCK_SOURCE"),
    (0x0002, "CONTROL_SOURCE"),
    (0x0001, "OTHER_SOURCE"),
];

const LISTENER_CAPS: [(u16, &str); 8] = [
    (0x8000, "IMPLEMENTED"),
    (0x0040, "VIDEO_SINK"),
    (0x0020, "AUDIO_SINK"),
    (0x0010, "MIDI_SINK"),
    (0x0008, "SMPTE_SINK"),
    (0x0004, "MEDIA_CLOCK_SINK"),
    (0x0002, "CONTROL_SINK"),
    (0x0001, "OTHER_SINK"),
];

fn decode<T: Copy + std::ops::BitAnd<Output = T> + PartialEq + Default>(
    value: T,
    table: &[(T, &'static str)],
) -> Vec<&'static str> {
    table
        .iter()
        .filter(|(bit, _)| value & *bit != T::default())
        .map(|(_, name)| *name)
        .collect()
}

impl AdpEntity {
    /// Human-readable entity capability flags.
    pub fn entity_capability_names(&self) -> Vec<&'static str> {
        decode(self.entity_capabilities, &ENTITY_CAPS)
    }

    pub fn talker_capability_names(&self) -> Vec<&'static str> {
        decode(self.talker_capabilities, &TALKER_CAPS)
    }

    pub fn listener_capability_names(&self) -> Vec<&'static str> {
        decode(self.listener_capabilities, &LISTENER_CAPS)
    }

    /// True when the entity supports the AVDECC Entity Model — i.e. it can be
    /// enumerated for its descriptor tree. Milan mandates this.
    pub fn supports_aem(&self) -> bool {
        self.entity_capabilities & 0x0000_0008 != 0
    }

    /// Whether this entity *could* be a Milan device, and why we cannot say
    /// more from ADP alone.
    ///
    /// Milan compliance is asserted by answering a Milan Vendor Unique (MVU)
    /// `GET_MILAN_INFO` command — an AECP request/response exchange. It is not
    /// a bit in the ADP announcement. So the honest options here are
    /// "definitely not" (when the entity lacks capabilities Milan requires)
    /// and "possible, ask it" — never a bare "yes".
    pub fn milan_assessment(&self) -> &'static str {
        if !self.supports_aem() {
            "no — AEM not supported, Milan requires it"
        } else if self.entity_capabilities & 0x0000_0400 == 0 {
            "no — gPTP not supported, Milan requires it"
        } else if self.entity_capabilities & 0x0000_0100 == 0 {
            "unlikely — Class A not supported, Milan requires it"
        } else {
            "possible — confirm with MVU GET_MILAN_INFO (not carried in ADP)"
        }
    }

    /// One-line summary for the console.
    pub fn summary(&self) -> String {
        format!(
            "{} | talker {}src listener {}sink | gPTP GM {} domain {}",
            format_id(self.entity_id),
            self.talker_stream_sources,
            self.listener_stream_sinks,
            format_id(self.gptp_grandmaster_id),
            self.gptp_domain_number
        )
    }
}

/// Build an ADP `ENTITY_DISCOVER` frame addressed to all entities.
///
/// This is the one frame this crate transmits, and it is a question, not a
/// change: it is exactly what Hive or any AVDECC controller emits on startup,
/// and it is the Layer 2 equivalent of the mDNS query `openair-dnssd` already
/// sends. An entity ID of zero means "everyone answer".
///
/// Nothing here reserves bandwidth (SRP) or alters a stream connection (ACMP).
/// Those change network state; this does not.
pub fn build_discover_frame(source_mac: [u8; 6]) -> Vec<u8> {
    let mut frame = Vec::with_capacity(14 + ADPDU_LEN);
    frame.extend_from_slice(&AVDECC_MULTICAST_MAC);
    frame.extend_from_slice(&source_mac);
    frame.extend_from_slice(&ETHERTYPE_AVTP.to_be_bytes());

    frame.push(SUBTYPE_ADP);
    // sv=0, version=0, message_type=2 (ENTITY_DISCOVER)
    frame.push(0x02);
    // valid_time=0, control_data_length=56
    frame.push(0x00);
    frame.push(56);
    // entity_id 0 = discover all, then a zeroed body.
    frame.resize(14 + ADPDU_LEN, 0);
    frame
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A synthetic ENTITY_AVAILABLE with every field set to a distinguishable
    /// value, so a field-offset mistake cannot pass by reading a neighbour's
    /// bytes and still looking plausible.
    fn available_frame() -> Vec<u8> {
        let mut f = Vec::new();
        f.extend_from_slice(&AVDECC_MULTICAST_MAC); // dst
        f.extend_from_slice(&[0x00, 0x1B, 0x92, 0x0A, 0x1B, 0x2C]); // src
        f.extend_from_slice(&ETHERTYPE_AVTP.to_be_bytes());

        f.push(SUBTYPE_ADP);
        f.push(0x00); // ENTITY_AVAILABLE
        f.push(31 << 3); // valid_time = 31 -> 62s
        f.push(56);
        f.extend_from_slice(&0x001B_920A_1B2C_0001u64.to_be_bytes()); // entity_id
        f.extend_from_slice(&0x001B_9200_0000_00AAu64.to_be_bytes()); // model_id
        // AEM | CLASS_A | GPTP | AEM_INTERFACE_INDEX_VALID
        f.extend_from_slice(&0x0000_8508u32.to_be_bytes());
        f.extend_from_slice(&8u16.to_be_bytes()); // talker sources
        f.extend_from_slice(&0x8020u16.to_be_bytes()); // IMPLEMENTED|AUDIO_SOURCE
        f.extend_from_slice(&4u16.to_be_bytes()); // listener sinks
        f.extend_from_slice(&0x8020u16.to_be_bytes()); // IMPLEMENTED|AUDIO_SINK
        f.extend_from_slice(&0u32.to_be_bytes()); // controller caps
        f.extend_from_slice(&42u32.to_be_bytes()); // available_index
        f.extend_from_slice(&0x001B_92FF_FE00_0001u64.to_be_bytes()); // gPTP GM
        f.push(0); // gptp domain
        f.push(0); // reserved
        f.extend_from_slice(&1u16.to_be_bytes()); // current_configuration_index
        f.extend_from_slice(&2u16.to_be_bytes()); // identify_control_index
        f.extend_from_slice(&3u16.to_be_bytes()); // interface_index
        f.extend_from_slice(&0u64.to_be_bytes()); // association_id
        f.extend_from_slice(&0u32.to_be_bytes()); // reserved
        f
    }

    #[test]
    fn parses_an_entity_available_announcement() {
        let e = parse_frame(&available_frame()).unwrap();
        assert_eq!(e.message_type, MessageType::EntityAvailable);
        assert_eq!(format_mac(&e.source_mac), "00:1B:92:0A:1B:2C");
        assert_eq!(format_id(e.entity_id), "00:1B:92:0A:1B:2C:00:01");
        assert_eq!(e.entity_model_id, 0x001B_9200_0000_00AA);
        assert_eq!(e.talker_stream_sources, 8);
        assert_eq!(e.listener_stream_sinks, 4);
        assert_eq!(e.available_index, 42);
        assert_eq!(format_id(e.gptp_grandmaster_id), "00:1B:92:FF:FE:00:00:01");
        assert_eq!(e.current_configuration_index, 1);
        assert_eq!(e.identify_control_index, 2);
        assert_eq!(e.interface_index, 3);
        assert_eq!(e.valid_time_secs, 62);
    }

    #[test]
    fn decodes_capability_bitfields() {
        let e = parse_frame(&available_frame()).unwrap();
        assert!(e.supports_aem());
        let caps = e.entity_capability_names();
        assert!(caps.contains(&"AEM_SUPPORTED"));
        assert!(caps.contains(&"CLASS_A_SUPPORTED"));
        assert!(caps.contains(&"GPTP_SUPPORTED"));
        assert!(!caps.contains(&"ENTITY_NOT_READY"));
        assert_eq!(e.talker_capability_names(), vec!["IMPLEMENTED", "AUDIO_SOURCE"]);
        assert_eq!(e.listener_capability_names(), vec!["IMPLEMENTED", "AUDIO_SINK"]);
    }

    /// Milan cannot be asserted from ADP. The assessment must stay hedged for a
    /// capable entity and only ever go negative on hard evidence.
    #[test]
    fn milan_is_never_claimed_from_adp_alone() {
        let e = parse_frame(&available_frame()).unwrap();
        assert!(e.milan_assessment().starts_with("possible"));

        // Strip AEM support: now it definitively is not Milan.
        let mut bytes = available_frame();
        bytes[14 + 20..14 + 24].copy_from_slice(&0u32.to_be_bytes());
        let plain = parse_frame(&bytes).unwrap();
        assert!(plain.milan_assessment().starts_with("no"));
    }

    #[test]
    fn departing_entities_are_distinguished() {
        let mut bytes = available_frame();
        bytes[15] = 0x01;
        assert_eq!(parse_frame(&bytes).unwrap().message_type, MessageType::EntityDeparting);
    }

    /// AVB control frames are sometimes priority-tagged, and the kernel only
    /// strips the tag when the NIC offloads it. Both forms must parse.
    #[test]
    fn vlan_tagged_frames_parse_identically() {
        let plain = available_frame();
        let mut tagged = Vec::new();
        tagged.extend_from_slice(&plain[..12]);
        tagged.extend_from_slice(&[0x81, 0x00, 0xE0, 0x02]); // VLAN 2, PCP 7
        tagged.extend_from_slice(&plain[12..]);
        assert_eq!(parse_frame(&tagged).unwrap(), parse_frame(&plain).unwrap());
    }

    /// AVTP carries stream audio on the same EtherType. A 48kHz stream is
    /// thousands of frames a second and must be rejected on the subtype, not
    /// mistaken for a very short announcement.
    #[test]
    fn stream_data_on_the_same_ethertype_is_rejected() {
        let mut f = Vec::new();
        f.extend_from_slice(&[0x91, 0xE0, 0xF0, 0x00, 0x12, 0x34]);
        f.extend_from_slice(&[0x00, 0x1B, 0x92, 0x0A, 0x1B, 0x2C]);
        f.extend_from_slice(&ETHERTYPE_AVTP.to_be_bytes());
        f.push(0x02); // AAF audio stream subtype
        f.resize(80, 0);
        assert_eq!(parse_frame(&f), Err(AdpError::NotAdp(0x02)));
    }

    #[test]
    fn non_avtp_traffic_is_rejected() {
        let mut f = vec![0u8; 60];
        f[12] = 0x08; // IPv4
        f[13] = 0x00;
        assert_eq!(parse_frame(&f), Err(AdpError::NotAvtp));
        assert_eq!(parse_frame(&[0u8; 6]), Err(AdpError::TooShort));
    }

    #[test]
    fn discover_frame_is_well_formed() {
        let mac = [0xA0, 0x36, 0x9F, 0x2A, 0xC7, 0x78];
        let f = build_discover_frame(mac);
        assert_eq!(f.len(), 14 + ADPDU_LEN);
        assert_eq!(&f[0..6], &AVDECC_MULTICAST_MAC);
        assert_eq!(&f[6..12], &mac);
        assert_eq!(u16::from_be_bytes([f[12], f[13]]), ETHERTYPE_AVTP);
        // It must parse as a DISCOVER addressed to entity 0 (= everyone).
        let parsed = parse_frame(&f).unwrap();
        assert_eq!(parsed.message_type, MessageType::EntityDiscover);
        assert_eq!(parsed.entity_id, 0);
    }
}
