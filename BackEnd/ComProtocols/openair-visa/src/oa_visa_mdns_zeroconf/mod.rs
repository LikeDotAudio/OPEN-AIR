/**
 * Header: mod.rs
 * Purpose: mDNS/DNS-SD discovery of VISA-reachable instruments.
 * Description: Browses the service types instruments actually advertise, then
 *              confirms which SCPI transport each advertised host really speaks.
 *
 * Version: 26.07.18.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 * - 2026-07-18: Browse beyond _lxi/_oca, and port-probe the advertised host
 *               rather than trusting the advertised port.
 */

use std::collections::HashSet;
use std::net::{IpAddr, SocketAddr, TcpStream};
use std::time::Duration;

/// Service types worth browsing.
///
/// This used to browse only `_lxi._tcp` and `_oca._tcp`, which misses a large
/// slice of real hardware. A Rigol scope on the bench advertises itself as plain
/// **`_http._tcp`** (`rigollan._http._tcp.local.`) and was therefore invisible to
/// this path — even though the standalone DNS-SD agent saw it and the instrument
/// was listening on both VXI-11 and a raw-socket port.
///
/// `_http._tcp` is included deliberately even though HTTP is not SCPI: many LXI
/// instruments advertise only their web UI. The advertisement's value is that it
/// names a *host worth probing*; PROBE_PORTS decides what it actually speaks.
const SERVICE_TYPES: [&str; 6] = [
    "_lxi._tcp.local.",         // LXI — the standards-compliant case
    "_oca._tcp.local.",         // AES70 / OCA
    "_vxi-11._tcp.local.",      // VXI-11
    "_scpi-raw._tcp.local.",    // raw SCPI socket
    "_hislip._tcp.local.",      // HiSLIP
    "_http._tcp.local.",        // web UI only — e.g. Rigol
];

/// Instrument transports probed against every advertised host.
///
/// The advertised port is frequently NOT the control port: a scope announcing
/// `_http._tcp` on :80 still takes SCPI on 5555. Trusting the advertisement
/// produced resources that pointed at a web server.
const PROBE_PORTS: [(u16, &str); 3] = [
    (111, "INSTR"),    // VXI-11 portmapper -> TCPIP::<ip>::INSTR
    (5025, "SOCKET"),  // raw SCPI
    (5555, "SOCKET"),  // raw SCPI (Rigol and friends)
];

const PROBE_TIMEOUT: Duration = Duration::from_millis(700);

fn port_open(ip: IpAddr, port: u16) -> bool {
    TcpStream::connect_timeout(&SocketAddr::new(ip, port), PROBE_TIMEOUT).is_ok()
}

/// Turn one advertised host into the VISA resource strings it can actually serve.
fn resources_for_host(ip: IpAddr) -> Vec<String> {
    let mut out = Vec::new();
    for (port, kind) in PROBE_PORTS {
        if !port_open(ip, port) {
            continue;
        }
        if kind == "INSTR" {
            // VXI-11 is addressed without a port in VISA syntax.
            out.push(format!("TCPIP::{}::INSTR", ip));
        } else {
            out.push(format!("TCPIP::{}::{}::SOCKET", ip, port));
        }
    }
    out
}

// Inline comment: Logic for discover_mdns_devices
pub fn discover_mdns_devices() -> Vec<String> {
    let mut resources: Vec<String> = Vec::new();
    let mut seen_hosts: HashSet<IpAddr> = HashSet::new();

    let mdns = match mdns_sd::ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            eprintln!("   ⚠️  [VISA mDNS] could not start service daemon: {e}");
            return resources;
        }
    };

    // Collect hosts first, probe second. One instrument commonly advertises
    // several service types (_lxi AND _http, say); probing per advertisement
    // would connect to it once per type for no benefit.
    for service_type in SERVICE_TYPES {
        let receiver = match mdns.browse(service_type) {
            Ok(r) => r,
            Err(_) => continue,
        };
        let start = std::time::Instant::now();
        // A budget, not an expected wait: mDNS answers arrive within tens of ms
        // on a quiet LAN.
        while start.elapsed() < Duration::from_millis(500) {
            if let Ok(mdns_sd::ServiceEvent::ServiceResolved(info)) =
                receiver.recv_timeout(Duration::from_millis(50))
            {
                for addr in info.get_addresses() {
                    seen_hosts.insert(addr.to_ip_addr());
                }
            }
        }
        let _ = mdns.stop_browse(service_type);
    }

    for ip in seen_hosts {
        // Loopback is not an instrument, and probing it burns the timeout budget.
        if ip.is_loopback() {
            continue;
        }
        let found = resources_for_host(ip);
        if !found.is_empty() {
            println!("   📡 [VISA mDNS] {} -> {}", ip, found.join(", "));
        }
        resources.extend(found);
    }

    resources
}
