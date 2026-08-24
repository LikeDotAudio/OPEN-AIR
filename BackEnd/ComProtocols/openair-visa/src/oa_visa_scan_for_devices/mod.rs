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
/// Priority rule:
/// 1. New candidate resources / gateway scrapes are probed & processed FIRST.
/// 2. Active connected resources are re-checked LAST to preserve session integrity.
pub fn list_resources() -> Vec<String> {
    list_resources_prioritized(&[])
}

/// Enumerate VISA resources, prioritizing new/unconnected devices first and placing
/// active connected resources at the end of the probe queue.
pub fn list_resources_prioritized(active_resources: &[String]) -> Vec<String> {
    let mut resources = Vec::new();

    // 1. USB/Local Enumerator
    resources.extend(oa_visa_usb_enumerator::discover_local_devices());

    // 2. mDNS / ZeroConf (AES70 & LXI)
    resources.extend(oa_visa_mdns_zeroconf::discover_mdns_devices());

    // 3. Static IP / Subnet Prober & Web Gateway Scraper (Scrapes port 80 / HTML gateway pages)
    resources.extend(oa_visa_scanner::hunt_for_devices());

    // Deduplicate while maintaining first-sighting order
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

    // Sort order:
    // Primary: New/unconnected candidates first (0), active connected devices LAST (1)
    // Secondary: Prefer VXI-11 (`::INSTR`, 0) over raw sockets (`::SOCKET`, 1)
    let active_set: std::collections::HashSet<&String> = active_resources.iter().collect();
    resources.sort_by_key(|r| {
        let is_active = active_set.contains(r);
        let is_instr = r.ends_with("::INSTR");
        (is_active, if is_instr { 0 } else { 1 })
    });

    resources
}

