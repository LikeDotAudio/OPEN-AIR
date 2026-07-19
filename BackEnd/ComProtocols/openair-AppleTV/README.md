# openair-appletv — AirPlay / HomeKit receiver discovery

Finds Apple TVs, HomePods and other AirPlay receivers.

**Discovery only.** No pairing, playback or remote control.

## One device, many roles

An Apple TV is chatty on mDNS, and each service answers a different question:

| Service | Role label | What it tells you |
|---|---|---|
| `_airplay._tcp` | `airplay` | video / screen mirroring receiver |
| `_raop._tcp` | `airplay-audio` | AirPlay audio — **the richest TXT** |
| `_homekit._tcp` | `homekit` | paired HomeKit accessory |
| `_hap._tcp` | `homekit-hap` | HomeKit Accessory Protocol |
| `_companion-link._tcp` | `continuity` | Handoff / Continuity |
| `_mediaremotetv._tcp` | `media-remote` | the Remote app |
| `_touch-able._tcp` | `remote-legacy` | legacy DACP remote |
| `_sleep-proxy._udp` | `sleep-proxy` | answers Bonjour for sleeping devices |

As with printers, that is one device with many roles, so the service list
becomes a `roles` column. **Grouping is by hostname**, which every service shares.

## What `_raop` carries

```text
am=AppleTV5,3     model identifier  -> "Apple TV HD (4th gen)"
ov=26.5           tvOS version
vs=950.7.1        AirPlay source version
cn=0,1,2,3        codecs   -> PCM, ALAC, AAC, AAC-ELD
md=0,1,2          metadata -> text, artwork, progress
ft=0x5A7FDFD5,…   feature bitmask
pk=…              pairing public key
```

Codec and metadata lists are decoded — short, stable, documented. The **feature
bitmask is not**: its bits are only partly public and vary by tvOS release, so
it is published raw rather than guessed at.

Unknown model identifiers pass through verbatim. `AppleTV99,9` meaning nothing
is better than it meaning the wrong thing.

## The `_sleep-proxy` trap

A device is only published once something has actually **identified** it —
`airplay`, `airplay-audio`, `homekit`, `homekit-hap` or `media-remote`.

`_sleep-proxy` alone is not enough: it is a Bonjour feature, and a router or a
Mac can offer it. Publishing those as Apple TVs would be wrong.

## TXT merge rule

Fills gaps, never overwrites. `_raop` carries the rich record and the others are
nearly empty, so last-write-wins would erase the good data.

## Why there is no control

AirPlay control requires the pairing/encryption handshake advertised by `pk`/`et`
— a protocol implementation in its own right, and not needed to answer *what
Apple hardware is here and what will it accept?*

## Tests

`cargo test -p openair-appletv` — model decoding (known and unknown), codec and
metadata lists pinned to the real bench values, and unknown codes being skipped
rather than invented.
