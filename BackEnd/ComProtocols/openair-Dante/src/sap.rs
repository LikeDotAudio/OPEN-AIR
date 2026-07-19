//! SAP (Session Announcement Protocol, RFC 2974) listener.
//!
//! This is how AES67 streams announce themselves when the vendor did not choose
//! mDNS. Dante uses it exclusively for its AES67 mode: enable AES67 on a device
//! and it stops describing those streams over mDNS entirely and starts pushing
//! SDP payloads to `239.255.255.255:9875`.
//!
//! # Packet layout (RFC 2974 §1)
//!
//! ```text
//!  0                   1                   2                   3
//!  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
//! +-+-+-+-+-+-+-+-+---------------+-------------------------------+
//! |V=1|A|R|T|E|C| auth len      |         msg id hash             |
//! +---------------+---------------+-------------------------------+
//! |             originating source (32 or 128 bits)               |
//! +---------------------------------------------------------------+
//! |                    optional authentication data               |
//! +---------------------------------------------------------------+
//! |            optional payload type ("application/sdp\0")        |
//! +---------------------------------------------------------------+
//! |                          SDP payload                          |
//! ```
//!
//! The payload-type string is optional and its presence must be *detected*, not
//! assumed — some senders omit it and start the SDP immediately.

/// One decoded SAP announcement.
#[derive(Debug, Clone, PartialEq)]
pub struct SapAnnouncement {
    /// True when the `T` bit is set: this is a session *deletion*, not an
    /// announcement. Treating a deletion as an announcement would resurrect
    /// streams that have just been torn down.
    pub is_deletion: bool,
    /// The originating source address from the header.
    pub origin: String,
    /// The raw SDP payload.
    pub sdp: String,
}

/// Parse a SAP datagram.
///
/// Returns `None` for anything that is not a well-formed v1 SAP packet, rather
/// than guessing at malformed input — this socket receives whatever else is on
/// the multicast group.
pub fn parse(packet: &[u8]) -> Option<SapAnnouncement> {
    if packet.len() < 8 {
        return None;
    }
    let flags = packet[0];
    // Version must be 1 (bits 5-7 of the first octet).
    if (flags >> 5) & 0x07 != 1 {
        return None;
    }
    let addr_is_ipv6 = flags & 0x10 != 0; // A bit
    let is_deletion = flags & 0x04 != 0; // T bit
    let encrypted = flags & 0x02 != 0; // E bit
    if encrypted {
        // Nothing useful can be read; do not pretend otherwise.
        return None;
    }

    let auth_len = packet[1] as usize;
    let addr_len = if addr_is_ipv6 { 16 } else { 4 };

    let origin = if addr_is_ipv6 {
        packet.get(4..4 + 16).map(|b| {
            let mut seg = [0u16; 8];
            for (i, s) in seg.iter_mut().enumerate() {
                *s = u16::from_be_bytes([b[i * 2], b[i * 2 + 1]]);
            }
            std::net::Ipv6Addr::from(seg).to_string()
        })?
    } else {
        packet
            .get(4..8)
            .map(|b| format!("{}.{}.{}.{}", b[0], b[1], b[2], b[3]))?
    };

    // Header + address + authentication data (counted in 32-bit words).
    let mut offset = 4 + addr_len + auth_len * 4;
    if offset >= packet.len() {
        return None;
    }

    // Optional NUL-terminated payload type. Detect it rather than assume it:
    // if the bytes at `offset` look like SDP already ("v=0"), there is none.
    let rest = &packet[offset..];
    if !rest.starts_with(b"v=") {
        if let Some(nul) = rest.iter().position(|&b| b == 0) {
            // Only skip it when it really is a MIME type, so a stray NUL inside
            // an unexpected payload cannot silently eat the record.
            let candidate = String::from_utf8_lossy(&rest[..nul]).to_ascii_lowercase();
            if candidate.contains("sdp") || candidate.contains('/') {
                offset += nul + 1;
            }
        }
    }

    let sdp = String::from_utf8_lossy(packet.get(offset..)?).to_string();
    if !sdp.contains("v=0") {
        return None;
    }

    Some(SapAnnouncement { is_deletion, origin, sdp })
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Build a SAP packet the way a real sender does.
    fn packet(flags: u8, origin: [u8; 4], with_type: bool, sdp: &str) -> Vec<u8> {
        let mut p = vec![flags, 0, 0x12, 0x34];
        p.extend_from_slice(&origin);
        if with_type {
            p.extend_from_slice(b"application/sdp\0");
        }
        p.extend_from_slice(sdp.as_bytes());
        p
    }

    const SDP: &str = "v=0\no=- 6 0 IN IP4 44.44.44.173\ns=Digital inputs 1-2\n\
                       m=audio 5004 RTP/AVP 98\na=rtpmap:98 L24/48000/2\n";

    #[test]
    fn parses_announcement_with_payload_type() {
        let a = parse(&packet(0x20, [44, 44, 44, 173], true, SDP)).expect("should parse");
        assert!(!a.is_deletion);
        assert_eq!(a.origin, "44.44.44.173");
        assert!(a.sdp.starts_with("v=0"));
    }

    /// The payload-type string is optional; senders that omit it must still work.
    #[test]
    fn parses_announcement_without_payload_type() {
        let a = parse(&packet(0x20, [10, 0, 0, 5], false, SDP)).expect("should parse");
        assert_eq!(a.origin, "10.0.0.5");
        assert!(a.sdp.starts_with("v=0"));
    }

    /// A deletion must not be mistaken for an announcement, or torn-down streams
    /// reappear.
    #[test]
    fn detects_session_deletion() {
        let a = parse(&packet(0x24, [44, 44, 44, 173], true, SDP)).expect("should parse");
        assert!(a.is_deletion);
    }

    #[test]
    fn rejects_non_sap_and_encrypted_traffic() {
        assert!(parse(b"not a sap packet at all").is_none());
        assert!(parse(&[]).is_none());
        // E bit set: unreadable, so no claim is made.
        assert!(parse(&packet(0x22, [1, 2, 3, 4], true, SDP)).is_none());
        // Version 0 is not SAP v1.
        assert!(parse(&packet(0x00, [1, 2, 3, 4], true, SDP)).is_none());
    }

    #[test]
    fn rejects_payload_that_is_not_sdp() {
        let p = packet(0x20, [1, 2, 3, 4], false, "this is not sdp");
        assert!(parse(&p).is_none());
    }
}
