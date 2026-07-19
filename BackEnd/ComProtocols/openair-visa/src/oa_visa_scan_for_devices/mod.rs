/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use crate::oa_visa_mdns_zeroconf;
use crate::oa_visa_usb_enumerator;
use crate::oa_visa_scanner;

/// Enumerate every VISA resource this machine can reach, from all sources.
///
/// The three sources overlap by design — an instrument that answers mDNS is very
/// often also visible to the subnet prober — so the combined list is
/// **de-duplicated** before it is returned. Without this the same resource
/// string is probed once per source: a Rigol scope appeared twice in the scan and
/// twice again in the Discovered table, identical rows differing only by the
/// second they were probed.
///
/// Order is preserved and the first sighting wins, so the cheaper, more specific
/// sources (USB, then mDNS) take precedence over the brute-force subnet sweep.
pub fn list_resources() -> Vec<String> {
    let mut resources = Vec::new();

    // 1. USB/Local Enumerator
    resources.extend(oa_visa_usb_enumerator::discover_local_devices());

    // 2. mDNS / ZeroConf (AES70 & LXI)
    resources.extend(oa_visa_mdns_zeroconf::discover_mdns_devices());

    // 3. Static IP / Subnet Prober & Gateway Scraper
    resources.extend(oa_visa_scanner::hunt_for_devices());

    // Prefer VXI-11 (`::INSTR`) over a raw socket when the same host offers both.
    //
    // This has to be an explicit sort, not a happy accident of source order: the
    // subnet scanner pushes its SOCKET resource BEFORE its INSTR one, so
    // first-wins alone would keep the raw socket. VXI-11 is the standard VISA
    // transport — it carries proper device semantics (timeouts, SRQ, clear),
    // where a raw socket is a bare TCP pipe.
    //
    // Stable sort: only the INSTR/SOCKET axis moves, so the source ordering
    // (USB -> mDNS -> subnet sweep) is preserved within each class.
    resources.sort_by_key(|r| if r.ends_with("::INSTR") { 0 } else { 1 });

    let before = resources.len();
    let mut seen = std::collections::HashSet::new();
    resources.retain(|r| seen.insert(r.clone()));
    if before != resources.len() {
        println!(
            "   🧹 [VISA] {} duplicate resource(s) removed ({} sources overlap)",
            before - resources.len(),
            3
        );
    }

    resources
}
