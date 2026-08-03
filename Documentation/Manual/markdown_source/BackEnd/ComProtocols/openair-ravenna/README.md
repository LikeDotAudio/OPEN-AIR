# openair-ravenna — RAVENNA / AES67 stream discovery

Finds RAVENNA audio streams and reads their actual parameters.

**Discovery + description only.** No RTP receive, no subscription.

## The chain it follows

RAVENNA announces over mDNS and describes streams with SDP, fetched over RTSP.
This agent walks the whole chain:

1. **mDNS** — browse `_ravenna._tcp` and `_rtsp._tcp`
2. **RTSP DESCRIBE** — `rtsp://<ip>:554/by-name/<session>`
3. **SDP parse** — the parameters an engineer needs

Published to `OpenAir/System/Protocols/ravenna/Device/<host>/<stream>/…`

## What you get per stream

| Column | From SDP | Example |
|---|---|---|
| `format` | `a=rtpmap:` | `L24 48000Hz 2ch` |
| `destination` | `c=` | `239.1.44.117` (multicast) |
| `rtp_port` | `m=audio` | `5004` |
| `ptime_ms` | `a=ptime:` | `1` |
| `clock_domain` | `a=clock-domain:` | `PTPv2 0` |
| `refclk` | `a=ts-refclk:` | the PTP grandmaster it is locked to |
| `direction` | `a=recvonly` etc. | `recvonly` |

`refclk` is the one people forget to check: two streams that will not lock
together usually disagree here.

## Why the SDP fetch is not optional

**Port 554 proves nothing** — IP cameras answer RTSP too. The SDP is the
discriminator: an `m=audio` line means audio, `m=video` means a doorbell.
A service is only published here once *its own SDP* says it carries audio.
Anything else is logged and skipped:

```
⏭️ [RAVENNA] <name> @ <ip> is not an audio stream — skipping
```

Publishing every RTSP responder as a "RAVENNA device" would be a guess dressed
as a discovery.

## Grouping

By **hostname**. One node commonly publishes several streams — a desk might
offer `Digital inputs 1-2` and a monitor feed from the same host — so the UI
shows one device with N streams rather than N unrelated rows.

## Gotchas handled

- **Session names need URL-encoding.** `Digital inputs 1-2 (42-04-BA)` will not
  fetch without `%20`/`%28`.
- **Mono omits the channel count.** `L24/48000` is 1 channel, not 0.

## Tests

`cargo test -p openair-ravenna` — the SDP parser is pinned against a **verbatim
record from real hardware**, plus video rejection, mono defaulting, and URL
encoding. `sdp.rs` is public and reused by `openair-dante`.
