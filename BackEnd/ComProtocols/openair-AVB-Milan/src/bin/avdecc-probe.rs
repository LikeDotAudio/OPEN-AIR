//! `avdecc-probe` — is there an AVB/Milan device on this network?
//!
//! A standalone answer to that one question, with no MQTT broker and no
//! orchestrator in the way. Run it, watch for 30 seconds, get a verdict.
//!
//! ```text
//! sudo ./avdecc-probe            # listen on every Ethernet interface
//! sudo ./avdecc-probe enp5s0f0   # ...or just the audio network
//! ```
//!
//! It needs `CAP_NET_RAW` because AVDECC is a Layer 2 protocol; there is no
//! unprivileged way to read raw Ethernet frames on Linux.
//!
//! Two things make this worth having as its own binary rather than a flag on
//! the agent. It reports the **negative** result usefully — "listened on these
//! interfaces, sent this many queries, heard nothing" is a diagnosis, whereas
//! an agent that publishes no topics is indistinguishable from one that never
//! started. And it prints every AVTP subtype it sees, so a device that streams
//! but does not announce still shows up as evidence of *something* on the wire.

use openair_avb_milan::{adp, capture};
use std::collections::HashMap;
use std::time::{Duration, Instant};

const LISTEN_SECS: u64 = 30;

fn main() {
    let only_iface: Option<String> = std::env::args().nth(1);

    println!("╔══════════════════════════════════════════════════════════════╗");
    println!("║  AVDECC probe — looking for AVB / Milan entities (IEEE 1722.1)║");
    println!("╚══════════════════════════════════════════════════════════════╝");

    let socket = match capture::RawSocket::open() {
        Ok(s) => s,
        Err(e) => {
            eprintln!("\n🛑 {}\n", capture::explain_error(&e));
            std::process::exit(1);
        }
    };

    let all = match capture::list_interfaces() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("🛑 cannot enumerate interfaces: {e}");
            std::process::exit(1);
        }
    };

    let selected: Vec<capture::Interface> = all
        .into_iter()
        .filter(|i| only_iface.as_ref().is_none_or(|want| &i.name == want))
        .collect();

    if selected.is_empty() {
        eprintln!("🛑 no matching Ethernet interface");
        std::process::exit(1);
    }

    println!("\nInterfaces:");
    let mut listening = Vec::new();
    for iface in selected {
        let carrier = if iface.is_up { "up" } else { "NO CARRIER" };
        match socket.join_avdecc_group(iface.index) {
            Ok(()) => {
                println!(
                    "  ✔ {:<12} {} [{}] — joined 91:E0:F0:01:00:00",
                    iface.name,
                    adp::format_mac(&iface.mac),
                    carrier
                );
                listening.push(iface);
            }
            Err(e) => println!("  ✘ {:<12} join failed: {e}", iface.name),
        }
    }
    if listening.is_empty() {
        eprintln!("\n🛑 joined no interfaces — nothing to listen on");
        std::process::exit(1);
    }

    // Ask, rather than wait up to a full heartbeat interval. This is the same
    // query Hive sends on startup; it changes nothing on the network.
    let sent = openair_avb_milan::send_discover(&socket, &listening);
    println!("\n📣 ENTITY_DISCOVER sent on {sent:?}");
    println!("👂 listening {LISTEN_SECS}s...\n");

    let by_index: HashMap<u32, String> =
        listening.iter().map(|i| (i.index, i.name.clone())).collect();

    let mut entities: HashMap<u64, (adp::AdpEntity, String)> = HashMap::new();
    // Non-ADP AVTP subtypes seen. Evidence of AVB life even without ADP.
    let mut other_subtypes: HashMap<u8, usize> = HashMap::new();
    let mut frames = 0usize;

    let deadline = Instant::now() + Duration::from_secs(LISTEN_SECS);
    let mut buf = [0u8; 2048];
    while Instant::now() < deadline {
        match socket.recv(&mut buf) {
            Ok(Some((len, if_index))) => {
                frames += 1;
                let iface = by_index.get(&if_index).cloned().unwrap_or_else(|| "?".into());
                match adp::parse_frame(&buf[..len]) {
                    Ok(entity) => {
                        if entity.message_type == adp::MessageType::EntityDiscover {
                            continue; // Another controller, not a device.
                        }
                        if !entities.contains_key(&entity.entity_id) {
                            println!("  🎛️  found {}", entity.summary());
                        }
                        entities.insert(entity.entity_id, (entity, iface));
                    }
                    Err(adp::AdpError::NotAdp(subtype)) => {
                        *other_subtypes.entry(subtype).or_default() += 1;
                    }
                    Err(_) => {}
                }
            }
            Ok(None) => {}
            Err(e) => {
                eprintln!("🛑 capture failed: {}", capture::explain_error(&e));
                break;
            }
        }
    }

    report(&entities, &other_subtypes, frames, LISTEN_SECS);
}

fn report(
    entities: &HashMap<u64, (adp::AdpEntity, String)>,
    other_subtypes: &HashMap<u8, usize>,
    frames: usize,
    secs: u64,
) {
    println!("\n═══════════════════════ RESULT ═══════════════════════");
    println!("AVTP frames seen: {frames} in {secs}s");

    if entities.is_empty() {
        println!("\n❌ No AVDECC entities announced.\n");
        if other_subtypes.is_empty() {
            // The honest reading: silence on 0x22F0 is silence, and the causes
            // are worth listing because they are all things the operator can
            // check in about a minute each.
            println!("No AVTP traffic of any kind was seen. Most likely one of:");
            println!("  • the device is not on a listening interface (check the cable/VLAN)");
            println!("  • the switch is not AVB-capable and is dropping the multicast");
            println!("  • the device's AVB/Milan mode is not enabled");
            println!("  • the device announces only after gPTP lock — give it a minute");
        } else {
            println!("But AVTP traffic IS present — so the wire is alive:");
            for (subtype, count) in other_subtypes {
                let label = match subtype {
                    0x00 => "IEC 61883/IIDC stream",
                    0x02 => "AAF audio stream",
                    0x03 => "CVF video stream",
                    0x7B => "AECP (enumeration/control)",
                    0x7C => "ACMP (connection management)",
                    0x7D => "MAAP (address allocation)",
                    _ => "unrecognised",
                };
                println!("  • subtype 0x{subtype:02X} ({label}): {count} frames");
            }
            println!("\nAVTP without ADP usually means a device streaming but not");
            println!("announcing — check whether AVDECC is enabled separately from AVB.");
        }
        return;
    }

    println!("\n✅ {} AVDECC entit{} found:\n", entities.len(),
        if entities.len() == 1 { "y" } else { "ies" });

    for (entity, iface) in entities.values() {
        println!("┌─ Entity {}", adp::format_id(entity.entity_id));
        println!("│  MAC            {} (OUI {})", adp::format_mac(&entity.source_mac), adp::format_oui(&entity.source_mac));
        println!("│  Interface      {iface}");
        println!("│  Model ID       {}", adp::format_id(entity.entity_model_id));
        println!("│  Talker         {} stream source(s)  [{}]",
            entity.talker_stream_sources, entity.talker_capability_names().join(", "));
        println!("│  Listener       {} stream sink(s)    [{}]",
            entity.listener_stream_sinks, entity.listener_capability_names().join(", "));
        println!("│  Capabilities   {}", entity.entity_capability_names().join(", "));
        println!("│  gPTP GM        {} (domain {})",
            adp::format_id(entity.gptp_grandmaster_id), entity.gptp_domain_number);
        println!("│  Config index   {}", entity.current_configuration_index);
        println!("│  Valid for      {}s", entity.valid_time_secs);
        println!("│  Milan          {}", entity.milan_assessment());
        println!("└─");
    }

    // Grandmaster agreement is the single most common cause of "discovered but
    // will not pass audio", and it is free to check once entities are in hand.
    let masters: std::collections::HashSet<u64> =
        entities.values().map(|(e, _)| e.gptp_grandmaster_id).collect();
    if masters.len() > 1 {
        println!("\n⚠️  Entities report {} different gPTP grandmasters.", masters.len());
        println!("   Devices on different clocks cannot stream to each other.");
    }

    println!("\nNote: ADP carries capability flags and stream counts only.");
    println!("Channel names and routing need AEM enumeration, which this does not do.");
}
