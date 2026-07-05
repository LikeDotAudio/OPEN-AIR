/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use std::time::Duration;

// Inline comment: Logic for discover_mdns_devices
pub fn discover_mdns_devices() -> Vec<String> {
    let mut resources = Vec::new();
    
    if let Ok(mdns) = mdns_sd::ServiceDaemon::new() {
        let service_type = "_lxi._tcp.local.";
        if let Ok(receiver) = mdns.browse(service_type) {
            let start = std::time::Instant::now();
            while start.elapsed() < Duration::from_millis(500) {
                if let Ok(event) = receiver.recv_timeout(Duration::from_millis(50)) {
                    if let mdns_sd::ServiceEvent::ServiceResolved(info) = event {
                        for addr in info.get_addresses() {
                            let port = info.get_port();
                            resources.push(format!("TCPIP::{}::{}::SOCKET", addr, port));
                        }
                    }
                }
            }
        }
        
        let service_type = "_oca._tcp.local.";
        if let Ok(receiver) = mdns.browse(service_type) {
            let start = std::time::Instant::now();
            while start.elapsed() < Duration::from_millis(150) {
                if let Ok(event) = receiver.recv_timeout(Duration::from_millis(50)) {
                    if let mdns_sd::ServiceEvent::ServiceResolved(info) = event {
                        for addr in info.get_addresses() {
                            let port = info.get_port();
                            resources.push(format!("TCPIP::{}::{}::SOCKET", addr, port));
                        }
                    }
                }
            }
        }
    }
    resources
}
