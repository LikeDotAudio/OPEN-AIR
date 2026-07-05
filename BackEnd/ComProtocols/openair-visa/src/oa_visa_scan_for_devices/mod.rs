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

// Inline comment: Logic for list_resources
pub fn list_resources() -> Vec<String> {
    let mut resources = Vec::new();
    
    // 1. USB/Local Enumerator
    resources.extend(oa_visa_usb_enumerator::discover_local_devices());
    
    // 2. mDNS / ZeroConf (AES70 & LXI)
    resources.extend(oa_visa_mdns_zeroconf::discover_mdns_devices());

    // 3. Static IP / Subnet Prober & Gateway Scraper
    resources.extend(oa_visa_scanner::hunt_for_devices());

    resources
}
