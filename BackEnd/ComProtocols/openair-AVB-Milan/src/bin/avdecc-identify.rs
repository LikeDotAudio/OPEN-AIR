//! `avdecc-identify` — make an AVB device blink its front-panel LED.
//!
//! The "which box in the rack are you" tool. This is Hive's Identify button as
//! a command line.
//!
//! ```text
//! sudo ./avdecc-identify                      # one entity on the network: blink it
//! sudo ./avdecc-identify --list               # just show what is out there
//! sudo ./avdecc-identify 1B:2C                # match an entity ID or MAC by substring
//! sudo ./avdecc-identify 1B:2C --seconds 30   # blink longer
//! ```
//!
//! Needs `CAP_NET_RAW`, like every AVDECC tool.
//!
//! # This one writes to the device
//!
//! Every other tool in these crates only listens. This sends a command to real
//! hardware. Two guards follow from that, and both are deliberate:
//!
//! * With no target argument it will only act when **exactly one** entity is
//!   present. Ambiguity means listing what was found and stopping — picking a
//!   device for you is how the wrong console in a different room starts
//!   flashing.
//! * The blink is always turned back off, including on Ctrl-C.

use openair_avb_milan::{adp, aecp, capture, identify};
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{Duration, Instant};

/// How long to gather announcements before deciding what is on the network.
const DISCOVER_SECS: u64 = 6;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let list_only = args.iter().any(|a| a == "--list" || a == "-l");
    let blink_secs = args
        .windows(2)
        .find(|w| w[0] == "--seconds" || w[0] == "-s")
        .and_then(|w| w[1].parse::<u64>().ok())
        .unwrap_or(identify::DEFAULT_BLINK_SECS);
    let target: Option<String> = args
        .iter()
        .find(|a| !a.starts_with('-') && a.parse::<u64>().is_err())
        .cloned();

    let socket = match capture::RawSocket::open() {
        Ok(s) => s,
        Err(e) => {
            eprintln!("🛑 {}", capture::explain_error(&e));
            std::process::exit(1);
        }
    };

    let interfaces = match openair_avb_milan::start_capture() {
        Ok((_, ifaces)) if ifaces.is_empty() => {
            eprintln!("🛑 no capturable Ethernet interfaces");
            std::process::exit(1);
        }
        Ok((_, ifaces)) => {
            for i in &ifaces {
                let _ = socket.join_avdecc_group(i.index);
            }
            ifaces
        }
        Err(e) => {
            eprintln!("🛑 {}", capture::explain_error(&e));
            std::process::exit(1);
        }
    };

    println!("📣 discovering entities for {DISCOVER_SECS}s...");
    openair_avb_milan::send_discover(&socket, &interfaces);

    // Which interface an entity was heard on decides which one we answer from —
    // on a multi-homed host the wrong source interface reaches nothing.
    let by_index: HashMap<u32, capture::Interface> =
        interfaces.iter().map(|i| (i.index, i.clone())).collect();
    let mut found: HashMap<u64, (adp::AdpEntity, capture::Interface)> = HashMap::new();

    let deadline = Instant::now() + Duration::from_secs(DISCOVER_SECS);
    let mut buf = [0u8; 2048];
    while Instant::now() < deadline {
        if let Ok(Some((len, if_index))) = socket.recv(&mut buf) {
            if let Ok(entity) = adp::parse_frame(&buf[..len]) {
                if entity.message_type != adp::MessageType::EntityAvailable {
                    continue;
                }
                if let Some(iface) = by_index.get(&if_index) {
                    found.entry(entity.entity_id).or_insert((entity, iface.clone()));
                }
            }
        }
    }

    if found.is_empty() {
        eprintln!("\n❌ No AVDECC entities found. Run avdecc-probe for a fuller diagnosis.");
        std::process::exit(1);
    }

    println!("\nEntities:");
    for (entity, iface) in found.values() {
        let can = if entity.entity_capabilities & 0x4000 != 0 {
            format!("identify index {}", entity.identify_control_index)
        } else {
            "no identify control advertised".to_string()
        };
        println!(
            "  • {}  {}  on {}  ({can})",
            adp::format_id(entity.entity_id),
            adp::format_mac(&entity.source_mac),
            iface.name
        );
    }

    if list_only {
        return;
    }

    // Select the target. Substring match against entity ID or MAC, case
    // insensitive, so "1b:2c" or "0A:1B" both work from a glance at the list.
    let matches: Vec<&(adp::AdpEntity, capture::Interface)> = match &target {
        Some(want) => {
            let want = want.to_uppercase();
            found
                .values()
                .filter(|(e, _)| {
                    adp::format_id(e.entity_id).contains(&want)
                        || adp::format_mac(&e.source_mac).contains(&want)
                })
                .collect()
        }
        None => found.values().collect(),
    };

    let (entity, iface) = match matches.as_slice() {
        [one] => *one,
        [] => {
            eprintln!("\n🛑 no entity matches {:?}", target.unwrap_or_default());
            std::process::exit(1);
        }
        many => {
            // Refusing to choose is the whole point: the cost of guessing is a
            // stranger's console flashing in another room.
            eprintln!(
                "\n🛑 {} entities match — narrow it down with a longer substring.",
                many.len()
            );
            std::process::exit(1);
        }
    };

    // Ctrl-C during the blink must still send the off command, so the handler
    // sets a flag that identify() polls rather than letting the default
    // disposition kill the process mid-blink.
    let interrupted: &'static AtomicBool = Box::leak(Box::new(AtomicBool::new(false)));
    let _ = unsafe {
        signal_hook_lite::on_sigint(|| interrupted.store(true, Ordering::SeqCst))
    };

    println!(
        "\n💡 identifying {} on {} for {blink_secs}s — watch the front panel\n",
        adp::format_id(entity.entity_id),
        iface.name
    );

    let outcome = identify::identify(&socket, iface, entity, blink_secs, interrupted);

    println!("\n═══════════════════════ RESULT ═══════════════════════");
    println!("{}", outcome.describe());

    if let identify::IdentifyOutcome::Answered(status) = &outcome {
        if *status != aecp::AemStatus::Success {
            std::process::exit(2);
        }
    }
}

/// Minimal SIGINT hook.
///
/// A dependency for this would be a whole crate to set one flag; the blink-off
/// path is the only thing that needs it, and it needs it to be reliable rather
/// than featureful.
mod signal_hook_lite {
    use std::sync::OnceLock;

    static HANDLER: OnceLock<Box<dyn Fn() + Send + Sync>> = OnceLock::new();

    extern "C" fn trampoline(_sig: i32) {
        if let Some(h) = HANDLER.get() {
            h();
        }
    }

    /// # Safety
    /// Installs a process-wide signal handler; call once, early.
    pub unsafe fn on_sigint<F: Fn() + Send + Sync + 'static>(f: F) -> Result<(), ()> {
        HANDLER.set(Box::new(f)).map_err(|_| ())?;
        unsafe { libc::signal(libc::SIGINT, trampoline as *const () as libc::sighandler_t) };
        Ok(())
    }
}
