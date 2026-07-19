//! Raw Layer 2 capture for AVDECC frames.
//!
//! Every other discovery agent in this repo opens a UDP socket. AVB has no IP
//! layer at all, so this one opens `AF_PACKET`/`SOCK_RAW` and reads Ethernet
//! frames directly. Two consequences follow, and both are visible to the
//! operator rather than hidden:
//!
//! 1. **It needs `CAP_NET_RAW`.** Unprivileged capture of raw frames is not
//!    possible on Linux, so a permission failure is reported with the exact
//!    command that fixes it rather than as a generic I/O error.
//! 2. **It is Linux-only.** `AF_PACKET` is a Linux interface; the module
//!    compiles elsewhere but reports that plainly instead of silently
//!    discovering nothing.
//!
//! # Why multicast membership, not promiscuous mode
//!
//! A NIC drops multicast frames for groups it has not joined, so an AVDECC
//! listener must ask for `91:E0:F0:01:00:00` explicitly. The lazy alternative
//! is promiscuous mode, which lifts *all* filtering and hands userspace every
//! frame on the segment — on an audio network that is a firehose of RTP, and
//! it is a far broader claim on the network's traffic than discovery needs.
//! `PACKET_ADD_MEMBERSHIP` asks for exactly the one group.

use std::io;

/// One network interface we can capture on.
#[derive(Debug, Clone)]
pub struct Interface {
    pub name: String,
    pub index: u32,
    pub mac: [u8; 6],
    /// Whether the link is actually up with a carrier. A down interface is
    /// still listed — an AVB device on an unplugged port is a common enough
    /// mistake that "we looked there and the cable is dead" is useful output.
    pub is_up: bool,
}

/// Enumerate usable Ethernet interfaces, skipping loopback and virtual
/// bridges (docker/br-*), which cannot carry AVB.
pub fn list_interfaces() -> io::Result<Vec<Interface>> {
    let mut out = Vec::new();
    for entry in std::fs::read_dir("/sys/class/net")? {
        let entry = entry?;
        let name = entry.file_name().to_string_lossy().to_string();
        if name == "lo" || name.starts_with("br-") || name.starts_with("docker") {
            continue;
        }
        let read = |file: &str| {
            std::fs::read_to_string(entry.path().join(file))
                .map(|s| s.trim().to_string())
                .unwrap_or_default()
        };

        let mac_text = read("address");
        let mut mac = [0u8; 6];
        let octets: Vec<&str> = mac_text.split(':').collect();
        if octets.len() != 6 {
            continue; // Not an Ethernet interface.
        }
        for (slot, octet) in mac.iter_mut().zip(&octets) {
            *slot = u8::from_str_radix(octet, 16).unwrap_or(0);
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

        out.push(Interface {
            name,
            index,
            mac,
            is_up: read("operstate") == "up" || read("carrier") == "1",
        });
    }
    out.sort_by(|a, b| a.name.cmp(&b.name));
    Ok(out)
}

/// An open raw-packet socket.
///
/// Owns the file descriptor and closes it on drop.
pub struct RawSocket {
    fd: i32,
}

impl Drop for RawSocket {
    fn drop(&mut self) {
        unsafe { libc::close(self.fd) };
    }
}

/// Human-readable explanation for a capture failure that names the fix.
///
/// A bare `EPERM` from a discovery agent reads as "AVB is broken"; it actually
/// means "you have not granted packet capture", which is a one-line remedy.
pub fn explain_error(e: &io::Error) -> String {
    match e.raw_os_error() {
        Some(libc::EPERM) | Some(libc::EACCES) => concat!(
            "raw packet capture denied — AVDECC is a Layer 2 protocol and needs CAP_NET_RAW.\n",
            "         Grant it once to the binary:  sudo setcap cap_net_raw,cap_net_admin+eip <binary>\n",
            "         ...or run the probe with sudo."
        )
        .to_string(),
        _ => e.to_string(),
    }
}

impl RawSocket {
    /// Open a raw socket filtered to the AVTP EtherType.
    ///
    /// Filtering in the kernel by EtherType rather than taking `ETH_P_ALL`
    /// matters on an audio network: `ETH_P_ALL` would wake userspace for every
    /// RTP packet in flight. AVTP stream data shares this EtherType with ADP,
    /// so a subtype check still happens per frame — but that is a byte compare
    /// on frames we were going to see anyway, not the whole network.
    pub fn open() -> io::Result<Self> {
        #[cfg(not(target_os = "linux"))]
        {
            return Err(io::Error::new(
                io::ErrorKind::Unsupported,
                "AF_PACKET capture is Linux-only; AVDECC discovery is unavailable on this platform",
            ));
        }

        #[cfg(target_os = "linux")]
        {
            let proto = (super::adp::ETHERTYPE_AVTP as u16).to_be() as i32;
            let fd = unsafe { libc::socket(libc::AF_PACKET, libc::SOCK_RAW, proto) };
            if fd < 0 {
                return Err(io::Error::last_os_error());
            }
            let socket = RawSocket { fd };

            // Without a read timeout the listen loop could never run its
            // expiry sweep on a silent network.
            let tv = libc::timeval { tv_sec: 2, tv_usec: 0 };
            unsafe {
                libc::setsockopt(
                    fd,
                    libc::SOL_SOCKET,
                    libc::SO_RCVTIMEO,
                    &tv as *const _ as *const libc::c_void,
                    std::mem::size_of::<libc::timeval>() as libc::socklen_t,
                );
            }
            Ok(socket)
        }
    }

    /// Join the AVDECC multicast group on one interface.
    pub fn join_avdecc_group(&self, if_index: u32) -> io::Result<()> {
        let mut mreq: libc::packet_mreq = unsafe { std::mem::zeroed() };
        mreq.mr_ifindex = if_index as i32;
        mreq.mr_type = libc::PACKET_MR_MULTICAST as u16;
        mreq.mr_alen = 6;
        mreq.mr_address[..6].copy_from_slice(&super::adp::AVDECC_MULTICAST_MAC);

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

    /// Receive one frame. Returns the byte count and the interface index it
    /// arrived on, so a multi-homed host can report *where* an entity lives.
    ///
    /// `Ok(None)` means the read timed out — the caller should use the tick to
    /// expire stale entities rather than treat it as an error.
    pub fn recv(&self, buf: &mut [u8]) -> io::Result<Option<(usize, u32)>> {
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
        Ok(Some((n as usize, addr.sll_ifindex as u32)))
    }

    /// Transmit one frame on a specific interface.
    pub fn send_on(&self, if_index: u32, frame: &[u8]) -> io::Result<()> {
        let mut addr: libc::sockaddr_ll = unsafe { std::mem::zeroed() };
        addr.sll_family = libc::AF_PACKET as u16;
        addr.sll_protocol = (super::adp::ETHERTYPE_AVTP as u16).to_be();
        addr.sll_ifindex = if_index as i32;
        addr.sll_halen = 6;
        addr.sll_addr[..6].copy_from_slice(&super::adp::AVDECC_MULTICAST_MAC);

        let n = unsafe {
            libc::sendto(
                self.fd,
                frame.as_ptr() as *const libc::c_void,
                frame.len(),
                0,
                &addr as *const _ as *const libc::sockaddr,
                std::mem::size_of::<libc::sockaddr_ll>() as libc::socklen_t,
            )
        };
        if n < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Interface enumeration must not need privileges — the probe relies on
    /// being able to say "here is where I would have looked" even when raw
    /// capture is denied.
    #[test]
    fn interfaces_enumerate_without_privileges() {
        let ifaces = list_interfaces().expect("read /sys/class/net");
        for i in &ifaces {
            assert_ne!(i.index, 0);
            assert_ne!(i.mac, [0u8; 6]);
            assert!(!i.name.starts_with("br-") && i.name != "lo");
        }
    }

    /// A permission failure must name the remedy, not just the errno.
    #[test]
    fn permission_errors_explain_the_fix() {
        let e = io::Error::from_raw_os_error(libc::EPERM);
        let text = explain_error(&e);
        assert!(text.contains("CAP_NET_RAW"));
        assert!(text.contains("setcap"));
    }
}
