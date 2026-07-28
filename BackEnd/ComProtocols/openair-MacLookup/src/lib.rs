//! `openair-maclookup` — who made this device, from the first 24 bits of its MAC.
//!
//! Every discovery agent here ends up holding a hardware address and nothing
//! else to show for it. A PTP tab listing `00:07:F5:FF:FE:00:54:72` four times
//! is technically complete and practically useless; the same table saying
//! *Bosch Security Systems* against each one is the same data made readable.
//!
//! The first three bytes of a MAC are the OUI — the block IEEE assigned to a
//! manufacturer — so one lookup per OUI names every device that shares it.
//!
//! # The budget is the design
//!
//! <https://api.macvendors.com> needs no key and allows **1000 requests a day at
//! 1 per second**. Both limits shape this crate:
//!
//! * **Cache by OUI, not by MAC.** A bench of 40 devices is perhaps 8 vendors.
//! * **Cache misses too.** A 404 means IEEE never assigned that block. Asking
//!   again tomorrow will not change that, and each retry costs a request.
//! * **Persist across restarts**, or a restart loop spends the day's budget by
//!   lunchtime re-learning what it already knew.
//! * **Never ask about an address that cannot have a vendor** — multicast,
//!   locally-administered and all-zero addresses are free to reject locally.
//! * **Never block the caller.** [`MacVendors::vendor`] answers from cache or
//!   returns `None` and queues the OUI; one worker thread drains that queue at
//!   the permitted rate. Discovery agents call this from packet-handling paths
//!   where a one-second sleep drops frames.
//!
//! So a name appears a flush or two after a device does, and from then on it is
//! free and offline.
//!
//! ```no_run
//! let vendors = openair_maclookup::MacVendors::start();
//! // First call for an unseen OUI: None, and the OUI is queued.
//! let _ = vendors.vendor("00:0A:92:FF:FE:01:56:A3");
//! // A moment later the worker has answered, and it stays answered.
//! ```

use std::collections::{HashMap, HashSet, VecDeque};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Condvar, Mutex};
use std::time::Duration;

/// One IEEE-assigned block: the first three bytes of a hardware address.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub struct Oui([u8; 3]);

impl std::fmt::Display for Oui {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:02X}:{:02X}:{:02X}", self.0[0], self.0[1], self.0[2])
    }
}

impl Oui {
    /// The OUI of any hardware address the bench actually produces.
    ///
    /// Accepts everything the API accepts — `00-11-22-33-44-55`, `00:11:22:…`,
    /// `0011.2233.4455`, `001122334455` — by the simple expedient of keeping the
    /// hex digits and discarding everything else.
    ///
    /// It also accepts the **EUI-64** form, which matters more here than the
    /// tidy MAC-48 case: a PTP clock identity and an AVDECC entity ID are both a
    /// MAC with `FF:FE` inserted in the middle, so `00:0A:92:FF:FE:01:56:A3` is
    /// the same PreSonus-or-whoever block as `00:0A:92:01:56:A3`. Since the OUI
    /// is the leading three bytes either way, the insertion needs no special
    /// case — only the length check has to allow 16 hex digits as well as 12.
    ///
    /// Returns `None` for anything that cannot have a manufacturer:
    ///
    /// * **multicast** (low bit of the first byte) — `01:00:5E:…`, `91:E0:F0:…`
    ///   and every other group address. AVDECC's own discovery address is one of
    ///   these, so an agent that forwarded raw frame destinations here would
    ///   otherwise burn the daily budget on `91:E0:F0`.
    /// * **locally administered** (second bit) — a MAC someone assigned by hand
    ///   or a hypervisor invented. IEEE assigned it to nobody by definition.
    /// * **all zero** — the "no address" placeholder several of these protocols
    ///   emit before they know their own identity.
    pub fn parse(raw: &str) -> Option<Self> {
        let hex: Vec<u8> = raw
            .chars()
            .filter(|c| c.is_ascii_hexdigit())
            .map(|c| c.to_digit(16).unwrap_or(0) as u8)
            .collect();

        // 12 nibbles is a MAC-48, 16 an EUI-64. Anything else is not an address
        // that got mangled — it is a different kind of string, and guessing at
        // it would put junk in the cache and spend requests on it.
        if hex.len() != 12 && hex.len() != 16 {
            return None;
        }

        let byte = |i: usize| (hex[i * 2] << 4) | hex[i * 2 + 1];
        let oui = [byte(0), byte(1), byte(2)];

        if oui[0] & 0x01 != 0 {
            return None; // multicast / group address
        }
        if oui[0] & 0x02 != 0 {
            return None; // locally administered
        }
        if oui == [0, 0, 0] {
            return None;
        }
        Some(Oui(oui))
    }

    /// `00:0A:92` — the form the API takes and the cache file stores.
    pub fn as_query(&self) -> String {
        self.to_string()
    }

    /// The OUI hiding inside an IPv6 address, if the host built it from its MAC.
    ///
    /// This is how a vendor name reaches the tables that have no MAC column at
    /// all. DNS-SD publishes no hardware address — but it publishes link-local
    /// addresses, and a **SLAAC** address derives its low 64 bits from the MAC
    /// by the *modified* EUI-64 rule: insert `FF:FE` in the middle, and **flip
    /// the universal/local bit**.
    ///
    /// ```text
    /// fe80::46fa:66ff:fee4:2fbf   ->  44:FA:66:E4:2F:BF
    /// ```
    ///
    /// That flip is why this cannot go through [`Oui::parse`]. Inverting bit 1
    /// makes a globally-assigned MAC look locally-administered, so the address
    /// above presents as `46:FA:66` — which `parse` rejects on sight, correctly,
    /// because in a plain MAC that bit means "IEEE assigned this to nobody".
    /// Undoing the flip first turns it back into Brother's real block.
    ///
    /// Returns `None` for a **privacy address** (RFC 4941), where the interface
    /// ID is random and has no `FF:FE` marker. Apple devices use these, so their
    /// rows legitimately have no vendor to show — and inventing one from random
    /// bytes would be worse than a blank cell.
    pub fn from_ipv6(addr: &str) -> Option<Self> {
        // Trim the zone index a link-local address carries: `%enp5s0f0`.
        let addr = addr.split('%').next()?.trim();
        let bytes = expand_ipv6(addr)?;

        // Only the interface ID matters, and only if it was built from a MAC.
        let iid = &bytes[8..];
        if iid[3] != 0xFF || iid[4] != 0xFE {
            return None; // privacy address, or a hand-assigned one
        }

        let first = iid[0] ^ 0x02; // undo the modified-EUI-64 flip
        let oui = [first, iid[1], iid[2]];
        if oui[0] & 0x01 != 0 || oui[0] & 0x02 != 0 || oui == [0, 0, 0] {
            return None;
        }
        Some(Oui(oui))
    }
}

/// A full 48-bit hardware address.
///
/// The OUI is what gets looked up, but the address itself is worth publishing
/// on its own: on the mDNS tabs there is no MAC column at all, and "this row is
/// `44:FA:66:E4:2F:BF`" is a fact you cannot otherwise get out of DNS-SD without
/// running `ip neigh` by hand.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub struct Mac([u8; 6]);

impl std::fmt::Display for Mac {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let hex: Vec<String> = self.0.iter().map(|b| format!("{b:02X}")).collect();
        write!(f, "{}", hex.join(":"))
    }
}

impl Mac {
    /// The MAC a SLAAC IPv6 address was built from. See [`Oui::from_ipv6`] for
    /// why the universal/local bit has to be flipped back.
    pub fn from_ipv6(addr: &str) -> Option<Self> {
        let addr = addr.split('%').next()?.trim();
        let bytes = expand_ipv6(addr)?;
        let iid = &bytes[8..];
        if iid[3] != 0xFF || iid[4] != 0xFE {
            return None;
        }
        let mac = [iid[0] ^ 0x02, iid[1], iid[2], iid[5], iid[6], iid[7]];
        if mac[0] & 0x01 != 0 || mac[0] & 0x02 != 0 || mac[..3] == [0, 0, 0] {
            return None;
        }
        Some(Mac(mac))
    }

    /// Any of the written forms, MAC-48 only — an EUI-64 is not an address.
    pub fn parse(raw: &str) -> Option<Self> {
        let hex: Vec<u8> = raw
            .chars()
            .filter(|c| c.is_ascii_hexdigit())
            .map(|c| c.to_digit(16).unwrap_or(0) as u8)
            .collect();
        if hex.len() != 12 {
            return None;
        }
        let mut mac = [0u8; 6];
        for (i, b) in mac.iter_mut().enumerate() {
            *b = (hex[i * 2] << 4) | hex[i * 2 + 1];
        }
        if mac[0] & 0x01 != 0 || mac[0] & 0x02 != 0 || mac[..3] == [0, 0, 0] {
            return None;
        }
        Some(Mac(mac))
    }

    /// The block this address belongs to.
    pub fn oui(&self) -> Oui {
        Oui([self.0[0], self.0[1], self.0[2]])
    }
}

/// An IPv6 address as 16 bytes, `::` and all.
///
/// Hand-rolled because `Ipv6Addr::from_str` would do it — but only after the
/// zone index is gone, and it rejects the whole address rather than the suffix,
/// which is a worse error to debug than this is to write.
fn expand_ipv6(addr: &str) -> Option<[u8; 16]> {
    let (head, tail) = match addr.split_once("::") {
        Some((h, t)) => (h, Some(t)),
        None => (addr, None),
    };
    let parse_groups = |s: &str| -> Option<Vec<u16>> {
        if s.is_empty() {
            return Some(Vec::new());
        }
        s.split(':').map(|g| u16::from_str_radix(g, 16).ok()).collect()
    };

    let head = parse_groups(head)?;
    let tail = match tail {
        Some(t) => parse_groups(t)?,
        None => Vec::new(),
    };
    if head.len() + tail.len() > 8 {
        return None;
    }
    // Without `::` the address must be complete; with it, the gap is zeros.
    if addr.find("::").is_none() && head.len() != 8 {
        return None;
    }

    let mut groups = [0u16; 8];
    groups[..head.len()].copy_from_slice(&head);
    let start = 8 - tail.len();
    groups[start..].copy_from_slice(&tail);

    let mut out = [0u8; 16];
    for (i, g) in groups.iter().enumerate() {
        out[i * 2] = (g >> 8) as u8;
        out[i * 2 + 1] = (g & 0xFF) as u8;
    }
    Some(out)
}

/// What is known about one OUI.
#[derive(Clone, PartialEq, Eq, Debug)]
enum Known {
    /// The API named it.
    Vendor(String),
    /// The API returned 404 — IEEE assigned this block to nobody. Remembered so
    /// it is never asked again.
    Unassigned,
}

struct Shared {
    known: HashMap<Oui, Known>,
    /// OUIs seen but not yet asked about, oldest first.
    queue: VecDeque<Oui>,
    /// In the queue or in flight — so a device seen on every packet does not
    /// enqueue itself a thousand times before the first answer lands.
    pending: HashSet<Oui>,
    /// Requests spent today, and the day they were spent on.
    spent: u32,
    day: u64,
    /// When the last request left, so the rate gate is shared. The worker and a
    /// CLI call go through the same door — a tool run while an agent is
    /// resolving must not double the rate and earn both of them a 429.
    last_request: Option<std::time::Instant>,
    dirty: bool,
    stop: bool,
}

/// A lookup table with a worker thread behind it.
///
/// Cloneable and shareable: every clone talks to the same cache and the same
/// worker. Dropping the last one stops the thread.
#[derive(Clone)]
pub struct MacVendors {
    shared: Arc<(Mutex<Shared>, Condvar)>,
    path: Option<PathBuf>,
}

/// The published ceiling for a keyless caller.
const DAILY_BUDGET: u32 = 1000;

/// One request per second, plus a little — the limit is a rate, and being
/// exactly at it invites the 429 that costs more than the wait.
const REQUEST_SPACING: Duration = Duration::from_millis(1100);

/// How long to sit out after a 429 before trying again.
///
/// Being told to slow down is not the same as being at the daily ceiling, so it
/// pauses rather than gives up — but a tight retry would just earn another 429.
const THROTTLE_BACKOFF: Duration = Duration::from_secs(60);

impl MacVendors {
    /// Start with the default cache location.
    ///
    /// `OPENAIR_MAC_CACHE` overrides it; otherwise `mac_vendors.tsv` beside the
    /// working directory. Losing the file costs a day's budget, not correctness.
    pub fn start() -> Self {
        let path = std::env::var_os("OPENAIR_MAC_CACHE")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("mac_vendors.tsv"));
        Self::start_with_cache(Some(path))
    }

    /// Start against a specific cache file, or none at all (tests).
    pub fn start_with_cache(path: Option<PathBuf>) -> Self {
        let (known, spent, day) = path
            .as_deref()
            .map(load_cache)
            .unwrap_or_else(|| (HashMap::new(), 0, today()));

        let shared = Arc::new((
            Mutex::new(Shared {
                known,
                queue: VecDeque::new(),
                pending: HashSet::new(),
                spent,
                day,
                last_request: None,
                dirty: false,
                stop: false,
            }),
            Condvar::new(),
        ));

        let me = MacVendors { shared: shared.clone(), path: path.clone() };
        let worker = me.clone();
        std::thread::Builder::new()
            .name("mac-vendor-lookup".into())
            .spawn(move || worker.run())
            .ok();
        me
    }

    /// The manufacturer for a hardware address, if it is already known.
    ///
    /// Never blocks and never fails: an unknown OUI is queued and this returns
    /// `None`, so a caller on a capture thread pays nothing. Ask again next
    /// flush.
    pub fn vendor(&self, mac: &str) -> Option<String> {
        self.vendor_of(Oui::parse(mac)?)
    }

    /// `Vendor / 00:0A:92:FF:FE:01:56:A3`, or the address alone until the name
    /// arrives.
    ///
    /// The label a table cell wants: it is never empty, never shorter than the
    /// address it replaces, and it gains the name in place when the worker
    /// answers.
    pub fn label(&self, mac: &str) -> String {
        match self.vendor(mac) {
            Some(name) => format!("{name} / {mac}"),
            None => mac.to_string(),
        }
    }

    /// The manufacturer behind whatever identifiers a discovery record holds.
    ///
    /// For agents with no MAC column. Give it every address and identifier on
    /// the record — a comma- or space-separated address list is fine — and it
    /// takes the first thing a vendor can be read out of, trying hardware
    /// addresses before IPv6 because a MAC states the OUI where an address only
    /// implies it.
    ///
    /// DNS-SD is the caller this exists for: it publishes no hardware address,
    /// but a SLAAC link-local address carries one, so
    /// `fe80::46fa:66ff:fee4:2fbf` is enough to say *Brother*.
    pub fn vendor_of_any<'a>(&self, candidates: impl IntoIterator<Item = &'a str>) -> Option<String> {
        let mut ipv6: Vec<Oui> = Vec::new();
        let mut queued: Option<String> = None;

        for candidate in candidates {
            for token in candidate.split([',', ' ', '\t', ';']) {
                let token = token.trim();
                if token.is_empty() {
                    continue;
                }
                if let Some(oui) = Oui::parse(token) {
                    if let Some(name) = self.vendor_of(oui) {
                        return Some(name);
                    }
                    queued = queued.or(Some(String::new()));
                } else if let Some(oui) = Oui::from_ipv6(token) {
                    ipv6.push(oui);
                }
            }
        }
        // Only now fall back to what an address implies.
        for oui in ipv6 {
            if let Some(name) = self.vendor_of(oui) {
                return Some(name);
            }
        }
        let _ = queued;
        None
    }

    /// The hardware address hiding in a discovery record, if one is.
    ///
    /// The companion to [`MacVendors::vendor_of_any`], and it takes the same
    /// candidates. Publish both: the vendor is the readable fact, the MAC is the
    /// evidence for it, and a row showing *Google, Inc.* with no address to
    /// check it against is a claim rather than a finding.
    ///
    /// A stated MAC wins over one inferred from an IPv6 address.
    pub fn mac_of_any<'a>(&self, candidates: impl IntoIterator<Item = &'a str>) -> Option<Mac> {
        let mut inferred: Option<Mac> = None;
        for candidate in candidates {
            for token in candidate.split([',', ' ', '\t', ';']) {
                let token = token.trim();
                if token.is_empty() {
                    continue;
                }
                if let Some(mac) = Mac::parse(token) {
                    return Some(mac);
                }
                if inferred.is_none() {
                    inferred = Mac::from_ipv6(token);
                }
            }
        }
        inferred
    }

    /// Cache hit, or queue it and answer `None`. The single place that decides.
    fn vendor_of(&self, oui: Oui) -> Option<String> {
        let (lock, cv) = &*self.shared;
        let mut shared = lock.lock().ok()?;
        match shared.known.get(&oui) {
            Some(Known::Vendor(name)) => return Some(name.clone()),
            Some(Known::Unassigned) => return None,
            None => {}
        }
        if shared.pending.insert(oui) {
            shared.queue.push_back(oui);
            cv.notify_one();
        }
        None
    }

    /// Ask now and wait for the answer — for one-shot tools, never for agents.
    pub fn blocking_vendor(&self, mac: &str) -> Option<String> {
        let oui = Oui::parse(mac)?;
        {
            let (lock, _) = &*self.shared;
            let shared = lock.lock().ok()?;
            match shared.known.get(&oui) {
                Some(Known::Vendor(name)) => return Some(name.clone()),
                Some(Known::Unassigned) => return None,
                None => {}
            }
        }
        if !self.take_slot() {
            return None; // out of allowance for today
        }
        match fetch(oui) {
            Fetched::Vendor(name) => {
                self.remember(oui, Known::Vendor(name.clone()));
                Some(name)
            }
            Fetched::Unassigned => {
                self.remember(oui, Known::Unassigned);
                None
            }
            Fetched::Throttled | Fetched::Failed => None,
        }
    }

    /// Everything learned so far, for a caller that wants to render the table.
    pub fn known(&self) -> Vec<(Oui, String)> {
        let (lock, _) = &*self.shared;
        let shared = match lock.lock() {
            Ok(s) => s,
            Err(_) => return Vec::new(),
        };
        let mut out: Vec<(Oui, String)> = shared
            .known
            .iter()
            .filter_map(|(oui, k)| match k {
                Known::Vendor(name) => Some((*oui, name.clone())),
                Known::Unassigned => None,
            })
            .collect();
        out.sort_by_key(|(oui, _)| oui.0);
        out
    }

    /// Wait for this caller's turn to make a request, and charge it.
    ///
    /// Returns false when today's allowance is gone. Both the worker and
    /// [`MacVendors::blocking_vendor`] come through here, because the limit is
    /// per source address and not per thread — before this existed, running the
    /// CLI five times in a row was five requests in one second and the API said
    /// so.
    ///
    /// Sleeps with the lock RELEASED. Holding a mutex across a one-second sleep
    /// would stall every `vendor()` call on the capture thread, which is the one
    /// thing this crate promises not to do.
    fn take_slot(&self) -> bool {
        loop {
            let wait = {
                let (lock, _) = &*self.shared;
                let Ok(mut shared) = lock.lock() else { return false };

                let now_day = today();
                if now_day != shared.day {
                    shared.day = now_day;
                    shared.spent = 0;
                    shared.dirty = true;
                }
                if shared.spent >= DAILY_BUDGET {
                    return false;
                }

                let wait = shared
                    .last_request
                    .map(|t| REQUEST_SPACING.saturating_sub(t.elapsed()))
                    .unwrap_or_default();
                if wait.is_zero() {
                    shared.last_request = Some(std::time::Instant::now());
                    shared.spent += 1;
                    shared.dirty = true;
                    return true;
                }
                wait
            };
            std::thread::sleep(wait);
        }
    }

    fn remember(&self, oui: Oui, what: Known) {
        let (lock, _) = &*self.shared;
        if let Ok(mut shared) = lock.lock() {
            shared.known.insert(oui, what);
            shared.pending.remove(&oui);
            shared.dirty = true;
        }
        self.persist();
    }

    /// Write the cache out. Cheap enough to do per answer — the file is one
    /// short line per vendor and answers arrive at most once a second.
    fn persist(&self) {
        let Some(path) = self.path.as_deref() else { return };
        let (lock, _) = &*self.shared;
        let Ok(mut shared) = lock.lock() else { return };
        if !shared.dirty {
            return;
        }
        let mut out = String::new();
        out.push_str("# openair-maclookup vendor cache — one OUI per line\n");
        out.push_str(&format!("#budget\t{}\t{}\n", shared.day, shared.spent));
        let mut entries: Vec<(&Oui, &Known)> = shared.known.iter().collect();
        entries.sort_by_key(|(oui, _)| oui.0);
        for (oui, known) in entries {
            let name = match known {
                Known::Vendor(n) => n.as_str(),
                // A tab-delimited empty field, so the negative survives a
                // round trip instead of being re-asked on every restart.
                Known::Unassigned => "",
            };
            out.push_str(&format!("{oui}\t{name}\n"));
        }
        shared.dirty = false;
        drop(shared);

        // Write-then-rename, or a restart during the write leaves a truncated
        // cache that reads as "nothing is known".
        let tmp = path.with_extension("tsv.tmp");
        if let Some(parent) = tmp.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        if let Ok(mut f) = std::fs::File::create(&tmp) {
            if f.write_all(out.as_bytes()).is_ok() && f.sync_all().is_ok() {
                let _ = std::fs::rename(&tmp, path);
            }
        }
    }

    /// The worker: one OUI at a time, no faster than allowed.
    fn run(self) {
        loop {
            let oui = {
                let (lock, cv) = &*self.shared;
                let mut shared = match lock.lock() {
                    Ok(s) => s,
                    Err(_) => return,
                };
                loop {
                    if shared.stop || Arc::strong_count(&self.shared) <= 1 {
                        return;
                    }
                    // A new day restores the allowance.
                    let now = today();
                    if now != shared.day {
                        shared.day = now;
                        shared.spent = 0;
                        shared.dirty = true;
                    }
                    if shared.spent < DAILY_BUDGET {
                        if let Some(oui) = shared.queue.pop_front() {
                            break oui;
                        }
                    }
                    // Over budget, or nothing waiting: idle. Tomorrow's worker
                    // finds the queue already populated.
                    let (guard, _) = match cv.wait_timeout(shared, Duration::from_secs(30)) {
                        Ok(pair) => pair,
                        Err(_) => return,
                    };
                    shared = guard;
                }
            };

            // The gate both charges the budget and enforces the spacing, so
            // there is no sleep at the bottom of this loop.
            if !self.take_slot() {
                self.requeue(oui);
                std::thread::sleep(THROTTLE_BACKOFF);
                continue;
            }
            match fetch(oui) {
                Fetched::Vendor(name) => self.remember(oui, Known::Vendor(name)),
                Fetched::Unassigned => self.remember(oui, Known::Unassigned),
                // Neither of these says anything about the OUI, so neither is
                // cached — requeue and wait rather than remembering a wrong
                // "unknown" that would never be retried.
                Fetched::Throttled | Fetched::Failed => {
                    self.requeue(oui);
                    std::thread::sleep(THROTTLE_BACKOFF);
                }
            }
        }
    }

    fn requeue(&self, oui: Oui) {
        let (lock, _) = &*self.shared;
        if let Ok(mut shared) = lock.lock() {
            shared.queue.push_back(oui);
        }
    }
}

impl Drop for MacVendors {
    fn drop(&mut self) {
        // 2 = this handle and the worker's. Past that, someone still holds one.
        if Arc::strong_count(&self.shared) <= 2 {
            let (lock, cv) = &*self.shared;
            if let Ok(mut shared) = lock.lock() {
                shared.stop = true;
            }
            cv.notify_all();
        }
    }
}

enum Fetched {
    Vendor(String),
    Unassigned,
    Throttled,
    Failed,
}

/// One GET. The API answers with a bare string, or 404, or 429.
fn fetch(oui: Oui) -> Fetched {
    let url = format!("https://api.macvendors.com/{}", oui.as_query());
    match ureq::get(&url)
        .timeout(Duration::from_secs(10))
        .call()
    {
        Ok(response) => match response.into_string() {
            Ok(body) => {
                let name = body.trim().to_string();
                if name.is_empty() {
                    Fetched::Unassigned
                } else {
                    Fetched::Vendor(name)
                }
            }
            Err(_) => Fetched::Failed,
        },
        // 404 is an answer: no such assignment. Anything else in 4xx/5xx is not.
        Err(ureq::Error::Status(404, _)) => Fetched::Unassigned,
        Err(ureq::Error::Status(429, _)) => Fetched::Throttled,
        Err(_) => Fetched::Failed,
    }
}

/// Days since the epoch — the coarsest clock that can tell "is it tomorrow yet".
fn today() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs() / 86_400)
        .unwrap_or(0)
}

fn load_cache(path: &Path) -> (HashMap<Oui, Known>, u32, u64) {
    let mut known = HashMap::new();
    let mut spent = 0;
    let mut day = today();

    let Ok(text) = std::fs::read_to_string(path) else {
        return (known, spent, day);
    };
    for line in text.lines() {
        if let Some(rest) = line.strip_prefix("#budget\t") {
            let mut parts = rest.split('\t');
            let stored_day: u64 = parts.next().and_then(|d| d.parse().ok()).unwrap_or(0);
            let stored_spent: u32 = parts.next().and_then(|s| s.parse().ok()).unwrap_or(0);
            // Yesterday's tally is not today's problem.
            if stored_day == day {
                spent = stored_spent;
            } else {
                day = today();
            }
            continue;
        }
        if line.starts_with('#') || line.trim().is_empty() {
            continue;
        }
        let mut parts = line.splitn(2, '\t');
        let Some(oui) = parts.next().and_then(Oui::parse_exact) else { continue };
        let name = parts.next().unwrap_or("").trim();
        known.insert(
            oui,
            if name.is_empty() { Known::Unassigned } else { Known::Vendor(name.to_string()) },
        );
    }
    (known, spent, day)
}

impl Oui {
    /// Parse the 3-byte form the cache file stores.
    ///
    /// Separate from [`Oui::parse`], which insists on a whole address: a cache
    /// line is 6 hex digits and would fail that length check.
    fn parse_exact(raw: &str) -> Option<Self> {
        let hex: Vec<u8> = raw
            .chars()
            .filter(|c| c.is_ascii_hexdigit())
            .map(|c| c.to_digit(16).unwrap_or(0) as u8)
            .collect();
        if hex.len() != 6 {
            return None;
        }
        let byte = |i: usize| (hex[i * 2] << 4) | hex[i * 2 + 1];
        Some(Oui([byte(0), byte(1), byte(2)]))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_separator_the_api_accepts() {
        let expected = Oui([0x00, 0x11, 0x22]);
        for form in [
            "00-11-22-33-44-55",
            "00:11:22:33:44:55",
            "00.11.22.33.44.55",
            "001122334455",
            "0011.2233.4455",
            "00/11/22/33/44/55",
            "  00:11:22:33:44:55  ",
        ] {
            assert_eq!(Oui::parse(form), Some(expected), "failed on {form}");
        }
    }

    /// The case this crate exists for: a PTP clock identity and an AVDECC
    /// entity ID are the device's MAC with FF:FE wedged into the middle, and
    /// both must resolve to the same vendor as the plain MAC.
    #[test]
    fn eui64_resolves_to_the_same_block_as_the_mac() {
        let clock_id = Oui::parse("00:0A:92:FF:FE:01:56:A3").unwrap();
        let mac = Oui::parse("00:0A:92:01:56:A3").unwrap();
        assert_eq!(clock_id, mac);
        assert_eq!(clock_id.to_string(), "00:0A:92");
    }

    #[test]
    fn lowercase_is_fine_and_output_is_not() {
        assert_eq!(Oui::parse("fc:a1:3e:2a:1c:33").unwrap().to_string(), "FC:A1:3E");
    }

    /// Every rejection here is a request not spent.
    #[test]
    fn addresses_that_cannot_have_a_vendor_are_never_queried() {
        // AVDECC's own discovery destination — the one an L2 agent is most
        // likely to hand over by accident.
        assert_eq!(Oui::parse("91:E0:F0:01:00:00"), None, "multicast");
        assert_eq!(Oui::parse("01:00:5E:00:00:01"), None, "IPv4 multicast");
        assert_eq!(Oui::parse("FF:FF:FF:FF:FF:FF"), None, "broadcast");
        assert_eq!(Oui::parse("02:42:AC:11:00:02"), None, "locally administered");
        assert_eq!(Oui::parse("00:00:00:00:00:00"), None, "the null address");
    }

    #[test]
    fn strings_that_are_not_addresses_are_rejected() {
        for junk in ["", "-", "unknown", "192.168.1.1", "00:11:22", "00:11:22:33:44:55:66"] {
            assert_eq!(Oui::parse(junk), None, "accepted {junk:?}");
        }
    }

    /// The Brother printer is the case that proves the bit flip, because the
    /// same device states its MAC twice by two unrelated routes: the link-local
    /// address and the hostname `BRW44FA66E42FBF.local`. They have to agree.
    #[test]
    fn ipv6_link_local_yields_the_mac_the_hostname_also_states() {
        let from_addr = Oui::from_ipv6("fe80::46fa:66ff:fee4:2fbf%enp5s0f0").unwrap();
        assert_eq!(from_addr.to_string(), "44:FA:66");
        // BRW44FA66E42FBF — the hostname's own copy of the same address.
        assert_eq!(from_addr, Oui::parse("44:FA:66:E4:2F:BF").unwrap());
    }

    #[test]
    fn ipv6_without_the_flip_would_have_been_rejected() {
        // The raw interface ID reads as locally administered, and `parse` is
        // right to refuse it. Only undoing the flip recovers the real block.
        assert_eq!(Oui::parse("46:FA:66:E4:2F:BF"), None);
        assert!(Oui::from_ipv6("fe80::46fa:66ff:fee4:2fbf").is_some());
    }

    #[test]
    fn slaac_addresses_across_the_bench() {
        for (addr, expected) in [
            ("fe80::4ad6:d5ff:fe8d:d6b7%enp5s0f0", "48:D6:D5"),
            ("fe80::f2ef:86ff:fe51:1afb%wlp13s0", "F0:EF:86"),
            ("fe80::22df:b9ff:fe9e:cd4b", "20:DF:B9"),
        ] {
            assert_eq!(Oui::from_ipv6(addr).unwrap().to_string(), expected, "{addr}");
        }
    }

    /// A privacy address is random bytes. Reading a vendor out of it would be
    /// inventing one, which is worse than the blank cell it replaces.
    #[test]
    fn privacy_addresses_yield_nothing() {
        assert_eq!(Oui::from_ipv6("fe80::1029:72a0:3793:8b5b%enp5s0f0"), None);
        assert_eq!(Oui::from_ipv6("44.44.44.155"), None);
        assert_eq!(Oui::from_ipv6("not an address"), None);
    }

    #[test]
    fn expands_every_shape_of_ipv6() {
        assert_eq!(expand_ipv6("::").unwrap(), [0u8; 16]);
        assert_eq!(expand_ipv6("fe80::1").unwrap()[0], 0xFE);
        assert_eq!(*expand_ipv6("fe80::1").unwrap().last().unwrap(), 1);
        assert!(expand_ipv6("fe80:0:0:0:0:0:0").is_none(), "short without ::");
        assert!(expand_ipv6("gg::1").is_none());
    }

    /// The DNS-SD case: an address list, no MAC anywhere, vendor still found.
    #[test]
    fn vendor_of_any_reads_the_address_list() {
        let v = MacVendors::start_with_cache(None);
        v.remember(Oui([0x44, 0xFA, 0x66]), Known::Vendor("Brother".into()));
        let addresses = "44.44.44.165, fe80::46fa:66ff:fee4:2fbf%enp5s0f0";
        assert_eq!(v.vendor_of_any([addresses]).as_deref(), Some("Brother"));
    }

    /// A real MAC on the record outranks an address that merely implies one.
    #[test]
    fn a_hardware_address_wins_over_an_inferred_one() {
        let v = MacVendors::start_with_cache(None);
        v.remember(Oui([0x00, 0x0A, 0x92]), Known::Vendor("Presonus".into()));
        v.remember(Oui([0x44, 0xFA, 0x66]), Known::Vendor("Brother".into()));
        assert_eq!(
            v.vendor_of_any(["fe80::46fa:66ff:fee4:2fbf", "00:0A:92:01:56:A3"])
                .as_deref(),
            Some("Presonus")
        );
    }

    /// The evidence half: the address a DNS-SD row never states, recovered.
    #[test]
    fn full_mac_comes_back_out_of_a_slaac_address() {
        for (addr, expected) in [
            ("fe80::46fa:66ff:fee4:2fbf%enp5s0f0", "44:FA:66:E4:2F:BF"),
            ("fe80::4ad6:d5ff:fe8d:d6b7", "48:D6:D5:8D:D6:B7"),
            ("fe80::f2ef:86ff:fe51:1afb%wlp13s0", "F0:EF:86:51:1A:FB"),
            ("fe80::22df:b9ff:fe9e:cd4b", "20:DF:B9:9E:CD:4B"),
        ] {
            assert_eq!(Mac::from_ipv6(addr).unwrap().to_string(), expected, "{addr}");
        }
        assert_eq!(Mac::from_ipv6("fe80::1029:72a0:3793:8b5b"), None, "privacy");
    }

    #[test]
    fn a_mac_and_its_oui_agree() {
        let mac = Mac::from_ipv6("fe80::46fa:66ff:fee4:2fbf").unwrap();
        assert_eq!(mac.oui(), Oui::from_ipv6("fe80::46fa:66ff:fee4:2fbf").unwrap());
        assert_eq!(mac.oui().to_string(), "44:FA:66");
    }

    #[test]
    fn mac_of_any_prefers_a_stated_address_over_an_inferred_one() {
        let v = MacVendors::start_with_cache(None);
        assert_eq!(
            v.mac_of_any(["fe80::46fa:66ff:fee4:2fbf", "00:0A:92:01:56:A3"])
                .unwrap()
                .to_string(),
            "00:0A:92:01:56:A3"
        );
        assert_eq!(
            v.mac_of_any(["44.44.44.165, fe80::46fa:66ff:fee4:2fbf%enp5s0f0"])
                .unwrap()
                .to_string(),
            "44:FA:66:E4:2F:BF"
        );
        assert_eq!(v.mac_of_any(["44.44.44.160"]), None);
    }

    #[test]
    fn label_falls_back_to_the_address_until_the_name_arrives() {
        let v = MacVendors::start_with_cache(None);
        assert_eq!(v.label("00:0A:92:01:56:A3"), "00:0A:92:01:56:A3");
    }

    /// A row whose address is a dash must not enqueue anything — that is the
    /// placeholder the PTP agent writes for an unknown grandmaster.
    #[test]
    fn placeholder_rows_queue_nothing() {
        let v = MacVendors::start_with_cache(None);
        assert_eq!(v.vendor("-"), None);
        let (lock, _) = &*v.shared;
        assert!(lock.lock().unwrap().queue.is_empty());
    }

    #[test]
    fn a_repeated_address_is_queued_once() {
        let v = MacVendors::start_with_cache(None);
        for _ in 0..50 {
            let _ = v.vendor("00:0A:92:FF:FE:01:56:A3");
        }
        let (lock, _) = &*v.shared;
        let shared = lock.lock().unwrap();
        // The worker may already have taken it; either way it was never twice.
        assert!(shared.queue.len() <= 1, "queued {} times", shared.queue.len());
    }

    #[test]
    fn cache_round_trips_names_and_negatives() {
        let dir = std::env::temp_dir().join(format!("oam-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("mac_vendors.tsv");

        let v = MacVendors::start_with_cache(Some(path.clone()));
        v.remember(Oui([0x00, 0x0A, 0x92]), Known::Vendor("PreSonus".into()));
        v.remember(Oui([0x00, 0x07, 0xF5]), Known::Unassigned);

        let (known, _, _) = load_cache(&path);
        assert_eq!(
            known.get(&Oui([0x00, 0x0A, 0x92])),
            Some(&Known::Vendor("PreSonus".into()))
        );
        // The negative has to survive, or every restart re-asks and the day's
        // budget goes on addresses IEEE never assigned.
        assert_eq!(known.get(&Oui([0x00, 0x07, 0xF5])), Some(&Known::Unassigned));

        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn a_cached_name_answers_without_the_network() {
        let v = MacVendors::start_with_cache(None);
        v.remember(Oui([0x00, 0x0A, 0x92]), Known::Vendor("PreSonus".into()));
        assert_eq!(v.vendor("00:0A:92:FF:FE:01:56:A3").as_deref(), Some("PreSonus"));
        assert_eq!(
            v.label("00:0A:92:FF:FE:01:56:A3"),
            "PreSonus / 00:0A:92:FF:FE:01:56:A3"
        );
    }

    #[test]
    fn a_cached_negative_is_not_re_queued() {
        let v = MacVendors::start_with_cache(None);
        v.remember(Oui([0x00, 0x07, 0xF5]), Known::Unassigned);
        assert_eq!(v.vendor("00:07:F5:FF:FE:00:54:72"), None);
        let (lock, _) = &*v.shared;
        assert!(lock.lock().unwrap().queue.is_empty(), "spent a request on a known 404");
    }
}
