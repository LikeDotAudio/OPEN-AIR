//! SAP packet header parsing — RFC 2974.
//!
//! A SAP packet is a small binary header followed by the payload the
//! announcement carries, which for every AoIP device in practice is SDP text:
//!
//! ```text
//!  0                   1                   2                   3
//!  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
//! +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//! | V=1 |A|R|T|E|C|  auth len     |         msg id hash           |
//! +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//! |                originating source (32 or 128 bits)            |
//! +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//! |                    optional authentication data               |
//! +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//! |            optional payload type, NUL-terminated              |
//! +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//! |                            payload                            |
//! +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
//! ```
//!
//! Two flags decide whether a packet is usable, and both are refusals rather
//! than best-effort guesses:
//!
//! * **E (encrypted)** — the payload is ciphertext. There is nothing to read.
//! * **C (compressed)** — the payload is zlib-deflated. We do not carry a
//!   decompressor, so the announcement is skipped rather than published as
//!   garbage. No AES67 device observed on the bench sets this bit.
//!
//! The **T** flag is the announce/delete distinction, and it is the reason a
//! SAP listener can clear a vanished stream at all: unlike mDNS there is no
//! goodbye packet with a service name, only "the session whose SDP hashes to
//! this id is gone".

use std::net::{IpAddr, Ipv4Addr, Ipv6Addr};

/// One decoded SAP packet.
#[derive(Debug, Clone, PartialEq)]
pub struct SapPacket {
    /// `T` flag set — this is a session *deletion*, not an announcement.
    pub is_delete: bool,
    /// The announcing node's own address, from the header rather than the UDP
    /// source. These agree in practice, but the header is what RFC 2974 defines
    /// as identity, and a relay (RAV2SAP, for one) rewrites the UDP source
    /// while preserving this field.
    pub origin: IpAddr,
    /// 16-bit message id hash. Combined with `origin` it identifies a session
    /// across announcements, and is the only handle a deletion packet is
    /// guaranteed to carry.
    pub msg_id: u16,
    /// Declared payload type, e.g. `application/sdp`. Empty when the sender
    /// omitted it — which RFC 2974 says means SDP, so absence is not a problem.
    pub payload_type: String,
    /// The payload itself, as text.
    pub payload: String,
}

/// Why a packet could not be decoded.
///
/// These are distinct variants rather than a bare `None` so the listener can
/// log an encrypted announcement differently from a truncated one: the first is
/// a working device we choose not to read, the second is a network problem.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SapError {
    /// Fewer bytes than the fixed header requires.
    TooShort,
    /// Version field is not 1. Nothing else is deployed; treating an unknown
    /// version as v1 would be inventing a wire format.
    UnsupportedVersion(u8),
    /// `E` flag set — payload is encrypted.
    Encrypted,
    /// `C` flag set — payload is zlib-compressed and we carry no decompressor.
    Compressed,
    /// Header claims more auth/address bytes than the datagram contains.
    Truncated,
}

/// Decode a SAP datagram.
pub fn parse(buf: &[u8]) -> Result<SapPacket, SapError> {
    if buf.len() < 8 {
        return Err(SapError::TooShort);
    }

    let flags = buf[0];
    let version = (flags >> 5) & 0b111;
    if version != 1 {
        return Err(SapError::UnsupportedVersion(version));
    }

    let addr_is_v6 = flags & 0b0001_0000 != 0; // A
    let is_delete = flags & 0b0000_0100 != 0; // T
    if flags & 0b0000_0010 != 0 {
        return Err(SapError::Encrypted); // E
    }
    if flags & 0b0000_0001 != 0 {
        return Err(SapError::Compressed); // C
    }

    // Auth length counts 32-bit words, not bytes.
    let auth_bytes = buf[1] as usize * 4;
    let msg_id = u16::from_be_bytes([buf[2], buf[3]]);

    let addr_bytes = if addr_is_v6 { 16 } else { 4 };
    let addr_end = 4 + addr_bytes;
    if buf.len() < addr_end + auth_bytes {
        return Err(SapError::Truncated);
    }

    let origin = if addr_is_v6 {
        let mut octets = [0u8; 16];
        octets.copy_from_slice(&buf[4..addr_end]);
        IpAddr::V6(Ipv6Addr::from(octets))
    } else {
        IpAddr::V4(Ipv4Addr::new(buf[4], buf[5], buf[6], buf[7]))
    };

    let body = &buf[addr_end + auth_bytes..];

    // The payload type is optional. RFC 2974 says a sender may omit it, in
    // which case the payload is SDP — and an SDP record always begins `v=0`,
    // which is how we tell an omitted type from a present one without guessing.
    let (payload_type, payload) = match body.iter().position(|&b| b == 0) {
        Some(nul) if !body.starts_with(b"v=") => (
            String::from_utf8_lossy(&body[..nul]).trim().to_string(),
            &body[nul + 1..],
        ),
        _ => (String::new(), body),
    };

    Ok(SapPacket {
        is_delete,
        origin,
        msg_id,
        payload_type,
        payload: String::from_utf8_lossy(payload).to_string(),
    })
}

impl SapPacket {
    /// True when this packet carries SDP — either declared as such, or with the
    /// type omitted (which RFC 2974 defines as SDP).
    ///
    /// Anything else on 9875 is somebody else's protocol and is left alone.
    pub fn is_sdp(&self) -> bool {
        self.payload_type.is_empty()
            || self.payload_type.eq_ignore_ascii_case("application/sdp")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A Dante-in-AES67-mode announcement, header hand-built around a real SDP
    /// body: v1, IPv4, announce, no auth, explicit `application/sdp`.
    fn announce_bytes() -> Vec<u8> {
        let mut p = vec![0x20, 0x00, 0xAB, 0xCD, 44, 44, 44, 12];
        p.extend_from_slice(b"application/sdp\0");
        p.extend_from_slice(b"v=0\r\no=- 1 1 IN IP4 44.44.44.12\r\ns=Dante-Out\r\n");
        p
    }

    #[test]
    fn parses_an_announcement() {
        let p = parse(&announce_bytes()).unwrap();
        assert!(!p.is_delete);
        assert_eq!(p.origin, "44.44.44.12".parse::<IpAddr>().unwrap());
        assert_eq!(p.msg_id, 0xABCD);
        assert_eq!(p.payload_type, "application/sdp");
        assert!(p.is_sdp());
        assert!(p.payload.starts_with("v=0"));
    }

    #[test]
    fn t_flag_marks_a_deletion() {
        let mut bytes = announce_bytes();
        bytes[0] |= 0b0000_0100;
        assert!(parse(&bytes).unwrap().is_delete);
    }

    /// Senders that omit the payload type are legal and mean SDP. The body
    /// starting `v=` is what keeps us from eating the first SDP line looking
    /// for a NUL that was never written.
    #[test]
    fn omitted_payload_type_is_still_sdp() {
        let mut p = vec![0x20, 0x00, 0x00, 0x01, 10, 0, 0, 5];
        p.extend_from_slice(b"v=0\r\ns=Bare\r\n");
        let parsed = parse(&p).unwrap();
        assert_eq!(parsed.payload_type, "");
        assert!(parsed.is_sdp());
        assert_eq!(parsed.payload, "v=0\r\ns=Bare\r\n");
    }

    /// Auth data is counted in 32-bit words and must be stepped over, not
    /// parsed. Getting this wrong shifts the whole payload.
    #[test]
    fn authentication_data_is_skipped() {
        let mut p = vec![0x20, 0x02, 0x00, 0x01, 10, 0, 0, 5];
        p.extend_from_slice(&[0xDE; 8]); // 2 words of auth
        p.extend_from_slice(b"v=0\r\ns=Signed\r\n");
        assert_eq!(parse(&p).unwrap().payload, "v=0\r\ns=Signed\r\n");
    }

    #[test]
    fn ipv6_origin_widens_the_header() {
        let mut p = vec![0x30, 0x00, 0x00, 0x01];
        p.extend_from_slice(&[0u8; 15]);
        p.push(1); // ::1
        p.extend_from_slice(b"v=0\r\n");
        let parsed = parse(&p).unwrap();
        assert_eq!(parsed.origin, "::1".parse::<IpAddr>().unwrap());
    }

    #[test]
    fn unreadable_payloads_are_refused_not_guessed() {
        let mut enc = announce_bytes();
        enc[0] |= 0b0000_0010;
        assert_eq!(parse(&enc), Err(SapError::Encrypted));

        let mut comp = announce_bytes();
        comp[0] |= 0b0000_0001;
        assert_eq!(parse(&comp), Err(SapError::Compressed));

        assert_eq!(parse(&[0x20, 0x00, 0x00]), Err(SapError::TooShort));
        assert_eq!(parse(&[0x00; 8]), Err(SapError::UnsupportedVersion(0)));

        // Claims 4 words (16 bytes) of auth in an 8-byte-body datagram.
        let mut short = announce_bytes();
        short[1] = 0xFF;
        assert_eq!(parse(&short), Err(SapError::Truncated));
    }

    #[test]
    fn non_sdp_payloads_are_not_ours() {
        let mut p = vec![0x20, 0x00, 0x00, 0x01, 10, 0, 0, 5];
        p.extend_from_slice(b"application/mbms\0somebody-elses-protocol");
        assert!(!parse(&p).unwrap().is_sdp());
    }
}
