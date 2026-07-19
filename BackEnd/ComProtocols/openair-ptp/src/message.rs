//! PTPv2 / gPTP message parsing — IEEE 1588-2008 and IEEE 802.1AS.
//!
//! Both use the same 34-byte common header and the same wire format; 802.1AS
//! is a *profile* of 1588, not a separate protocol. What distinguishes them is
//! how they are carried and configured, which is why [`Variant`] is derived
//! from the transport and the `transportSpecific` nibble rather than guessed
//! from the payload.
//!
//! ```text
//! PTPv2 common header (34 bytes)
//!   0       majorSdoId / transportSpecific (high nibble) | messageType (low)
//!   1       minorVersionPTP (high nibble) | versionPTP (low nibble) = 2
//!   2..3    messageLength
//!   4       domainNumber
//!   5       minorSdoId (reserved in 2008)
//!   6..7    flagField
//!   8..15   correctionField (int64, nanoseconds × 2^16)
//!   16..19  messageTypeSpecific (reserved in 2008)
//!   20..27  sourcePortIdentity.clockIdentity
//!   28..29  sourcePortIdentity.portNumber
//!   30..31  sequenceId
//!   32      controlField (legacy; messageType is authoritative in v2)
//!   33      logMessageInterval (int8)
//! ```
//!
//! Message bodies follow at offset 34. Only the fields an engineer diagnoses
//! with are extracted — the grandmaster's identity and quality, the timestamps,
//! and the flags that say whether a Follow_Up is coming.

/// Which flavour of PTP a message belongs to.
///
/// This is the distinction the user cares about when three of them share one
/// NIC, and it cannot be read from a single field: it comes from the transport
/// the frame arrived on plus the `transportSpecific` nibble.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Variant {
    /// IEEE 1588-2002. A different header layout entirely — see [`crate::v1`].
    V1,
    /// IEEE 1588-2008/2019 carried over UDP/IPv4 (ports 319/320).
    V2Udp,
    /// IEEE 1588-2008 carried directly over Ethernet, EtherType 0x88F7,
    /// destination `01:1B:19:00:00:00`. Common in AES67/RAVENNA installs.
    V2Ethernet,
    /// IEEE 802.1AS (gPTP). Always Layer 2, destination `01:80:C2:00:00:0E`,
    /// `transportSpecific` = 1. The AVB world's clock.
    Gptp,
}

impl Variant {
    pub fn label(&self) -> &'static str {
        match self {
            Self::V1 => "PTPv1",
            Self::V2Udp => "PTPv2/UDP",
            Self::V2Ethernet => "PTPv2/L2",
            Self::Gptp => "gPTP",
        }
    }
}

/// PTPv2 message types (§13.3.2.2). The low nibble of byte 0.
///
/// Event messages (0x0–0x3) are timestamped on transmit and receive and travel
/// on UDP port 319; general messages (0x8+) carry no hardware timestamp and use
/// port 320. That split is why a Sync and its Follow_Up arrive on *different
/// ports* — a detail that makes captures confusing until you know it.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum MessageType {
    Sync,
    DelayReq,
    PdelayReq,
    PdelayResp,
    FollowUp,
    DelayResp,
    PdelayRespFollowUp,
    Announce,
    Signaling,
    Management,
    Reserved(u8),
}

impl MessageType {
    pub fn from_bits(bits: u8) -> Self {
        match bits {
            0x0 => Self::Sync,
            0x1 => Self::DelayReq,
            0x2 => Self::PdelayReq,
            0x3 => Self::PdelayResp,
            0x8 => Self::FollowUp,
            0x9 => Self::DelayResp,
            0xA => Self::PdelayRespFollowUp,
            0xB => Self::Announce,
            0xC => Self::Signaling,
            0xD => Self::Management,
            n => Self::Reserved(n),
        }
    }

    pub fn label(&self) -> &'static str {
        match self {
            Self::Sync => "Sync",
            Self::DelayReq => "Delay_Req",
            Self::PdelayReq => "Pdelay_Req",
            Self::PdelayResp => "Pdelay_Resp",
            Self::FollowUp => "Follow_Up",
            Self::DelayResp => "Delay_Resp",
            Self::PdelayRespFollowUp => "Pdelay_Resp_Follow_Up",
            Self::Announce => "Announce",
            Self::Signaling => "Signaling",
            Self::Management => "Management",
            Self::Reserved(_) => "Reserved",
        }
    }

    /// Event messages are hardware-timestamped and travel on port 319.
    pub fn is_event(&self) -> bool {
        matches!(self, Self::Sync | Self::DelayReq | Self::PdelayReq | Self::PdelayResp)
    }
}

/// A PTP timestamp: 48-bit seconds plus 32-bit nanoseconds.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct Timestamp {
    pub seconds: u64,
    pub nanos: u32,
}

impl Timestamp {
    fn parse(b: &[u8]) -> Self {
        if b.len() < 10 {
            return Self::default();
        }
        let seconds = ((b[0] as u64) << 40)
            | ((b[1] as u64) << 32)
            | ((b[2] as u64) << 24)
            | ((b[3] as u64) << 16)
            | ((b[4] as u64) << 8)
            | (b[5] as u64);
        Self { seconds, nanos: u32::from_be_bytes([b[6], b[7], b[8], b[9]]) }
    }

    pub fn is_zero(&self) -> bool {
        self.seconds == 0 && self.nanos == 0
    }

    /// Seconds since the PTP epoch as a float, for interval arithmetic.
    pub fn as_secs_f64(&self) -> f64 {
        self.seconds as f64 + self.nanos as f64 / 1e9
    }
}

impl std::fmt::Display for Timestamp {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}.{:09}", self.seconds, self.nanos)
    }
}

/// The `grandmasterClockQuality` triple from an Announce.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct ClockQuality {
    pub class: u8,
    pub accuracy: u8,
    pub offset_scaled_log_variance: u16,
}

impl ClockQuality {
    /// What the clockClass actually means (§7.6.2.5). This is the field that
    /// answers "is the grandmaster still locked to its reference, or has it
    /// fallen into holdover?" — the question behind most drift complaints.
    pub fn class_meaning(&self) -> &'static str {
        match self.class {
            6 => "locked to primary reference (e.g. GPS)",
            7 => "holdover, was primary reference",
            13 => "locked to application-specific reference",
            14 => "holdover, was application-specific reference",
            52 | 187 => "degraded holdover A",
            58 | 193 => "degraded holdover B",
            248 => "default — free-running, no reference",
            255 => "slave-only clock",
            _ => "reserved / profile-specific",
        }
    }

    /// Decoded `clockAccuracy` (§7.6.2.6).
    pub fn accuracy_meaning(&self) -> &'static str {
        match self.accuracy {
            0x20 => "25ns",
            0x21 => "100ns",
            0x22 => "250ns",
            0x23 => "1us",
            0x24 => "2.5us",
            0x25 => "10us",
            0x26 => "25us",
            0x27 => "100us",
            0x28 => "250us",
            0x29 => "1ms",
            0x2A => "2.5ms",
            0x2B => "10ms",
            0x2C => "25ms",
            0x2D => "100ms",
            0x2E => "250ms",
            0x2F => "1s",
            0x30 => "10s",
            0x31 => ">10s",
            0xFE => "unknown",
            _ => "reserved",
        }
    }
}

/// Announce-specific fields — the Best Master Clock Algorithm's inputs.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Announce {
    pub origin_timestamp: Timestamp,
    pub current_utc_offset: i16,
    pub grandmaster_priority1: u8,
    pub grandmaster_quality: ClockQuality,
    pub grandmaster_priority2: u8,
    pub grandmaster_identity: [u8; 8],
    /// Hops from the grandmaster. 0 means this device *is* the grandmaster.
    pub steps_removed: u16,
    pub time_source: u8,
}

impl Announce {
    pub fn time_source_meaning(&self) -> &'static str {
        match self.time_source {
            0x10 => "atomic clock",
            0x20 => "GNSS/GPS",
            0x30 => "terrestrial radio",
            0x40 => "PTP",
            0x50 => "NTP",
            0x60 => "hand set",
            0x90 => "other",
            0xA0 => "internal oscillator",
            _ => "reserved",
        }
    }
}

/// Everything parsed out of one PTPv2/gPTP message.
#[derive(Debug, Clone, PartialEq)]
pub struct PtpMessage {
    pub variant: Variant,
    pub message_type: MessageType,
    /// High nibble of byte 0. 1 identifies 802.1AS.
    pub transport_specific: u8,
    pub version: u8,
    pub message_length: u16,
    pub domain: u8,
    pub flags: u16,
    /// Residence/asymmetry correction in nanoseconds (the wire value is
    /// scaled by 2^16).
    pub correction_ns: f64,
    pub source_clock_identity: [u8; 8],
    pub source_port_number: u16,
    pub sequence_id: u16,
    pub log_message_interval: i8,
    /// Present on Sync, Delay_Req, Follow_Up, Pdelay_* — whichever timestamp
    /// that message type carries at offset 34.
    pub timestamp: Option<Timestamp>,
    /// Present only on Announce.
    pub announce: Option<Announce>,
    /// Present on Delay_Resp and the Pdelay responses: who this answers.
    pub requesting_clock_identity: Option<[u8; 8]>,
    pub requesting_port_number: Option<u16>,
}

/// Why a payload was not a PTPv2 message.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ParseError {
    /// Shorter than the 34-byte common header.
    TooShort(usize),
    /// `versionPTP` is not 2. PTPv1 lands here and is handled by [`crate::v1`].
    NotVersion2(u8),
    /// Header parsed, but the body for this message type is truncated.
    ShortBody { message_type: MessageType, need: usize, got: usize },
}

/// `twoStepFlag` — the single most useful bit in the header.
///
/// When set, the Sync's timestamp is *not* in the Sync: the transmitter could
/// not stamp the outgoing packet with its own departure time, so a Follow_Up
/// carrying the precise time follows. When clear, the Sync is one-step and no
/// Follow_Up will ever arrive. Waiting for one that is never coming is a
/// classic way to misread a capture.
pub const FLAG_TWO_STEP: u16 = 0x0200;
pub const FLAG_ALTERNATE_MASTER: u16 = 0x0100;
pub const FLAG_UNICAST: u16 = 0x0400;
pub const FLAG_LEAP61: u16 = 0x0001;
pub const FLAG_LEAP59: u16 = 0x0002;
pub const FLAG_UTC_OFFSET_VALID: u16 = 0x0004;
pub const FLAG_PTP_TIMESCALE: u16 = 0x0008;
pub const FLAG_TIME_TRACEABLE: u16 = 0x0010;
pub const FLAG_FREQUENCY_TRACEABLE: u16 = 0x0020;

impl PtpMessage {
    /// True when a Follow_Up should be expected for this Sync.
    pub fn is_two_step(&self) -> bool {
        self.flags & FLAG_TWO_STEP != 0
    }

    /// Human-readable flag names, for the live display.
    pub fn flag_names(&self) -> Vec<&'static str> {
        const TABLE: [(u16, &str); 9] = [
            (FLAG_TWO_STEP, "twoStep"),
            (FLAG_UNICAST, "unicast"),
            (FLAG_ALTERNATE_MASTER, "altMaster"),
            (FLAG_LEAP61, "leap61"),
            (FLAG_LEAP59, "leap59"),
            (FLAG_UTC_OFFSET_VALID, "utcValid"),
            (FLAG_PTP_TIMESCALE, "ptpTimescale"),
            (FLAG_TIME_TRACEABLE, "timeTraceable"),
            (FLAG_FREQUENCY_TRACEABLE, "freqTraceable"),
        ];
        TABLE.iter().filter(|(bit, _)| self.flags & bit != 0).map(|(_, n)| *n).collect()
    }

    /// The interval between messages of this type, in seconds.
    ///
    /// `logMessageInterval` is a signed power of two: -3 means 2^-3 = 125ms,
    /// the usual gPTP Sync rate.
    pub fn interval_secs(&self) -> f64 {
        2f64.powi(self.log_message_interval as i32)
    }

    /// Identity of the sending port, as controllers display it.
    pub fn source_id(&self) -> String {
        format!("{}/{}", format_clock_id(&self.source_clock_identity), self.source_port_number)
    }
}

/// Format a 64-bit clock identity the way every PTP tool displays it.
pub fn format_clock_id(id: &[u8; 8]) -> String {
    format!(
        "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}",
        id[0], id[1], id[2], id[3], id[4], id[5], id[6], id[7]
    )
}

/// A clock identity is normally a MAC address with `FF:FE` spliced into the
/// middle (EUI-64). Recovering the MAC is what lets a clock be correlated with
/// a device discovered by another agent.
///
/// Returns `None` when the identity is not EUI-64-derived, rather than
/// returning six bytes that mean nothing.
pub fn clock_id_to_mac(id: &[u8; 8]) -> Option<[u8; 6]> {
    if id[3] == 0xFF && id[4] == 0xFE {
        Some([id[0], id[1], id[2], id[5], id[6], id[7]])
    } else {
        None
    }
}

/// Parse a PTPv2/gPTP message from the PTP payload (no Ethernet/UDP headers).
pub fn parse(payload: &[u8], variant: Variant) -> Result<PtpMessage, ParseError> {
    if payload.len() < 34 {
        return Err(ParseError::TooShort(payload.len()));
    }
    let version = payload[1] & 0x0F;
    if version != 2 {
        return Err(ParseError::NotVersion2(version));
    }

    let message_type = MessageType::from_bits(payload[0] & 0x0F);
    let transport_specific = payload[0] >> 4;

    // correctionField is a 64-bit signed value in nanoseconds scaled by 2^16.
    let correction_raw = i64::from_be_bytes([
        payload[8], payload[9], payload[10], payload[11], payload[12], payload[13], payload[14],
        payload[15],
    ]);

    let mut source_clock_identity = [0u8; 8];
    source_clock_identity.copy_from_slice(&payload[20..28]);

    // 802.1AS sets transportSpecific to 1. A caller that guessed V2Ethernet
    // from the destination MAC alone is corrected here.
    let variant = if transport_specific == 1 && variant == Variant::V2Ethernet {
        Variant::Gptp
    } else {
        variant
    };

    let body = &payload[34..];
    let mut msg = PtpMessage {
        variant,
        message_type,
        transport_specific,
        version,
        message_length: u16::from_be_bytes([payload[2], payload[3]]),
        domain: payload[4],
        flags: u16::from_be_bytes([payload[6], payload[7]]),
        correction_ns: correction_raw as f64 / 65536.0,
        source_clock_identity,
        source_port_number: u16::from_be_bytes([payload[28], payload[29]]),
        sequence_id: u16::from_be_bytes([payload[30], payload[31]]),
        log_message_interval: payload[33] as i8,
        timestamp: None,
        announce: None,
        requesting_clock_identity: None,
        requesting_port_number: None,
    };

    let need = |n: usize| -> Result<(), ParseError> {
        if body.len() < n {
            Err(ParseError::ShortBody { message_type, need: n, got: body.len() })
        } else {
            Ok(())
        }
    };

    match message_type {
        MessageType::Sync
        | MessageType::DelayReq
        | MessageType::FollowUp
        | MessageType::PdelayReq => {
            need(10)?;
            msg.timestamp = Some(Timestamp::parse(&body[..10]));
        }
        MessageType::DelayResp
        | MessageType::PdelayResp
        | MessageType::PdelayRespFollowUp => {
            need(20)?;
            msg.timestamp = Some(Timestamp::parse(&body[..10]));
            let mut req = [0u8; 8];
            req.copy_from_slice(&body[10..18]);
            msg.requesting_clock_identity = Some(req);
            msg.requesting_port_number = Some(u16::from_be_bytes([body[18], body[19]]));
        }
        MessageType::Announce => {
            need(30)?;
            let mut gm = [0u8; 8];
            gm.copy_from_slice(&body[19..27]);
            msg.announce = Some(Announce {
                origin_timestamp: Timestamp::parse(&body[..10]),
                current_utc_offset: i16::from_be_bytes([body[10], body[11]]),
                grandmaster_priority1: body[13],
                grandmaster_quality: ClockQuality {
                    class: body[14],
                    accuracy: body[15],
                    offset_scaled_log_variance: u16::from_be_bytes([body[16], body[17]]),
                },
                grandmaster_priority2: body[18],
                grandmaster_identity: gm,
                steps_removed: u16::from_be_bytes([body[27], body[28]]),
                time_source: body[29],
            });
        }
        _ => {}
    }

    Ok(msg)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The grandmaster the user reported on the bench.
    const GM: [u8; 8] = [0x00, 0x0A, 0x92, 0xFF, 0xFE, 0x01, 0x56, 0xA3];

    fn header(msg_type: u8, transport_specific: u8, seq: u16, domain: u8) -> Vec<u8> {
        let mut p = vec![0u8; 34];
        p[0] = (transport_specific << 4) | msg_type;
        p[1] = 0x02; // versionPTP = 2
        p[4] = domain;
        p[6] = 0x02; // flagField octet 0: twoStepFlag
        p[20..28].copy_from_slice(&GM);
        p[28..30].copy_from_slice(&1u16.to_be_bytes()); // portNumber
        p[30..32].copy_from_slice(&seq.to_be_bytes());
        p[33] = 0xFD; // logMessageInterval = -3 -> 125ms
        p
    }

    #[test]
    fn parses_a_gptp_sync() {
        let mut f = header(0x0, 1, 4521, 0);
        f.extend_from_slice(&[0, 0, 0, 0, 0x68, 0x00, 0x12, 0x34, 0x56, 0x78]); // timestamp
        let m = parse(&f, Variant::V2Ethernet).unwrap();

        // transportSpecific = 1 promotes V2Ethernet to gPTP.
        assert_eq!(m.variant, Variant::Gptp);
        assert_eq!(m.message_type, MessageType::Sync);
        assert_eq!(m.sequence_id, 4521);
        assert_eq!(m.domain, 0);
        assert!(m.is_two_step(), "Follow_Up should be expected");
        assert!(m.message_type.is_event());
        assert_eq!(format_clock_id(&m.source_clock_identity), "00:0A:92:FF:FE:01:56:A3");
        assert_eq!(m.source_id(), "00:0A:92:FF:FE:01:56:A3/1");
        // -3 -> 2^-3 = 125ms, the standard gPTP Sync rate.
        assert!((m.interval_secs() - 0.125).abs() < 1e-9);
    }

    /// PTPv2 over Ethernet is NOT gPTP unless transportSpecific says so. AES67
    /// installs run plain 1588 at Layer 2, and conflating the two would file a
    /// RAVENNA clock as an AVB one.
    #[test]
    fn l2_ptpv2_is_not_promoted_to_gptp() {
        let f = header(0x0, 0, 1, 0);
        let mut f2 = f.clone();
        f2.extend_from_slice(&[0u8; 10]);
        assert_eq!(parse(&f2, Variant::V2Ethernet).unwrap().variant, Variant::V2Ethernet);
        // ...and a UDP-carried message stays UDP regardless.
        assert_eq!(parse(&f2, Variant::V2Udp).unwrap().variant, Variant::V2Udp);
    }

    #[test]
    fn parses_an_announce_with_grandmaster_quality() {
        let mut f = header(0xB, 1, 77, 0);
        let mut body = vec![0u8; 30];
        body[10..12].copy_from_slice(&37i16.to_be_bytes()); // currentUtcOffset
        body[13] = 128; // priority1
        body[14] = 6; // clockClass: locked to primary reference
        body[15] = 0x21; // clockAccuracy: 100ns
        body[16..18].copy_from_slice(&0x436Au16.to_be_bytes());
        body[18] = 128; // priority2
        body[19..27].copy_from_slice(&GM);
        body[27..29].copy_from_slice(&0u16.to_be_bytes()); // stepsRemoved = 0
        body[29] = 0x20; // GNSS
        f.extend_from_slice(&body);

        let m = parse(&f, Variant::V2Ethernet).unwrap();
        let a = m.announce.expect("announce body");
        assert_eq!(format_clock_id(&a.grandmaster_identity), "00:0A:92:FF:FE:01:56:A3");
        assert_eq!(a.current_utc_offset, 37);
        assert_eq!(a.grandmaster_quality.class, 6);
        assert_eq!(a.grandmaster_quality.class_meaning(), "locked to primary reference (e.g. GPS)");
        assert_eq!(a.grandmaster_quality.accuracy_meaning(), "100ns");
        assert_eq!(a.time_source_meaning(), "GNSS/GPS");
        // stepsRemoved 0 means this device IS the grandmaster.
        assert_eq!(a.steps_removed, 0);
    }

    /// The correctionField is scaled by 2^16 — reading it raw overstates the
    /// residence time by 65536×, which looks like a catastrophically broken
    /// network rather than a parsing bug.
    #[test]
    fn correction_field_is_descaled() {
        let mut f = header(0x8, 1, 1, 0);
        // 1500.5ns = 1500.5 * 65536
        let scaled = (1500.5f64 * 65536.0) as i64;
        f[8..16].copy_from_slice(&scaled.to_be_bytes());
        f.extend_from_slice(&[0u8; 10]);
        let m = parse(&f, Variant::Gptp).unwrap();
        assert!((m.correction_ns - 1500.5).abs() < 0.01, "got {}", m.correction_ns);
    }

    /// A negative correction is legal and must survive as negative — an
    /// unsigned read turns a small negative into an enormous positive.
    #[test]
    fn negative_corrections_stay_negative() {
        let mut f = header(0x8, 1, 1, 0);
        f[8..16].copy_from_slice(&(-(250i64 * 65536)).to_be_bytes());
        f.extend_from_slice(&[0u8; 10]);
        assert!((parse(&f, Variant::Gptp).unwrap().correction_ns + 250.0).abs() < 0.01);
    }

    #[test]
    fn parses_delay_resp_requesting_port() {
        let mut f = header(0x9, 0, 55, 0);
        let mut body = vec![0u8; 20];
        body[..10].copy_from_slice(&[0, 0, 0, 0, 0x68, 0x01, 0, 0, 0x03, 0xE8]);
        body[10..18].copy_from_slice(&[0x11; 8]);
        body[18..20].copy_from_slice(&7u16.to_be_bytes());
        f.extend_from_slice(&body);

        let m = parse(&f, Variant::V2Udp).unwrap();
        assert_eq!(m.message_type, MessageType::DelayResp);
        assert_eq!(m.requesting_clock_identity, Some([0x11; 8]));
        assert_eq!(m.requesting_port_number, Some(7));
        assert_eq!(m.timestamp.unwrap().nanos, 1000);
    }

    #[test]
    fn timestamps_use_48_bit_seconds() {
        // 0x0000_6800_0000 seconds — beyond 32 bits would truncate.
        let ts = Timestamp::parse(&[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0, 0, 0x03, 0xE8]);
        assert_eq!(ts.seconds, 0x0102_0304_0506);
        assert_eq!(ts.nanos, 1000);
        assert_eq!(ts.to_string(), "1108152157446.000001000");
    }

    /// Clock identities embed the MAC with FF:FE spliced in. Recovering it is
    /// what lets a PTP clock be matched to a device found by another agent —
    /// but only when the identity really is EUI-64 derived.
    #[test]
    fn clock_identity_yields_a_mac_only_when_eui64() {
        assert_eq!(clock_id_to_mac(&GM), Some([0x00, 0x0A, 0x92, 0x01, 0x56, 0xA3]));
        // Not EUI-64: must refuse rather than invent six bytes.
        assert_eq!(clock_id_to_mac(&[0x11; 8]), None);
    }

    #[test]
    fn ptpv1_and_junk_are_rejected_not_guessed() {
        let mut v1 = vec![0u8; 40];
        v1[1] = 0x01; // versionPTP = 1
        assert_eq!(parse(&v1, Variant::V2Udp), Err(ParseError::NotVersion2(1)));
        assert_eq!(parse(&[0u8; 10], Variant::V2Udp), Err(ParseError::TooShort(10)));

        // Header fine, Announce body truncated: must not read past the buffer.
        let mut short = header(0xB, 1, 1, 0);
        short.extend_from_slice(&[0u8; 12]);
        assert!(matches!(
            parse(&short, Variant::Gptp),
            Err(ParseError::ShortBody { need: 30, got: 12, .. })
        ));
    }

    #[test]
    fn flags_decode_to_names() {
        let mut f = header(0x0, 1, 1, 0);
        f[7] = 0x0C; // ptpTimescale | currentUtcOffsetValid
        f.extend_from_slice(&[0u8; 10]);
        let m = parse(&f, Variant::Gptp).unwrap();
        let names = m.flag_names();
        assert!(names.contains(&"twoStep"));
        assert!(names.contains(&"ptpTimescale"));
        assert!(names.contains(&"utcValid"));
        assert!(!names.contains(&"unicast"));
    }
}
