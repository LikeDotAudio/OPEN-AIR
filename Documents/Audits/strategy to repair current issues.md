# Strategy to Repair Current Issues

**Responds to:** [2026-07-18PM Executive Review](../Executive_Review_Business_Value/2026-07-18PM_Executive_Review_Business_Value.md)
**Method:** every point raised by the twelve personas was re-audited against the
**working tree only** — no history, no archives, no logs. Each finding below is
marked ✅ verified, ⚠️ partly true, or ❌ rejected, with the evidence that decided
it. Nothing is accepted because a persona said it.

> ## 🚨 One finding outranks the entire review
>
> The audit turned up a defect **no persona raised**: `POST /api/save` is an
> **unauthenticated arbitrary-file-write reachable from any host on the network**.
> The path guard uses `Path::starts_with` on an unnormalised path, so `..` is never
> resolved and traversal passes the check — **verified by execution**, not by
> reading. See [N3](#n3-in-full--path-traversal-in-the-save-endpoint).
>
> It is now **W1-0**, ahead of every other task here. It is the same class of bug as
> the VISA injection fixed earlier today: a guard that performs string matching
> where it needs structural validation.

**Related:** [1 Plan of attack.md](1%20Plan%20of%20attack.md) (the Day-14 pass already
executed) · [Design audit](../notes/1_Design_Audit.md) · [Diagrams §7](../notes/2_Architecture_Diagrams.md#7-current-state--2026-07-18)

---

## Part I — The audit

### I.1 Findings verified

| # | Finding | Evidence |
|---|---|---|
| **F1** ✅ | ~~**No one-command startup.**~~ **Fixed 2026-07-18** — see [`docker/`](../../docker/README.md): `python3 docker/launch.py`. *Original finding:* no Dockerfile, compose file, or Makefile anywhere; quick start was 7 commands and never mentioned `corepack`/`pnpm install`, so the typed frontend was outside the documented path entirely. |
| **F2** | **`allow_anonymous true`, no ACL.** | `broker/mosquitto.conf` — anonymous is on; safety rests solely on the `127.0.0.1` bind. No `acl_file` anywhere, so any client reaching the bus may publish any topic, including the ones that drive hardware. |
| **F3** | **10 of 15 protocol crates are `cargo new` templates.** | `ember`, `mdns`, `mqtt`, `nmos`, `ptp`, `rest`, `sap`, `smpte2138`, `snmp`, `websocket` all still assert `2 + 2`. Only `aes70`, `dnssd`, `midi`, `osc`, `visa` have real `lib.rs`. |
| **F4** | **The README over-claims.** | Pillar 1 lists "SNMP, Ember+, SMPTE 2138, PTP — devices announce themselves and appear in the UI." All four are template crates. The Status table further down *is* honest; the pillar is not, and the pillar is what people read. |
| **F5** | **`/ws` is routed with zero consumers.** | Route exists at `orchestrator/src/main.rs:392`. Nothing in `FrontEnd/` or `ui/src` opens a WebSocket to it — the only `/ws` matches in the browser code are prose about MQTT-over-WebSocket transport, a different path (port 9001). |
| **F6** | **OSC and AES70 reach nothing.** | Both build a `SystemState { topic, value }` (`main.rs:66`, `:202`) and send it *only* to the broadcast channel. MIDI and VISA also publish to MQTT (`:184`, `:256`) and therefore survive; OSC and AES70 do not. |
| **F7** | **Discovery launders live data through the filesystem.** | `Deployment/build_discovered_gui.py` writes panel JSON into `Gui_Frames/0_discovered/`. Values are baked as static text at scan time, so a "live" discovered reading shows whatever was true when the scan ran. |
| **F8** | **`ui/` is a wrapper, not a port.** | 4 source files. `legacy.ts` is **140 side-effect imports of untouched `FrontEnd/*.jsx`**. `globals.d.ts` records **178 globals, 175 still `any`**. The served runtime is still `FrontEnd/` (`ServeDir`, `main.rs:402`). |
| **F9** | **VISA forks a Python interpreter per command.** | Still `python3 -c` per probe and per write. The *injection* is fixed (argv), the *fork* is not. |
| **F10** | **2,093 deprecations + 169 errors unpaid.** | Ratchet reports 0 new — correct and healthy — but nothing has been repaired. |
| **F11** | **Bus factor 1.0.** | Nothing in the tree changes this. The contract layer improves *transferability*, which is a different property. |
| **F12** | **Zero external users, nothing shipped.** | Correct, and not disputed. |

### I.2 Findings partly true — the nuance changes the fix

| # | Finding as stated | What is actually true |
|---|---|---|
| **F3a** | "Ten crates are boilerplate" | ⚠️ Two different situations. **Five** (`ember`, `mqtt`, `ptp`, `snmp`, `smpte2138`) have a template `lib.rs` **but real sibling modules** — they are pyo3 shims, so the code exists and the crate root is vestigial. **Five** (`mdns`, `nmos`, `rest`, `sap`, `websocket`) are genuinely empty. The first group needs a 10-minute re-export; the second needs a decision. Treating all ten identically wastes effort on five and under-treats the other five. |
| **F5a** | "Retire the `/ws` side-bus" | ⚠️ Retiring the route is the *second* step. The first is F6 — OSC and AES70 must publish to MQTT before the route is deleted, or two protocols go from "reaching nothing" to "not existing." Order matters. |
| **F10a** | "Pay down the debt" | ⚠️ 67% of it is **two mechanical rules**: `legacy-widget-type` (856) and `legacy-label-form` (655) = 1,511 of 2,262. These are codemoddable. The remaining third needs judgement. Planning a uniform grind across all 2,262 would be five times the work for the same number. |

### I.3 Findings rejected or reframed

| # | Claim | Verdict |
|---|---|---|
| **R1** | Resistant Engineer: *"the ratchet means CI ignores the debt forever"* | ❌ **Rejected.** Baselining is how you stop the bleeding while you triage; you cannot pay down what you never measured. The legitimate half of his complaint is that nothing has been paid *yet* — that is F10, and it is scheduled. |
| **R2** | Resistant Engineer: *"the old way shipped on every push, now it asks permission"* | ❌ **Rejected as a defect, kept as a constraint.** Gating on tests is the point. Every-branch publishing was deliberate and is preserved — the gate blocks *broken* pushes, not *branches*. |
| **R3** | CTO: *"10% baseline reduction per sprint"* | ❌ **Rejected as a metric.** As the CEO noted, it is satisfiable by deleting sample files. Replaced by per-rule targets that exclude deletions — see W4. |
| **R4** | Jaded Engineer: *"we moved from unauthenticated remote to unauthenticated local, which is progress, not safety"* | ✅ **Accepted, and sharper than it sounds.** This is F2 and it is the top of the plan. |

### I.4 New findings — raised by nobody, found during this audit

| # | Finding | Evidence |
|---|---|---|
| **N1** | **The OSC agent binds all interfaces.** | `OscAgent::new("0.0.0.0".to_string(), 8000)` (`main.rs:60`). The broker was bound to loopback; this listener was not. Any host on the network can inject OSC events into the orchestrator. Same class of exposure the broker fix addressed, in a second place nobody looked. Note AES70, MIDI, and DNS-SD all correctly use `127.0.0.1` — OSC is the lone outlier. |
| **N2** | **The `/ws` orphan makes F6 invisible.** | Because `SystemState` events *are* delivered somewhere (a live broadcast channel with no subscribers), OSC and AES70 look wired in code review. Nothing errors, nothing logs, nothing is dropped — the data simply arrives nowhere. This is why F6 survived multiple audits. |
| **N3** 🚨 | **`POST /api/save` is an unauthenticated arbitrary-file-write, reachable from any host.** | See below — this is the most severe finding in the audit and was raised by nobody. |

#### N3 in full — path traversal in the save endpoint

The HTTP server binds **all interfaces** (`SocketAddr::from(([0, 0, 0, 0], args.port))`,
`main.rs:406`) and exposes `POST /api/save` (`api.rs:36`), which writes files. There
is **no authentication** — the only layer is `CorsLayer`, and CORS is a browser
policy, not access control; it does nothing against a direct HTTP client.

The endpoint's guard (`api.rs`) is:

```rust
let clean_rel = payload.path.trim_start_matches('/');
let abs_path  = gui_frames_dir.join(clean_rel);
if !abs_path.starts_with(&gui_frames_dir) || !abs_path.to_string_lossy().ends_with(".json") {
    return FORBIDDEN;
}
```

**`Path::starts_with` compares path *components* and does not resolve `..`, and
`abs_path` is never canonicalised.** So `/repo/FrontEnd/Gui_Frames/../../../tmp/x.json`
literally begins with the components of `Gui_Frames` and passes the check. The
operating system then resolves `..` at `fs::write` time, and the write lands
outside the tree.

**Verified by execution**, not by reading:

```
guard: PASSED (thinks it is inside Gui_Frames)
wrote: ptdemo/repo/FrontEnd/Gui_Frames/../../../outside/ESCAPED.json
$ find ptdemo -name ESCAPED.json
  ptdemo/outside/ESCAPED.json          ← landed OUTSIDE Gui_Frames
```

**Impact.** Any host that can reach the orchestrator's HTTP port can overwrite any
`.json` file the process user can write — `package.json`, `tsconfig.json`, any
config, any application state. The `.json` suffix constrains the filename, not the
directory, and on most machines there is at least one `.json` a process reads with
authority. It also silently overwrites (it takes a `.old` backup first, which is a
courtesy to the attacker as much as the user).

**This is the same class of defect as the VISA injection fixed earlier today** — a
guard that *looks* like validation but is doing string/component matching on
unnormalised input. It deserves the same treatment: make the check structural
rather than textual.

---

## Part II — The strategy

### II.0 The organising insight

The Senior Architect identified the root cause and it is worth stating plainly,
because it collapses four separate complaints into one fix:

> **Live state belongs on the bus. Authored intent belongs in the filesystem.**

That separation is the best thing in this design — it is why late joiners work, why
a dead agent announces its own death, and why the editor can run inside the live
app. **F7 is the one place the system violates its own rule**, taking live bus data
and writing it into the authored tree as generated files.

Fixing that boundary retires F7 *and* the "discovery is a broken pipeline"
complaint *and* the stale-values complaint *and* removes the reason
`Gui_Frames/0_discovered/` has to be gitignored-but-generated. **One category fix,
four symptoms.** It is the highest-leverage work in this document, and it is why
W3 is sequenced ahead of the cosmetic items despite being larger.

### II.1 Sequencing rationale

Four workstreams, ordered by *liability per hour of effort*, not by size:

```
W1  Front door        →  Day 14   security + the thing blocking every evaluation
W2  Stop over-claiming→  Day 14   cheapest credibility fix in the repo (~half a day)
W3  One bus, one truth→  Day 45   the Architect's category fix; retires 4 symptoms
W4  Debt paydown      →  Day 45   67% is two codemods; do the cheap two-thirds
```

W2 is pulled *forward* from the CEO's Day-45 assignment because it costs almost
nothing and is the finding most likely to embarrass us in front of the first
external user — which Day 90 requires us to have.

---

### W1 — The front door *(Day 14)*

**Answers:** F1, F2, N1 · Lazy Engineer, Jaded Engineer, CFO risks #2 and #4

| Task | What | Effort |
|---|---|---|
| **W1-0** 🚨 | **Fix the `/api/save` path traversal (N3) — do this before anything else in this document.** Replace the textual guard with a structural one: `canonicalize()` the *parent* directory and confirm the result is inside a canonicalised `Gui_Frames` before writing; reject any component that is `..`; keep the `.json` check as a secondary filter, not the primary control. Then **bind the HTTP server to loopback by default** with the same documented opt-in as the broker, and put authentication in front of every mutating route before it is ever widened. Add a regression test with `../` payloads — the same discipline applied to the VISA fix. | 4 h |
| **W1-1** | **`docker compose up`.** Three services — broker, orchestrator, UI. The compose file *is* the documentation; it cannot drift from reality the way a 7-command README can. | 1 day |
| **W1-2** | **Close the broker properly.** `allow_anonymous false`, a password file, and — the part that matters — an **ACL** so an authenticated UI client still cannot publish to `…/Write`. Today safety is one line (`bind 127.0.0.1`); after this it is defence in depth. | 4 h |
| **W1-3** | **Bind the OSC listener** to loopback by default (N1), with the same documented opt-in pattern as the broker. Audit every other `0.0.0.0` in the tree while in there. | 1 h |
| **W1-4** | **Rewrite the quick start** against the compose path, and delete the 7-command sequence rather than leaving both. Two documented ways to start is how one of them rots. | 2 h |

**Definition of done:** a machine that has never built this project runs one
command and reaches a working UI; **no mutating endpoint accepts unauthenticated
input, and no path derived from user input is trusted without canonicalisation**;
no service accepts anonymous connections from off-box; no listener binds all
interfaces by default.

> **Sequencing note.** N3 displaces W1-1 as the first task. A one-command startup
> that ships an unauthenticated arbitrary-file-write to more machines makes the
> problem worse, not better — the easier this is to run, the more urgent it is that
> running it is safe. Ship W1-0 first, then make it easy.

**Why this first:** F1 is not a convenience issue, it is the **revenue gate**. Every
evaluation currently costs the author's calendar, which caps the pipeline at one
person's time and makes the Day-90 stranger test impossible by construction.

---

### W2 — Stop describing what we have not built *(Day 14 — pulled forward)*

**Answers:** F3, F3a, F4 · Jaded Engineer, CFO risk #3 (certification overhang)

The CEO's instruction was "delete the template or remove the protocol from our own
front page — I do not care which." Given F3a, the honest answer differs per crate:

| Group | Crates | Action | Effort |
|---|---|---|---|
| **Real code, vestigial root** | `ember`, `mqtt`, `ptp`, `snmp`, `smpte2138` | Delete the template `lib.rs`, re-export the real sibling modules. The code exists; only the front door is boilerplate. | 1 h total |
| **Genuinely empty** | `mdns`, `nmos`, `rest`, `sap`, `websocket` | **Do not implement.** Mark `status = stub` end-to-end and remove them from Pillar 1 of the README. They stay in the tree as declared intent, described accurately. | 2 h |
| **Documentation** | — | Rewrite Pillar 1 to list only what discovers: VISA/SCPI, MIDI, DNS-SD/mDNS, AES70, OSC. Move the rest to a "planned" line. The Status table is already honest — make the pillar match it. | 1 h |

**Definition of done:** every protocol named as working in the README has a real
implementation, and every stub says so in both the code and the docs.

**Why pulled forward:** it is half a day, it removes a compliance liability the CFO
flagged, and Day 90 puts a stranger in front of that README.

---

### W3 — One bus, one truth *(Day 45)*

**Answers:** F5, F5a, F6, F7, N2 · the Architect's gem, the Jaded Engineer's third paragraph

**Strict ordering — this is the part that goes wrong if rushed:**

**W3-1 — Publish OSC and AES70 to MQTT *(half a day)*.** Both call sites already
compute `topic` and `value` (`main.rs:66`, `:202`); they simply never publish. This
is roughly three lines each — clone an MQTT client into those tasks and publish
alongside the existing channel send. **Two protocols start working.** Do this before
touching the route, or F6 turns into "deleted."

**W3-2 — Delete the `/ws` route *(1 h)*.** Once nothing produces to it uniquely, the
route, the `SystemState` broadcast channel, and the handler all go. This also kills
N2: with the orphan gone, a protocol that reaches nothing will *look* like it
reaches nothing.

**W3-3 — Discovery becomes live data *(3–5 days — the category fix)*.**
Agents publish canonical retained device records to
`OpenAir/Discovery/<protocol>/<deviceId>`. The Discovered tab becomes a **live
widget** subscribed to `OpenAir/Discovery/#`, rendering a row per retained record —
not a generated panel file. "Promote to panel" stays as an explicit user action that
writes an authored frame via the existing save endpoint.

The payoff is disproportionate to the effort:

- discovered values become **live** instead of baked-at-scan-time (F7)
- the filesystem-generation step disappears entirely, along with the builder
- `Gui_Frames/0_discovered/` stops being a generated directory inside the authored tree
- the architecture stops contradicting its own best idea

**Definition of done:** no live device state is written to disk; the Discovered tab
updates without a rescan; `/ws` no longer exists; every protocol either publishes to
the bus or is declared a stub.

---

### W4 — Debt paydown, the honest version *(Day 45)*

**Answers:** F10, F10a, R3 · Resistant Engineer's legitimate half

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

- **W4-1 — Codemod the two big rules.** 1,511 findings, 67% of the total. Target:
  deprecations **below 750**. Two afternoons plus review.
- **W4-2 — Repair the named judgement items.** The duplicate 34401A first: one
  definition tree is complete, the other holds a single file. Because the YAK
  repository keys on model and the caller passes `None`, the two **silently shadow
  each other** — this is a correctness bug, not tidiness. Then the root-level
  folder-prefix collision.
- **W4-3 — Make the ratchet ungameable.** Report **per rule**, not just a total;
  exclude deletions from the reduction target; fail if file counts drop without a
  ledger entry. This is the direct answer to R3 — a target that cannot be hit by
  deleting sample files.

**Definition of done:** errors < 100, deprecations < 750, achieved by repair, with
the per-rule breakdown published so the number cannot be gamed.

---

### W5 — The stranger test *(Day 90)*

Unchanged from the verdict, and entirely dependent on W1. Someone outside the
building installs it **without contacting the author**, discovers a real instrument,
renders its panel, and puts a command on the wire. The written case study lands in
`Documents/Audits/`.

**If they have to ask a question, the question they asked is the bug** — log it as a
finding, not as support.

---

## Part III — What we are deliberately not doing

Stated explicitly, because silence is what got the project in trouble before.

| Not doing | Why |
|---|---|
| **Native Rust VXI-11 (F9)** | The *injection* is fixed; what remains is a fork-per-command performance tax with no correctness or security consequence. Real work, wrong quarter. Revisit after Day 45. |
| **YAK 2 / capability model** | Frozen by standing order. W4-2 defuses the duplicate-34401A shadowing without it. |
| **WASM core** | Frozen. No user-visible consequence today. |
| **Completing the `ui/` port (F8)** | 140 files and 175 `any` globals is a quarter of work that changes nothing a user sees. The bundle already builds; leave it building. Cutover is a decision for after Day 90, not a Day-45 task. |
| **Fixing bus factor (F11)** | No task in this document changes it. Only W1 and W5 can — a second person cannot exist until a second person can *start the thing*. Named here so it is not mistaken for solved. |

### Preserving the Quant's optionality — free, so do it

The replay idea (record a known-good run, replay against a live bench, localise
divergence) is **not funded** and not on this plan. But two decisions above happen
to keep the door open at zero extra cost, and it would be careless to close it by
accident:

- **W3-3 puts every device record on the bus as a retained, addressable document.**
  That is precisely the substrate a recorder would snapshot. Doing discovery *any*
  other way would foreclose it.
- **The contract layer already gives the comparison a vocabulary** — a replay diff
  can be semantic rather than numeric.

**One cheap guardrail:** when defining the `OpenAir/Discovery/…` record shape in
W3-3, include a timestamp field. Costs nothing now; without it, every future replay
feature starts with a migration.

---

## Part IV — Scoreboard

| Metric | Now | After W1–W2 (Day 14) | After W3–W4 (Day 45) |
|---|---|---|---|
| Commands to a running UI | 7 (+undocumented toolchain) | **1** | 1 |
| **Unauthenticated arbitrary-file-write (N3)** | 🚨 **present** | **fixed** | fixed |
| Services accepting anonymous off-box connections | broker: loopback-only; **OSC + HTTP: all interfaces** | **0** | 0 |
| User-supplied paths canonicalised before use | no | **yes** | yes |
| Broker ACL | none | **enforced** | enforced |
| Protocols named as working but unimplemented | 4 | **0** | 0 |
| Template `lib.rs` in shipped crates | 10 | **0** | 0 |
| Protocols publishing to a bus nobody reads | 2 | 2 | **0** |
| Live device state written to disk | yes | yes | **no** |
| Discovered values stale between scans | yes | yes | **no** |
| Baseline errors / deprecations | 169 / 2,093 | 169 / 2,093 | **< 100 / < 750** |
| Debt target gameable by deletion | yes | yes | **no** |
| External users | 0 | 0 | 0 → **1 by Day 90** |

**Deliberately absent from this table:** bus factor. Nothing here moves it, and a
scoreboard that implied otherwise would be the same self-flattery the ratchet rules
exist to prevent.

---

*Every finding in Part I was verified against the working tree at the time of
writing. Where a persona's claim did not survive that check it is recorded in §I.3
as rejected, with reasoning — and where the audit found something no persona raised,
it is recorded in §I.4.*
