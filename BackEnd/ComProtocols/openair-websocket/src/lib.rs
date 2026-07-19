//! `openair-websocket` — generic WebSocket device control.
//!
//! # ⚠️ STUB — not implemented
//!
//! This crate is **declared intent, not working code**. No client implemented. Note the browser's MQTT-over-WebSocket transport is unrelated and does not use this crate.
//!
//! It is deliberately left unimplemented rather than half-built, and it is
//! deliberately *not* listed among the working protocols in the project README.
//! The agent that would run it reports `status = stub` on the bus, so the system
//! does not claim health it does not have.
//!
//! The `cargo new` template `add()` that used to live here has been removed: a
//! function asserting 2 + 2 as a crate's public entry point reads as "someone
//! started this," which is a stronger claim than the truth.
//!
//! **Before implementing:** confirm the protocol is still in scope. Several of
//! these were scaffolded ahead of demand.

/// Marker describing this crate's implementation state.
///
/// Exists so the stub status is greppable and testable from code rather than
/// living only in prose.
pub const STATUS: &str = "stub";

#[cfg(test)]
mod tests {
    #[test]
    fn crate_is_declared_a_stub() {
        // Guards against this crate quietly appearing implemented. If you
        // implement it, change STATUS and update the README's protocol list in
        // the same commit.
        assert_eq!(super::STATUS, "stub");
    }
}
