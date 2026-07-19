//! `ptp-monitor` — watch PTP traffic live, as it arrives.
//!
//! Shows every PTP message on the NIC with its conversation partner resolved:
//! a Sync appears, then its Follow_Up is shown linked to it with the observed
//! gap; a Pdelay_Req is followed by its Resp and Resp_Follow_Up. All three
//! flavours — PTPv1, PTPv2 and gPTP — are decoded from the same stream.
//!
//! ```text
//! sudo ./ptp-monitor                 # live tail of everything
//! sudo ./ptp-monitor --summary       # clock table, refreshed periodically
//! sudo ./ptp-monitor --seconds 30    # stop after 30s and print the summary
//! sudo ./ptp-monitor --domain 0      # only this PTP domain
//! ```
//!
//! Needs privileged ports (319/320) and raw capture:
//! `sudo setcap cap_net_raw,cap_net_bind_service+eip ptp-monitor`

use openair_ptp::flow::FlowTracker;
use openair_ptp::message::{format_clock_id, MessageType, Variant};
use openair_ptp::monitor::{ClockTable, Observation, Transports};
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{Duration, Instant};

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let summary_only = args.iter().any(|a| a == "--summary");
    let seconds = arg_value(&args, "--seconds").and_then(|v| v.parse::<u64>().ok());
    let domain_filter = arg_value(&args, "--domain").and_then(|v| v.parse::<u8>().ok());

    println!("╔═══════════════════════════════════════════════════════════════╗");
    println!("║  PTP monitor — PTPv1 + PTPv2 + gPTP on one NIC                ║");
    println!("╚═══════════════════════════════════════════════════════════════╝");

    let transports = Transports::open();
    for problem in &transports.problems {
        println!("⚠️  {problem}");
    }
    if !transports.any_open() {
        eprintln!("\n🛑 no PTP transport could be opened — nothing to listen to.");
        std::process::exit(1);
    }

    let ifaces: Vec<&str> =
        transports.interfaces.iter().map(|(n, _, _, _)| n.as_str()).collect();
    println!(
        "\n👂 listening: {} UDP port(s), L2 {} — interfaces {ifaces:?}",
        transports.udp.len(),
        if transports.l2.is_some() { "yes" } else { "NO" }
    );
    if let Some(d) = domain_filter {
        println!("   filtered to domain {d}");
    }
    println!();

    let stop: &'static AtomicBool = Box::leak(Box::new(AtomicBool::new(false)));
    unsafe { install_sigint(|| stop.store(true, Ordering::SeqCst)) };

    let started = Instant::now();
    let deadline = seconds.map(|s| started + Duration::from_secs(s));

    let mut tracker = FlowTracker::default();
    let mut table = ClockTable::default();
    let mut total = 0u64;
    let mut undecodable = 0u64;
    // Split by transport. "UDP sockets opened fine but received nothing while
    // Layer 2 works" is not an empty network — it is the exact signature of a
    // host firewall, because raw AF_PACKET capture sits BELOW netfilter and
    // UDP does not. Diagnosed the hard way on this bench: ufw with a default
    // INPUT DROP silently ate every PTPv1/PTPv2 packet while gPTP flowed.
    let mut udp_seen = 0u64;
    let mut l2_seen = 0u64;
    let mut last_summary = Instant::now();

    openair_ptp::monitor::run(
        &transports,
        &mut tracker,
        |obs| {
            total += 1;
            match &obs {
                Observation::V2(_, _, meta) | Observation::V1(_, meta) => {
                    if meta.port.is_some() { udp_seen += 1 } else { l2_seen += 1 }
                }
                Observation::Undecodable { .. } => {}
            }
            match obs {
                Observation::V2(msg, correlation, meta) => {
                    if domain_filter.is_some_and(|d| d != msg.domain) {
                        return;
                    }
                    table.record(&msg, &meta);
                    if summary_only {
                        return;
                    }

                    let elapsed = meta.at.saturating_duration_since(started);
                    let transport = match msg.variant {
                        Variant::Gptp => "gPTP",
                        Variant::V2Ethernet => "v2/L2",
                        Variant::V2Udp => "v2/UDP",
                        Variant::V1 => "v1",
                    };
                    let port = meta.port.map(|p| p.to_string()).unwrap_or_else(|| "L2".into());

                    let mut line = format!(
                        "{:>8.3}s {:6} {:>4} {:<21} seq {:5} dom {:3} from {}",
                        elapsed.as_secs_f64(),
                        transport,
                        port,
                        msg.message_type.label(),
                        msg.sequence_id,
                        msg.domain,
                        msg.source_id()
                    );

                    // The detail that makes each message type worth reading.
                    match msg.message_type {
                        MessageType::Sync => {
                            line.push_str(if msg.is_two_step() {
                                "  [twoStep — Follow_Up expected]"
                            } else {
                                "  [oneStep — no Follow_Up will come]"
                            });
                        }
                        MessageType::Announce => {
                            if let Some(a) = &msg.announce {
                                line.push_str(&format!(
                                    "\n           ↳ GM {} prio {}/{} class {} ({}) acc {} src {} steps {}",
                                    format_clock_id(&a.grandmaster_identity),
                                    a.grandmaster_priority1,
                                    a.grandmaster_priority2,
                                    a.grandmaster_quality.class,
                                    a.grandmaster_quality.class_meaning(),
                                    a.grandmaster_quality.accuracy_meaning(),
                                    a.time_source_meaning(),
                                    a.steps_removed,
                                ));
                            }
                        }
                        _ => {
                            if let Some(ts) = msg.timestamp {
                                if !ts.is_zero() {
                                    line.push_str(&format!("  t={ts}"));
                                }
                            }
                        }
                    }
                    if msg.correction_ns.abs() > 0.001 {
                        line.push_str(&format!("  corr {:.3}ns", msg.correction_ns));
                    }
                    println!("{line}");

                    // The whole point: show what this message answered.
                    if let Some(c) = correlation {
                        println!(
                            "           ↳ completes {} seq {} — observed {:.3}ms after it",
                            c.responds_to.label(),
                            c.sequence_id,
                            c.observed_gap.as_secs_f64() * 1000.0
                        );
                    }
                }
                Observation::V1(m, meta) => {
                    if summary_only {
                        return;
                    }
                    println!(
                        "{:>8.3}s {:6} {:>4} {:<21} seq {:5} sub {:8} from {}",
                        meta.at.saturating_duration_since(started).as_secs_f64(),
                        "v1",
                        meta.port.map(|p| p.to_string()).unwrap_or_else(|| "L2".into()),
                        m.message_type.label(),
                        m.sequence_id,
                        m.subdomain,
                        openair_ptp::v1::format_uuid(&m.source_uuid),
                    );
                }
                Observation::Undecodable { reason, meta } => {
                    undecodable += 1;
                    if !summary_only {
                        println!("           ⚠️  undecodable from {}: {reason}", meta.source);
                    }
                }
            }

            if summary_only && last_summary.elapsed() > Duration::from_secs(5) {
                last_summary = Instant::now();
                print_summary(&table, total, undecodable, udp_seen, l2_seen, &transports);
            }
        },
        || stop.load(Ordering::SeqCst) || deadline.is_some_and(|d| Instant::now() > d),
    );

    print_summary(&table, total, undecodable, udp_seen, l2_seen, &transports);
}

fn arg_value(args: &[String], flag: &str) -> Option<String> {
    args.windows(2).find(|w| w[0] == flag).map(|w| w[1].clone())
}

fn print_summary(
    table: &ClockTable,
    total: u64,
    undecodable: u64,
    udp_seen: u64,
    l2_seen: u64,
    transports: &Transports,
) {
    println!("\n═══════════════════════ CLOCKS SEEN ═══════════════════════");
    println!("{total} PTP messages ({undecodable} undecodable) — {udp_seen} UDP, {l2_seen} Layer 2\n");

    // The firewall signature. Worth shouting about: every other symptom of it
    // looks exactly like "there is no PTP here".
    if udp_seen == 0 && !transports.udp.is_empty() {
        println!("⚠️  UDP sockets are open but received NOTHING.");
        if l2_seen > 0 {
            println!("   Layer 2 capture IS working, which narrows it sharply: raw AF_PACKET");
            println!("   sits below netfilter, UDP does not. A host firewall dropping inbound");
            println!("   UDP produces exactly this split.");
        }
        println!("   Check:  sudo ufw status   (or: sudo iptables -S | grep INPUT)");
        println!("   Allow:  sudo ufw allow in on <iface> to any port 319,320 proto udp");
        println!("   Verify the traffic exists with a tap below netfilter:");
        println!("     sudo tcpdump -i <iface> -nn -c 5 'udp port 319 or udp port 320'");
        println!();
    }

    if table.clocks.is_empty() {
        println!("No PTP clocks seen. If you expected some:");
        println!("  • gPTP is Layer 2 — it needs CAP_NET_RAW, check the warnings above");
        println!("  • PTP over UDP needs ports 319/320, which are privileged");
        println!("  • the switch may not be forwarding the multicast to this port");
        return;
    }

    let mut clocks: Vec<_> = table.clocks.values().collect();
    // Grandmasters first, then by identity, so the important rows lead.
    clocks.sort_by_key(|c| (c.steps_removed.unwrap_or(u16::MAX), c.key.label()));

    for c in clocks {
        let role = if c.is_grandmaster() { "GRANDMASTER" } else { "clock" };
        println!("┌─ {} {} [{}] domain {}", role, c.key.label(), c.variant.label(), c.domain);
        if let Some(gm) = c.grandmaster {
            println!("│  follows GM   {}", format_clock_id(&gm));
        }
        if let Some(class) = c.grandmaster_class {
            let q = openair_ptp::message::ClockQuality {
                class,
                accuracy: c.grandmaster_accuracy.unwrap_or(0xFE),
                offset_scaled_log_variance: 0,
            };
            println!("│  GM quality   class {class} ({}) / accuracy {}", q.class_meaning(), q.accuracy_meaning());
        }
        if let Some(steps) = c.steps_removed {
            println!("│  stepsRemoved {steps}");
        }
        if let (Some(p1), Some(p2)) = (c.priority1, c.priority2) {
            println!("│  priority     {p1} / {p2}");
        }
        if let Some(utc) = c.utc_offset {
            println!("│  UTC offset   {utc}s");
        }
        if let Some(i) = c.sync_interval {
            println!("│  Sync every   {:.3}s  ({})", i, if c.two_step { "two-step" } else { "one-step" });
        }
        if let Some(i) = c.announce_interval {
            println!("│  Announce ev. {i:.3}s");
        }
        let mut counts: Vec<_> = c.message_counts.iter().collect();
        counts.sort();
        let counts: Vec<String> = counts.iter().map(|(k, v)| format!("{k} ×{v}")).collect();
        println!("│  messages     {}", counts.join(", "));
        println!("│  seen on      {} via {}", c.interface, c.source);
        println!("└─");
    }

    // The diagnosis worth leading with when it applies.
    for ((domain, variant), gms) in table.grandmasters_by_domain() {
        if gms.len() > 1 {
            println!(
                "\n⚠️  {} grandmasters claimed in domain {domain} ({}):",
                gms.len(),
                variant.label()
            );
            for gm in &gms {
                println!("     {}", format_clock_id(gm));
            }
            println!("   Devices following different grandmasters are not on the same time.");
        }
    }
}

/// Minimal SIGINT hook so a Ctrl-C prints the summary instead of discarding it.
unsafe fn install_sigint<F: Fn() + Send + Sync + 'static>(f: F) {
    use std::sync::OnceLock;
    static HANDLER: OnceLock<Box<dyn Fn() + Send + Sync>> = OnceLock::new();
    extern "C" fn trampoline(_sig: i32) {
        if let Some(h) = HANDLER.get() {
            h();
        }
    }
    let _ = HANDLER.set(Box::new(f));
    unsafe { libc::signal(libc::SIGINT, trampoline as *const () as libc::sighandler_t) };
}
