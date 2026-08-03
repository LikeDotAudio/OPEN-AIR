# openair-sap — SAP/SDP session announcement discovery

Passive listener for AES67 streams announced over SAP.

**Listen only.** This agent never transmits a SAP packet, and never subscribes
to RTP.

## Why SAP exists alongside mDNS

AES67 standardises how audio is clocked, packetised and transported, but
deliberately says nothing about how you *find* a stream. The ecosystem split:

| | Announces via | Handled by |
|---|---|---|
| **RAVENNA** | mDNS/DNS-SD + SDP pulled over RTSP | [`openair-ravenna`](../openair-ravenna/) |
| **Dante in AES67 mode** | SAP push to a multicast group | **this crate** |

Dante abandons mDNS entirely for AES67 streams: no queries, no resolution, no
handshake. The device pushes raw SDP to UDP 9875 every few seconds, and anything
listening builds a directory for free.

## Overlap with RAVENNA is intentional

A node running RAV2SAP, or a RAVENNA device with SAP publishing enabled, appears
under **both** agents. That is not a duplicate to suppress here — the two topic
trees record two different observations ("announced over mDNS" / "announced over
SAP"), and *which mechanisms a stream actually uses* is precisely the interop
question you are asking when something will not connect.

Correlating them into one device is the Device Registry's job, not the
listener's.

## Three multicast groups, not one

| Group | Why |
|---|---|
| `239.255.255.255` | what Dante uses |
| `224.2.127.254` | the IANA-assigned SAP group |
| `239.195.255.255` | organisation-local range, used by some installs |

Listening to only one silently misses devices; an unused membership costs
nothing.

## Sessions expire

SAP is periodic push with **no goodbye guarantee** — an unplugged device simply
stops talking, and the `T`-flag deletion packet only arrives on a clean
shutdown. Without expiry the Discovered tab would accumulate ghosts forever.

`SESSION_TIMEOUT` is 5 minutes: RFC 2974 suggests ten announcement intervals,
and observed AoIP gear announces every 5–30 s, so this covers a slow announcer
while still clearing a dead one promptly. Expiry is checked on the same loop as
the socket read rather than from a second thread holding a lock.

## Columns

The first ten deliberately match `openair-ravenna`'s, so streams from both
protocols read side by side. Then `source`, `announced_via`, `msg_id`.

## Topics

```
OpenAir/System/Protocols/sap/Device/{origin_ip}/{session}/{key}
```

Grouped by the **announcing node's IP** rather than by session, because one
Dante device commonly announces every transmit flow separately — the UI should
show one device with N streams.

## Why it never transmits

Publishing a SAP announcement would insert a phantom source into every routing
matrix on the network. That is not something a discovery tool gets to do as a
side effect of looking.

## Tests

`cargo test -p openair-sap` — decoding a real bench announcement, a Dante AES67
announcement, and rejecting video sessions that happen to be on 9875.
