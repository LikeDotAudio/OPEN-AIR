//! Conversation tracking — turning a stream of packets into exchanges.
//!
//! A PTP capture read message-by-message is nearly useless: what matters is
//! which messages belong together. Three exchanges carry the whole protocol:
//!
//! ```text
//! Two-step sync        master ──Sync(seq N)──▶ slave
//!                      master ──Follow_Up(seq N, precise t1)──▶ slave
//!
//! Delay request        slave  ──Delay_Req(seq M)──▶ master        (E2E)
//!                      master ──Delay_Resp(seq M, t4)──▶ slave
//!
//! Peer delay           A ──Pdelay_Req(seq K)──▶ B                 (P2P / gPTP)
//!                      B ──Pdelay_Resp(seq K, t2)──▶ A
//!                      B ──Pdelay_Resp_Follow_Up(seq K, t3)──▶ A
//! ```
//!
//! Messages are correlated by `sequenceId` **scoped to the sender's port
//! identity and domain**. Sequence IDs are per-port counters, so two clocks
//! will happily both be on sequence 4521 at the same moment; a global map keyed
//! on the sequence alone would pair a Follow_Up from one grandmaster with a
//! Sync from another and report a plausible, entirely fictional delta.
//!
//! Responses are keyed by the *requester's* identity rather than the sender's,
//! because that is what makes a Delay_Resp find the Delay_Req it answers.

use crate::message::{MessageType, PtpMessage, Variant};
use std::collections::HashMap;
use std::time::{Duration, Instant};

/// Identifies one PTP port: who is talking, in which domain, on which variant.
///
/// The variant is part of the key because a device running v2 and gPTP on the
/// same NIC is *two* logical clocks that may not even agree, and merging them
/// would hide exactly the disagreement worth seeing.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct PortKey {
    pub clock_identity: [u8; 8],
    pub port_number: u16,
    pub domain: u8,
    pub variant: Variant,
}

impl PortKey {
    pub fn of(msg: &PtpMessage) -> Self {
        Self {
            clock_identity: msg.source_clock_identity,
            port_number: msg.source_port_number,
            domain: msg.domain,
            variant: msg.variant,
        }
    }

    /// The key a response should be filed under: the requester's port.
    fn of_requester(msg: &PtpMessage) -> Option<Self> {
        Some(Self {
            clock_identity: msg.requesting_clock_identity?,
            port_number: msg.requesting_port_number?,
            domain: msg.domain,
            variant: msg.variant,
        })
    }

    pub fn label(&self) -> String {
        format!(
            "{}/{}",
            crate::message::format_clock_id(&self.clock_identity),
            self.port_number
        )
    }
}

/// A message that completed an exchange started by an earlier one.
#[derive(Debug, Clone, PartialEq)]
pub struct Correlation {
    /// What the earlier message was.
    pub responds_to: MessageType,
    /// The shared sequence ID.
    pub sequence_id: u16,
    /// Wall-clock gap between the two, as observed at *this* capture point.
    ///
    /// Not a protocol measurement: it is arrival-to-arrival on our NIC,
    /// inflated by our own scheduling. Useful for spotting a Follow_Up that
    /// took 40ms; useless for computing offset. The protocol's own numbers
    /// live in the timestamp fields.
    pub observed_gap: Duration,
}

/// A pending message awaiting its partner.
struct Pending {
    seen_at: Instant,
    message_type: MessageType,
}

/// Tracks in-flight exchanges and reports completions.
pub struct FlowTracker {
    pending: HashMap<(PortKey, MessageType, u16), Pending>,
    /// Anything unanswered for longer than this is abandoned. Sequence IDs are
    /// 16-bit and wrap; without expiry a lost Follow_Up would leave an entry
    /// that a wrapped sequence 65536 messages later would falsely complete.
    timeout: Duration,
}

impl Default for FlowTracker {
    fn default() -> Self {
        Self::new(Duration::from_secs(10))
    }
}

impl FlowTracker {
    pub fn new(timeout: Duration) -> Self {
        Self { pending: HashMap::new(), timeout }
    }

    /// Feed one message. Returns the exchange it completed, if any.
    pub fn observe(&mut self, msg: &PtpMessage, now: Instant) -> Option<Correlation> {
        self.expire(now);

        match msg.message_type {
            // Openers: recorded, awaiting their partner.
            MessageType::Sync => {
                // A one-step Sync carries its own timestamp and no Follow_Up
                // will ever come. Recording it would leave an entry that only
                // ever expires — and would imply to a reader that something is
                // missing when nothing is.
                if msg.is_two_step() {
                    self.remember(msg, now);
                }
                None
            }
            MessageType::DelayReq | MessageType::PdelayReq => {
                self.remember(msg, now);
                None
            }

            // Follow_Up answers this same port's own Sync.
            MessageType::FollowUp => {
                self.complete(PortKey::of(msg), MessageType::Sync, msg.sequence_id, now)
            }

            // Responses are filed under the requester's port, not the sender's.
            MessageType::DelayResp => {
                let key = PortKey::of_requester(msg)?;
                self.complete(key, MessageType::DelayReq, msg.sequence_id, now)
            }
            MessageType::PdelayResp => {
                let key = PortKey::of_requester(msg)?;
                let done =
                    self.complete(key, MessageType::PdelayReq, msg.sequence_id, now);
                // The responder may still send a Pdelay_Resp_Follow_Up; record
                // this response so that third leg can be matched too.
                if msg.is_two_step() {
                    self.remember_as(PortKey::of(msg), MessageType::PdelayResp, msg.sequence_id, now);
                }
                done
            }
            MessageType::PdelayRespFollowUp => {
                self.complete(PortKey::of(msg), MessageType::PdelayResp, msg.sequence_id, now)
            }

            _ => None,
        }
    }

    fn remember(&mut self, msg: &PtpMessage, now: Instant) {
        self.remember_as(PortKey::of(msg), msg.message_type, msg.sequence_id, now);
    }

    fn remember_as(&mut self, key: PortKey, mt: MessageType, seq: u16, now: Instant) {
        self.pending.insert((key, mt, seq), Pending { seen_at: now, message_type: mt });
    }

    fn complete(
        &mut self,
        key: PortKey,
        opener: MessageType,
        seq: u16,
        now: Instant,
    ) -> Option<Correlation> {
        let pending = self.pending.remove(&(key, opener, seq))?;
        Some(Correlation {
            responds_to: pending.message_type,
            sequence_id: seq,
            observed_gap: now.saturating_duration_since(pending.seen_at),
        })
    }

    fn expire(&mut self, now: Instant) {
        let timeout = self.timeout;
        self.pending.retain(|_, p| now.saturating_duration_since(p.seen_at) < timeout);
    }

    /// How many exchanges are currently unanswered.
    pub fn pending_count(&self) -> usize {
        self.pending.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::message::{parse, Variant};

    const GM: [u8; 8] = [0x00, 0x0A, 0x92, 0xFF, 0xFE, 0x01, 0x56, 0xA3];
    const OTHER: [u8; 8] = [0xAA, 0xBB, 0xCC, 0xFF, 0xFE, 0x00, 0x00, 0x01];

    fn msg(mt: u8, seq: u16, clock: [u8; 8], two_step: bool, domain: u8) -> PtpMessage {
        let mut p = vec![0u8; 34];
        p[0] = (1 << 4) | mt;
        p[1] = 0x02;
        p[4] = domain;
        p[6] = if two_step { 0x02 } else { 0x00 };
        p[20..28].copy_from_slice(&clock);
        p[28..30].copy_from_slice(&1u16.to_be_bytes());
        p[30..32].copy_from_slice(&seq.to_be_bytes());
        match mt {
            0x9 | 0x3 | 0xA => {
                let mut body = vec![0u8; 20];
                body[10..18].copy_from_slice(&OTHER);
                body[18..20].copy_from_slice(&1u16.to_be_bytes());
                p.extend_from_slice(&body);
            }
            0xB => p.extend_from_slice(&[0u8; 30]),
            _ => p.extend_from_slice(&[0u8; 10]),
        }
        parse(&p, Variant::V2Ethernet).unwrap()
    }

    #[test]
    fn sync_is_matched_by_its_follow_up() {
        let mut t = FlowTracker::default();
        let now = Instant::now();
        assert!(t.observe(&msg(0x0, 4521, GM, true, 0), now).is_none());

        let later = now + Duration::from_millis(3);
        let c = t.observe(&msg(0x8, 4521, GM, true, 0), later).expect("correlated");
        assert_eq!(c.responds_to, MessageType::Sync);
        assert_eq!(c.sequence_id, 4521);
        assert_eq!(c.observed_gap, Duration::from_millis(3));
        assert_eq!(t.pending_count(), 0);
    }

    /// The bug this design exists to prevent: two grandmasters both on
    /// sequence 4521. A tracker keyed on the sequence alone would pair the
    /// wrong Sync with the wrong Follow_Up and report a fictional delta.
    #[test]
    fn identical_sequence_ids_from_different_clocks_do_not_cross_match() {
        let mut t = FlowTracker::default();
        let now = Instant::now();
        t.observe(&msg(0x0, 4521, GM, true, 0), now);
        t.observe(&msg(0x0, 4521, OTHER, true, 0), now);
        assert_eq!(t.pending_count(), 2);

        // GM's Follow_Up must complete GM's Sync and leave OTHER's alone.
        let c = t.observe(&msg(0x8, 4521, GM, true, 0), now).unwrap();
        assert_eq!(c.sequence_id, 4521);
        assert_eq!(t.pending_count(), 1, "the other clock's Sync must survive");
    }

    /// The same clock in two domains is two independent conversations.
    #[test]
    fn domains_do_not_cross_match() {
        let mut t = FlowTracker::default();
        let now = Instant::now();
        t.observe(&msg(0x0, 7, GM, true, 0), now);
        t.observe(&msg(0x0, 7, GM, true, 127), now);
        t.observe(&msg(0x8, 7, GM, true, 0), now);
        assert_eq!(t.pending_count(), 1, "domain 127's Sync must survive");
    }

    /// A one-step Sync has no Follow_Up coming. Recording it would leave an
    /// entry that only ever expires, implying something went missing.
    #[test]
    fn one_step_sync_is_not_left_pending() {
        let mut t = FlowTracker::default();
        assert!(t.observe(&msg(0x0, 1, GM, false, 0), Instant::now()).is_none());
        assert_eq!(t.pending_count(), 0);
    }

    /// Delay_Resp is filed under the requester, so it finds the Delay_Req it
    /// answers rather than a message from the responder.
    #[test]
    fn delay_resp_matches_the_requesters_delay_req() {
        let mut t = FlowTracker::default();
        let now = Instant::now();
        // OTHER asks, GM answers.
        t.observe(&msg(0x1, 55, OTHER, false, 0), now);
        let c = t.observe(&msg(0x9, 55, GM, false, 0), now).expect("correlated");
        assert_eq!(c.responds_to, MessageType::DelayReq);
    }

    /// The gPTP three-legged peer-delay exchange, end to end.
    #[test]
    fn peer_delay_chain_correlates_both_legs() {
        let mut t = FlowTracker::default();
        let now = Instant::now();

        t.observe(&msg(0x2, 12, OTHER, false, 0), now); // Pdelay_Req from OTHER
        let resp = t.observe(&msg(0x3, 12, GM, true, 0), now).expect("resp matches req");
        assert_eq!(resp.responds_to, MessageType::PdelayReq);

        // ...and the third leg matches the response.
        let fu = t.observe(&msg(0xA, 12, GM, true, 0), now).expect("follow-up matches resp");
        assert_eq!(fu.responds_to, MessageType::PdelayResp);
        assert_eq!(t.pending_count(), 0);
    }

    /// Sequence IDs are 16-bit and wrap. Without expiry, a Sync whose Follow_Up
    /// was lost would linger and be falsely completed 65536 messages later.
    #[test]
    fn unanswered_exchanges_expire() {
        let mut t = FlowTracker::new(Duration::from_secs(10));
        let now = Instant::now();
        t.observe(&msg(0x0, 1, GM, true, 0), now);
        assert_eq!(t.pending_count(), 1);

        // A later message drives the expiry sweep.
        t.observe(&msg(0x0, 2, GM, true, 0), now + Duration::from_secs(11));
        assert_eq!(t.pending_count(), 1, "only the fresh Sync remains");

        // The stale one must no longer be completable.
        assert!(t.observe(&msg(0x8, 1, GM, true, 0), now + Duration::from_secs(11)).is_none());
    }

    /// An unsolicited Follow_Up (capture started mid-stream) is not an error
    /// and must not fabricate a correlation.
    #[test]
    fn orphan_follow_up_correlates_to_nothing() {
        let mut t = FlowTracker::default();
        assert!(t.observe(&msg(0x8, 99, GM, true, 0), Instant::now()).is_none());
    }
}
