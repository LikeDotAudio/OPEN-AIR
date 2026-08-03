# OpenAir PTP Backend (`openair-ptp`)

Discovery and live traffic monitoring for **all three clock protocols that can
share one NIC**: PTPv1 (IEEE 1588-2002), PTPv2 (IEEE 1588-2008) and gPTP
(IEEE 802.1AS).

It watches the packets arrive, decodes them, and — the part that makes a
capture readable — correlates them into the exchanges they actually form:
Sync ↔ Follow_Up, Delay_Req ↔ Delay_Resp, and the three-legged peer-delay
chain.

---

## Why three protocols on one NIC is the hard case

They are not three variations of one thing. They disagree about the header
layout, the transport, and even how a clock is named:

| | Standard | Transport | Address | Identity |
|---|---|---|---|---|
| PTPv1 | 1588-2002 | UDP/IPv4 | `224.0.1.129` :319/:320 | 6-byte UUID |
| PTPv2 | 1588-2008 | UDP/IPv4 | `224.0.1.129` :319/:320 | 8-byte clock identity |
| PTPv2 | 1588-2008 | Ethernet | `01:1B:19:00:00:00`, 0x88F7 | 8-byte clock identity |
| gPTP | 802.1AS | Ethernet | `01:80:C2:00:00:0E`, 0x88F7 | 8-byte clock identity |

Four consequences drive the whole design:

**1. v1 and v2 share the group *and* the ports.** One socket receives both, and
only the leading bytes tell them apart. This is precisely how a v1 device hides
on a network everyone believes is v2-only — nothing about the transport betrays
it.

**2. Listening means two different kinds of socket at once.** UDP for v1/v2 and
a raw `AF_PACKET` socket for gPTP. There is no single API that sees both.

**3. Event and general messages arrive on different sockets.** Sync, Delay_Req
and Pdelay_* are hardware-timestamped and use port 319; Follow_Up, Delay_Resp
and Announce use port 320. **A Sync and its own Follow_Up therefore arrive on
different sockets** — a detail that makes captures baffling until you know it.
Both are polled and merged into one stream, which is what makes correlation
possible at all.

**4. gPTP and PTPv2-over-Ethernet look identical at first glance.** Same
EtherType, both Layer 2. What separates them is `transportSpecific = 1` and the
destination MAC. Since AES67/RAVENNA installs commonly run plain 1588 at Layer
2, conflating the two would file a RAVENNA clock as an AVB one. The variant is
part of a clock's identity here, so they stay distinct rows.

---

## Core Architecture

- **`message.rs`** — PTPv2 / gPTP parsing. The 34-byte common header plus the
  bodies worth reading: Announce (grandmaster identity, priority, clock class
  and accuracy, time source, stepsRemoved), the timestamps on Sync/Follow_Up/
  Delay_*, and the flag field.
- **`v1.rs`** — PTPv1. A separate parser because it shares nothing but the
  wire. Also maps a v1 UUID onto the v2 clock-identity convention, so one box
  running both stacks can be recognised as one device.
- **`net.rs`** — capture across both transports: UDP 319/320 joined to the PTP
  groups, and raw Ethernet filtered to 0x88F7 with membership in both PTP
  multicast MACs.
- **`flow.rs`** — correlation. Turns a packet stream into exchanges.
- **`monitor.rs`** — the shared capture loop, plus the accumulated clock table.
- **`agent.rs`** — the MQTT agent.
- **`bin/ptp-monitor.rs`** — the live view.

The legacy `oa_ptp_clock_rs` / `oa_ptp_parser_rs` PyO3 modules predate all of
this and remain behind the non-default `python` feature. They are untouched and
nothing above depends on them.

---

## Correlation: the part that matters

A PTP capture read message-by-message is nearly useless. What you want to know
is which messages belong together:

```
Two-step sync    master ──Sync(seq N)──▶ slave
                 master ──Follow_Up(seq N, precise t1)──▶ slave

Delay request    slave  ──Delay_Req(seq M)──▶ master          (E2E)
                 master ──Delay_Resp(seq M, t4)──▶ slave

Peer delay       A ──Pdelay_Req(seq K)──▶ B                   (P2P / gPTP)
                 B ──Pdelay_Resp(seq K, t2)──▶ A
                 B ──Pdelay_Resp_Follow_Up(seq K, t3)──▶ A
```

Three rules make this correct rather than merely plausible:

**Messages are keyed per-port, not per-sequence.** Sequence IDs are per-port
counters, so two grandmasters will happily both be on sequence 4521 at the same
moment. A tracker keyed on the sequence alone pairs the wrong Sync with the
wrong Follow_Up and reports a fictional delta that looks entirely reasonable.
The key is (clock identity, port number, domain, variant).

**Responses are filed under the requester, not the sender.** A Delay_Resp is
sent by the master but answers the *slave's* Delay_Req, so it is looked up by
the requesting port identity carried in its body. Keying it by the sender would
never find anything.

**A one-step Sync is never left pending.** When `twoStepFlag` is clear, the
Sync carries its own timestamp and no Follow_Up is ever coming. Recording it
would leave an entry that only ever expires — and would suggest to whoever
reads the output that something went missing when nothing did.

Unanswered exchanges expire after 10s. Sequence IDs are 16-bit and wrap; without
expiry, a Sync whose Follow_Up was lost would linger and be falsely completed
65536 messages later.

The gap the monitor prints is **arrival-to-arrival at this capture point**, not
a protocol measurement. It is inflated by our own scheduling and is useful for
spotting a Follow_Up that took 40ms — not for computing offset. The protocol's
own numbers are in the timestamp fields.

---

## The monitor

```bash
sudo ./ptp-monitor                 # live tail of everything
sudo ./ptp-monitor --summary       # clock table, refreshed every 5s
sudo ./ptp-monitor --seconds 30    # run 30s, then print the summary
sudo ./ptp-monitor --domain 0      # only this PTP domain
```

The live tail shows each message with the detail that makes it worth reading —
whether a Sync is one-step or two-step, an Announce's full grandmaster claim,
the correction field when non-zero — and, underneath, what it completed:

```
   1.234s gPTP     L2 Sync                  seq  4521 dom   0 from 00:0A:92:FF:FE:01:56:A3/1  [twoStep — Follow_Up expected]
   1.237s gPTP     L2 Follow_Up             seq  4521 dom   0 from 00:0A:92:FF:FE:01:56:A3/1  t=1784...
           ↳ completes Sync seq 4521 — observed 3.102ms after it
```

Ctrl-C prints the summary rather than discarding it.

The summary sorts grandmasters first, and flags the diagnosis worth leading
with: **more than one grandmaster claimed in the same domain.** Devices
following different grandmasters are not on the same time and cannot exchange
audio, and it is free to check once the clocks are in hand.

---

## Privileges

PTP needs two grants, for two separate reasons — ports 319/320 are below 1024,
and raw Ethernet capture is privileged on Linux:

```bash
sudo setcap cap_net_raw,cap_net_bind_service+eip target/release/ptp-monitor
```

...or run with `sudo`.

**Each transport opens independently, and a partial capture still runs.**
Seeing only gPTP because the UDP bind was refused is a legitimate result — as
long as it says so, which it does, both on the console and on the bus. The
alternative (failing outright) throws away half a working diagnosis.

---

## MQTT topics

```
OpenAir/System/Protocols/ptp/Device/{clock_id}-{port}-d{domain}/{key}
```

One row per **PTP port**, not per device. A box can run several ports, several
domains, and more than one flavour at once — each is an independent clock that
can disagree with the others, and merging them by device would hide exactly the
disagreement worth seeing.

Keys: `clock_id`, `port`, `variant`, `domain`, `role`, `grandmaster`,
`gm_class`, `gm_class_meaning`, `gm_accuracy`, `time_source`, `steps_removed`,
`priority1`, `priority2`, `sync_interval_s`, `two_step`, `status`,
`last_online`.

Agent health, for the same reason as the AVB agent — the orchestrator infers
`online` from a `config.ini` and cannot know a capability is missing:

```
OpenAir/System/Protocols/ptp/Agent/state    listening | partial | unavailable
OpenAir/System/Protocols/ptp/Agent/detail   which transports opened, or why not
```

`partial` is its own state on purpose: "no gPTP clocks" and "could not listen
for gPTP" are indistinguishable downstream otherwise.

### Publishing policy differs from every other agent here

PTP is continuous, high-rate traffic. gPTP Sync runs at 8 messages per second
per port by default; an mDNS device announces every few minutes. Republishing a
retained topic per Sync would put thousands of writes a minute on the bus to say
nothing new.

So the agent publishes **on state change plus a 30-second heartbeat**, and only
writes keys whose values actually changed. The packet-by-packet view is
`ptp-monitor`'s job — that is a tool you watch, not a state store.

Clocks that go quiet for 30s are cleared. PTP is continuous by nature: a healthy
clock is never silent that long at any standard rate, so silence means gone
rather than idle.

---

## Discovered tab

`BackEnd/Core/orchestrator/gui/build_discovered_gui.py` subscribes to the tree above and builds a
`ptp` tab, one row per port, with the grandmaster columns first — `grandmaster`
and `gm_class` answer "is time healthy?", which is the question the tab exists
for.

---

## How the tests work

`cargo test -p openair-ptp` — 37 tests, no hardware or network required. Every
test builds real frame bytes and parses them.

The tests worth knowing about are the ones pinning down mistakes that would
otherwise produce *plausible* output:

- **`correction_field_is_descaled`** — `correctionField` is nanoseconds scaled
  by 2^16. Reading it raw overstates residence time by 65536×, which looks like
  a catastrophically broken network rather than a parsing bug.
- **`negative_corrections_stay_negative`** — an unsigned read turns a small
  negative correction into an enormous positive one.
- **`identical_sequence_ids_from_different_clocks_do_not_cross_match`** — the
  fictional-delta bug described above.
- **`control_field_names_the_message_not_byte_20`** — in PTPv1, byte 20 is
  event-vs-general and byte 32 (`control`) names the message. Reading byte 20 as
  if it were v2's `messageType` turns every v1 Sync into a Delay_Req.
- **`l2_ptpv2_is_not_promoted_to_gptp`** — the RAVENNA-filed-as-AVB error.
- **`timestamps_use_48_bit_seconds`** — seconds are 48-bit; a 32-bit read
  truncates.
- **`clock_identity_yields_a_mac_only_when_eui64`** — clock identities are
  conventionally a MAC with `FF:FE` spliced in, but only conventionally, so the
  MAC is returned only when the identity really has that shape rather than
  inventing six bytes.
- **`vlan_tagged_frames_parse_identically`** — gPTP is class SR-A traffic and is
  routinely priority-tagged; the kernel only strips the tag when the NIC
  offloads it, so both forms reach us.

Fixtures are synthetic, built from the standards. The AES67 agents in this repo
test against byte-verbatim bench captures, and this crate should too — capture
one frame of each flavour off the wire and add them, the way `openair-sap` did.

---

## Scope

Discovery and observation only. This crate **never transmits a PTP message**.

That is a harder line than it is for the other agents, and deliberate: a device
emitting Announce messages participates in the Best Master Clock Algorithm, and
a monitoring tool that accidentally wins a grandmaster election would take over
timing for the entire network. Reading is safe; speaking is not. There is no
send path in this crate at all.

It also does not discipline the local clock — no `clock_gettime`/`adjtimex`, no
PHC access. That is `ptp4l`/`phc2sys`'s job, and doing it from a discovery agent
would fight whatever daemon is already doing it properly.

### Known overlap

`net.rs`'s raw-socket handling duplicates `openair-avb-milan`'s `capture.rs` —
same `AF_PACKET` setup, same multicast-membership-not-promiscuous reasoning,
different EtherType and groups. Two users is not yet three, so the shared
abstraction is deliberately **not** extracted; when a third Layer 2 protocol
arrives, that is the moment to pull it into a common crate rather than now.
