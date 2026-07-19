# openair-nmos — AMWA NMOS discovery (IS-04 / IS-09)

Finds NMOS Nodes, Registries, Query and System APIs.

**Discovery only** — `STATUS = "discovery-only"`. The IS-04/IS-05 HTTP APIs are
not called: nothing is enumerated, registered, or connected.

## Services

| Service | Typical port | Role |
|---|---|---|
| `_nmos-node._tcp` | 3212 | Node API — a device offering senders/receivers |
| `_nmos-query._tcp` | 3211 | Query API — what clients ask to find things |
| `_nmos-register._tcp` | 3210 | Registration API (current name) |
| `_nmos-registration._tcp` | 3210 | Registration API (legacy name, same service) |
| `_nmos-system._tcp` | 10641 | System API (IS-09) — global config, PTP domain |

## Grouping: host **and port**

Unlike printers or AirPlay — many services, one device — each NMOS service is a
distinct **API role**, and one host commonly runs several. The key has to
separate one case while merging another:

- **Two Node APIs on one host** (`:3212` and `:3300`) are genuinely two nodes.
  Grouping by hostname would hide one.
- **`_nmos-register` and `_nmos-registration` on `:3210`** are one service under
  two names — the spec renamed it and implementations advertise both for
  compatibility. Not merging these makes every registry appear twice.

Host+port does both.

## `api_auth` gets its own column

The TXT record states whether the API requires authorisation. `api_auth=false`
means **an unauthenticated HTTP API is controlling media routing** — worth
seeing at a glance rather than buried in a TXT blob.

As elsewhere, absent ≠ false: a registry that never advertises the key shows
`?`, not `NONE`. Reporting "NONE" would assert a security property nobody stated.

## Versions

`v1.0,v1.1,v1.2,v1.3` becomes `v1.3 (of v1.0, v1.1, v1.2, v1.3)` — clients
negotiate to the highest common version, so that is what leads. Sorting is
numeric, not lexical, so `v1.10` correctly ranks above `v1.9`.

## Addresses

`nmos-cpp` advertises every interface it has, including loopback and IPv6
link-local. Neither helps anyone reach the API, so both are filtered out.

## History

This crate was previously a declared stub with a test asserting
`STATUS == "stub"`, specifically so that implementing it could not pass silently
while the README still called it unimplemented. That test now asserts
`discovery-only`, and the project README was updated in the same change.

## Tests

`cargo test -p openair-nmos` — auth labelling (absent vs false), version
summarising pinned to the real advertisement, and numeric version ordering.
