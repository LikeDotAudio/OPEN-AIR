# openair-maclookup

Names the manufacturer behind a hardware address, from the first 24 bits.

Not an agent — it publishes nothing and owns no topic. It is a library the
discovery agents call, because every one of them ends up holding a MAC and
nothing to show for it. A PTP tab listing `00:07:F5:FF:FE:00:54:72` four times is
complete and unreadable; the same table saying *Bridgeco Co AG* is the same data.

```rust
let vendors = openair_maclookup::MacVendors::start();
vendors.vendor("00:0A:92:FF:FE:01:56:A3");  // Some("Presonus Corporation")
vendors.label("00:0A:92:FF:FE:01:56:A3");   // "Presonus Corporation / 00:0A:92:…"
```

    mac-lookup 00:0A:92:FF:FE:01:56:A3    # one address, waits for the answer
    mac-lookup --cached                   # everything already learned
    … | mac-lookup                        # or pipe addresses in

## The budget is the design

[api.macvendors.com](https://macvendors.com/api) needs no key and allows **1000
requests a day at 1 per second**. Every design decision here falls out of that:

| | |
|---|---|
| Cache by **OUI**, not by MAC | 40 devices on a bench are perhaps 8 vendors |
| Cache the **misses** too | a 404 means IEEE assigned that block to nobody, and that will not be different tomorrow |
| **Persist** to disk | a restart loop would otherwise spend the day's budget re-learning what it knew |
| Reject **locally** what cannot have a vendor | multicast, locally-administered and all-zero addresses never cost a request |
| **One shared rate gate** | the CLI and the agent go through the same door; the limit is per source address, not per thread |
| **Never block the caller** | `vendor()` answers from cache or returns `None` and queues |

That last one is the load-bearing one. Discovery agents call this from packet
paths — the PTP agent from a capture callback that also handles Sync at 8/s — and
a one-second sleep there drops frames. So an unknown OUI is queued, one worker
thread drains the queue at the permitted rate, and the name appears a flush or
two after the device does. From then on it is free and offline.

The cache is a TSV so it can be read, grepped and hand-edited:

    # openair-maclookup vendor cache — one OUI per line
    #budget	20662	3
    00:07:F5	Bridgeco Co AG
    00:0A:92	Presonus Corporation
    FC:A1:3E	Samsung Electronics Co.,Ltd

An empty name is a remembered 404. `OPENAIR_MAC_CACHE` sets the path; it defaults
to `mac_vendors.tsv` in the working directory. Losing the file costs a day's
budget, not correctness.

## EUI-64

The addresses this bench actually produces are mostly **not** plain MAC-48. A PTP
clock identity and an AVDECC entity ID are both a MAC with `FF:FE` inserted in
the middle:

    00:0A:92:01:56:A3          the MAC
    00:0A:92:FF:FE:01:56:A3    the same device's clock identity

Since the OUI is the leading three bytes either way, the insertion needs no
special case — only the length check has to accept 16 hex digits as well as 12.
Both forms resolve to `00:0A:92`.

## Reading a MAC out of an IPv6 address

Most discovery here never sees a hardware address. DNS-SD advertises none, and
neither do the agents built on it — but they all publish **addresses**, and a
host that configured itself by SLAAC put its MAC in the low 64 bits of every one:
insert `FF:FE` in the middle, flip the universal/local bit.

    fe80::46fa:66ff:fee4:2fbf%enp5s0f0   ->   44:FA:66:E4:2F:BF

That flip is the whole subtlety, and it is why this cannot reuse `Oui::parse`.
Inverting bit 1 makes a globally-assigned MAC *look* locally-administered, so the
raw interface ID reads as `46:FA:66` — which `parse` rejects on sight, correctly,
because in a plain MAC that bit means IEEE assigned it to nobody. Undo the flip
first and it is Brother's real block.

The bench confirms it independently: that printer states the same address twice
by two unrelated routes, once in its link-local address and once in its hostname,
`BRW44FA66E42FBF.local`. There is a test pinning them together.

**Privacy addresses yield nothing, on purpose.** An RFC 4941 interface ID is
random and carries no `FF:FE` marker. Apple hosts use them, so their rows have no
vendor — reading one out of random bytes would be worse than a blank cell.

## The OUI names the builder, not always the brand

Worth knowing before trusting a cell. The Brother printer on this bench resolves
to *Cloud Network Technology Singapore* — the ODM that made its network module.
Both facts are true and they are different facts, which is why the printer and
Dante tabs keep their own `manufacturer` column: that one is the device's own
claim (`usb_MFG=Brother`, `mf=PreSonus`), this one is the IEEE registry.

## Who uses it

Every agent that has anything to read publishes **both** columns — `mac` and
`vendor`. The name is the readable fact; the address is the evidence for it, and
a row asserting *Google, Inc.* with no address to check it against is a claim
rather than a finding.

| Crate | Columns | Read from |
|---|---|---|
| `openair-ptp` | `vendor` | the EUI-64 clock identity |
| `openair-avb-milan` | `vendor` | the entity's source MAC |
| `openair-dnssd` | `mac`, `vendor` | the SLAAC link-local address |
| `openair-chromecast` | `mac`, `vendor` | ″ — Cast hardware is not all Google-built |
| `openair-printers` | `mac`, `vendor` | ″ — alongside the printer's own `manufacturer` |
| `openair-dante` | `mac`, `vendor` | ″ — alongside `mf=` from the TXT |
| `openair-appletv` | `mac`, `vendor` | ″ — usually blank, see below |
| `openair-nmos` | `mac`, `vendor` | ″ |

PTP and AVB carry no `mac` column because they already state the address: the
clock identity and the entity's source MAC *are* the hardware address.

Where a tab already had a `manufacturer` — printers, Dante — the two now sit
side by side rather than one being chosen. They answer different questions and
they disagree usefully: on this bench the Brother printer's own TXT says
`usb_MFG=Brother` while its OUI says *Cloud Network Technology Singapore*.

`openair-appletv` will mostly show `-` in both, and that is the true answer: Apple
uses RFC 4941 privacy addressing, so there is no MAC in the address to recover.
The column is there so the blank is visible as a fact rather than an omission.

`openair-ravenna` and `openair-sap` are the only discovery agents with nothing to
read — they discover streams, not hosts, and publish no address of any kind.

## One caveat, if you run many agents

Each agent starts its own `MacVendors`, so each keeps its own daily tally while
sharing one cache file. Six agents could in principle spend six budgets. In
practice they resolve the same handful of OUIs off the same bench and the shared
cache means the second agent to start finds most of them already answered — real
usage is tens of requests a day against a ceiling of a thousand. If that ever
stops being true, the tally has to move onto the bus like everything else here.
