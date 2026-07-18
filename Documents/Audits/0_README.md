# OPEN-AIR Design Audit — 2026-07-17

A high-level design audit of OPEN-AIR at **v40**: the good, the bad, and the
ugly — measured against the project's actual goal.

> ## 📌 Historical record — many findings are now FIXED
>
> This audit is a **snapshot of 2026-07-17** and is deliberately left as
> written. What it recommended has largely shipped; those parts are now
> documented as features:
>
> - [`README.md`](../../README.md) — the project, its pillars, and status
> - [`contracts/README.md`](../../contracts/README.md) — the contract layer the audit called for
> - [`BackEnd/ComProtocols/README.md`](../../BackEnd/ComProtocols/README.md) — protocol agents, discovery, liveness
> - [`ui/README.md`](../../ui/README.md) — the typed frontend
>
> Resolution status for every finding is in the table below.

## Contents

| File | What it covers |
|---|---|
| [1_Design_Audit.md](1_Design_Audit.md) | The extracted mission statement, the scorecard, and the good/bad/ugly analysis of every subsystem — including the Discovered-tab case study |
| [2_Architecture_Diagrams.md](2_Architecture_Diagrams.md) | Diagrams: data transfer (current vs. target), YAK translation, file/folder structure, folders-make-tabs, the WYSIWYG loop, and the library map |
| [../2026-07-17_Executive_Review_Business_Value.md](../2026-07-17_Executive_Review_Business_Value.md) | The business-value review |
| [../Strategies/](../Strategies/) | The plans that came out of this audit — historical; see their README for what shipped |

## Resolution status

### §4 The Bad

| Finding | Status | Now documented / tracked |
|---|---|---|
| §4.1 Two sources of truth — UI tree (stale `tree.json` snapshot) | ✅ **Fixed** | Browser fetches live `GET /api/tree`; snapshot is only the static-host fallback |
| §4.1 — MQTT topics (three namespaces, config.ini vs hardcoded) | ✅ **Fixed** | One declared topic tree + legacy classifier — `contracts/README.md`; config.ini values now linted |
| §4.1 — duplicate 34401A definitions | ⚠️ **Detected, not repaired** | `openair-validate` reports it as an error; baselined |
| §4.1 — `/ws` side-bus alongside MQTT | ⏳ Open | Phase 4 (retire the side-bus) |
| §4.2 Stringly-typed boundaries with no contracts | ✅ **Fixed** | The whole point of `contracts/` — topics, device records, heartbeats, layout, YAK wire message |
| §4.3 YAK has no capability model | ⏳ Open | Phase 3 (class/model split, WASM core) |
| §4.4 Supervision is a facade — no heartbeats, stubs claim `online` | ✅ **Mostly fixed** | Real `AgentHeartbeat` + MQTT Last Will on every agent and browser session; stubs publish `status = stub` — `BackEnd/ComProtocols/README.md`. Restart/supervision remains Phase 4 |
| §4.5 Frontend platform has no floor | 🔄 **In progress** | `ui/` package builds the entire app with strict TS + lint/CI ratchets; cutover pending — `ui/README.md` |
| §4.6 Three parallel logging systems | ⏳ Open | Phase 4 (`OpenAir/System/Log/…`; `LogEvent` shape already planned) |

### §5 The Ugly

| Finding | Status | Notes |
|---|---|---|
| 1. Hard-coded absolute paths (YAK repo, discovered-GUI builder) | ✅ **Fixed** | Both derive their paths at runtime; the same class of bug was later found and fixed in the VISA knowledge-base loader |
| 2. VISA agent shells out to `python3 -c` | ⏳ Open | Phase 4 (native Rust VXI-11) |
| 3. YAK is transmit-only (replies go nowhere) | ⏳ Open | Phase 3 (reply parsers; NAB requires one by contract) |
| 4. `retain: true` on every publish at 45 Hz | ✅ **Fixed** | Control values publish non-retained; one settle-delayed retained publish preserves late-joiner state |
| 5. Dead things that still bite | 🔄 Partial | `topicUtils.js` deleted; `_Legacy_Commands/`, `*.json.old`, `temp_norm_*` now *reported* by validate |
| 6. Folder-prefix collisions as identity | ⚠️ **Detected, not repaired** | 57 `N_` prefix collisions reported by validate, including at the tree root |

### §6 Case study — "why the Discovered tab is empty"

**✅ Fully resolved.** All four documented breaks plus the latent fifth were
fixed, and two further bugs were found in the process:

| Break | Fix |
|---|---|
| (a) builder subscribed to the wrong topic | Subscribes to what the agents actually publish (visa + midi + dnssd) |
| (b) output path pointed at a phantom directory | Derived from the script's own location |
| (c) nothing ever launched the builder | Orchestrator spawns it after every scan |
| (d) browser read a stale snapshot | Live `GET /api/tree` |
| (5th) builder emitted a dead schema | Emits contract-valid panels, verified against the layout schema |
| *(found later)* VISA knowledge base never loaded — every instrument read "Unknown Instrument" | Walk-up path resolution + knowledge base compiled into the binary |
| *(found later)* orchestrator dropped most retained publishes at boot | Drain runs until the queue flushes — 16/16 protocol statuses now land |

Beyond repair, the tab gained capability: sortable `OcaTable` device tables,
an on-demand **RESCAN** button, and a **dnssd** category from a
newly-real DNS-SD agent (previously a 25-line stub).

## The one-paragraph verdict *(as written, 2026-07-17)*

OPEN-AIR's architecture ideas are genuinely good — a filesystem-driven UI, an
MQTT spine, a verb-based instrument grammar, Rust protocol agents. What is
hurting it is not any single idea but the **absence of contracts between the
ideas**: every boundary (topics, YAK commands, widget types, layout JSON,
config files) is an unchecked string, and nearly every subsystem has quietly
grown **two sources of truth**. The Discovered-tab failure is not a bug; it is
the architecture demonstrating its central weakness in one pipeline. The
TypeScript migration is the right move precisely because its main deliverable
is not "the frontend in a new language" — it is **a single, typed contract
layer shared by the browser, the Rust agents, and the YAK definition plane**.

> **Epilogue.** That contract layer now exists, is enforced in CI, and has
> consumers in the browser, the YAK agent, and the orchestrator.
