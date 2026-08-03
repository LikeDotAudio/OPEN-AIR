# openair-chromecast — Google Cast discovery

Finds Chromecasts, Nest speakers, and Cast groups, and decodes what each one is.

**Discovery only.** No control.

## What it does

Browses `_googlecast._tcp` and publishes one retained topic tree per device to
`OpenAir/System/Protocols/chromecast/Device/<Category>/<Name>/…`.

The value over the raw DNS-SD tab is **decoding the TXT record**. `openair-dnssd`
sees these devices too, but publishes TXT verbatim because it cannot know what
any given service's keys mean. Cast's keys *are* defined:

| TXT key | Becomes |
|---|---|
| `fn` | `friendly_name` — "Garage speaker" |
| `md` | `model` — "Google Nest Mini" |
| `ca` | `capabilities` — decoded bitmask |
| `id` | `cast_id` |
| `rs` | `status_text` — what it is playing, or `idle` |
| `ve` | `protocol_version` |

## Categories

Devices are filed into `Speaker`, `Video Cast`, `Smart Display`, `Speaker Group`,
or `Cast Device`, from the model string with a capability-bit fallback.

**Category is derived, not intrinsic** — improve the classifier and a device
*moves*. The agent therefore clears a device's retained topics under every other
category before publishing, or it would appear twice. (This is not theoretical:
"Chromecast Audio" was initially filed as Video Cast because it matched the
generic `chromecast` rule before anything checked it was an audio-only puck.)

## What is deliberately not decoded

Only the low `ca` bits are publicly documented and stable, so only those become
flags. **The raw value is always published alongside** (`audio_out, … (raw:198660)`)
— a wrong guess dressed as a fact would be worse than an undecoded number.

## Why there is no control

Sending commands means **Cast V2**: a TLS socket to port 8009, a constant
heartbeat, and protobuf messages multiplexed over virtual channels
(`urn:x-cast:com.google.cast.{tp.heartbeat,tp.connection,receiver,media}`). The
`rust-cast` crate exists for that. It is a substantial protocol implementation
and is not needed to answer *what Cast hardware is here and what can it do?*

Discovery is also the safe half: passive, no pairing, and it cannot disturb a
device someone is listening to.

## Tests

`cargo test -p openair-chromecast` — capability decoding (including that the raw
value always survives), category rules, and topic-segment sanitising.
