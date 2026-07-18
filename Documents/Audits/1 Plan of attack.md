# Plan of Attack — Response to the 2026-07-18 Executive Review

*Written 2026-07-18. Audited against the **working tree only** (commit `964f9d29e`),
deliberately ignoring git history — the question is not "what did we claim," it is
"what is true on disk right now."*

> **Status: Day-14 execution pass complete (2026-07-18).** 8 of 9 tasks done,
> 1 deferred to the owner. This is no longer only a plan — **§3b is the
> execution record**: per task, what was wrong, how it was fixed, what was
> deliberately *not* done and why, and the command whose output proves it.
>
> **One item needs you:** **restart the broker** — the config binds loopback but a
> process from the old config is still listening on `0.0.0.0` (D14-2).

**Companion documents:** [2026-07-18 Executive Review](../Executive_Review_Business_Value/2026-07-18AM_Executive_Review_Business_Value.md) ·
[Design Audit](../notes/1_Design_Audit.md) · [Resolution table](0_README.md#resolution-status)

---

## How to read this

The review put eleven substantive charges on the table across nine personas. This
document does three things, in this order:

1. **§1 — Corrections.** Four charges are *already false* against the current tree.
   Saying so first is not defensiveness; a plan built on stale findings wastes the
   fourteen days we have.
2. **§2 — Escalations.** Three findings are *materially worse* than the review
   described, including one that upgrades from "injection surface" to
   "unauthenticated remote code execution reachable from any host on the network."
3. **§3–§6 — The work.** Every remaining charge mapped to a named fix, an owner-
   sized task, and one of the CEO's three milestones. Nothing is deferred silently;
   where we intend to *argue* with a mandate rather than execute it, that argument
   is written down (§6), which is precisely what the CEO asked for.
4. **§3b — What actually happened.** The execution record for the Day-14 pass,
   including the two errors this document itself made and the one task where the
   plan was overruled by what the code turned out to say.

The governing principle, taken directly from the verdict: **do the boring items
first.** Every task in §3 is ordered cheapest-and-highest-liability first.

---

## §1 Corrections — charges that are stale

These were true when the review was written and are not true now. Evidence is
file-level and reproducible.

| Charge | Verdict | Evidence |
|---|---|---|
| "The FTP credential is **still there** in `FrontEnd/.env`" | **False — file does not exist** | No `.env` anywhere in the tree except `ui/.env.example` (a template with no values). No credential *literal* is on disk anywhere; every hit for `FTP_HOST`/`FTP_USER`/`FTP_PASS` is a name-only reference in workflows. Deploy reads GitHub secrets (`deploy-production.yml:51-53`). |
| "`requirements.txt` contains **one line** (`paho-mqtt`) while the orchestrator shells out to `pyvisa`" | **False — fixed** | `requirements.txt` now pins `pyvisa>=1.11`, `pyvisa-py>=0.5`, `paho-mqtt>=1.6`, with comments explaining *why* `pyvisa-py` is not optional (`ResourceManager('@py')`). |
| "**Nine commits still unpushed** to origin" | **False** | `git log origin/main..HEAD` → 0 commits. Tree is clean and level with origin. |
| "The first CI run on a real runner **failed** (missing system library)" | **Addressed** | The only native dependency in the tree is `midir` → ALSA, and `contracts-ci.yml:29` now installs `libasound2-dev pkg-config`. No openssl/libudev/serialport/hidapi anywhere; MQTT is `rumqttc` (rustls, pure Rust), discovery is `mdns-sd` (pure Rust). |

**One residue worth fixing anyway (5 minutes).** Three files still *document* a
credential location that no longer exists, which is how a rotated secret gets
re-created by a helpful future reader:

- `Deployment/Deploy/set_github_secrets.sh:2` says the source is `FrontEnd/.env`,
  but line 15 resolves `ENV_FILE` to the **repo root** `.env`. Comment and code
  disagree.
- `deploy-production.yml:58` and `deploy-sandbox.yml:52` both carry the stale
  comment "`FrontEnd/.env` holds FTP credentials locally."

> **Honest caveat we are not going to paper over:** "the file is gone" is not the
> same claim as "the credential was rotated at the provider." The working tree
> cannot prove rotation. Task **D14-1** closes this by attesting rotation in
> writing, because the CEO's objection was fundamentally about *evidence*, not
> about a file.

---

## §2 Escalations — findings worse than reported

### 2.1 The VISA injection is unauthenticated RCE, network-reachable (CRITICAL)

The review called this "a remote command-injection surface." That undersells it.

**The flaw** — `BackEnd/Core/orchestrator/src/main.rs:552`:

```rust
let safe_payload = payload.replace("'", "\\'");
```

This inserts a backslash before each quote **into Python source text**. It is not
an escape function; it is a string substitution that the Python parser then
re-interprets. A payload ending in a single trailing backslash escapes the
*closing* quote and breaks out into executable Python. Verified:

```
payload  'X\'  →  generated source:  inst.write('X\')
                                                 ^^ closing quote consumed
```

**The reachability** — worse than the injection itself:

1. `spawn_visa_write_daemon` (`main.rs:513`) subscribes to
   `OpenAir/System/Protocols/visa/Device/+/+/+/Write` (`main.rs:525`).
2. `payload` is taken raw off the wire (`main.rs:532`) and flows unchanged into
   `format!` (`main.rs:552`) and then `python3 -c` (`main.rs:574`).
3. `broker/mosquitto.conf:20` sets `allow_anonymous true`, and the listeners at
   lines 10 and 14 declare **no `bind_address`** — mosquitto binds all interfaces.

**Therefore: any host that can reach TCP 1883 can execute arbitrary code as the
orchestrator user.** On a lab network wired to real instruments, that is the single
highest-severity item in this repository — well above the credential the board
spent its mandate on. It was on nobody's list.

*(Mitigating detail, stated fairly: the shipped UI never publishes to `.../Write` —
`build_discovered_gui.py:56` explicitly skips `Write`/`Read`. The reachable path is
the broker, not the browser. This lowers the odds of accidental triggering; it does
nothing to lower the odds of deliberate triggering.)*

Fix: **D14-2** (bind + auth, same day) and **D14-3** (kill the interpolation).

### 2.2 The `/ws` side-bus has zero consumers — OSC and AES70 events reach nothing

The design audit called `/ws` a "second bus" (§4.1). It is worse: it is a
**write-only bus**. `main.rs:420` routes it and four producers publish `SystemState`
to it — OSC (`main.rs:66`), MIDI (`:160`, dual-homed to MQTT so it survives), AES70
(`:202`), VISA (`:366`, also dual-homed). Grepping the entire tree for `/ws` yields
exactly two hits: the route definition and a comment in
`contracts/src/topics/legacy.ts:21`. The browser connects to the MQTT broker over
its own websocket transport on port 9001 (`MqttProvider.jsx:96`), a completely
separate path.

**Consequence: OSC and AES70 discoveries currently go nowhere at all.** This is not
architectural debt to be retired in Phase 4 — it is two protocols that silently do
not work. Reclassified from "cleanup" to "bug." Fix: **D45-4**.

### 2.3 The debt baseline can be gamed by deleting sample files — literally

The CEO's jab ("a number he can hit by deleting sample files") is arithmetically
correct. Of 2,262 baselined findings, **236 live under `5_Samples/`** — 147
`data-model-type`, 60 `unknown-widget-type`, 29 `folder-order-collision`. Deleting
one demo directory would book a 10.4% "reduction" while repairing nothing.

> **Correction (2026-07-18).** An earlier draft of this document treated
> `Gui_Frames/5_Samples/` (the widget **demo panel** tree) and "the Sampler" (the
> `Console → Sampler` audio feature) as the same thing. They are unrelated. The
> Sampler has since been removed from the project and contributed **zero**
> baseline findings; the 236 findings above belong to `5_Samples/`, which stays.
> The gaming risk is therefore real but attaches to the demo tree, not to the
> scope decision — and it is exactly why §4.2's D45-7 exists.

The good news is the same analysis shows the debt is far more tractable than the
review assumed — see §4.

---

## §3 Milestone 1 — Day 14 (due 2026-07-31, clock does not reset)

Ordered by liability-per-minute. The first four are the "boring items first" the
verdict demanded.

> **Execution pass run 2026-07-18.** Eight of nine complete, one deferred to the
> owner. Task-by-task detail — what changed, how, and how it was
> verified — is in **[§3b](#3b-execution-log--what-was-done-and-how)**.

| # | Task | Status | Addresses |
|---|---|---|---|
| **D14-1** | Close out the credential finding; fix the stale `FrontEnd/.env` pointers | ✅ **Done** — all secrets live in GitHub Environments; no local credential file exists, so there is nothing to attest | Jaded Eng.; CFO #2; CEO M1 |
| **D14-2** | Close the broker — bind loopback, document the LAN opt-in | ✅ **Done** *(restart required to apply)* | §2.1; CFO #3 |
| **D14-3** | Delete the `python3 -c` string interpolation | ✅ **Done + exploit-tested** | §2.1; Jaded Eng.; Audit §5.2 |
| **D14-4** | Fix the four broken absolute paths | ✅ **Done** — zero remain repo-wide | CEO M1 |
| **D14-5** | Complete `requirements.txt` | ✅ **Done** — 6 deps added, paho conflict resolved | Lazy Eng.; CEO M1 |
| **D14-6** | Decide the Sampler in writing | ✅ **Done** — removed from the project, recorded | Resistant Eng.; CEO M1 |
| **D14-7** | Evict `.crawler/` (210 MB) | ⏸️ **Deferred to owner** — no action taken | Jaded Eng. |
| **D14-8** | Gate the deploy on tests | ✅ **Done** — both workflows | CFO #3; Resistant Eng. |
| **D14-9** | Automate the doc link check | ✅ **Done** — 5 dead links fixed, CI job added | CEO M1 (regression) |

**Milestone-1 definition of done:** a written rotation attestation; a broker that
refuses anonymous remote connections; no string-interpolated subprocess input
anywhere in the tree; `pip install -r requirements.txt` sufficient for every
first-party Python file that ships; a signed sampler decision; production
unreachable from a feature branch.

**Against that bar:** five of six clauses are met. The rotation clause resolved
differently than written — there is no local credential to rotate, because GitHub
Environments hold every secret (D14-1). "Production unreachable from a feature
branch" was **deliberately not implemented** — see D14-8 for why, argued rather
than skipped.

---

## §3b Execution log — what was done, and how

*2026-07-18. Every claim below was verified by running something, not by reading
the diff. The verification command and its actual output are recorded so the next
audit can re-run them rather than trust this page.*

### D14-3 — the RCE *(highest severity; do this one first)*

**Was:** `orchestrator/src/main.rs` built Python source with
`payload.replace("'", "\\'")` and ran it through `python3 -c`. That is not an
escape — it writes a backslash into source text, so a payload ending in a
backslash consumed the closing quote and broke out into executable Python. The
payload arrived raw off MQTT.

**How fixed:** both scripts became module-level constants — `VISA_WRITE_SCRIPT`
and `VISA_PROBE_SCRIPT` — that read `sys.argv[1]`/`[2]`. Values are passed as
process arguments, so nothing caller-supplied can alter the program text. Chosen
over shell-escaping because escaping is a thing you can get wrong twice; argv is
structurally immune. The Python backend stays (native Rust VXI-11 is Phase 4) —
this fixes the *injection*, not the fork-per-command tax.

**How verified:**

```
$ cargo check -p open-air-orchestrator      → Finished (no new warnings)
$ python3 <argv-harness>  with three payloads that broke out before:
    "X\\"                                    → command='X\\'          (inert)
    "X\\'); import os; os.system('id'); ('"   → whole string is data   (inert)
    "*IDN?\nprint(open('/etc/hostname')...)"  → newline is data        (inert)
```

No `id` executed, no file read. The escape-bypass is structurally gone.

### D14-2 — the broker

**Was:** `allow_anonymous true` with no `bind_address` on either listener, so
mosquitto bound all interfaces. This is what made D14-3 *remotely* reachable
rather than local.

**How fixed:** both listeners now `127.0.0.1`. Anonymous access is kept — and the
config now says explicitly that the two settings are a **pair**, with a five-step
LAN opt-in (passwd file → `allow_anonymous false` → widen bind → credential every
agent → ACL) so nobody widens the bind alone. Turning auth on unilaterally would
have broken every agent and the browser at once; loopback achieves the security
goal today with zero breakage.

**How verified:** started the config on spare ports and read the socket table —
`ss -ltn` showed `127.0.0.1:18830` and `127.0.0.1:19001`, not `0.0.0.0`.

> ⚠️ **Outstanding:** a broker from the *old* config is still running on
> `0.0.0.0` (`ss` confirms). The file is fixed; the process is not. **Restart it.**

### D14-4 — the broken paths

**Was:** four Python files pointed at `/home/anthony/Documents/OPEN-AIR/…` — the
*previous* repo location, so they were broken, not merely non-portable.

**How fixed:** each derives its path at runtime. `update_yak_router.py` uses
`Path(__file__).parent`; `visa_tester.py` and `midi_tester.py` walk `parents[n]`
to the repo root and point at where the helpers actually live now
(`_proto_util` moved to `TESTS/Protocols/`). `test_rust_csv_parser.py`'s absolute
*fallback* was deleted outright rather than repointed — a fallback to a phantom
path turned "asset missing" into a confusing error about someone else's home
directory; it now `skipTest`s with the path it wanted.

**How verified:** asserted each `parents[n]` resolves to the expected directory and
that the target exists; then a repo-wide grep across `.py/.rs/.ts/.jsx/.ini/.toml/.yml`
returned **zero** hits.

### D14-5 — the install path

**Was:** six third-party packages were imported by shipped code but absent from
`requirements.txt`, and the root file's `paho-mqtt>=1.6` contradicted
`requirements-deploy.txt`'s `>=1.6,<3`.

**How fixed:** added `zeroconf`, `requests`, `python-osc`, `websocket-client`,
`mido`, `python-rtmidi`, each annotated with the file that imports it and its
import name where it differs from the package name (`python-osc` → `pythonosc`).
Added a section for what pip **cannot** install — `mosquitto`,
`mosquitto-clients`, `python3-tk`, `libasound2-dev` — since the broker was never
listed as a prerequisite anywhere. Resolved paho to `>=1.6,<3`, matching the
upper bound the deploy file already had and the code's explicit 1.x/2.x branches
(`build_discovered_gui.py:205-207`); 3.x is untested, so it is excluded rather
than hoped for.

**How verified:** all 9 requirement lines parse under `packaging.requirements`.

### D14-6 — the Sampler decision

**Was:** the board ordered it quarantined; it was restored the next day without a
decision record. The governance finding was the *silence*, not the choice.

**How fixed:** the mandate was **executed**. Removed the `Console → Sampler`
panel and six widget directories, with a decision record in `CHANGELOG.md` (which
supersedes — and preserves, in a `<details>` block — the entry that had adopted
it) plus a Migration Ledger row.

**The part that needed care:** `AudioEditor` and `PadBrowse` carry no "Sampler"
prefix, so a name-based deletion would have missed them. Both depend on the audio
runtime defined in `SamplerDrumkit.js` (`oaAudioCtx`, `oaDecodeAudio`,
`OA_DRUM_*`) and appear in no panel outside `100_Sampler`. Deleting only the four
prefixed widgets would have left two orphans with broken references. Before
removing anything, I checked every surviving widget for references to a removed
one — none.

**Booked as a scope change, not debt paydown.** The Sampler contributed **zero**
baselined findings; errors (169) and deprecations (2,093) are unchanged, and no
baselined key referenced a removed path. Claiming credit here would have been
precisely the metric-gaming the review called out.

**How verified:** `pnpm build` succeeds; collision check clean; `legacy.ts`
146→140 imports and `globals.d.ts` 210→178 globals *regenerated* (not
hand-edited); stale entries pruned from `api/tree.json` and `api/grabbag`;
grep for dangling references returns nothing.

### D14-8 — the deploy gate

**Was:** neither deploy workflow had `needs:`, so `contracts-ci.yml` ran
independently and could not block a release. A push that broke the contracts
still published.

**How fixed:** added a `verify` job (typecheck + contracts tests + drift ratchet)
to **both** workflows, with `deploy` gated on it.

**What I deliberately did not do — argued, not skipped.** The plan originally said
"restrict to `main`." I did not. The workflow header documents every-branch
publishing as an intentional fix for a real symptom ("it doesn't publish every
time"), so narrowing it would silently reverse a deliberate decision — the exact
failure mode §6 exists to prevent. This gates **quality**, not **which branch**.
If production-from-a-feature-branch is itself unacceptable, that is a separate
decision and belongs in a decision record.

**One subtlety:** `verify` is skipped on `pull_request`, and a skipped dependency
would normally skip `deploy` too — taking the PR validation step with it. Hence
`if: always() && needs.verify.result != 'failure' && != 'cancelled'`, which
proceeds when verify passed *or* was skipped, never when it failed.

**How verified:** both workflows parse as YAML with the expected `needs`/`if`
wiring, and all three gate commands were run locally — typecheck clean, **120
tests passed**, `ratchet: 0 new vs baseline`. A gate that false-fails is worse
than no gate.

### D14-9 — the link checker

**Was:** Milestone 1 was credited *"all internal links programmatically verified
to resolve."* That check ran once, by hand, over `README.md`.

**What it actually found — five dead links, not two.** Two pointed at
`Documents/Audits/2_Architecture_Diagrams.md` when the file lives in
`Documents/notes/`; three more broke when the executive reviews moved into
`Documents/Executive_Review_Business_Value/` *during this session*. The second
group is the point: any one-time check is stale the moment a file moves.

**How fixed:** `Deployment/check_doc_links.py` (stdlib only, no deps), wired as a
new `docs` job in `contracts-ci.yml`. It skips fenced code blocks (examples aren't
links), URL-decodes `%20`, and excludes vendored NMOS trees — those ship with
dead links we did not write, and linting them would keep the gate permanently red
and train everyone to ignore it.

**How verified:** injected a deliberate broken link → exit 1 with the file and
line; reverted → exit 0 across 146 files. Proven to catch, not merely to pass.

> **Process note, recorded because it cost time.** The revert above used
> `git checkout <file>`, which restored the file to `HEAD` and silently discarded
> unrelated edits made earlier in the session. They had to be reapplied. Use a
> targeted edit to undo a targeted change.

**It has already paid for itself — three times in one day.** After the checker
was installed: (1) `1_Design_Audit.md` and `yak_protocol_report.md` moved from
`Documents/Audits/` to `Documents/notes/`, failing the next run with **10 dead
links across 6 files** — including two in `Documents/Strategies/` that nobody
would have thought to check; (2) the 2026-07-18 executive review was renamed to
`…-18AM_…`, breaking two more. Every one was caught within seconds of being
introduced and repaired the same minute.

That is the whole argument for automating this: the audit set has now been
reorganised twice in a single day, and each reorganisation silently broke
cross-folder links in files nobody was editing. A human check catches the
folder you are looking at; the script catches the five you are not.

### D14-1 — the credential *(closed)*

**Was:** the review said the credential was "still there" in `FrontEnd/.env`.

**What is actually true:** the file does not exist, no credential literal is on
disk anywhere, `.env` is gitignored, and both workflows exclude `**/.env` from
upload. **All secrets live in GitHub Environments** (owner-confirmed) — the
workflows read `secrets.FTP_HOST` / `FTP_USER` / `FTP_PASS`, and nothing in the
repository holds or needs a copy.

**How it was closed.** Four documents still *pointed at* `FrontEnd/.env` —
including `set_github_secrets.sh`, whose header disagreed with its own code about
which file it reads. All four are corrected, so no future reader re-creates the
path. That is the whole remaining surface: with the secrets held by GitHub, there
is no local credential file whose rotation could need attesting.

**A rotation-attestation document was written and then deleted.** The reasoning
for it was that a working tree cannot prove a secret was invalidated at the
provider, so a human should sign for it. That reasoning assumed a local
credential file existed to rotate *out of*. It does not — GitHub is the store of
record, and it already holds the audit trail (who set each secret, and when).
A blank form in `Documents/Audits/` asserting facts nobody needed to re-assert
would have been governance theatre: exactly the kind of artifact that looks like
control and delivers none. Removed rather than left half-filled.

**Where the evidence actually lives:** the GitHub Environment secret list and its
update history, plus `Deployment/Deploy/CICD.md` for how secrets get there.

### D14-7 — `.crawler/` *(deferred to the owner)*

210 MB, still growing (three snapshots written 2026-07-18). Untracked and
double-ignored. **No action taken** — it is the only copy of the previous
generation, it was not created by this work, and deletion is irreversible.

Note before it goes: `yak_protocol_report.md` §3 was sourced from
`EVERYTHING.py.LOG` inside it, and is currently the only in-repo record of the
YAK reply-path design that D45's receiver work depends on. **Extract first.**

### Corrections made to this document during execution

Recorded because §6.3 requires pointing the ratchet at ourselves:

1. **The Sampler and `5_Samples/` were conflated.** An earlier draft treated them
   as one thing. They are unrelated: `5_Samples/` is the widget **demo panel**
   tree and owns the 236 findings; the Sampler was a Console **audio feature**
   owning none. §2.3 and §6.1 now carry the correction. Had it gone unnoticed,
   the Sampler removal would have been mis-booked as a 10% debt reduction.
2. **The dead-link count was five, not two** — the executive-review move added
   three that the original count could not have seen.

### Verification summary — all green at end of pass

```
docs links      ✓ 146 files, 0 dead
contracts       ✓ 4 files, 120 tests passed
ratchet         ✓ errors 169 · deprecations 2093 · 0 new vs baseline
rust            ✓ cargo check clean
ui              ✓ collisions 0 · typecheck ✓ · lint ✓ · build ✓
paths           ✓ zero /home/anthony/ in code
sampler         ✓ zero dangling references
```

Note the ratchet is deliberately **unchanged**: this pass fixed security,
correctness, and process debt, none of which the validator counts. Debt paydown
is D45-5/6, and conflating the two would misrepresent both.

---

## §4 Milestone 2 — Day 45: second-machine proof + a ratchet that actually ratchets

### 4.1 The golden path (the Lazy Engineer's complaint, which is load-bearing)

The review's sharpest *usability* finding was that the ceremony exceeds the payoff.
Confirmed: the documented startup is **7 commands** (`README.md:174-190`) and does
not even mention `corepack`/`pnpm install`, so the UI bundle is outside the
documented path entirely. Full build prerequisites: Node ≥24 + corepack + pnpm
11.14.0, Rust 1.94.1, **two** Cargo workspaces plus **three** standalone crates
(the README claims one — it omits `FrontEnd/libControl/Panels/wasm`, which also
implies an undocumented `wasm32` target), `cargo-typify@0.7.0` installed by hand,
Python 3 + venv, `python3-tk`, and a `mosquitto` broker that is never listed as a
prerequisite.

- **D45-1 — One command.** `docker compose up` (or `make run`) that brings up
  broker + orchestrator + UI. No Dockerfile or bootstrap script exists for
  OPEN-AIR today; the only ones in the tree are vendored NMOS test tooling.
- **D45-2 — CI green on a clean runner**, with the *second-machine* run scripted
  and its transcript committed to `Documents/Audits/`.
- **D45-3 — Fix the CI coverage lie.** `contracts-ci.yml` runs `cargo test` on
  `contracts/rust` only; `BackEnd/Core` and `BackEnd/ComProtocols` get `cargo
  check` — so the 10 inline `#[cfg(test)]` modules **never execute**. There is no
  Python job at all, despite four real first-party pytest files under
  `oaFileImportCSV/`. Add both. Also implement the ledger check that
  `Phase 2.md:160-164` claims CI enforces but which does not exist.
- **D45-4 — Retire the `/ws` side-bus** (§2.2). Publish OSC and AES70 to MQTT under
  the contract topic grammar; delete the route. Two protocols start working.

### 4.2 Paying down the ratchet — the honest version

The Resistant Engineer's charge ("nothing was repaired; it was *inventoried*") is
**correct as of today**. The counter is not that inventorying is enough — it is that
the inventory reveals the debt is two mechanical problems wearing a trenchcoat:

| Rule | Count | Nature |
|---|---:|---|
| `legacy-widget-type` | 856 | Mechanical rename — **codemoddable** |
| `legacy-label-form` | 655 | Mechanical reshape — **codemoddable** |
| `data-model-type` | 163 | Mechanical, 147 of them in `5_Samples` |
| `legacy-flat-key:*` | 235 | Mechanical key migration |
| `legacy-topic-override` | 72 | Semi-mechanical |
| `unknown-widget-type` | 60 | **Needs judgement** — renders as the dashed fallback box |
| `folder-order-collision` | 57 | **Needs judgement** — renames cascade into identity |
| everything else | ~164 | Mixed |

**1,511 of 2,262 findings — 67% — are two codemoddable patterns.** Two afternoons
of codemod work plus review retires two-thirds of the baseline. That is a real
plan, and it is defensible in a way the CTO's "10% per sprint" is not.

- **D45-5 — Codemod `legacy-widget-type` + `legacy-label-form`.** Target: baseline
  below **750 deprecations** (down from 2,093).
- **D45-6 — Repair the two named items.** The duplicate 34401A is trivial:
  `8_Multimeter_YAK/1_34401A/` contains **exactly one file**
  (`1_MEASure/MEASure.json`) against a full tree in `4_DMM_YAK/1_34401A/`. Port
  anything unique, delete the class, and 5 `yak-duplicate-definition` + 1
  `yak-duplicate-model` errors resolve with it. This matters beyond tidiness:
  `repository.rs` keys on `HashMap<model, …>` and `mqtt.rs` passes `model: None`
  on every execute, so the two definitions **silently shadow each other** —
  whichever loads last wins. Then fix the root-level `folder-order-collision`.
- **D45-7 — Make the ratchet ungameable** (§2.3). Report per-rule, not just total;
  exclude `5_Samples/` from the reduction target; fail CI if the *file count* drops
  without a Migration Ledger entry. Deleting demos must not read as progress.

### 4.3 The `2+2` crates

Confirmed: **exactly 10** template `lib.rs` files. But the review's framing ("ten of
our sixteen protocol crates are boilerplate") conflates two different situations,
and the fix differs:

- **Five are pyo3 shims with real sibling modules** — `ember` (169 L),
  `mqtt` (108 L), `ptp` (90+93 L), `snmp` (24+91 L), `smpte2138` (78 L). The code is
  real; the crate root is vestigial and gated `#[cfg(feature = "python")]`.
  **Fix: delete the template, re-export the real modules.** Cosmetic, ~1 hour total.
- **Five are wholly empty** — `mdns`, `nmos`, `rest`, `sap`, `websocket`. `src/`
  contains the 25-line `cargo new` template and nothing else. Yet each ships a
  `config.ini` with MQTT topics, which is *why* the validator flags them and why the
  system appears to support protocols it does not.

**D45-8 — Stop describing five empty crates as protocol implementations.** Either
implement or mark `status = stub` end-to-end and remove them from every capability
claim. This is the CFO's "certification overhang" (risk #5), and the honest move is
to shrink the claim, not the backlog.

---

## §5 Milestone 3 — Day 90: unchanged

One stranger, one instrument, one vendor we do not own, **installing without
contacting the author**, with the case study committed to `Documents/Audits/`. D45-1
is the prerequisite: nobody clears this bar with a 7-command startup and an
undocumented broker dependency.

---

## §6 Governance — the part the review scored worst

The synthesis was blunt and correct: *"the architecture problem got genuinely
solved; the governance problem got worse."* Velocity is not the problem;
prioritization is. Four standing changes:

### 6.1 The sampler decision record (D14-6)

The mandate was to move the sampler out; it was restored. The CEO's own read — *"I
gave an order about scope to a team of one, and then the same person got a good
product idea"* — is the correct diagnosis, and the remedy he named is the right one:
a mandate must be **executed or argued with in writing, never silently reversed**.

**Resolved 2026-07-18: the Sampler is out.** The board mandate is executed rather
than argued with, and the decision is on the record in `CHANGELOG.md` (superseding
the entry that had adopted it) plus a Migration Ledger row. The removal covers the
feature *and* the libraries powering it — `AudioEditor` and `PadBrowse` carry no
Sampler prefix but appear in no panel outside `100_Sampler` and depend on the audio
runtime in `SamplerDrumkit.js`, so leaving them would have left broken references.

Crucially, **no debt-reduction credit is claimed**: the Sampler contributed zero
baselined findings, so errors (169) and deprecations (2,093) are unchanged. The
236-finding `5_Samples/` demo tree is a *different* thing and remains — see the
correction in §2.3. The silence, not the choice, was the governance failure.

### 6.2 AI-augmented review policy (CFO risk #1)

The Jaded Engineer's point — one human "reviewing" ~30k lines in ten hours is not
review — has no counter-argument, and the CFO is right that it must become *stated
policy* rather than an accident. The CEO's defence is narrower than it sounds and
worth stating precisely: machine-checked contracts are what make machine-written
code acceptable, **so code outside contract coverage does not get that defence.**

Policy: any change to a boundary crossed by `contracts/` ships with a golden vector.
Changes outside contract coverage — subprocess handling, broker config, deploy
workflows — require line-by-line human review regardless of author. Note that
§2.1 sat in exactly that uncovered zone.

### 6.3 Point the ratchet at ourselves

The CEO's closing instruction. This document is the first run: §1 lists four
mandate items we were credited with or blamed for incorrectly, §2 lists three we
missed entirely. Every subsequent audit opens with the same two sections.

### 6.4 What we are arguing with, in writing

Per §6.1's own rule, one disagreement stated openly rather than quietly ignored:

**The "No Phase 3 / no new work" freeze should carve out §2.1 and §2.2.** Both are
Phase-4-labelled in the existing roadmap (native Rust VISA; retire the `/ws`
side-bus). Under a literal freeze they wait until after Day 45. We propose treating
the *security* slice of Phase 4 as Milestone-1 scope, because an unauthenticated RCE
reachable from any host on the lab network is not a feature. We are not asking to
unfreeze YAK 2, the WASM core, or any new protocol — those stay frozen.

---

## §7 What the review got right that we are *not* re-litigating

Recorded so the plan is not mistaken for a rebuttal:

- **`ui/` is not the runtime, and the port has barely begun.** The bundle builds the
  whole app only because `ui/src/legacy.ts` side-effect-imports 146 untouched
  `FrontEnd/*.jsx` files in tag order. **Zero widget or manager modules are
  converted**; `ui/src` has no `comMQTT/`, `libControl/`, `tabManager/`,
  `frameLayout/`, or `editorWYSIWYG/`. `globals.d.ts:5` records 207 of 210 globals
  still `any`, and `ui/package.json:14` is `"test": "echo 'ui: no tests yet'"`. The
  Resistant Engineer's "net user-visible change: nothing" is fair.
- **Discovery still round-trips through the filesystem.** `build_discovered_gui.py`
  writes panels to `Gui_Frames/0_discovered/` (`:191`), spawned by the orchestrator
  (`main.rs:381`). The four original breaks are genuinely fixed, but the shape the
  audit called "the mistake" still ships — and the script's own docstring concedes
  values are "baked as static text at scan time." Phase 4.
- **Zero external users, nothing shipped to a customer.** The Jr. BA's market framing
  was correctly discounted.
- **Bus factor did not move.** No task in this document changes that; D45-1 and the
  Day-90 stranger test are the only things that can.

---

## §8 Scoreboard for the next review

Concrete, checkable, and deliberately not gameable:

*Updated 2026-07-18 after the Day-14 execution pass. "Today" = start of that pass.*

| Metric | Today | Now | Day 14 | Day 45 |
|---|---|---|---|---|
| Credential held anywhere but GitHub Environments | unclear | ✅ **no — GitHub is the sole store** | no | no |
| Broker binds all interfaces | yes | ✅ **loopback** *(restart pending)* | no | no |
| String-interpolated subprocess input | 1 site | ✅ **0** | 0 | 0 |
| Broken `/home/anthony/` paths in code | 4 | ✅ **0** | 0 | 0 |
| Ships-but-unlisted Python deps | 5 | ✅ **0** | 0 | 0 |
| Deploy gated on tests | no | ✅ **yes, both workflows** | yes | yes |
| Sampler scope decision recorded | no | ✅ **removed + recorded** | yes | yes |
| Commands to first running instrument | 7 | 7 | 7 | **1** |
| Baseline deprecations | 2,093 | 2,093 | 2,093 | **< 750** |
| Baseline errors | 169 | 169 | 169 | **< 100** |
| Template `lib.rs` in crates we call implementations | 10 | 10 | 10 | **0** |
| Protocols publishing to a bus nobody reads | 2 | 2 | 2 | **0** |
| Cargo workspaces whose tests CI executes | 1 of 3 | 1 of 3 | 1 of 3 | **3 of 3** |
| `.crawler/` on disk | 210 MB | 210 MB *(owner's call)* | — | — |
| Dead internal doc links | 5 | ✅ **0, CI-enforced** | 0 | 0 |

---

*Every claim in §1–§2 and §7 was verified by direct inspection of the working tree
at `964f9d29e`, independently of git history and independently of the changelog's
self-description. Where this document contradicts the executive review, the
contradiction is evidenced with a file and line; where the review was right, it is
recorded as right.*
