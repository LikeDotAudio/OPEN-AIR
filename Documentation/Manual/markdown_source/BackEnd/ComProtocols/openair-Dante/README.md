# openair-dante — Dante discovery

Finds Dante devices and their channels.

**Discovery only.** Dante's connection management is proprietary — this agent
reports what exists and never routes or subscribes.

## Dante's split personality

Dante announces itself two entirely different ways depending on who it is
talking to. This agent handles the **native** half; the AES67 half lives
elsewhere on purpose (see below).

### Native Dante — mDNS

Audinate's proprietary service tags:

| Service | Meaning |
|---|---|
| `_netaudio-arc._udp` | Audinate Routing Control — the device's control endpoint |
| `_netaudio-cmc._udp` | Conmon control |
| `_netaudio-dbc._udp` | Device browsing/config |
| `_netaudio-chan._udp` | **one advertisement per channel** |

This is how Dante Controller populates its routing matrix. It is enough to find
and describe a device — but unlike RAVENNA there is no SDP to read, so this
reports what a Dante device **is**, not what it streams.

### AES67 mode — SAP, handled by `openair-sap`

Tick "Enable AES67" in Dante Controller and the device **stops using mDNS for
those streams entirely** and starts pushing SDP to `239.255.255.255:9875`.

That belongs to [`openair-sap`](../openair-sap/), not here, for two reasons:

1. **SAP is vendor-neutral.** RAVENNA gear, RAV2SAP translators and Dante all
   land on that group. Filing it all under "Dante" would mislabel most of it.
2. **One socket, one owner.** Two agents cannot both bind UDP 9875 — the second
   silently receives nothing. This agent originally shipped its own listener and
   collided with `openair-sap`; the Dante stream tab stayed empty while SAP
   quietly worked. Duplicated listeners fail exactly that way.

## Channels live under their device

`_netaudio-chan` advertises **one service per channel**, named
`Ch10@Metro16-DANTE2AVB`. Taken at face value a 16-channel interface produced
sixteen device rows — accurate, useless.

The device is the part after `@`. Channels are published beneath it:

```
…/dante/Device/<device>/…                    ← one row: identity, services, channel count
…/dante/Device/<device>/Channel/<Ch>/…       ← one row per channel
```

Per channel, from its own TXT: `id`, `sample_rate`, `bit_depth`,
`latency_ms` (converted from `latency_ns` — 1 ms reads better than 1000000),
`frames_per_packet`, `flow_channels`, `redundancy`.

These can differ from the device defaults, which is why they are kept rather
than summarised away.

## Identity merging

Only the `arc` service carries `mf`/`model`. Channel advertisements carry none,
so the agent **keeps the best value seen** — a later channel update cannot
overwrite "PreSonus" with "Unknown".

## Tests

`cargo test -p openair-dante` — SAP packet parsing (incl. deletions and
encrypted packets), channel/device name splitting, and latency conversion.
