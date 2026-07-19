# openair-printers — network printer discovery

Finds printers and answers the questions people actually ask about them.

**Discovery only.** No print jobs, no state changes.

## Why this is easy: printers are standardised

Every modern network printer implements the **Bonjour Printing Specification**
(the basis of AirPrint, Mopria and IPP Everywhere). The TXT record is not vendor
soup — it is a documented schema, so it can be decoded into real columns.

## The design problem: one printer, six announcements

A single Brother HL-L2405W advertises **six** services:

| Service | Port | What it is |
|---|---|---|
| `_ipp._tcp` | 631 | IPP — the modern default |
| `_ipps._tcp` | 443 | IPP over TLS |
| `_ipp-tls._tcp` | 631 | IPP with STARTTLS |
| `_printer._tcp` | 515 | LPD/LPR — legacy |
| `_pdl-datastream._tcp` | 9100 | raw socket ("JetDirect") |
| `_http._tcp` | 80 | admin web UI |

Six rows would be accurate and useless. This is **one printer with six ways in**,
so the service list becomes a `transports` column — which is the genuinely
useful fact, because it tells you how you can actually print to it.

## Grouping: by `UUID`

Identical across all six announcements, stable across reboots, survives a DHCP
change. Hostname breaks on a dual-interface printer; the friendly name is
user-editable.

A host seen **only** over `_http._tcp` is never published — that service is far
too generic to identify a printer, and without a UUID there is nothing to group.

## Capabilities, decoded

`Color=F`, `Duplex=F`, `Scan=F` become Yes/No columns, because those are
answerable questions.

**`?` is a distinct answer from `No`.** The spec does not require every flag, so
a printer that never advertises `Scan` shows `?`. Reporting "No" would assert
something the announcement never said.

`pdl` is summarised: `application/octet-stream` is dropped (every printer claims
it; it distinguishes nothing), leaving `AirPrint(URF), PWG-raster`.

## TXT merge rule

Fills gaps, never overwrites. `_pdl-datastream` carries a thinner record than
`_ipp`, so last-write-wins would strip capabilities the printer had already
reported.

## Tests

`cargo test -p openair-printers` — flag decoding (including absent-vs-false),
and `pdl` summarising pinned against the real Brother record.
