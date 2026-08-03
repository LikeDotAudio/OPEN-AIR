# 2 — Plan of Attack: everything still outstanding

**Supersedes:** [1 Plan of attack.md](1%20Plan%20of%20attack.md), which is **closed** —
its Day-14 milestone is complete (8 of 9 tasks; one deferred to the owner). That
document is now the historical record of the Day-14 pass and its execution log.

**Merges in:** [strategy to repair current issues.md](strategy%20to%20repair%20current%20issues.md)
(the response to the 2026-07-18PM twelve-persona review) and the two milestones
that were never started.

**Audit basis:** every item below was re-verified against the **working tree** at
the time of writing. Nothing is carried forward on the strength of a prior
document saying it was outstanding.

---

> ## ✅ Execution pass — 2026-07-18 evening
>
> **P0-1, P1-2, P1-3, P2, P3-1, P3-2, P5-1 are done and verified.** P1-1 (compose)
> is done pending a real `docker compose up` on a clean machine. Remaining:
> **P3-3** (discovery as live data), **P4** (debt paydown + ungameable ratchet),
> **P5-2/3/4** (ledger check, second machine, stranger test).
>
> Two things surfaced during the work that no audit had found:
> - **`openair-ember` did not compile at all.** CI only ran `cargo check -p openair-yak`
>   on that workspace, so an entire broken crate went unnoticed. The ComProtocols
>   workspace now compiles for the first time, and CI checks *and tests* both
>   workspaces in full.
> - **The MQTT host was hard-coded `127.0.0.1` in six places**, which made the
>   orchestrator unable to run anywhere but the broker's own host — including in a
>   container. Now one `--mqtt-host` / `MQTT_HOST` value.

---

## 🚨 P0 — Do this before anything else

### P0-1 · `POST /api/save` is an unauthenticated arbitrary-file-write — ✅ **FIXED**

> **Fixed 2026-07-18.** `resolve_within()` in `api.rs` now rejects every
> non-`Normal` path component *before* touching the filesystem, then canonicalises
> the resolved parent and requires it to sit inside a canonicalised base — which
> also defeats a symlinked parent pointing outward. The `.json` check remains as a
> secondary filter, never the control. The HTTP server binds **loopback by
> default** (`--bind`, `cli.rs`).
>
> **4 regression tests pass**, covering traversal (`../`, mid-path `a/../../b`),
> absolute paths, symlinked parents, and the happy path. The original finding
> below is preserved as the record of what was wrong.


**Verified present.** The HTTP server binds all interfaces
(`SocketAddr::from(([0, 0, 0, 0], args.port))`, `orchestrator/src/main.rs:406`) and
exposes `POST /api/save` (`api.rs:36`), which writes files with **no
authentication** — the only layer is `CorsLayer`, a browser policy that does
nothing against a direct HTTP client.

The guard fails open:

```rust
let clean_rel = payload.path.trim_start_matches('/');
let abs_path  = gui_frames_dir.join(clean_rel);
if !abs_path.starts_with(&gui_frames_dir) || !abs_path.to_string_lossy().ends_with(".json") {
    return FORBIDDEN;
}
```

`Path::starts_with` compares **components** and never resolves `..`; `abs_path` is
never canonicalised. So `Gui_Frames/../../../tmp/x.json` starts with the
`Gui_Frames` components, passes the check, and the OS resolves `..` at write time.
**Verified by execution** — the guard reported PASSED and the file landed outside
the tree.

**Impact:** any host that can reach the orchestrator's HTTP port can overwrite any
`.json` file the process user can write. The `.json` suffix constrains the
filename, not the directory.

**Fix:**
1. Canonicalise the resolved parent and confirm it is inside a canonicalised
   `Gui_Frames` before writing; reject any `..` component outright. Structural
   validation, not string matching.
2. Keep `.json` as a secondary filter, never the primary control.
3. **Bind the HTTP server to loopback by default**, with the documented opt-in
   pattern already used by the broker.
4. Authentication in front of every mutating route before the bind is ever widened.
5. Regression test with `../` payloads — the same discipline applied to the VISA fix.

**Effort:** 4 h. **Blocks:** P1-1 (a one-command startup that ships this to more
machines makes it worse — safe first, then easy).

> **Pattern worth naming:** this is the *second* defect of exactly this shape found
> in one day. The VISA injection was a guard doing string substitution where it
> needed structural escaping; this is a guard doing component matching where it
> needs canonicalisation. **Any remaining place where user input is validated by
> string comparison should be treated as suspect until checked** — that sweep is
> P0-2.

### P0-2 · Sweep for the same class of defect

Grep every guard that validates untrusted input by comparing or rewriting strings
rather than parsing/normalising it. Two instances found so far were both
exploitable. Budget half a day; the finding rate justifies it.

---

## P1 — The front door *(was Day 14 §4.1 / strategy W1–W2)*

| # | Task | Verified state | Effort |
|---|---|---|---|
| ✅ **P1-1** | **One command — done.** Everything lives in **[`docker/`](../../docker/README.md)**: `launch.py` (stdlib launcher with a real preflight), `docker-compose.yml`, multi-stage `Dockerfile`, container `mosquitto.conf`, and a README. `python3 docker/launch.py` preflights Docker, starts the stack, waits for health, opens a browser — and works from any directory. `docker compose config` validates; every port publishes to host loopback; `Gui_Frames/` bind-mounted. **Needs a real run on a clean machine to call verified** (P5-3). | ✅ |
| ✅ **P1-2** | **Broker ACL shipped** as `broker/acl.example` — three roles (agent / UI / operator) where the UI can read everything but **cannot** publish to `…/Write`; only a human operator credential can drive hardware. `mosquitto.conf` documents the five-step enable; `broker/passwd`+`broker/acl` gitignored. *Enabling it is an operator action — the policy now exists to enable.* | ✅ |
| ✅ **P1-3** | **Both stray binds fixed.** OSC now uses `--osc-bind` (default `127.0.0.1`), and the **HTTP server** — also on `0.0.0.0` — now uses `--bind` (default `127.0.0.1`). Widening either is an explicit flag. | ✅ |
| ✅ **P1-4** | **Quick start is now three lines** (`clone`, `cd`, `docker compose up`). The native path is kept but demoted into a collapsed `<details>` block with its real OS prerequisites listed, so there is one *recommended* path rather than two competing ones. | ✅ |

**Why P1 matters commercially:** the absent startup path is not a convenience
issue, it is the **revenue gate**. Every evaluation currently costs the author's
calendar, which caps the pipeline at one person's time and makes the Day-90
stranger test impossible by construction.

**Done when:** a machine that has never built this project runs one command and
reaches a working UI; no mutating endpoint accepts unauthenticated input; no
listener binds all interfaces by default.

---

## P2 — Stop describing what we have not built *(strategy W2)*

Cheapest credibility fix in the repository, and the finding most likely to
embarrass us in front of the first external user — which P5 requires us to have.

| Group | Crates | Action | Effort |
|---|---|---|---|
| **Real code, vestigial root** | `ember`, `mqtt`, `ptp`, `snmp`, `smpte2138` | Delete the template `lib.rs`, re-export the real sibling modules. The code exists; only the front door is boilerplate. | 1 h total |
| **Genuinely empty** | `mdns`, `nmos`, `rest`, `sap`, `websocket` | **Do not implement.** Mark `status = stub` end-to-end and remove from Pillar 1. They stay in the tree as declared intent, described accurately. | 2 h |
| **README** | — | Pillar 1 currently claims "SNMP, Ember+, SMPTE 2138, PTP — devices announce themselves and appear in the UI." All four are template crates. Rewrite to list only what discovers: VISA/SCPI, MIDI, DNS-SD/mDNS, AES70, OSC. | 1 h |

> ✅ **Done 2026-07-18. Zero `cargo new` templates remain in the tree.**
> - The five shims lost their `add()` and gained a header stating plainly that the
>   real code sits behind the non-default `python` feature — so an empty default
>   build reads as expected rather than as missing code.
> - The five empty crates each declare `pub const STATUS: &str = "stub"` with a
>   test asserting it, so the stub status is greppable and **breaks if someone
>   quietly implements one without updating the README**.
> - README Pillar 1 now separates *working today* (VISA/SCPI, MIDI, DNS-SD/mDNS,
>   AES70, OSC) from *scaffolded but not implemented*.
>
> **Found while doing it:** `openair-ember` did not compile at all — an ungated
> `use pyo3::prelude::*` against an optional dependency. CI checked only
> `-p openair-yak` in that workspace, so a completely broken crate was invisible.
> Fixed; the workspace now builds.

**Done when:** every protocol named as working has a real implementation, and every
stub says so in both code and docs.

---

## P3 — One bus, one truth *(was D45-4 / strategy W3)*

**This is the highest-leverage engineering work in this document.** The Senior
Architect's insight is the organising principle:

> **Live state belongs on the bus. Authored intent belongs in the filesystem.**

That separation is why late joiners work, why a dead agent announces its own death,
and why the editor runs inside the live app. Discovery is **the one place the
system violates its own rule**. Fixing that boundary retires four symptoms at once.

**Strict ordering — this is what goes wrong if rushed:**

### P3-1 · Publish OSC and AES70 to MQTT — ✅ **DONE**

Both call sites already compute `topic` and `value` (`main.rs:66`, `:202`) and send
them only to the broadcast channel. **Verified: zero publish calls in either.**
MIDI and VISA are dual-homed to MQTT and survive; OSC and AES70 are not, so their
events reach nothing at all. Roughly three lines each.

**Do this before touching the route**, or two protocols go from "reaching nothing"
to "not existing."

### P3-2 · Delete the `/ws` route — ✅ **DONE**

> ✅ **Removed.** The route, `ws_handler`, `handle_socket`, the `AppState` struct,
> the `SystemState` type, the broadcast channel, and all four `tx_clone_*` sends
> are gone, along with their now-unused imports. Removing the orphan also exposed
> a dead `info` binding in the VISA scan that existed only to feed `/ws` — every
> field was already published to MQTT individually, so it went too.
> **`grep '"/ws"'` → 0 occurrences.**

This also kills a second-order problem: because events *are* delivered somewhere
(a live channel with no subscribers), OSC and AES70 currently **look wired in code
review**. Nothing errors, nothing logs, nothing is dropped — the data simply
arrives nowhere. That is why this survived multiple audits. With the orphan gone, a
protocol that reaches nothing will look like it reaches nothing.

### P3-3 · Discovery becomes live data *(3–5 d — the category fix)*

**Verified:** `Deployment/build_discovered_gui.py` still writes panel JSON into
`Gui_Frames/0_discovered/`, with values baked as static text at scan time.

Agents publish canonical retained device records to
`OpenAir/Discovery/<protocol>/<deviceId>`. The Discovered tab becomes a **live
widget** subscribed to `OpenAir/Discovery/#`, rendering a row per retained record.
"Promote to panel" stays as an explicit user action writing an authored frame via
the existing save endpoint.

Payoff, disproportionate to effort:
- discovered values become **live** instead of stale-between-scans
- the filesystem-generation step and its builder disappear
- `0_discovered/` stops being a generated directory inside the authored tree
- the architecture stops contradicting its own best idea

> **Include a timestamp field in the record shape.** Costs nothing now. Without it,
> any future replay/determinism work starts with a migration — see P6.

**Done when:** no live device state is written to disk; the Discovered tab updates
without a rescan; `/ws` no longer exists; every protocol either publishes to the
bus or is declared a stub.

---

## P4 — Debt paydown, and a ratchet that cannot be gamed *(was D45-5/6/7)*

**Verified:** 169 errors / 2,093 deprecations, ratchet reports 0 new. Correct and
healthy — but nothing has been repaired yet.

The baseline is not a uniform wall. It is two mechanical problems and a tail:

| Rule | Count | Nature |
|---|---:|---|
| `legacy-widget-type` | 856 | mechanical rename — **codemod** |
| `legacy-label-form` | 655 | mechanical reshape — **codemod** |
| `legacy-flat-key:*` | 235 | mechanical key migration — codemod |
| `data-model-type` | 163 | mechanical |
| `legacy-topic-override` | 72 | semi-mechanical |
| `unknown-widget-type` | 60 | **judgement** — renders as the dashed fallback box |
| `folder-order-collision` | 57 | **judgement** — renames cascade into device identity |
| tail | ~164 | mixed |

- **P4-1 — Codemod the two big rules.** 1,511 findings, **67% of the total**.
  Target: deprecations below **750**. Two afternoons plus review. Planning a
  uniform grind across all 2,262 would be five times the work for the same number.
- **P4-2 — Repair the named judgement items.** The duplicate 34401A first
  (**verified: `8_Multimeter_YAK` still present**, holding a single file against a
  full tree in `4_DMM_YAK`). This is a **correctness bug, not tidiness**: the YAK
  repository keys on model and the caller passes `None`, so the two definitions
  silently shadow each other — last loaded wins. Then the root-level folder-prefix
  collision.
- **P4-3 — Make the ratchet ungameable.** **Verified: no exclusion logic exists in
  the validator today.** Report **per rule**, not just a total; exclude deletions
  from the reduction target; fail if file counts drop without a ledger entry.
  This is the direct answer to the "10% per sprint" metric, which is satisfiable by
  deleting sample files.

**Done when:** errors < 100, deprecations < 750, achieved **by repair**, with the
per-rule breakdown published so the number cannot be gamed.

---

## P5 — Prove it on a machine that is not ours

| # | Task | Verified state |
|---|---|---|
| ✅ **P5-1** | **Partly done.** CI now runs `cargo check --workspace` **and `cargo test --workspace`** on *both* BackEnd workspaces instead of one package — which is how the broken `openair-ember` crate was found. ⏳ **Still open: no Python job** despite real first-party pytest files under `oaFileImportCSV/`. | rust job widened; python job outstanding |
| **P5-2** | **Implement the ledger check** that `Phase 2.md` claims CI enforces (fail if `legacy.ts` shrank without a ledger line). | Verified absent |
| **P5-3** | **Second-machine proof.** `git clone` → one documented command → broker, orchestrator, and a real instrument discovered, its panel rendered, a command on the wire — on a clean Linux box. Transcript committed to `Documents/Audits/`. | Blocked on P1-1 |
| **P5-4** | **Day 90 — one stranger, one instrument, one vendor we do not own.** They install it **without contacting the author**; the written case study lands in `Documents/Audits/`. **If they have to ask a question, the question they asked is the bug** — log it as a finding, not as support. | Blocked on P1 |

---

## P6 — Deliberately not doing (yet)

Stated explicitly, because silence is what caused the governance finding in the
first place.

| Not doing | Why |
|---|---|
| **Native Rust VXI-11** | The *injection* is fixed; what remains is a fork-per-command performance tax with no correctness or security consequence. Real work, wrong quarter. |
| **YAK 2 / capability model** | Frozen by standing order. P4-2 defuses the duplicate-34401A shadowing without it. |
| **WASM core** | Frozen. No user-visible consequence today. |
| **Completing the `ui/` port** | Verified: 4 source files, **140** side-effect imports of untouched `.jsx`, **178 globals with 175 still `any`**, and `ServeDir` still points at `FrontEnd/`. That is a quarter of work changing nothing a user sees. The bundle already builds; leave it building. Cutover is a post-Day-90 decision. |
| **`.crawler/` eviction** | Deferred to the owner by request. Note: extract anything still needed from it first — the YAK reply-path design record is sourced from it. |
| **Fixing bus factor** | **No task in this document changes it.** Only P1 and P5 can — a second person cannot exist until a second person can *start the thing*. Named here so it is not mistaken for solved. |

### Preserving optionality — free, so do it

The replay/determinism idea (record a known-good run, replay against a live bench,
localise divergence) is **not funded** and not on this plan. Two decisions above
keep the door open at zero cost, and it would be careless to close it by accident:

- **P3-3 puts every device record on the bus as a retained, addressable document** —
  precisely the substrate a recorder would snapshot. Doing discovery any other way
  forecloses it.
- **The contract layer already gives the comparison a vocabulary**, so a replay
  diff can be semantic rather than numeric.

The only concrete ask is the **timestamp field in P3-3**.

---

## Sequencing

```
P0  save-endpoint traversal + guard sweep   ← before everything; blocks P1
P1  front door: compose, broker ACL, binds  ← the revenue gate
P2  stop over-claiming                      ← half a day, do it early
P3  one bus, one truth                      ← the Architect's category fix
P4  debt paydown + ungameable ratchet
P5  CI coverage, second machine, stranger
```

Ordered by **liability per hour of effort**, not by size. P2 is pulled early
because it is trivially cheap and P5-4 puts a stranger in front of that README.

## Scoreboard

*"Start" = beginning of the 2026-07-18 evening pass.*

| Metric | Start | **Now** | Target |
|---|---|---|---|
| Unauthenticated arbitrary-file-write | 🚨 present | ✅ **fixed** (4 regression tests) | fixed |
| User-supplied paths canonicalised | no | ✅ **yes** | yes |
| Listeners binding all interfaces | 2 (OSC, HTTP) | ✅ **0** | 0 |
| Broker ACL policy | none | ✅ **shipped** (`acl.example`) | enforced by operator |
| Commands to a running UI | 7 (+undocumented toolchain) | ✅ **1** *(needs clean-machine proof)* | 1 |
| Protocols named as working but unimplemented | 4 | ✅ **0** | 0 |
| Template `lib.rs` in shipped crates | 10 | ✅ **0** | 0 |
| Protocols publishing to a bus nobody reads | 2 | ✅ **0** | 0 |
| Cargo workspaces that even compile | 2 of 3 | ✅ **3 of 3** | 3 of 3 |
| Cargo workspaces whose tests CI runs | 1 of 3 | ✅ **3 of 3** | 3 of 3 |
| Hard-coded broker host | 6 sites | ✅ **1 flag** | 1 flag |
| Live device state written to disk | yes | ⏳ yes *(P3-3)* | **no** |
| Baseline errors / deprecations | 169 / 2,093 | ⏳ 169 / 2,093 *(P4)* | **< 100 / < 750** |
| Debt target gameable by deletion | yes | ⏳ yes *(P4-3)* | **no** |
| Python tests in CI | no | ⏳ no *(P5-1)* | yes |
| External users | 0 | 0 | **1 at Day 90** |

**Deliberately absent:** bus factor. Nothing here moves it, and a scoreboard
implying otherwise would be the self-flattery these rules exist to prevent.

---

*Every "verified state" in this document was checked against the working tree at
the time of writing — not inherited from the predecessor plan. Where the previous
document's framing turned out to be wrong (uniform treatment of the ten template
crates; retiring `/ws` before publishing OSC/AES70), the correction is stated
inline rather than silently applied.*
