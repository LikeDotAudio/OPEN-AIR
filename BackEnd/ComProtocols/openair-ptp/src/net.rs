//! Capture for all three PTP transports at once.
//!
//! Running PTPv1, PTPv2 and gPTP on one NIC means listening two different ways
//! simultaneously, because they do not share a transport:
//!
//! | Variant | Transport | Address | Privilege |
//! |---|---|---|---|
//! | PTPv1 | UDP/IPv4 | `224.0.1.129` ports 319/320 | bind <1024 |
//! | PTPv2 | UDP/IPv4 | `224.0.1.129` ports 319/320 | bind <1024 |
//! | PTPv2 | Ethernet | `01:1B:19:00:00:00`, EtherType 0x88F7 | `CAP_NET_RAW` |
//! | gPTP | Ethernet | `01:80:C2:00:00:0E`, EtherType 0x88F7 | `CAP_NET_RAW` |
//!
//! PTPv1 and PTPv2 share the group *and* the ports, so one socket receives
//! both and the version byte sorts them out. That sharing is precisely how a
//! v1 device goes unnoticed on a network everyone believes is v2-only.
//!
//! Event messages (Sync, Delay_Req, Pdelay_*) use port 319 and general
//! messages (Follow_Up, Delay_Resp, Announce) use port 320 — so a Sync and its
//! own Follow_Up arrive on *different sockets*. Both are polled here and merged
//! into one stream, which is what makes the pairing in [`crate::flow`] possible.
//!
//! # Privileges
//!
//! Ports 319 and 320 are below 1024, and raw Ethernet capture needs
//! `CAP_NET_RAW`. Grant both:
//!
//! ```text
//! sudo setcap cap_net_raw,cap_net_bind_service+eip <binary>
//! ```
//!
//! Each transport is opened independently and a failure on one is reported
//! rather than fatal: seeing only gPTP because the UDP bind was refused is a
//! useful, honest partial result — as long as it says so.

use crate::message::Variant;
use std::io;
use std::net::{Ipv4Addr, SocketAddr, UdpSocket};

/// PTP event messages (hardware-timestamped).
pub const PORT_EVENT: u16 = 319;
/// PTP general messages.
pub const PORT_GENERAL: u16 = 320;

/// The primary PTP multicast group, shared by v1 and v2.
pub const PTP_PRIMARY_GROUP: Ipv4Addr = Ipv4Addr::new(224, 0, 1, 129);
/// Peer-delay messages over UDP (§ Annex D) use a link-local group.
pub const PTP_PDELAY_GROUP: Ipv4Addr = Ipv4Addr::new(224, 0, 0, 107);

/// PTPv1 alternate subdomain groups.
///
/// PTPv2 puts the domain number in the payload, so every domain shares
/// `224.0.1.129`. **PTPv1 does not** — its `_ALT1`/`_ALT2`/`_ALT3` subdomains
/// are carried on separate multicast addresses. A listener joined only to the
/// primary group sees the `_DFLT` subdomain and is structurally blind to the
/// rest: not "no v1 traffic", but "no v1 traffic we subscribed to", which looks
/// identical from the outside.
pub const PTP_V1_ALT_GROUPS: [Ipv4Addr; 3] = [
    Ipv4Addr::new(224, 0, 1, 130),
    Ipv4Addr::new(224, 0, 1, 131),
    Ipv4Addr::new(224, 0, 1, 132),
];

/// EtherType for PTP over Ethernet (both plain 1588 and 802.1AS).
pub const ETHERTYPE_PTP: u16 = 0x88F7;
/// Destination MAC for non-peer-delay PTPv2 over Ethernet.
pub const MAC_PTP_PRIMARY: [u8; 6] = [0x01, 0x1B, 0x19, 0x00, 0x00, 0x00];
/// Destination MAC for 802.1AS (gPTP) and peer-delay messages.
pub const MAC_PTP_PEER_DELAY: [u8; 6] = [0x01, 0x80, 0xC2, 0x00, 0x00, 0x0E];

/// One captured PTP payload plus where it came from.
pub struct Captured {
    /// PTP payload only — Ethernet/UDP headers already stripped.
    pub payload: Vec<u8>,
    /// Best guess at the variant from the transport alone. The parser refines
    /// it (a Layer 2 frame with `transportSpecific` = 1 becomes gPTP).
    pub variant: Variant,
    /// Source address, formatted for display: an IP for UDP, a MAC for L2.
    pub source: String,
    /// Which UDP port, or `None` for Layer 2.
    pub port: Option<u16>,
    pub interface: String,
}

/// Explain a capture failure in terms of the fix.
pub fn explain_error(e: &io::Error) -> String {
    match e.raw_os_error() {
        Some(libc::EPERM) | Some(libc::EACCES) => concat!(
            "permission denied — PTP needs privileged ports (319/320) and raw capture for gPTP.\n",
            "         Grant both once:  sudo setcap cap_net_raw,cap_net_bind_service+eip <binary>\n",
            "         ...or run with sudo."
        )
        .to_string(),
        _ => e.to_string(),
    }
}

/// Interfaces we can listen on, excluding loopback and virtual bridges.
pub fn list_interfaces() -> io::Result<Vec<(String, u32, [u8; 6], Ipv4Addr)>> {
    let mut out = Vec::new();
    for entry in std::fs::read_dir("/sys/class/net")? {
        let entry = entry?;
        let name = entry.file_name().to_string_lossy().to_string();
        if name == "lo" || name.starts_with("br-") || name.starts_with("docker") {
            continue;
        }
        let mac_text = std::fs::read_to_string(entry.path().join("address"))
            .unwrap_or_default()
            .trim()
            .to_string();
        let octets: Vec<&str> = mac_text.split(':').collect();
        if octets.len() != 6 {
            continue;
        }
        let mut mac = [0u8; 6];
        for (slot, o) in mac.iter_mut().zip(&octets) {
            *slot = u8::from_str_radix(o, 16).unwrap_or(0);
        }
        if mac == [0u8; 6] {
            continue;
        }
        let index = match std::ffi::CString::new(name.clone()) {
            Ok(c) => unsafe { libc::if_nametoindex(c.as_ptr()) },
            Err(_) => 0,
        };
        if index == 0 {
            continue;
        }
        let ip = local_ipv4(&name).unwrap_or(Ipv4Addr::UNSPECIFIED);
        out.push((name, index, mac, ip));
    }
    out.sort_by(|a, b| a.0.cmp(&b.0));
    Ok(out)
}

/// The IPv4 address bound to an interface, via `SIOCGIFADDR`.
fn local_ipv4(name: &str) -> Option<Ipv4Addr> {
    let fd = unsafe { libc::socket(libc::AF_INET, libc::SOCK_DGRAM, 0) };
    if fd < 0 {
        return None;
    }
    let mut req: libc::ifreq = unsafe { std::mem::zeroed() };
    for (i, b) in name.bytes().take(15).enumerate() {
        req.ifr_name[i] = b as libc::c_char;
    }
    let rc = unsafe { libc::ioctl(fd, libc::SIOCGIFADDR, &mut req) };
    let addr = if rc == 0 {
        let sa = unsafe { &*(&req.ifr_ifru as *const _ as *const libc::sockaddr_in) };
        Some(Ipv4Addr::from(u32::from_be(sa.sin_addr.s_addr)))
    } else {
        None
    };
    unsafe { libc::close(fd) };
    addr
}

/// A UDP socket bound to one PTP port, joined to the PTP groups.
pub struct UdpCapture {
    socket: UdpSocket,
    pub port: u16,
}

impl UdpCapture {
    /// Bind a PTP UDP port and join the multicast groups on every interface.
    pub fn open(port: u16, interfaces: &[(String, u32, [u8; 6], Ipv4Addr)]) -> io::Result<Self> {
        let socket = socket2::Socket::new(
            socket2::Domain::IPV4,
            socket2::Type::DGRAM,
            Some(socket2::Protocol::UDP),
        )?;
        // A PTP daemon (ptp4l, or the device's own stack) very likely already
        // holds these ports. Multicast listeners are meant to coexist; without
        // reuse, whoever starts second simply fails.
        socket.set_reuse_address(true)?;
        #[cfg(unix)]
        socket.set_reuse_port(true)?;
        socket.bind(&SocketAddr::from((Ipv4Addr::UNSPECIFIED, port)).into())?;
        socket.set_read_timeout(Some(std::time::Duration::from_millis(200)))?;
        let socket: UdpSocket = socket.into();

        let groups: Vec<Ipv4Addr> = [PTP_PRIMARY_GROUP, PTP_PDELAY_GROUP]
            .into_iter()
            .chain(PTP_V1_ALT_GROUPS)
            .collect();
        for group in groups {
            // UNSPECIFIED covers the single-homed case; per-interface joins are
            // what make a multi-homed host hear the audio VLAN as well.
            let _ = socket.join_multicast_v4(&group, &Ipv4Addr::UNSPECIFIED);
            for (_, _, _, ip) in interfaces {
                if !ip.is_unspecified() {
                    let _ = socket.join_multicast_v4(&group, ip);
                }
            }
        }
        Ok(Self { socket, port })
    }

    /// Receive one datagram. `Ok(None)` on timeout.
    pub fn recv(&self, buf: &mut [u8]) -> io::Result<Option<Captured>> {
        match self.socket.recv_from(buf) {
            Ok((n, from)) => Ok(Some(Captured {
                payload: buf[..n].to_vec(),
                // Refined by the parser: v1 is detected from the payload.
                variant: Variant::V2Udp,
                source: from.ip().to_string(),
                port: Some(self.port),
                interface: "udp".to_string(),
            })),
            Err(ref e)
                if matches!(
                    e.kind(),
                    io::ErrorKind::WouldBlock | io::ErrorKind::TimedOut
                ) =>
            {
                Ok(None)
            }
            Err(e) => Err(e),
        }
    }
}

/// Raw Layer 2 capture for PTP over Ethernet and gPTP.
///
/// Shares its approach with `openair-avb-milan`'s AVDECC capture — same
/// `AF_PACKET` socket, same multicast-membership-not-promiscuous reasoning,
/// different EtherType and groups. Two users is not yet three, so the shared
/// abstraction is deliberately not extracted; see this crate's README.
pub struct L2Capture {
    fd: i32,
}

impl Drop for L2Capture {
    fn drop(&mut self) {
        unsafe { libc::close(self.fd) };
    }
}

impl L2Capture {
    /// Open a raw socket filtered to EtherType 0x88F7 and join both PTP
    /// multicast MACs on every interface.
    pub fn open(interfaces: &[(String, u32, [u8; 6], Ipv4Addr)]) -> io::Result<Self> {
        let proto = (ETHERTYPE_PTP).to_be() as i32;
        let fd = unsafe { libc::socket(libc::AF_PACKET, libc::SOCK_RAW, proto) };
        if fd < 0 {
            return Err(io::Error::last_os_error());
        }
        let cap = L2Capture { fd };

        let tv = libc::timeval { tv_sec: 0, tv_usec: 200_000 };
        unsafe {
            libc::setsockopt(
                fd,
                libc::SOL_SOCKET,
                libc::SO_RCVTIMEO,
                &tv as *const _ as *const libc::c_void,
                std::mem::size_of::<libc::timeval>() as libc::socklen_t,
            );
        }

        for (_, index, _, _) in interfaces {
            for mac in [MAC_PTP_PRIMARY, MAC_PTP_PEER_DELAY] {
                let _ = cap.join_group(*index, mac);
            }
        }
        Ok(cap)
    }

    fn join_group(&self, if_index: u32, mac: [u8; 6]) -> io::Result<()> {
        let mut mreq: libc::packet_mreq = unsafe { std::mem::zeroed() };
        mreq.mr_ifindex = if_index as i32;
        mreq.mr_type = libc::PACKET_MR_MULTICAST as u16;
        mreq.mr_alen = 6;
        mreq.mr_address[..6].copy_from_slice(&mac);
        let rc = unsafe {
            libc::setsockopt(
                self.fd,
                libc::SOL_PACKET,
                libc::PACKET_ADD_MEMBERSHIP,
                &mreq as *const _ as *const libc::c_void,
                std::mem::size_of::<libc::packet_mreq>() as libc::socklen_t,
            )
        };
        if rc < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(())
    }

    /// Receive one frame, stripping the Ethernet (and any VLAN) header.
    pub fn recv(&self, buf: &mut [u8], name_of: &dyn Fn(u32) -> String) -> io::Result<Option<Captured>> {
        let mut addr: libc::sockaddr_ll = unsafe { std::mem::zeroed() };
        let mut addr_len = std::mem::size_of::<libc::sockaddr_ll>() as libc::socklen_t;
        let n = unsafe {
            libc::recvfrom(
                self.fd,
                buf.as_mut_ptr() as *mut libc::c_void,
                buf.len(),
                0,
                &mut addr as *mut _ as *mut libc::sockaddr,
                &mut addr_len,
            )
        };
        if n < 0 {
            let e = io::Error::last_os_error();
            return match e.raw_os_error() {
                Some(libc::EAGAIN) | Some(libc::EINTR) => Ok(None),
                _ => Err(e),
            };
        }
        let frame = &buf[..n as usize];
        let Some((payload, dst_mac, src_mac)) = strip_ethernet(frame) else {
            return Ok(None);
        };

        // The destination MAC is the first hint at which flavour this is; the
        // parser corrects it from transportSpecific.
        let variant = if dst_mac == MAC_PTP_PEER_DELAY { Variant::Gptp } else { Variant::V2Ethernet };

        Ok(Some(Captured {
            payload: payload.to_vec(),
            variant,
            source: crate::v1::format_uuid(&src_mac),
            port: None,
            interface: name_of(addr.sll_ifindex as u32),
        }))
    }
}

/// Strip the Ethernet header (and an 802.1Q tag if present), returning the PTP
/// payload with the destination and source MACs.
///
/// PTP frames on an AVB network are routinely priority-tagged — gPTP is class
/// SR-A traffic — and the kernel only strips the tag when the NIC offloads it.
pub fn strip_ethernet(frame: &[u8]) -> Option<(&[u8], [u8; 6], [u8; 6])> {
    if frame.len() < 14 {
        return None;
    }
    let mut dst = [0u8; 6];
    let mut src = [0u8; 6];
    dst.copy_from_slice(&frame[0..6]);
    src.copy_from_slice(&frame[6..12]);

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
    if ethertype != ETHERTYPE_PTP {
        return None;
    }
    Some((&frame[offset..], dst, src))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn l2_frame(dst: [u8; 6], tagged: bool) -> Vec<u8> {
        let mut f = Vec::new();
        f.extend_from_slice(&dst);
        f.extend_from_slice(&[0x00, 0x0A, 0x92, 0x01, 0x56, 0xA3]);
        if tagged {
            f.extend_from_slice(&[0x81, 0x00, 0xE0, 0x02]); // PCP 7, VLAN 2
        }
        f.extend_from_slice(&ETHERTYPE_PTP.to_be_bytes());
        f.extend_from_slice(&[0x10, 0x02, 0x00, 0x2C]); // gPTP Sync header start
        f
    }

    #[test]
    fn strips_untagged_and_tagged_frames_identically() {
        let untagged_frame = l2_frame(MAC_PTP_PEER_DELAY, false);
        let tagged_frame = l2_frame(MAC_PTP_PEER_DELAY, true);
        let (plain, dst, src) = strip_ethernet(&untagged_frame).unwrap();
        let (tagged, dst2, _) = strip_ethernet(&tagged_frame).unwrap();
        assert_eq!(plain, tagged, "the VLAN tag must not shift the payload");
        assert_eq!(dst, MAC_PTP_PEER_DELAY);
        assert_eq!(dst2, MAC_PTP_PEER_DELAY);
        assert_eq!(format_uuid_local(&src), "00:0A:92:01:56:A3");
    }

    fn format_uuid_local(m: &[u8; 6]) -> String {
        crate::v1::format_uuid(m)
    }

    /// The two L2 destination MACs distinguish gPTP from plain 1588-over-
    /// Ethernet before the payload is even read.
    #[test]
    fn destination_mac_separates_gptp_from_l2_ptpv2() {
        assert_ne!(MAC_PTP_PRIMARY, MAC_PTP_PEER_DELAY);
        let frame = l2_frame(MAC_PTP_PRIMARY, false);
        let (_, dst, _) = strip_ethernet(&frame).unwrap();
        assert_eq!(dst, MAC_PTP_PRIMARY);
    }

    #[test]
    fn non_ptp_ethertypes_are_rejected() {
        let mut f = l2_frame(MAC_PTP_PEER_DELAY, false);
        f[12] = 0x08; // IPv4
        f[13] = 0x00;
        assert!(strip_ethernet(&f).is_none());
        assert!(strip_ethernet(&[0u8; 8]).is_none());
    }

    /// Interface enumeration must work without privileges so the monitor can
    /// still report where it would have listened when capture is denied.
    #[test]
    fn interfaces_enumerate_unprivileged() {
        let ifaces = list_interfaces().expect("read /sys/class/net");
        for (name, index, mac, _) in &ifaces {
            assert_ne!(*index, 0);
            assert_ne!(*mac, [0u8; 6]);
            assert!(name != "lo");
        }
    }

    /// PTPv1's alternate subdomains live on their own multicast addresses, so
    /// joining only the primary group makes `_ALT1`-`_ALT3` invisible in a way
    /// that is indistinguishable from their absence.
    #[test]
    fn v1_alternate_subdomain_groups_are_joined() {
        assert_eq!(PTP_V1_ALT_GROUPS.len(), 3);
        for g in PTP_V1_ALT_GROUPS {
            assert!(g.is_multicast());
            assert_ne!(g, PTP_PRIMARY_GROUP);
        }
    }

    #[test]
    fn permission_errors_name_both_capabilities() {
        let text = explain_error(&io::Error::from_raw_os_error(libc::EPERM));
        assert!(text.contains("cap_net_raw"));
        assert!(text.contains("cap_net_bind_service"));
    }
}
