/**
 * Header: main.rs
 * Purpose: main.rs implementation.
 * Description: Logic and implementation for main.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

mod api;
mod cli;
mod discovered;
mod instruments;
mod mqtt;

use axum::{
    routing::get,
    Router,
};
use std::net::SocketAddr;
use clap::Parser;
use std::path::PathBuf;
use tower_http::services::ServeDir;
use tower_http::cors::CorsLayer;
use axum::http::Method;

#[tokio::main]
// Inline comment: Logic for main
async fn main() {
    let args = cli::Args::parse();
    println!("🚀 [RUST ORCHESTRATOR] Booting OPEN-AIR Native Core...");

    let root = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));

    // One broker address for every agent. Previously hard-coded six times.
    let mqtt_host = args.mqtt_host.clone();
    let mqtt_port = args.mqtt_port;
    
    // MQTT Config Publisher
    mqtt::publish_protocol_configs(&root, args.no_mqtt);

    let osc_bind = args.osc_bind;
    let (osc_mqtt_host, osc_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native OSC Agent on {osc_bind}:8000...");
        // SECURITY: loopback unless --osc-bind says otherwise. Every other agent
        // (AES70, MIDI, DNS-SD) already binds 127.0.0.1; this was the outlier.
        let osc_agent = openair_osc::OscAgent::new(osc_bind.to_string(), 8000);
        let (osc_tx, mut osc_rx) = tokio::sync::mpsc::channel(100);
        tokio::spawn(async move {
            let _ = osc_agent.start(osc_tx).await;
        });
        // Publish to MQTT — the one bus every consumer actually reads.
        // Previously these events went only to the /ws broadcast channel, which
        // has no subscribers, so OSC discoveries reached nothing at all. MIDI and
        // VISA were dual-homed and therefore worked; OSC and AES70 were not.
        let mut osc_mqtt_opts = rumqttc::MqttOptions::new("open-air-osc-publisher", &osc_mqtt_host, osc_mqtt_port);
        osc_mqtt_opts.set_keep_alive(std::time::Duration::from_secs(30));
        let (osc_mqtt, mut osc_conn) = rumqttc::Client::new(osc_mqtt_opts, 10);
        std::thread::spawn(move || { for _ in osc_conn.iter() {} });

        while let Some(osc_event) = osc_rx.recv().await {
            let topic = format!("OpenAir/Protocol/GuiOsc/{}", osc_event.address);
            let payload = osc_event.value.to_string();
            println!("   📡 [OSC MQTT] ⮜ {} = {}", topic, payload);
            let _ = osc_mqtt.publish(topic.clone(), rumqttc::QoS::AtLeastOnce, false, payload.into_bytes());

        }
    });

    let (midi_mqtt_host, midi_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native MIDI Agent...");
        
        let (dev_host, dev_port) = (midi_mqtt_host.clone(), midi_mqtt_port);
        let devices_task = tokio::task::spawn_blocking(move || {
            let inputs = openair_midi::oa_midi_scan::scan_inputs();
            let outputs = openair_midi::oa_midi_scan::scan_outputs();
            if !inputs.is_empty() || !outputs.is_empty() {
                let _ = openair_midi::oa_midi_mqtt_publish::publish_devices_mqtt(
                    &dev_host,
                    dev_port,
                    "OpenAir/System/Protocols/midi/Device", 
                    inputs, 
                    outputs
                );
            }
        });
        
        let midi_agent = std::sync::Arc::new(openair_midi::MidiAgent::new(None)); 
        let (midi_tx, mut midi_rx) = tokio::sync::mpsc::channel(100);
        
        let mut mqttoptions = rumqttc::MqttOptions::new("open-air-midi-listener", &midi_mqtt_host, midi_mqtt_port);
        mqttoptions.set_keep_alive(std::time::Duration::from_secs(30));
        let (mqtt_client, mut mqtt_connection) = rumqttc::Client::new(mqttoptions, 10);
        
        let _ = mqtt_client.subscribe("OpenAir/System/Protocols/midi/Device/Output/#", rumqttc::QoS::AtLeastOnce);
        
        let midi_agent_clone = midi_agent.clone();
        std::thread::spawn(move || {
            for notification in mqtt_connection.iter() {
                if let Ok(rumqttc::Event::Incoming(rumqttc::Packet::Publish(publish))) = notification {
                    let topic = publish.topic.clone();
                    if topic.contains("/Output/Dev") {
                        let parts: Vec<&str> = topic.split('/').collect();
                        if let Some(dev_idx) = parts.iter().position(|&p| p.starts_with("Dev")) {
                            if let Ok(port_idx) = parts[dev_idx].trim_start_matches("Dev").parse::<usize>() {
                                let payload = String::from_utf8_lossy(&publish.payload).trim().to_string();
                                
                                // Topic format: .../Output/Dev1/Channel0/Note/60
                                if dev_idx + 2 < parts.len() && parts[dev_idx + 1].starts_with("Channel") {
                                    if let Ok(channel_display) = parts[dev_idx + 1].trim_start_matches("Channel").parse::<u8>() {
                                        let channel = if channel_display > 0 { channel_display - 1 } else { 0 };
                                        let msg_type = parts[dev_idx + 2];
                                        let data1 = if dev_idx + 3 < parts.len() {
                                            parts[dev_idx + 3].parse::<u8>().unwrap_or(0)
                                        } else { 0 };
                                        
                                        let val = payload.parse::<u8>().unwrap_or(0);
                                        
                                        let mut raw_data = Vec::new();
                                        if msg_type == "Note" {
                                            if val > 0 {
                                                raw_data = vec![144 | channel, data1, val];
                                            } else {
                                                raw_data = vec![128 | channel, data1, 0];
                                            }
                                        } else if msg_type == "ControlChange" {
                                            raw_data = vec![176 | channel, data1, val];
                                        } else if msg_type == "ProgramChange" {
                                            raw_data = vec![192 | channel, val, 0];
                                        } else if msg_type == "PitchBend" {
                                            let pval = payload.parse::<u16>().unwrap_or(0);
                                            raw_data = vec![224 | channel, (pval & 0x7F) as u8, ((pval >> 7) & 0x7F) as u8];
                                        }
                                        
                                        if !raw_data.is_empty() {
                                            println!("   📡 [MIDI MQTT] ⮞ Output on Dev{} -> {} = {}", port_idx, topic, val);
                                            let _ = midi_agent_clone.send(port_idx, &raw_data);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        });

        tokio::spawn(async move {
            let _ = devices_task.await;
            if let Err(e) = midi_agent.start(midi_tx).await {
                eprintln!("🎹❌ [MIDI AGENT] Failed to start: {:?}", e);
            }
        });
        
        while let Some(midi_event) = midi_rx.recv().await {
            if let Some(port_idx) = midi_event.value.get("port_index").and_then(|v| v.as_u64()) {
                let channel = midi_event.value.get("channel").and_then(|v| v.as_u64()).unwrap_or(0) + 1;
                let command = midi_event.value.get("command").and_then(|v| v.as_u64()).unwrap_or(0);
                let data1 = midi_event.value.get("data1").and_then(|v| v.as_u64()).unwrap_or(0);
                let data2 = midi_event.value.get("data2").and_then(|v| v.as_u64()).unwrap_or(0);

                let (subtopic, payload_val) = match command {
                    128 => (format!("Channel{}/Note/{}", channel, data1), 0),
                    144 => (format!("Channel{}/Note/{}", channel, data1), data2),
                    176 => (format!("Channel{}/ControlChange/{}", channel, data1), data2),
                    192 => (format!("Channel{}/ProgramChange", channel), data1),
                    224 => (format!("Channel{}/PitchBend", channel), (data2 << 7) | data1),
                    _ => (format!("Channel{}/Raw/{}", channel, command), data1),
                };

                println!("   📡 [MIDI MQTT] ⮜ Input on Dev{} -> {} = {}", port_idx, subtopic, payload_val);
                let topic = format!("OpenAir/System/Protocols/midi/Device/Input/Dev{}/{}", port_idx, subtopic);
                let payload = payload_val.to_string();
                let _ = mqtt_client.publish(topic, rumqttc::QoS::AtLeastOnce, false, payload.as_bytes());
            }
        }
    });

    let (aes_mqtt_host, aes_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native AES70 Agent (OCP.1 TCP)...");
        let aes70_agent = openair_aes70::Aes70Agent::new("127.0.0.1".to_string(), 50014); 
        let (aes70_tx, mut aes70_rx) = tokio::sync::mpsc::channel(100);
        tokio::spawn(async move {
            if let Err(e) = aes70_agent.start(aes70_tx).await {
                if e.kind() != std::io::ErrorKind::ConnectionRefused {
                    eprintln!("🔊❌ [AES70 AGENT] Failed to start: {:?}", e);
                }
            }
        });
        // Publish to MQTT — see the OSC agent above for why this was missing.
        let mut aes_mqtt_opts = rumqttc::MqttOptions::new("open-air-aes70-publisher", &aes_mqtt_host, aes_mqtt_port);
        aes_mqtt_opts.set_keep_alive(std::time::Duration::from_secs(30));
        let (aes_mqtt, mut aes_conn) = rumqttc::Client::new(aes_mqtt_opts, 10);
        std::thread::spawn(move || { for _ in aes_conn.iter() {} });

        while let Some(aes70_event) = aes70_rx.recv().await {
            let topic = format!("OpenAir/Protocol/AES70/{}", aes70_event.address);
            let payload = aes70_event.value.to_string();
            println!("   📡 [AES70 MQTT] ⮜ {} = {}", topic, payload);
            let _ = aes_mqtt.publish(topic.clone(), rumqttc::QoS::AtLeastOnce, false, payload.into_bytes());

        }
    });

    // DNS-SD / mDNS discovery agent — continuous browse on its own thread
    // (mdns-sd is sync); retained topics land in the Discovered tab via the
    // same builder sweep as VISA/MIDI. No longer a stub.
    // Google Cast discovery. Separate from DNS-SD on purpose: that agent sees
    // these devices too, but publishes the TXT record verbatim because it cannot
    // know what any given service's keys mean. Cast TXT keys ARE defined, so this
    // agent decodes them into sortable columns (friendly name, model,
    // capabilities, status). Discovery only — no Cast V2 control.
    let (cast_mqtt_host, cast_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    std::thread::spawn(move || {
        openair_chromecast::run_browse_agent(&cast_mqtt_host, cast_mqtt_port);
    });

    // RAVENNA / AES67 audio streams. Follows mDNS -> RTSP DESCRIBE -> SDP, so a
    // stream is only claimed once its own SDP says it carries audio (port 554
    // alone proves nothing — IP cameras answer RTSP too).
    let (rav_mqtt_host, rav_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    std::thread::spawn(move || {
        openair_ravenna::run_browse_agent(&rav_mqtt_host, rav_mqtt_port);
    });

    // SAP — the other half of AES67 discovery. RAVENNA announces over mDNS;
    // Dante in AES67 mode pushes raw SDP to multicast 9875 instead, and never
    // answers a query. Streams announced both ways (RAV2SAP, or a device with
    // SAP publishing enabled) appear under both agents on purpose: which
    // mechanisms a stream announces on is itself the interop answer.
    let (sap_mqtt_host, sap_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    std::thread::spawn(move || {
        println!("🚀 [AGENT] Launching Native SAP Agent (passive multicast listen)...");
        openair_sap::run_listen_agent(&sap_mqtt_host, sap_mqtt_port);
    });

    // Dante, in both personalities: native mDNS (_netaudio-*) AND the SAP
    // multicast group it uses instead once AES67 mode is enabled.
    let (dante_mqtt_host, dante_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    std::thread::spawn(move || {
        openair_dante::run_browse_agent(&dante_mqtt_host, dante_mqtt_port);
    });

    // PTP / gPTP clock discovery. Spans two transports at once because the
    // three protocols do not share one: PTPv1 and PTPv2 over UDP 319/320,
    // gPTP over raw Ethernet 0x88F7. Publishes on state change plus a slow
    // heartbeat rather than per packet — gPTP Sync alone is 8/s per port, and
    // a retained write per Sync would be thousands a minute saying nothing new.
    let (ptp_mqtt_host, ptp_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    std::thread::spawn(move || {
        println!("🚀 [AGENT] Launching Native PTP Agent (v1 + v2 + gPTP)...");
        openair_ptp::run_listen_agent(&ptp_mqtt_host, ptp_mqtt_port);
    });

    // AVB / Milan via AVDECC (IEEE 1722.1). The odd one out: AVB is Layer 2,
    // so this agent reads raw Ethernet frames rather than opening a socket on
    // an IP address — and therefore needs CAP_NET_RAW. Without that capability
    // it logs the remedy once and exits its thread rather than restart-looping.
    // Discovery (ADP) only: no SRP reservation, no ACMP connection management.
    let (avb_mqtt_host, avb_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    std::thread::spawn(move || {
        println!("🚀 [AGENT] Launching Native AVB/Milan Agent (AVDECC ADP listen)...");
        openair_avb_milan::run_listen_agent(&avb_mqtt_host, avb_mqtt_port);
    });

    // Printers: six Bonjour services per device, merged into one row by UUID.
    let (prn_mqtt_host, prn_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    std::thread::spawn(move || {
        openair_printers::run_browse_agent(&prn_mqtt_host, prn_mqtt_port);
    });

    // AirPlay / HomeKit receivers — many roles, one device.
    let (atv_host, atv_port) = (mqtt_host.clone(), mqtt_port);
    std::thread::spawn(move || { openair_appletv::run_browse_agent(&atv_host, atv_port); });

    // AMWA NMOS IS-04/IS-09 — each service is a distinct API role, keyed host+port.
    let (nmos_host, nmos_port) = (mqtt_host.clone(), mqtt_port);
    std::thread::spawn(move || { openair_nmos::run_browse_agent(&nmos_host, nmos_port); });

    let (dnssd_mqtt_host, dnssd_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    std::thread::spawn(move || {
        println!("🚀 [AGENT] Launching Native DNS-SD Agent (continuous browse)...");
        openair_dnssd::run_browse_agent(&dnssd_mqtt_host, dnssd_mqtt_port);
    });

    // Discovered-device panels and live tables (see discovered.rs).
    // One mirror of the retained discovery tree serves both the scan loop, which
    // rebuilds the panel FILES, and the watcher task, which keeps the rows live.
    let discovered_mirror = discovered::Mirror::spawn(root.clone(), &mqtt_host, mqtt_port);

    let (visa_mqtt_host, visa_mqtt_port) = (mqtt_host.clone(), mqtt_port);
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native VISA Agent (Background Scan)...");

        // Let the retained tree land before anything is written. The first scan
        // starts immediately, and its opening rebuild would otherwise run against
        // an empty mirror — which does not merely write empty tables, it PRUNES
        // every existing category folder for having no devices in it.
        discovered_mirror.settle().await;
        // Rows go live from here, whether or not a scan ever runs: the dozen
        // network agents publish continuously and none of them needs VISA.
        discovered_mirror.spawn_watcher();

        let mut mqttoptions = rumqttc::MqttOptions::new("open-air-visa-scanner", &visa_mqtt_host, visa_mqtt_port);
        mqttoptions.set_keep_alive(std::time::Duration::from_secs(30));
        let (mqtt_client, mut mqtt_connection) = rumqttc::Client::new(mqttoptions, 10);

        std::thread::spawn(move || {
            for _ in mqtt_connection.iter() {}
        });

        // The Write daemon and the scan loop share the topic→resource map:
        // every rescan swaps in a fresh mapping.
        let topic_to_resource: std::sync::Arc<std::sync::Mutex<std::collections::HashMap<String, String>>> =
            Default::default();
        // Rescan trigger: the Discovered tab's Scan panel publishes value=1
        // (non-retained) to .../visa/Device/Rescan; the daemon thread signals
        // this loop. Capacity 1: triggers during a running scan coalesce.
        let (rescan_tx, mut rescan_rx) = tokio::sync::mpsc::channel::<()>(1);

        spawn_visa_write_daemon(topic_to_resource.clone(), rescan_tx, visa_mqtt_host.clone(), visa_mqtt_port);
        // Raised for the duration of a scan so the heartbeat stands aside: a
        // GPIB gateway serves one link at a time, and two probers competing for
        // it is how a healthy instrument reports as missing.
        let scanning_flag = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
        spawn_visa_heartbeat(topic_to_resource.clone(), scanning_flag.clone(),
                             visa_mqtt_host.clone(), visa_mqtt_port);

        // Seed the cleanup map from what is ALREADY retained on the broker.
        //
        // Retained topics outlive this process; the in-memory map does not. After
        // a restart the agent had no record of what it had published, so device
        // topics from previous runs were never cleared — they simply accumulated.
        // The visible symptom was one instrument appearing as several rows in the
        // Discovered tab, each a fossil of an earlier scan, and no rescan could
        // remove them because nothing knew they existed.
        //
        // Harvesting them at boot makes the existing cleanup work across
        // restarts, which is what it always intended to do.
        {
            // Run on a plain OS thread, NOT this one.
            //
            // This task is a `tokio::spawn`, so it runs on a runtime worker.
            // `harvest_retained_device_prefixes` iterates a blocking rumqttc
            // `Connection`, and that iterator calls `Runtime::block_on`
            // internally (rumqttc client.rs:433) — starting a runtime from
            // inside one, which tokio panics on. The panic killed this whole
            // task before it ever scanned, so no VISA device topics were ever
            // published and every instrument silently vanished from the
            // Discovered tab. A plain thread carries no runtime context, so
            // rumqttc's own runtime is free to block there.
            //
            // The other `connection.iter()` calls in this file were already on
            // `std::thread::spawn` for the same reason; this one was the outlier.
            let harvested = {
                let host = visa_mqtt_host.clone();
                std::thread::spawn(move || harvest_retained_device_prefixes(&host, visa_mqtt_port))
                    .join()
                    .unwrap_or_default()
            };
            if !harvested.is_empty() {
                println!("   🧹 [VISA AGENT] adopted {} retained device prefix(es) from a previous run", harvested.len());
                let mut map = topic_to_resource.lock().unwrap();
                for prefix in harvested {
                    // Value is unused by the cleanup (it only needs the keys);
                    // a real resource is filled in by the next successful scan.
                    map.entry(prefix).or_insert_with(String::new);
                }
            }
        }

        loop {

        // Clear the previous scan's retained topics first, so devices that
        // moved category (e.g. after a knowledge-base fix) or disappeared
        // don't linger as ghosts in the Discovered tab.
        {
            let old_prefixes: Vec<String> =
                topic_to_resource.lock().unwrap().keys().cloned().collect();
            if !old_prefixes.is_empty() {
                for prefix in &old_prefixes {
                    for key in DEVICE_TOPIC_KEYS {
                        let _ = mqtt_client.publish(
                            format!("{}/{}", prefix, key),
                            rumqttc::QoS::AtLeastOnce,
                            true,
                            Vec::<u8>::new(), // empty retained payload = delete
                        );
                    }
                }
                println!("   🧹 [VISA AGENT] cleared retained topics for {} previous device(s)", old_prefixes.len());
            }
        }

        scanning_flag.store(true, std::sync::atomic::Ordering::Relaxed);
        set_scan_state(&mqtt_client, "scanning");
        scan_log(&mqtt_client, "info", "Scan started — hunting for VXI-11/LAN gateways and instruments…");
        // Told directly rather than read back off the bus. The mirror does
        // subscribe to the scan-state topic, but the publish above has not
        // round-tripped the broker yet, and the rebuild below is immediate —
        // it would render last scan's rows green while this scan invalidates
        // them.
        discovered_mirror.set_scanning(true);
        // Regenerate panels immediately so the tables show "scanning" rather than
        // last scan's results while this one runs.
        discovered_mirror.build_async().await;

        let devices = tokio::task::spawn_blocking(|| {
            openair_visa::oa_visa_scan_for_devices::list_resources()
        }).await.unwrap_or_default();

        scan_log(&mqtt_client, "info", format!("Found {} candidate resource(s); probing *IDN?…", devices.len()));

        let mut counts: std::collections::HashMap<(String, String), usize> = std::collections::HashMap::new();

        // One physical instrument can be reachable by more than one transport —
        // a Rigol scope answers BOTH `TCPIP::<ip>::INSTR` (VXI-11) and
        // `TCPIP::<ip>::5555::SOCKET`, and showed up as two identical rows.
        // After *IDN? we know the real identity, so publish each instrument once.
        //
        // Keyed on the SERIAL, and only when the serial is actually meaningful.
        // This bench has four HP 34401A DMMs that all report serial "0"; keying
        // on (model, serial) alone would silently merge four real instruments
        // into one. When a device gives us nothing to identify itself with, every
        // resource is kept — a duplicate row is a far smaller error than a
        // disappeared instrument.
        let mut seen_identities: std::collections::HashSet<(String, String)> =
            std::collections::HashSet::new();

        // Fresh map per scan; swapped into the shared handle after the loop.
        let mut scan_topic_to_resource = std::collections::HashMap::new();

        let total = devices.len();
        for (i, dev) in devices.into_iter().enumerate() {
            scan_log(&mqtt_client, "info", format!("[{}/{}] probing {}", i + 1, total, dev));
            
            if let Ok(output) = tokio::process::Command::new("python3")
                .arg("-c")
                .arg(VISA_PROBE_SCRIPT)
                .arg(&dev)
                .output()
                .await
            {
                let out_str = String::from_utf8_lossy(&output.stdout);
                if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(&out_str) {
                    if parsed.get("error").is_none() {
                        let mut merged = parsed.as_object().unwrap().clone();
                        merged.insert("resource".to_string(), serde_json::Value::String(dev.clone()));
                        merged.insert("status".to_string(), serde_json::Value::String("identified".to_string()));
                        
                        let model_str = merged.get("model").and_then(|m| m.as_str()).unwrap_or("Unknown").to_string();
                        let (device_type, notes) = openair_visa::oa_visa_known_devices::get_device_info(&model_str);
                        merged.insert("device_type".to_string(), serde_json::Value::String(device_type.clone()));
                        merged.insert("notes".to_string(), serde_json::Value::String(notes));
                        
                        // Suppress a second transport for an instrument already
                        // published. First sighting wins, and list_resources()
                        // orders sources USB -> mDNS -> subnet sweep, so the more
                        // specific discovery (and VXI-11 INSTR before raw SOCKET)
                        // is the one that survives.
                        let serial = merged.get("serial").and_then(|v| v.as_str()).unwrap_or("").trim().to_string();
                        let serial_is_usable = !serial.is_empty()
                            && serial != "0"
                            && !serial.eq_ignore_ascii_case("none")
                            && !serial.eq_ignore_ascii_case("n/a");
                        if serial_is_usable {
                            let identity = (model_str.clone(), serial.clone());
                            if !seen_identities.insert(identity) {
                                scan_log(&mqtt_client, "info", format!(
                                    "{} (serial {}) already found on another transport — skipping {}",
                                    model_str, serial, dev));
                                continue;
                            }
                        }

                        let key = (device_type.clone(), model_str.clone());
                        let count = counts.entry(key).or_insert(0);
                        
                        let topic_prefix = format!("OpenAir/System/Protocols/visa/Device/{}/{}/Dev{}", device_type.replace(" ", "_"), model_str.replace(" ", "_"), count);
                        scan_topic_to_resource.insert(topic_prefix.clone(), dev.clone());
                        
                        let mut is_online = false;
                        if let Some(raw_idn) = merged.get("raw_idn").and_then(|r| r.as_str()) {
                            if !raw_idn.trim().is_empty() { is_online = true; }
                        }
                        
                        if let Ok(duration) = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH) {
                            merged.insert("last_online".to_string(), serde_json::Value::Number(duration.as_secs().into()));
                        }
                        merged.insert("connected".to_string(), serde_json::Value::Number((if is_online { 1 } else { 0 }).into()));
                        
                        for (k, v) in &merged {
                            let val_str = match v {
                                serde_json::Value::String(s) => s.clone(),
                                serde_json::Value::Number(n) => n.to_string(),
                                _ => v.to_string(),
                            };
                            let _ = mqtt_client.publish(format!("{}/{}", topic_prefix, k), rumqttc::QoS::AtLeastOnce, true, val_str.into_bytes());
                        }
                        
                        let _ = mqtt_client.publish(format!("{}/Write", topic_prefix), rumqttc::QoS::AtLeastOnce, true, "");
                        let _ = mqtt_client.publish(format!("{}/Read", topic_prefix), rumqttc::QoS::AtLeastOnce, true, "");
                        
                        *count += 1;
                        
                        scan_log(&mqtt_client, "ok",
                            format!("identified {} {} at {}", 
                                merged.get("manufacturer").and_then(|m| m.as_str()).unwrap_or("?"),
                                model_str, dev));
                    } else {
                        scan_log(&mqtt_client, "warn",
                            format!("no identity from {} — {}", dev,
                                parsed.get("error").and_then(|e| e.as_str()).unwrap_or("no response")));
                    }
                }
            }

        }
        scanning_flag.store(false, std::sync::atomic::Ordering::Relaxed);
        set_scan_state(&mqtt_client, "idle");
        scan_log(&mqtt_client, "ok",
            format!("Scan complete — {} device(s) published to the bus", scan_topic_to_resource.len()));

        // Publish the fresh topic→resource mapping for the Write daemon.
        *topic_to_resource.lock().unwrap() = scan_topic_to_resource;

        // Regenerate the Discovered tab panels from the retained discovery
        // topics just published. Phase 4 replaces this whole pipeline with the
        // Device Registry + a live Discovered widget.
        discovered_mirror.set_scanning(false);
        // The instruments this scan just found are published but not yet
        // mirrored — the retained tree has to come back round the broker. Give
        // it the same settle window a fresh subscribe gets, or the rebuild
        // writes tables that are one scan behind.
        discovered_mirror.settle().await;
        discovered_mirror.build_async().await;

        // Triggers that arrived DURING the scan are stale — the scan they
        // asked for just ran. This also absorbs the browser's 400 ms
        // settle-retained republish of the same press (forwarded live by
        // the broker), which would otherwise queue a second scan.
        while rescan_rx.try_recv().is_ok() {}

        // Wait for the Discovered tab's rescan trigger, then go again.
        println!("⏸️  [VISA AGENT] Scan idle — publish 1 (non-retained) to OpenAir/System/Protocols/visa/Device/Rescan to rescan.");
        if rescan_rx.recv().await.is_none() {
            break;
        }
        println!("🔁 [VISA AGENT] Rescan triggered from the bus.");

        } // end scan loop
    });

    // Sub-router for API endpoints
    let api_state = api::ApiState { root_dir: root.clone() };
    let api_router = api::router(api_state);

    let cors = CorsLayer::new()
        .allow_methods([Method::GET, Method::POST])
        .allow_origin(tower_http::cors::Any);

use axum::response::Redirect;

    let app = Router::new()
        .route("/", get(|| async { Redirect::temporary("/index.html") }))
        .nest("/api", api_router)
        .route("/api/health", get(|| async { "Rust Core is Healthy" }))
        .fallback_service(ServeDir::new(root.join("FrontEnd")).append_index_html_on_directories(true))
        .layer(cors);

    // Run on the frontend port, since orchestrator replaces the python server.
    // SECURITY: binds loopback unless --bind is given explicitly. This server
    // exposes POST /api/save (a file write) with no authentication, so exposing
    // it on the network is an opt-in decision, not the default. See cli.rs.
    let addr = SocketAddr::from((args.bind, args.port));
    
    let listener = match tokio::net::TcpListener::bind(addr).await {
        Ok(l) => l,
        Err(e) => {
            eprintln!("❌ [API] Could not bind {addr}: {e}");
            eprintln!("        Another instance might be running. Stop it or change port.");
            return;
        }
    };
    
    let local_ip = match std::net::UdpSocket::bind("0.0.0.0:0") {
        Ok(socket) => {
            if socket.connect("8.8.8.8:80").is_ok() {
                socket.local_addr().map(|addr| addr.ip().to_string()).unwrap_or_else(|_| "localhost".to_string())
            } else {
                "localhost".to_string()
            }
        },
        Err(_) => "localhost".to_string(),
    };
    let url = format!("http://{}:{}", local_ip, args.port);
    println!("🌐 [API] Frontend API Server listening on {}", url);
    if !args.no_browser {
        println!("🌐 [WEB] Opening {} in the browser…", url);
        let _ = open::that(url);
    }
    
    if let Err(e) = axum::serve(listener, app).await {
        eprintln!("❌ [API] server error: {e}");
    }
}


/// Topic carrying live scan narration to anyone watching — currently the browser
/// console (`MqttProvider.jsx`), which subscribes and prints each line.
///
/// Non-retained on purpose: this is an *event stream*, not state. A late joiner
/// should not be shown the tail of a scan that finished an hour ago as though it
/// were happening now. The resulting device records ARE retained; the narration
/// about producing them is not.
const SCAN_LOG_TOPIC: &str = "OpenAir/System/Protocols/visa/Scan/Log";

/// Retained scan state: `scanning` | `idle`.
///
/// Retained, unlike the log, because this IS state — a page loaded mid-scan
/// should know a scan is running. The Discovered-tab builder reads it and marks
/// every row amber while a scan is in flight, so a stale table cannot be
/// mistaken for a current one.
const SCAN_STATE_TOPIC: &str = "OpenAir/System/Protocols/visa/Scan/State";

/// Seconds between heartbeat probes. `OPENAIR_VISA_HEARTBEAT_SECS=0` disables it.
///
/// ONE instrument is probed per tick, round-robin, so this is also the per-device
/// load: a 24-instrument bench sees one VISA session every 20 seconds and each
/// instrument is re-verified about every 8 minutes — comfortably inside
/// ONLINE_WINDOW_SECONDS (15 min) in discovered.rs, which is what
/// decides whether a row is green.
///
/// Liveness used to be a by-product of scanning: `last_online` was stamped when a
/// scan probed an instrument and never touched again, so the Discovered table
/// turned red fifteen minutes after every scan whether or not anything had moved.
fn visa_heartbeat_secs() -> u64 {
    std::env::var("OPENAIR_VISA_HEARTBEAT_SECS")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(20)
}

/// Consecutive failed probes before an instrument is called unreachable.
///
/// One miss is a busy GPIB gateway mid-transaction, not a disconnected
/// instrument. Two is a pattern.
const VISA_HEARTBEAT_FAILS: u32 = 2;

/// Keep discovered instruments' liveness current between scans.
///
/// Probes with the SAME `*IDN?` path the scan uses — one python process, one
/// pyvisa session, opened and closed properly.
///
/// It is worth saying why, because the cheap-looking alternative is a trap. A
/// previous version of this opened a bare TCP connection to each instrument's
/// transport port instead: no python, no instrument traffic, microseconds per
/// device. For `::SOCKET` instruments that is harmless. For VXI-11 it means
/// knocking on the RPC portmapper (port 111), and this bench's LAN-GPIB gateways
/// do not reclaim the state that leaves behind. After roughly twenty minutes of
/// 30-second knocks BOTH gateways stopped creating links — every instrument
/// behind them went dark with VI_ERROR_IO, including to the scanner, and they
/// needed a power cycle. A directly-attached instrument on the same network was
/// unaffected, which is what identified the gateways as the victim.
///
/// So: no raw-socket probing. A real VISA session, one at a time, is both the
/// honest signal (the instrument answered, not merely its gateway's portmapper)
/// and the gentle one.
fn spawn_visa_heartbeat(
    topic_to_resource: std::sync::Arc<std::sync::Mutex<std::collections::HashMap<String, String>>>,
    scanning: std::sync::Arc<std::sync::atomic::AtomicBool>,
    mqtt_host: String,
    mqtt_port: u16,
) {
    let interval = visa_heartbeat_secs();
    if interval == 0 {
        println!("⏸️  [VISA HEARTBEAT] disabled (OPENAIR_VISA_HEARTBEAT_SECS=0)");
        return;
    }
    tokio::spawn(async move {
        let mut mqttoptions =
            rumqttc::MqttOptions::new("open-air-visa-heartbeat", &mqtt_host, mqtt_port);
        mqttoptions.set_keep_alive(std::time::Duration::from_secs(30));
        let (client, mut connection) = rumqttc::Client::new(mqttoptions, 10);
        std::thread::spawn(move || {
            for _ in connection.iter() {}
        });
        println!("💓 [VISA HEARTBEAT] one instrument re-verified every {interval}s");

        let mut misses: std::collections::HashMap<String, u32> = Default::default();
        let mut unreachable: std::collections::HashSet<String> = Default::default();
        let mut cursor: usize = 0;

        loop {
            tokio::time::sleep(std::time::Duration::from_secs(interval)).await;

            // A scan is already talking to every instrument on the bench, and
            // GPIB gateways serve one link at a time. Probing across it would
            // contend for the resource the scan is mid-way through using.
            if scanning.load(std::sync::atomic::Ordering::Relaxed) {
                continue;
            }

            let mut devices: Vec<(String, String)> = {
                let map = topic_to_resource.lock().unwrap();
                map.iter().map(|(k, v)| (k.clone(), v.clone())).collect()
            };
            if devices.is_empty() {
                continue;
            }
            // HashMap order is not stable across iterations; sorting makes the
            // rotation actually visit every device instead of resampling.
            devices.sort();
            misses.retain(|prefix, _| devices.iter().any(|(p, _)| p == prefix));

            let (prefix, resource) = devices[cursor % devices.len()].clone();
            cursor = cursor.wrapping_add(1);

            let alive = match tokio::process::Command::new("python3")
                .arg("-c")
                .arg(VISA_PROBE_SCRIPT)
                .arg(&resource)
                .output()
                .await
            {
                Ok(out) => {
                    let text = String::from_utf8_lossy(&out.stdout);
                    serde_json::from_str::<serde_json::Value>(&text)
                        .map(|v| v.get("error").is_none())
                        .unwrap_or(false)
                }
                Err(_) => false,
            };

            if alive {
                misses.insert(prefix.clone(), 0);
                let now = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs())
                    .unwrap_or(0);
                let _ = client.publish(format!("{prefix}/last_online"), rumqttc::QoS::AtMostOnce,
                                       true, now.to_string().into_bytes());
                let _ = client.publish(format!("{prefix}/reachable"), rumqttc::QoS::AtMostOnce,
                                       true, b"1".to_vec());
                if unreachable.remove(&prefix) {
                    let _ = client.publish(format!("{prefix}/status"), rumqttc::QoS::AtLeastOnce,
                                           true, b"identified".to_vec());
                    scan_log(&client, "ok", format!("{resource} is answering again"));
                }
            } else {
                let count = misses.entry(prefix.clone()).or_insert(0);
                *count += 1;
                if *count >= VISA_HEARTBEAT_FAILS && unreachable.insert(prefix.clone()) {
                    let _ = client.publish(format!("{prefix}/reachable"), rumqttc::QoS::AtLeastOnce,
                                           true, b"0".to_vec());
                    let _ = client.publish(format!("{prefix}/status"), rumqttc::QoS::AtLeastOnce,
                                           true, b"unreachable".to_vec());
                    scan_log(&client, "warn", format!("{resource} stopped answering"));
                }
            }
        }
    });
}

fn set_scan_state(client: &rumqttc::Client, state: &str) {
    let _ = client.publish(SCAN_STATE_TOPIC, rumqttc::QoS::AtLeastOnce, true, state.as_bytes().to_vec());
}

/// Print a scan line to the container log AND publish it to the bus.
///
/// The container log is invisible to anyone running the UI — which is the whole
/// problem this solves. Everything that matters goes on the bus (design audit
/// §4.6); this is that principle applied to the scan.
fn scan_log(client: &rumqttc::Client, level: &str, message: impl AsRef<str>) {
    let message = message.as_ref();
    println!("   📡 [VISA SCAN] {message}");
    let payload = serde_json::json!({
        "level": level,       // "info" | "ok" | "warn" | "error"
        "message": message,
        "ts": std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0),
    })
    .to_string();
    // QoS 0, non-retained: dropping a narration line under load is preferable to
    // slowing the scan down for it.
    let _ = client.publish(SCAN_LOG_TOPIC, rumqttc::QoS::AtMostOnce, false, payload.into_bytes());
}

/// Every attribute key published under a discovered-device prefix.
///
/// Shared by the per-scan cleanup and the CLEAR button, because deleting
/// retained state means publishing an empty payload to each exact topic — so
/// both paths must agree on the full key list or they leave fragments behind.
const DEVICE_TOPIC_KEYS: [&str; 14] = [
    "manufacturer", "model", "serial", "firmware", "raw_idn", "resource",
    "status", "device_type", "notes", "last_online", "connected", "Write", "Read",
    // Written by the heartbeat, not the scan — and just as retained, so it has
    // to be in the wipe list or a cleared device keeps a stale liveness flag.
    "reachable",
];

/// Collect the device-topic prefixes already retained on the broker.
///
/// MQTT has no "delete by wildcard": clearing retained state requires publishing
/// an empty payload to each exact topic. So to tidy up after a previous run we
/// must first find out what that run left behind.
///
/// Subscribes to the device wildcard, drains retained deliveries for a short
/// window, and returns the distinct `.../<Category>/<Model>/<DevN>` prefixes.
fn harvest_retained_device_prefixes(host: &str, port: u16) -> Vec<String> {
    use std::collections::HashSet;

    let mut opts = rumqttc::MqttOptions::new("open-air-visa-retained-harvest", host, port);
    opts.set_keep_alive(std::time::Duration::from_secs(5));
    let (client, mut connection) = rumqttc::Client::new(opts, 64);
    if client
        .subscribe("OpenAir/System/Protocols/visa/Device/#", rumqttc::QoS::AtLeastOnce)
        .is_err()
    {
        return Vec::new();
    }

    let mut prefixes: HashSet<String> = HashSet::new();
    let deadline = std::time::Instant::now() + std::time::Duration::from_millis(1500);
    for notification in connection.iter() {
        if std::time::Instant::now() > deadline {
            break;
        }
        if let Ok(rumqttc::Event::Incoming(rumqttc::Packet::Publish(p))) = notification {
            // Only retained deliveries describe prior state; live traffic during
            // the window is somebody else's business.
            if !p.retain || p.payload.is_empty() {
                continue;
            }
            // .../Device/<Category>/<Model>/<DevN>/<key>  ->  strip <key>
            if let Some((prefix, _key)) = p.topic.rsplit_once('/') {
                if prefix.contains("/Device/") && prefix != "OpenAir/System/Protocols/visa/Device" {
                    prefixes.insert(prefix.to_string());
                }
            }
        }
    }
    let _ = client.disconnect();
    prefixes.into_iter().collect()
}

/// Executes one SCPI write or query against one instrument.
///
/// Takes `sys.argv[1]` = VISA resource, `sys.argv[2]` = SCPI command. Nothing is
/// interpolated into this source — it is a constant, so no caller-supplied value
/// can alter the program. Invoked as `python3 -c SCRIPT <resource> <command>`,
/// which yields `sys.argv == ['-c', resource, command]`.
///
/// Phase 4 replaces this with native Rust VXI-11; until then argv is what keeps
/// the subshell safe.
const VISA_WRITE_SCRIPT: &str = r#"
import pyvisa
import sys

resource = sys.argv[1]
command = sys.argv[2]

try:
    rm = pyvisa.ResourceManager('@py')
except Exception:
    rm = pyvisa.ResourceManager()
try:
    inst = rm.open_resource(resource, open_timeout=2000)
    inst.timeout = 2000
    inst.read_termination = '\n'
    inst.write_termination = '\n'
    if '?' in command:
        print(inst.query(command).strip())
    else:
        inst.write(command)
    inst.close()
except Exception as e:
    print("ERROR:", str(e))
"#;

/// Probes one VISA resource for its `*IDN?` identity and prints a JSON record.
///
/// Takes `sys.argv[1]` = VISA resource. Same argv discipline as
/// [`VISA_WRITE_SCRIPT`]: the resource string comes from the local enumerator
/// rather than the network, but it is passed as data regardless — a resource
/// name is not a place to rely on the trustworthiness of its source.
const VISA_PROBE_SCRIPT: &str = r#"
import pyvisa
import json
import sys

resource = sys.argv[1]

try:
    rm = pyvisa.ResourceManager('@py')
except:
    try:
        rm = pyvisa.ResourceManager()
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

try:
    inst = rm.open_resource(resource, open_timeout=1500)
    inst.timeout = 1500
    inst.read_termination = '\n'
    inst.write_termination = '\n'
    idn = inst.query('*IDN?')
    inst.close()

    parts = [p.strip() for p in idn.split(',')]
    print(json.dumps({
        "manufacturer": parts[0] if len(parts) > 0 else 'Unknown',
        "model": parts[1] if len(parts) > 1 else 'Unknown',
        "serial": parts[2] if len(parts) > 2 else '',
        "firmware": parts[3] if len(parts) > 3 else '',
        "raw_idn": idn.strip()
    }))
except Exception as e:
    print(json.dumps({"error": str(e)}))
"#;

/// VISA Write daemon + rescan listener. Owns its own MQTT connection on a
/// dedicated OS thread (rumqttc sync iter blocks). `topic_to_resource` is
/// shared with the scan loop, which swaps in a fresh mapping per scan;
/// a non-retained truthy publish on .../Device/Rescan signals that loop.
fn spawn_visa_write_daemon(
    topic_to_resource: std::sync::Arc<std::sync::Mutex<std::collections::HashMap<String, String>>>,
    rescan_tx: tokio::sync::mpsc::Sender<()>,
    daemon_host: String,
    daemon_port: u16,
) {
    const RESCAN_TOPIC: &str = "OpenAir/System/Protocols/visa/Device/Rescan";
    /// Wipes every retained discovered-device topic. The Discovered tab's CLEAR
    /// button publishes here.
    const CLEAR_TOPIC: &str = "OpenAir/System/Protocols/visa/Device/Clear";
    println!("🚀 [VISA AGENT] Starting MQTT Daemon for live SCPI commands + rescan/clear triggers...");
    let mut mqttoptions_sub = rumqttc::MqttOptions::new("open-air-visa-daemon", &daemon_host, daemon_port);
    mqttoptions_sub.set_keep_alive(std::time::Duration::from_secs(30));
    let (mut mqtt_client_sub, mut mqtt_connection_sub) = rumqttc::Client::new(mqttoptions_sub, 10);

    let _ = mqtt_client_sub.subscribe("OpenAir/System/Protocols/visa/Device/+/+/+/Write", rumqttc::QoS::AtLeastOnce);
    let _ = mqtt_client_sub.subscribe(RESCAN_TOPIC, rumqttc::QoS::AtLeastOnce);
    let _ = mqtt_client_sub.subscribe(CLEAR_TOPIC, rumqttc::QoS::AtLeastOnce);

    std::thread::spawn(move || {
        for notification in mqtt_connection_sub.iter() {
            if let Ok(rumqttc::Event::Incoming(rumqttc::Packet::Publish(publish))) = notification {
                let topic = publish.topic.clone();
                let payload = String::from_utf8_lossy(&publish.payload).trim().to_string();

                if topic == CLEAR_TOPIC {
                    // Same retained-vs-live rule as rescan: a retained replay at
                    // boot must not wipe the registry.
                    if !publish.retain && is_truthy_trigger(&payload) {
                        println!("   🧹 [VISA MQTT] Clear requested — wiping retained device topics");
                        // Harvest what is actually retained, then delete each by
                        // publishing an empty retained payload. MQTT has no
                        // delete-by-wildcard, and the in-memory map only knows
                        // about devices this process found — anything left by an
                        // earlier run would otherwise survive forever.
                        let prefixes = harvest_retained_device_prefixes(&daemon_host, daemon_port);
                        let mut wiped = 0usize;
                        for prefix in &prefixes {
                            for key in DEVICE_TOPIC_KEYS {
                                let _ = mqtt_client_sub.publish(
                                    format!("{prefix}/{key}"),
                                    rumqttc::QoS::AtLeastOnce,
                                    true,
                                    Vec::<u8>::new(),
                                );
                            }
                            wiped += 1;
                        }
                        topic_to_resource.lock().unwrap().clear();
                        println!("   🧹 [VISA MQTT] cleared {wiped} device(s)");
                    }
                    continue;
                }

                if topic == RESCAN_TOPIC {
                    // Retained messages are state, not commands: only a live
                    // press triggers (the browser's settle-retained publish
                    // and boot-time retained replay must not start scans).
                    if !publish.retain && is_truthy_trigger(&payload) {
                        println!("   🔁 [VISA MQTT] Rescan requested via {}", topic);
                        let _ = rescan_tx.try_send(()); // full channel = scan already pending
                    }
                    continue;
                }

                if payload.is_empty() { continue; }

                if let Some(topic_prefix) = topic.strip_suffix("/Write") {
                    let resource = topic_to_resource.lock().unwrap().get(topic_prefix).cloned();
                    if let Some(resource_name) = resource {
                        println!("   📡 [VISA MQTT] Executing on {} -> {}", resource_name, payload);

                        // SECURITY: the resource and the SCPI command are passed as
                        // argv, never interpolated into the script body. The previous
                        // version built the source with `payload.replace("'", "\\'")`,
                        // which is not an escape — it writes a backslash into Python
                        // source, so a payload ending in a backslash consumed the
                        // closing quote and broke out into executable code. The
                        // payload arrives raw off MQTT, so that was remote code
                        // execution. As argv, a payload containing quotes,
                        // backslashes, or newlines is inert data to the interpreter.
                        if let Ok(output) = std::process::Command::new("python3")
                            .arg("-c")
                            .arg(VISA_WRITE_SCRIPT)
                            .arg(&resource_name)
                            .arg(&payload)
                            .output()
                        {
                            let out_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
                            if payload.contains('?') {
                                println!("      ⮜ [VISA MQTT] {} response -> {}", resource_name, out_str);
                                let read_topic = format!("{}/Read", topic_prefix);
                                let _ = mqtt_client_sub.publish(read_topic, rumqttc::QoS::AtLeastOnce, true, out_str.as_bytes());
                                let write_topic = format!("{}/Write", topic_prefix);
                                let _ = mqtt_client_sub.publish(write_topic, rumqttc::QoS::AtLeastOnce, true, "");
                            } else if !out_str.is_empty() {
                                println!("      ⚠️ [VISA MQTT] {} warning/error -> {}", resource_name, out_str);
                            }
                        }
                    }
                }
            }
        }
    });
}

/// Truthy scan trigger: the GUI envelope `{"value":1,...}`, or a bare
/// `1`/`true`/`scan`. `0`, `false`, and empty payloads never trigger.
pub(crate) fn is_truthy_trigger(payload: &str) -> bool {
    if let Ok(v) = serde_json::from_str::<serde_json::Value>(payload) {
        return match v.get("value").unwrap_or(&v) {
            serde_json::Value::Number(n) => n.as_f64().unwrap_or(0.0) != 0.0,
            serde_json::Value::Bool(b) => *b,
            serde_json::Value::String(s) => s == "1" || s.eq_ignore_ascii_case("true") || s.eq_ignore_ascii_case("scan"),
            _ => false,
        };
    }
    payload == "1" || payload.eq_ignore_ascii_case("true") || payload.eq_ignore_ascii_case("scan")
}
