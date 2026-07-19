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
use std::fs;
use std::io::{Read, Write};

// Inline comment: Logic for hunt_for_devices
pub fn hunt_for_devices() -> Vec<String> {
    let mut resources = Vec::new();

    println!("🔎 [VISA-RUST] Initiating Subnet VXI-11 Gateway Hunt...");
    if let Ok(socket) = std::net::UdpSocket::bind("0.0.0.0:0") {
        if socket.connect("8.8.8.8:80").is_ok() {
            if let Ok(local_addr) = socket.local_addr() {
                if let std::net::IpAddr::V4(ipv4) = local_addr.ip() {
                    let octets = ipv4.octets();
                    let subnet = format!("{}.{}.{}", octets[0], octets[1], octets[2]);
                    
                    let mut ips_to_scan = Vec::new();
                    for i in 1..=254 {
                        if i == octets[3] { continue; }
                        ips_to_scan.push(format!("{}.{}", subnet, i));
                    }
                    
                    let gateway_paths = [
                        "assets/gateways.json",
                        "../assets/gateways.json",
                        "/usr/local/share/openair/assets/gateways.json"
                    ];
                    for path in gateway_paths.iter() {
                        if let Ok(content) = fs::read_to_string(path) {
                            if let Ok(parsed) = serde_json::from_str::<Vec<String>>(&content) {
                                ips_to_scan.extend(parsed);
                                break;
                            }
                        }
                    }
                    
                    // Bounded concurrency + a realistic timeout.
                    //
                    // This used to spawn one thread per address — 254 at once —
                    // each racing several connects on a 200ms budget. Under that
                    // burst the OS and the switch drop enough SYNs that live
                    // instruments are missed: a Rigol at .161 answers port 111 in
                    // 25ms when probed alone, yet never appeared in a scan.
                    //
                    // A missed instrument is worse than a slow scan, and it fails
                    // silently — the device simply is not in the list.
                    const SCAN_CHUNK: usize = 48;
                    let mut handles = Vec::new();
                    let mut in_flight = 0usize;
                    let mut chunk_results: Vec<Vec<String>> = Vec::new();
                    for ip in ips_to_scan {
                        handles.push(std::thread::spawn(move || {
                            let mut found = Vec::new();
                            let mut is_dedicated = false;
                            // 200ms was too tight under a 254-way burst; see the
                            // concurrency note above.
                            const CONNECT_TIMEOUT: Duration = Duration::from_millis(600);
                            if std::net::TcpStream::connect_timeout(&format!("{}:111", ip).parse().unwrap(), CONNECT_TIMEOUT).is_ok() {
                                is_dedicated = true;
                            } else if std::net::TcpStream::connect_timeout(&format!("{}:5025", ip).parse().unwrap(), CONNECT_TIMEOUT).is_ok() {
                                is_dedicated = true;
                            }
                            
                            if std::net::TcpStream::connect_timeout(&format!("{}:5555", ip).parse().unwrap(), CONNECT_TIMEOUT).is_ok() {
                                let visa_res = format!("TCPIP::{}::5555::SOCKET", ip);
                                println!("     ➕ Added socket resource: {}", visa_res);
                                found.push(visa_res);
                            }
                            
                            if is_dedicated {
                                let visa_res = format!("TCPIP::{}::INSTR", ip);
                                println!("     ➕ Added dedicated resource: {}", visa_res);
                                found.push(visa_res);
                            }

                            if let Ok(mut stream) = std::net::TcpStream::connect_timeout(&format!("{}:80", ip).parse().unwrap(), Duration::from_millis(2000)) {
                                println!("   👉 Scraping Gateway {}...", ip);
                                let req = format!("GET /html/instrumentspage.html?whichbutton=find&timeout=5 HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n", ip);
                                let _ = stream.set_write_timeout(Some(Duration::from_millis(2000)));
                                let _ = stream.set_read_timeout(Some(Duration::from_millis(5000)));
                                if stream.write_all(req.as_bytes()).is_ok() {
                                    let mut html = String::new();
                                    if stream.read_to_string(&mut html).is_ok() {
                                        if let Ok(re) = regex::Regex::new(r"(?i)<option[^>]*>[\s\n]*([a-zA-Z0-9,]+)") {
                                            let mut match_count = 0;
                                            for cap in re.captures_iter(&html) {
                                                let res = cap[1].trim();
                                                if !res.contains("COM") {
                                                    let visa_res = format!("TCPIP::{}::{}::INSTR", ip, res);
                                                    println!("     ➕ Added gateway resource: {}", visa_res);
                                                    found.push(visa_res);
                                                    match_count += 1;
                                                }
                                            }
                                            if match_count > 0 {
                                                // If this is a gateway with actual gpib devices behind it, 
                                                // the root TCPIP::ip::INSTR address is just the chassis and shouldn't be probed!
                                                let root_res = format!("TCPIP::{}::INSTR", ip);
                                                found.retain(|x| x != &root_res);
                                            } else {
                                                println!("   ⚠️  Gateway {} responded on port 80 but no VISA GPIB interfaces were found in the HTML.", ip);
                                            }
                                        }
                                    } else {
                                        println!("   ❌ Gateway {} timed out while reading the HTTP response.", ip);
                                    }
                                }
                            }
                            found
                        }));
                        in_flight += 1;
                        if in_flight >= SCAN_CHUNK {
                            for handle in handles.drain(..) {
                                if let Ok(found) = handle.join() { chunk_results.push(found); }
                            }
                            in_flight = 0;
                        }
                    }
                    for handle in handles.drain(..) {
                        if let Ok(found) = handle.join() { chunk_results.push(found); }
                    }
                    for mut found in chunk_results {
                        resources.append(&mut found);
                    }
                }
            }
        }
    }
    println!("✅ [VISA-RUST] Gateway Hunt Complete.");
    resources
}
