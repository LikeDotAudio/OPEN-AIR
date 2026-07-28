//! `mac-lookup` — resolve hardware addresses to manufacturers from the shell.
//!
//! The agents use the non-blocking path; this one waits, because a person typing
//! a command wants the answer rather than a `None` and an invitation to ask
//! again. Same cache file, so anything looked up here is free for the agents
//! afterwards, and vice versa.
//!
//!     mac-lookup 00:0A:92:FF:FE:01:56:A3      # one address
//!     mac-lookup --cached                     # everything already known
//!     ptp-monitor … | mac-lookup              # or pipe addresses in

use openair_maclookup::MacVendors;
use std::io::BufRead;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let vendors = MacVendors::start();

    if args.iter().any(|a| a == "--help" || a == "-h") {
        eprintln!("usage: mac-lookup [--cached] [MAC ...]");
        eprintln!("       reads addresses from stdin when given none");
        return;
    }

    if args.iter().any(|a| a == "--cached") {
        let known = vendors.known();
        if known.is_empty() {
            println!("(nothing cached yet — look something up first)");
        }
        for (oui, name) in known {
            println!("{oui}\t{name}");
        }
        return;
    }

    if args.is_empty() {
        let stdin = std::io::stdin();
        for line in stdin.lock().lines().map_while(Result::ok) {
            report(&vendors, line.trim());
        }
    } else {
        for arg in &args {
            report(&vendors, arg);
        }
    }
}

fn report(vendors: &MacVendors, mac: &str) {
    if mac.is_empty() {
        return;
    }
    match vendors.blocking_vendor(mac) {
        Some(name) => println!("{name} / {mac}"),
        // Three different situations, and the distinction is worth a word:
        // the address cannot have a vendor, IEEE assigned the block to nobody,
        // or the request did not get through.
        None => match openair_maclookup::Oui::parse(mac) {
            Some(oui) => println!("? / {mac}   (no vendor for {oui})"),
            None => println!("? / {mac}   (not a vendor-bearing address)"),
        },
    }
}
