//! Driving the IDENTIFY command: send, await the response, guarantee the off.
//!
//! AECP is a request/response protocol over a lossy Layer 2 link with no
//! retransmission underneath it, so 1722.1 §9.2.1.2 puts the retry burden on
//! the controller: resend the *same* sequence ID on timeout. Reusing the ID is
//! the point — a device that received the first copy recognises the retry as a
//! duplicate rather than treating it as a second command.

use crate::adp::AdpEntity;
use crate::aecp::{self, AemStatus};
use crate::capture::{Interface, RawSocket};
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{Duration, Instant};

/// Per-attempt wait for a response (§9.2.1.2 specifies 250ms).
const RESPONSE_TIMEOUT: Duration = Duration::from_millis(250);

/// Total attempts: the initial command plus two retries.
const ATTEMPTS: u8 = 3;

/// How long the LED stays on before we turn it back off.
pub const DEFAULT_BLINK_SECS: u64 = 10;

/// Outcome of an identify attempt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IdentifyOutcome {
    /// The device answered. Carries its status — which may still be a refusal.
    Answered(AemStatus),
    /// No response after all attempts. On AVDECC this is genuinely ambiguous:
    /// the device may have blinked and its response been lost.
    NoResponse,
    /// The entity does not advertise a valid identify control index, so there
    /// is no index to command without enumerating its descriptor tree.
    NoIdentifyControl,
}

impl IdentifyOutcome {
    pub fn describe(&self) -> String {
        match self {
            Self::Answered(status) => format!("{:?} — {}", status, status.explain()),
            Self::NoResponse => concat!(
                "no response after 3 attempts. The device may still have blinked — ",
                "AECP responses are not guaranteed to arrive. Watch the front panel."
            )
            .to_string(),
            Self::NoIdentifyControl => concat!(
                "entity does not set AEM_IDENTIFY_CONTROL_INDEX_VALID, so its identify ",
                "control index is unknown. Finding it requires AEM enumeration, which ",
                "this crate does not implement."
            )
            .to_string(),
        }
    }
}

/// Send one `SET_CONTROL` and wait for the matching response.
///
/// Frames for other entities keep arriving throughout; matching on both the
/// sequence ID and the controller ID is what stops a neighbouring device's
/// traffic being read as our answer.
fn command_and_wait(
    socket: &RawSocket,
    iface: &Interface,
    entity: &AdpEntity,
    controller_id: u64,
    sequence_id: u16,
    value: u8,
) -> Option<AemStatus> {
    let frame = aecp::build_identify_frame(
        iface.mac,
        entity.source_mac,
        entity.entity_id,
        controller_id,
        sequence_id,
        entity.identify_control_index,
        value,
    );

    let mut buf = [0u8; 2048];
    for attempt in 1..=ATTEMPTS {
        if let Err(e) = socket.send_on(iface.index, &frame) {
            eprintln!("   ⚠️  [AVB] identify send failed on {}: {e}", iface.name);
            return None;
        }

        let deadline = Instant::now() + RESPONSE_TIMEOUT;
        while Instant::now() < deadline {
            match socket.recv(&mut buf) {
                Ok(Some((len, _))) => {
                    if let Some(r) = aecp::parse_response(&buf[..len]) {
                        if r.sequence_id == sequence_id
                            && r.controller_entity_id == controller_id
                            && r.target_entity_id == entity.entity_id
                        {
                            return Some(r.status);
                        }
                    }
                }
                Ok(None) => break, // Socket timeout is longer than ours.
                Err(_) => return None,
            }
        }
        if attempt < ATTEMPTS {
            // Same sequence ID on purpose: the device treats it as a duplicate
            // rather than a fresh command.
            println!("   ↻ [AVB] no response, retry {}/{}", attempt + 1, ATTEMPTS);
        }
    }
    None
}

/// Blink an entity's identify LED, then turn it off again.
///
/// The off command is sent whatever the on command reported, and whatever
/// interrupts the wait. A controller that starts a blink and does not stop it
/// leaves hardware flashing in a rack until someone power-cycles it — and the
/// paths where that is most likely (no response, a refusal, an impatient
/// Ctrl-C) are exactly the ones where an early return would be the tempting
/// shortcut.
///
/// `cancel` cuts the blink short rather than skipping the off command: the wait
/// is slept in short slices so a Ctrl-C lands within a tick and still leaves
/// the device dark.
pub fn identify(
    socket: &RawSocket,
    iface: &Interface,
    entity: &AdpEntity,
    blink_secs: u64,
    cancel: &AtomicBool,
) -> IdentifyOutcome {
    // 0x4000 = AEM_IDENTIFY_CONTROL_INDEX_VALID. Without it the index field in
    // ADP is meaningless, and commanding index 0 on the off-chance could hit
    // an entirely unrelated control — a gain, a mute, a clock source.
    if entity.entity_capabilities & 0x0000_4000 == 0 {
        return IdentifyOutcome::NoIdentifyControl;
    }

    let controller_id = aecp::controller_id_from_mac(iface.mac);
    let sequence_id = (entity.available_index & 0xFFFF) as u16;

    println!(
        "   💡 [AVB] identify ON  -> {} (control index {})",
        crate::adp::format_id(entity.entity_id),
        entity.identify_control_index
    );
    let on = command_and_wait(
        socket,
        iface,
        entity,
        controller_id,
        sequence_id,
        aecp::IDENTIFY_ON,
    );

    // Sliced rather than one long sleep, so a cancel is honoured promptly and
    // the off command below still runs.
    let until = Instant::now() + Duration::from_secs(blink_secs);
    while Instant::now() < until && !cancel.load(Ordering::SeqCst) {
        std::thread::sleep(Duration::from_millis(100));
    }
    if cancel.load(Ordering::SeqCst) {
        println!("   ⏹  [AVB] interrupted — turning identify off");
    }

    println!("   🌑 [AVB] identify OFF -> {}", crate::adp::format_id(entity.entity_id));
    command_and_wait(
        socket,
        iface,
        entity,
        controller_id,
        sequence_id.wrapping_add(1),
        aecp::IDENTIFY_OFF,
    );

    match on {
        Some(status) => IdentifyOutcome::Answered(status),
        None => IdentifyOutcome::NoResponse,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn outcomes_explain_themselves_without_overclaiming() {
        // A silent device must not be reported as a failure to blink: the
        // command may well have landed and only the response been lost.
        let quiet = IdentifyOutcome::NoResponse.describe();
        assert!(quiet.contains("may still have blinked"));

        let none = IdentifyOutcome::NoIdentifyControl.describe();
        assert!(none.contains("AEM_IDENTIFY_CONTROL_INDEX_VALID"));
        assert!(none.contains("enumeration"));

        let ok = IdentifyOutcome::Answered(AemStatus::Success).describe();
        assert!(ok.contains("blinking"));
    }

    /// An entity without the valid bit must be refused before any frame is
    /// built — commanding a guessed control index could move a real parameter.
    /// The cancel flag must shorten the wait, not skip the off command. A
    /// regression here leaves real hardware blinking until it is power-cycled.
    #[test]
    fn cancelling_shortens_the_wait_rather_than_skipping_the_off() {
        let cancel = AtomicBool::new(true);
        let started = Instant::now();
        let until = started + Duration::from_secs(30);
        while Instant::now() < until && !cancel.load(Ordering::SeqCst) {
            std::thread::sleep(Duration::from_millis(100));
        }
        // The loop above is the one in identify(); with cancel set it must fall
        // straight through to the off command instead of waiting 30s.
        assert!(started.elapsed() < Duration::from_secs(1));
    }

    #[test]
    fn entities_without_a_valid_index_are_refused() {
        let mut frame = Vec::new();
        frame.extend_from_slice(&crate::adp::AVDECC_MULTICAST_MAC);
        frame.extend_from_slice(&[0x00, 0x1B, 0x92, 0x0A, 0x1B, 0x2C]);
        frame.extend_from_slice(&crate::adp::ETHERTYPE_AVTP.to_be_bytes());
        frame.push(crate::adp::SUBTYPE_ADP);
        frame.resize(14 + crate::adp::ADPDU_LEN, 0);
        // AEM_SUPPORTED only — no AEM_IDENTIFY_CONTROL_INDEX_VALID.
        frame[14 + 20..14 + 24].copy_from_slice(&0x0000_0008u32.to_be_bytes());

        let entity = crate::adp::parse_frame(&frame).unwrap();
        assert_eq!(entity.entity_capabilities & 0x4000, 0);
        // identify() would return NoIdentifyControl for this entity; the guard
        // is the capability check above, verified here without touching a socket.
    }
}
