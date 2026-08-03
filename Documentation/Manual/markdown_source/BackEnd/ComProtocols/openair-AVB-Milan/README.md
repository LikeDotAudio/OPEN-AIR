# OpenAir AVB / Milan Backend (`openair-avb-milan`)

Discovery for AVB and Milan devices over **AVDECC** (IEEE 1722.1) — plus the
one control command worth having on day one: *identify*, which makes a device
blink its front-panel LED so you can tell which box in the rack it is.

This is the only agent in `ComProtocols` that works at **Layer 2**. Everything
else here opens a socket on an IP address; this one reads raw Ethernet frames.
That difference drives every design decision below.

---

## Why this crate shares no code with the AES67 agents

OPEN-AIR discovers three families of audio-over-network devices, and it is
worth being precise about how they differ, because two of them are close
cousins and the third is not related at all.

| | Layer | Discovery | Describes streams with | Agent |
|---|---|---|---|---|
| RAVENNA | 3 (IP) | mDNS query → RTSP pull | SDP text | `openair-ravenna` |
| Dante (AES67 mode) | 3 (IP) | SAP multicast push | SDP text | `openair-sap` |
| AVB / Milan | **2 (MAC)** | **AVDECC ADP** | **binary descriptor model** | **this crate** |

RAVENNA and Dante disagree only about *how an SDP record is delivered*. They
agree it is SDP, arriving over IP, describing a stream by multicast address and
port. That is why those two agents share a parser (`openair_ravenna::sdp`).

AVB agrees with neither. It moves audio addressed by MAC address and never
touches IP — no ports, no multicast group to subscribe to, no SDP anywhere.
A device is found by reading frames sent to the reserved MAC
`91:E0:F0:01:00:00`, and described by a hierarchical binary descriptor model.
Every assumption the other agents rest on is absent, so this crate starts at
the wire.

The other consequence: **AVB switches are participants, not pipes.** An AES67
switch forwards mDNS and SAP without understanding them. An AVB switch must be
AVB-certified and actively reserves bandwidth via SRP before audio flows. This
crate does not speak SRP — see [Scope](#scope-what-this-does-not-do) — but it
is why a device can be perfectly healthy, announce itself here, and still
refuse to pass audio through a non-AVB switch.

---

## Core Architecture

One module per protocol layer, in `src/`:

- **`adp.rs`** — the **AVDECC Discovery Protocol** parser (1722.1 clause 6).
  Decodes the 68-byte ADPDU: entity ID, model ID, capability bitfields,
  talker/listener stream counts, and the gPTP grandmaster. Handles the optional
  802.1Q tag. Also builds the `ENTITY_DISCOVER` query frame.
- **`capture.rs`** — raw `AF_PACKET`/`SOCK_RAW` capture. Interface
  enumeration, AVDECC multicast group membership, frame send/receive, and
  privilege-error explanation. Linux-only; says so plainly elsewhere.
- **`aecp.rs`** — the **AVDECC Enumeration and Control Protocol** (clause 9),
  scoped to a single command: `SET_CONTROL` against the IDENTIFY control.
  Builds command frames, parses responses, decodes AEM status codes.
- **`identify.rs`** — drives the identify exchange: send, await response with
  the spec's retry rules, guarantee the blink is turned back off.
- **`lib.rs`** — the agent. Listen loop, MQTT publishing, entity expiry.
- **`bin/avdecc-probe.rs`** — standalone "is there anything out there?".
- **`bin/avdecc-identify.rs`** — standalone "which box are you?".

---

## How discovery works

### 1. The announcement

An AVB **entity** (any device — a console, an amp, an I/O box) periodically
emits an ADP `ENTITY_AVAILABLE` frame to the AVDECC multicast MAC. There is no
query/response handshake and no resolution step; the frame *is* the
announcement.

```
Ethernet: | dst 91:E0:F0:01:00:00 | src <device MAC> | [802.1Q] | 0x22F0 |
AVTP common control header (12 bytes):
  0       subtype = 0x7A (ADP)
  1       sv | version | message_type   0=AVAILABLE 1=DEPARTING 2=DISCOVER
  2..3    valid_time(5) | control_data_length(11)
  4..11   entity_id
ADPDU body (56 bytes):
  12..19  entity_model_id          20..23  entity_capabilities
  24..25  talker_stream_sources    26..27  talker_capabilities
  28..29  listener_stream_sinks    30..31  listener_capabilities
  32..35  controller_capabilities  36..39  available_index
  40..47  gptp_grandmaster_id      48      gptp_domain_number
  50..51  current_configuration_index
  52..53  identify_control_index   54..55  interface_index
  56..63  association_id
```

### 2. Asking rather than waiting

Heartbeats can be tens of seconds apart, so on startup the agent sends one ADP
`ENTITY_DISCOVER` per interface — entity ID zero, meaning "everyone answer".

This is the **only frame discovery transmits**. It is what Hive and every other
AVDECC controller emits on startup, and it is the Layer 2 twin of the mDNS query
`openair-dnssd` already sends. It reserves no bandwidth and changes no routing.

### 3. Multicast membership, not promiscuous mode

A NIC drops multicast frames for groups it has not joined, so the listener asks
for `91:E0:F0:01:00:00` explicitly via `PACKET_ADD_MEMBERSHIP` on every
interface. The lazy alternative — promiscuous mode — lifts all filtering and
hands userspace every frame on the segment. On an audio network that is a
firehose of RTP, and a far broader claim on the network's traffic than
discovery needs.

The socket is also filtered to EtherType `0x22F0` in the kernel. AVTP *stream
data* shares that EtherType, so a subtype check still happens per frame — but
that is a byte comparison on frames we were going to see anyway.

### 4. Expiry

`ENTITY_DEPARTING` only arrives on a clean shutdown. A pulled cable produces
silence. So each entity is expired on its own announced `valid_time` (floored
at 10s so one dropped frame does not make the UI flicker), and its retained
topics are cleared.

---

## MQTT topics

One retained topic per attribute, matching the field-per-topic shape the
Discovered-tab builder sweeps:

```
OpenAir/System/Protocols/avb/Device/{entity_id}/{key}
```

Keyed by **entity ID, not name** — ADP carries no human-readable name at all.
The name lives in the descriptor tree, which requires enumeration.

Keys: `entity_id`, `mac`, `oui`, `interface`, `entity_model_id`,
`talker_sources`, `talker_capabilities`, `listener_sinks`,
`listener_capabilities`, `entity_capabilities`, `gptp_grandmaster`,
`gptp_domain`, `milan`, `available_index`, `configuration_index`,
`valid_time_s`, `status`, `last_online`.

The agent also publishes its own health, because it can fail for a reason that
has nothing to do with the code:

```
OpenAir/System/Protocols/avb/Agent/state    listening | unavailable
OpenAir/System/Protocols/avb/Agent/detail   which interfaces, or why not
```

The orchestrator marks a protocol `online` from the presence of its
`config.ini`, which is a fair proxy for every IP-based agent and a poor one
here — missing `CAP_NET_RAW` would otherwise show as a healthy agent silently
publishing nothing.

---

## Privileges

Raw frame capture requires `CAP_NET_RAW`. There is no unprivileged way to read
raw Ethernet on Linux, and no way around it: the protocol has no IP layer to
bind to.

```bash
sudo setcap cap_net_raw,cap_net_admin+eip target/release/avdecc-probe
sudo setcap cap_net_raw,cap_net_admin+eip target/release/avdecc-identify
```

...or run with `sudo`. Without it, every tool here prints that remedy rather
than a bare `EPERM`, because "permission denied" reads as "AVB is broken" when
it actually means "you have not granted packet capture".

---

## The tools

### `avdecc-probe` — is anything out there?

```bash
sudo ./avdecc-probe              # every Ethernet interface
sudo ./avdecc-probe enp5s0f0     # just the audio network
```

Listens 30 seconds and prints a verdict. Two things make it worth having
separately from the agent:

**It reports the negative usefully.** An agent that publishes no topics is
indistinguishable from one that never started. The probe says "listened on
these interfaces, sent these queries, heard nothing", and distinguishes:

- *No AVTP traffic at all* — device not on a listening interface, switch not
  AVB-capable and dropping the multicast, AVB mode disabled, or the device has
  not yet achieved gPTP lock.
- *AVTP present but no ADP* — the wire is alive and something is streaming, but
  nothing is announcing. Usually means AVDECC is disabled separately from AVB.

**It shows every AVTP subtype it sees**, so a device that streams but does not
announce still registers as evidence of something on the wire.

It also flags when discovered entities report **different gPTP grandmasters** —
devices on different clocks cannot stream to each other, and it is the most
common reason for "discovered but won't pass audio".

### `avdecc-identify` — which box are you?

Hive's Identify button, as a command line.

```bash
sudo ./avdecc-identify                    # exactly one entity present: blink it
sudo ./avdecc-identify --list             # show what is out there, do nothing
sudo ./avdecc-identify 1B:2C              # match entity ID or MAC by substring
sudo ./avdecc-identify 1B:2C --seconds 30 # blink longer
```

ADP carries `identify_control_index` directly, which is what lets this work
without implementing enumeration: an AECP `SET_CONTROL` writes 255 to that
CONTROL descriptor to start the blink and 0 to stop it.

```
  0       subtype = 0x7B (AECP)
  1       sv | version | message_type    0 = AEM_COMMAND, 1 = AEM_RESPONSE
  2..3    status(5) | control_data_length(11)
  4..11   target_entity_id
  12..19  controller_entity_id
  20..21  sequence_id
  22..23  u | command_type                0x0018 = SET_CONTROL
  24..25  descriptor_type                 0x001A = CONTROL
  26..27  descriptor_index                from ADP's identify_control_index
  28      value                           255 = on, 0 = off
```

**This is the only code in these crates that writes to hardware**, so it is
fenced accordingly:

- **Unicast, never the multicast group.** A test asserts the destination is not
  `91:E0:F0:01:00:00` — broadcasting an identify would light up a whole rack.
- **It refuses to guess a target.** No argument plus multiple entities means
  list and stop. Picking for you is how a console in another room starts
  flashing.
- **It refuses to guess the control index.** If the entity does not set
  `AEM_IDENTIFY_CONTROL_INDEX_VALID`, it stops. Commanding index 0 on the
  off-chance could hit a gain, a mute, or a clock source instead.
- **It always sends the off command** — on refusal, on no response, and on
  Ctrl-C (the wait is sliced into 100ms ticks that poll an interrupt flag, so
  the signal cannot kill the process mid-blink and leave hardware flashing).

Retries follow 1722.1 §9.2.1.2: 250ms timeout, two retries, **reusing the same
sequence ID** so the device recognises a duplicate rather than acting twice.

AEM status codes are decoded with plain-language explanations. The one you are
most likely to hit: **`EntityAcquired` — if Hive is open and holding the
entity, identify is refused.** Close it first.

---

## Scope: what this does *not* do

Deliberate omissions, each for a reason:

- **AEM enumeration (`READ_DESCRIPTOR`).** ADP gives capability flags and
  stream *counts*. Channel names, clock domains, and the routing matrix live in
  the descriptor tree, which is a request/response conversation with the
  device. Reporting counts we actually received beats implying we know a tree
  we never asked for. This is the natural next piece of work.
- **SRP (Stream Reservation Protocol).** Asks the switches to carve out
  guaranteed bandwidth. Changes network state.
- **ACMP (connection management).** Rewires audio between devices. Changes
  network state.
- **Claiming Milan compliance.** Milan is asserted by answering a Milan Vendor
  Unique `GET_MILAN_INFO` command — it is *not* a bit in the announcement. So
  `milan_assessment()` returns "possible — confirm with MVU" for a capable
  entity, and only goes negative on hard evidence (no AEM support, no gPTP, no
  Class A). A test pins that hedge in place. A definitive yes/no needs the MVU
  exchange, which is a small extension of `aecp.rs`.
- **MQTT-triggered identify.** `config.ini` declares `topic_listen` and a GUI
  Identify button is the obvious destination, but wiring it means anything that
  can publish to the bus can make hardware blink. That is a deliberate decision
  left open rather than made silently.

---

## How the tests work

`cargo test -p openair-avb-milan` — 22 tests, no hardware or network required.
Every test builds or parses real frame bytes.

- **`adp.rs`** — a synthetic `ENTITY_AVAILABLE` with every field set to a
  distinguishable value, so a field-offset mistake cannot pass by reading a
  neighbour's bytes and still looking plausible. Plus: VLAN-tagged frames parse
  identically to untagged; AVTP stream data on the same EtherType is rejected
  on subtype, not mistaken for a short announcement; Milan is never claimed
  from ADP alone.
- **`aecp.rs`** — the identify command's exact byte layout; that *off* differs
  from *on* in exactly one byte (a regression there leaves hardware blinking
  indefinitely); that our own outgoing command is not mistaken for a response,
  which would report a phantom success before the device replied.
- **`identify.rs`** — outcomes explain themselves without overclaiming (a
  silent device is reported as ambiguous, since the command may have landed and
  only the response been lost); cancelling shortens the wait rather than
  skipping the off command.
- **`capture.rs`** — interface enumeration works unprivileged; permission
  errors name the remedy.

The AES67 agents test against byte-verbatim captures from the bench. Doing the
same here needs an AVB entity on the wire — capture one ADP frame and add it as
a fixture the way `openair-sap` did.
