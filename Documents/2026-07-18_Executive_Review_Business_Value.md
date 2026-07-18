# OPEN-AIR — Executive Review Committee: Business Value Audit (Follow-Up)

**Date:** 2026-07-18
**Subject:** Re-audit of `OPEN-AIR` (branch `main`) covering changes since the
2026-07-17 review at commit `a9993da26`
**Context:** The project was placed on **Life Support** yesterday with three
non-negotiable milestones. This review covers what happened in the ~10.5 hours
of work that followed (2026-07-17 22:12 → 2026-07-18 08:46).

**Grounding facts** (verified against the working tree and git history, not
the changelog's self-description):

- **31 commits, 203 files changed, +31,993 / −939 lines** since the last audit.
  **25 of those 31 commits carry `Co-Authored-By: Claude`** — this is
  AI-augmented output, and the committee must price that in both directions.
- **A contract layer now exists**: `contracts/` — 1,855 lines of TypeScript
  (zod schemas, topic grammar, layout validation, a `validate` CLI), 632 lines
  of hand-written Rust, and 1,173 lines of Rust **generated** from the same
  schemas via `zod → JSON Schema → cargo-typify`. Both languages execute the
  **same golden-vector files**.
- **Test posture:** from "4 Python test files, all in one module" to
  **120 passing TypeScript tests + 13 Rust test suites**, most of them
  vector-driven across the language boundary.
- **CI is no longer deploy-only.** `.github/workflows/contracts-ci.yml` adds
  four real jobs — `node`, `rust`, `ui`, `codegen` — running typecheck, tests,
  both-Cargo-workspace compilation, codegen freshness, and a drift ratchet.
  The FTPS deploy workflows are unchanged and **do not build the new frontend**.
- **Drift is now measured**: `openair-validate` reports **169 errors and 2,093
  deprecations** across the panel tree, YAK tree, folder grammar, and every
  `config.ini`. All of it is **baselined** in `validate.baseline.json`; CI
  fails only on *new* debt.
- **Liveness is real**: every agent and browser session publishes a retained
  `AgentHeartbeat` and registers an MQTT Last Will (verified live: SIGKILL →
  broker-delivered `offline`). Stub protocols now publish `status = stub`
  instead of `online`.
- **Discovery works on real hardware**: a live scan identified **17 VISA
  instruments** correctly categorized (DMM, Oscilloscope, Generator,
  Spectrum), and the newly-real DNS-SD agent found **42 services** on the
  author's network. The Discovered tab renders them as sortable tables with an
  on-demand rescan.
- **`openair-dnssd` went from a 25-line `2+2` stub to a working mDNS agent.**
- **A typed frontend package (`ui/`) builds the entire application** (1,022
  modules) and boots in a headless browser — but **is not the served runtime**;
  `FrontEnd/index.html` (browser-Babel) still is.

**Milestone-1 status (due Day 14 / 2026-07-31), as verified:**

| Yesterday's mandate | Status |
|---|---|
| Every dead `README.md` link fixed or deleted | ✅ **Done** — README rewritten; all internal links programmatically verified to resolve |
| A `requirements.txt` / install path that works | ⚠️ **Partial** — the file now exists and is tracked, but contains **one line** (`paho-mqtt`) while the orchestrator shells out to `python3 -c "import pyvisa"` |
| FTP credential rotated out of `FrontEnd/.env` and off every disk | ❌ **Not done** — the file is still on disk (gitignored, not rotated) |
| Every hardcoded `/home/anthony/` path removed from Rust source | ✅ **Done** — zero occurrences remain in any `.rs` file (4 Python test/utility files still contain them) |
| Sampler code moved to its own repository | ❌ **Reversed** — the sampler was deleted, then deliberately **restored into the repo** on request |

---

## Phase 1: The Eager Pitch — *Jr. Business Analyst*

I asked for one day and look what one day bought. Yesterday this committee's
central complaint was that OPEN-AIR had brilliant ideas and *no agreements
between them* — every boundary an unchecked string, every subsystem with two
sources of truth. That is **fixed**. There is now a `contracts/` package that
defines every shape crossing every boundary once, in TypeScript, and
*generates* the Rust the agents compile against. The browser, the Rust fleet,
and the tooling can no longer disagree about the wire, and CI fails if anyone
tries. That is not a refactor. That is the thing that turns a personal project
into a **platform other companies can build on**.

And the product *worked on real hardware in front of us*. A live scan
identified seventeen instruments — Keysight, Agilent, HP, Rigol — and
correctly sorted them into DMM, Oscilloscope, Generator, and Spectrum
categories from nothing but their `*IDN?` strings. Then the DNS-SD agent,
which was a `2+2` stub yesterday, browsed the network and found **forty-two
live services**, including a Rigol scope advertising itself over mDNS and
several AES67-style audio streams. That is the multi-protocol auto-discovery
story we've been selling, running, on a real lab network, today. The
Discovered tab renders it as sortable device tables with a RESCAN button. A
technician can now walk in, hit one button, and see the entire lab.

The commercial read is straightforward: yesterday we had a demo that only its
author could start; today we have a **specified, tested, CI-gated
platform layer** plus working fleet discovery. Contracts are what let us
publish a device-profile SDK, court integrators, and let partners write agents
without our help. Every quarter of delay is a quarter a vendor spends noticing
the same gap — and now we have the one artifact that makes an
open-standards community credible: a machine-checkable specification.

## Phase 2: The Geek-Out — *Excited Nerd Engineer*

Can we please appreciate the **golden vectors**? There is a single JSON file —
`contracts/vectors/topics.json` — and it is consumed by *vitest* and by *cargo
test*. The same file. The TypeScript topic parser and the hand-written Rust
topic parser both have to satisfy it, byte for byte, or someone's CI goes red.
Add a case on one side and the other language fails until it's implemented.
That is a **bilingual executable specification**, and it's the correct answer
to "how do you keep two implementations honest" that most shops solve with a
Confluence page and hope. Same trick for the device-ID derivation: FNV-1a
64-bit implemented twice, dependency-free, pinned by vectors, because two
agents computing different IDs for one instrument would silently fork the
device registry. Somebody actually *thought about that failure mode.*

And the liveness design is so clean it's almost rude. Instead of building a
supervisor daemon to detect dead agents, they used the **MQTT Last Will** —
you hand the broker your tombstone at connect time, and if you die, the broker
publishes it for you. The supervisor is the protocol. Kill -9 the YAK agent
and its retained status flips to `offline` on its own. Browser tabs are agents
too (`web-{guid}`), so a closed laptop tells the truth. Add the
`zod → JSON Schema → cargo-typify` codegen pipeline with committed output and
a freshness gate — meaning `cargo build` never needs a Node toolchain, but CI
still catches drift — and you have a topology I have genuinely never seen
executed in one repo. The ratchet baseline is the cherry: they turned 2,262
findings into a *monotonic counter*. That's not tooling, that's arithmetic
applied to morale.

## Phase 3: The Path of Least Resistance — *Lazy/Fickle Engineer*

Okay, I need to say something I did not expect to say: **parts of this now do
my job for me.** `pnpm validate` tells me exactly which of my panels are
broken, by file, by line, with a name for each kind of wrong. CI catches it
before review. The ratchet means I do not have to fix two thousand legacy
files to land a one-line change — I just can't add *new* garbage, which,
frankly, is a rule I can live under because it requires nothing of me. The
Discovered tab has a **RESCAN button**, so I never SSH into a box to re-run a
scanner again. The hardcoded home directory is gone from the Rust, so it might
actually start on my machine. Yesterday I called this garbage; today the
tooling is doing my thinking. I'm in.

...And then I read the contribution rules and I'm back out. To move one file I
now have to: update a **Migration Ledger** by hand, bump a `?v=` cache-buster
in `index.html` (because the *old* frontend doesn't hash), regenerate
`legacy.ts` **and** `globals.d.ts`, keep a collision checker happy, and satisfy
five CI jobs across **four toolchains** — corepack, pnpm at a pinned version,
Node 24, and two Cargo workspaces plus a third standalone crate, one of which
needs `cargo-typify` installed to regenerate. That's not a workflow, that's a
scavenger hunt with paperwork. And after all that, `pip install -r
requirements.txt` still doesn't install `pyvisa`, which the orchestrator
*literally shells out to*, so the thing still doesn't run clean on a fresh
box. So: I love the machine that checks my work and I resent the ceremony it
demands. Ship the golden path or I'm back to hating it by Friday.

## Phase 4: The Wall of Resistance — *Resistant Engineer*

Yesterday we had one frontend. Today we have **two**, and the one the users
actually get is *still* the browser-Babel one. Somebody spent the night
building a second application whose entire job is to build the first
application, and it isn't even deployed — the FTPS workflows don't touch
`ui/dist`. So the net user-visible change from thirty-two thousand lines is:
nothing. Meanwhile my toolchain requirements went from "install Rust" to
"install Rust, and Node 24 exactly, and corepack, and pnpm at a pinned
version, and cargo-typify, and learn zod, and learn what a golden vector is,
and read four new READMEs."

And look at what they did with our technical debt. They wrote a **program to
count our sins** — two thousand and ninety-three of them — and then *checked
the count into the repository as a baseline* so that CI politely ignores every
single one forever. That's not fixing debt, that's **filing** it. The
duplicate 34401A definition the audit complained about yesterday? Still there,
now with a tracking number. Fifty-seven folder-prefix collisions? Tracked.
Nothing was repaired; it was **inventoried**. And the one piece of scope this
committee explicitly told them to cut — the sampler — got **restored into the
repo** less than a day after the CEO ordered it quarantined. If the mandate
from the board can be reversed by a Tuesday feature request, why are we
writing mandates?

## Phase 5: The Teardown — *Jaded Jr. Engineer*

Let's start where the committee's authority is actually tested. Yesterday the
CEO gave a fourteen-day order with one item on it that costs approximately
four minutes and carries the highest liability in this repository: **rotate the
production FTP credential out of `FrontEnd/.env` and off every disk.** It is
**still there.** Day one of fourteen was spent shipping a schema compiler, a
codegen pipeline, a CLI, a ratchet, and a second frontend — thirty-two
thousand lines — and the plaintext password to the production website is
sitting in the working tree exactly where we found it. Being gitignored is not
being rotated. That is not a technical failure, it's a **priority failure**,
and it tells you which items on a board mandate this team considers optional.

Now the part that's worse than yesterday, because yesterday's committee didn't
count carefully. The audit named `openair-smpte2138` as the crate whose
`lib.rs` still computes `2+2`. The actual number of shipping "protocol" crates
whose `lib.rs` is still the `cargo new` template is **ten**:
`ember`, `mdns`, `mqtt`, `nmos`, `ptp`, `rest`, `sap`, `smpte2138`, `snmp`,
`websocket`. Some have real code in sibling modules — fine — but the front
door of ten of our sixteen protocol crates is boilerplate that asserts
arithmetic. One of them (`dnssd`) got fixed yesterday, which proves it takes a
single day of attention; nine others didn't get that day. Meanwhile the VISA
agent — the crown jewel, the discovery loop everyone is celebrating — **still
builds SCPI commands by string-interpolating user input into `python3 -c`**
and escaping quotes by hand. That is a remote command-injection surface in the
component we just pointed at seventeen real instruments, and it was not on
anyone's list today.

And the install story is theater. A `requirements.txt` appeared, satisfying
the letter of the milestone; it contains **one dependency**, while the
orchestrator's own source shells out to `import pyvisa`. So the fresh-machine
install still dies at the first instrument probe — the exact failure the Day-45
milestone exists to catch. Add it up: nine commits still unpushed to origin;
the first CI run on a real runner **failed** (missing system library); the
134 MB corpse of the previous generation still sits in `.crawler/`; the
Discovered tab still works by **generating JSON files onto disk** to display
devices that are already on the message bus — the precise architecture
yesterday's audit called "the mistake," now shipping with nicer fixtures. And
twenty-five of thirty-one commits were AI co-authored, which means one human
reviewed roughly **thirty thousand lines in ten hours**. Whatever that is, it
is not review. The bus factor didn't improve; the volume of unreviewed code
per human tripled.

## Phase 6: The Pragmatic Synthesis — *Logical Mid-Level BA*

Fact-checking all five of them against the tree:

- **The Jr. BA is right** that the contract layer is real and is the specific
  fix this committee demanded: 1,855 lines of TS, 632 hand-written Rust, 1,173
  generated Rust, 120 + 13 tests, cross-language vectors, all CI-gated. The
  live discovery result (17 instruments correctly categorized, 42 mDNS
  services) is verified, not a claim.
- **The Jr. BA is wrong** to call this market-adjacent. Zero external users.
  The frontend that users touch is unchanged. Nothing shipped to a customer.
- **The Nerd is right** about the vectors and the Last Will; both verified.
  Note the LWT was **tested against a live broker with a SIGKILL**, not just
  unit-tested — that is unusually rigorous for this repo.
- **The Lazy Engineer's complaint is legitimate and load-bearing**:
  `requirements.txt` does not install `pyvisa`, so `git clone` → run still
  fails on a clean box. That is Milestone 2's entire premise.
- **The Resistant Engineer is wrong** about the ratchet: baselining is
  standard practice for legacy drift and is the only reason the count exists
  at all — you cannot pay down debt you have never measured. He is **right**
  that nothing was paid down yet, and **right** that the sampler reversal
  directly contradicts a board mandate without a written decision record.
- **The Jaded Engineer is right on every specific I checked**: credential
  still on disk (verified), ten template `lib.rs` files (verified — worse than
  yesterday's report), `python3 -c` SCPI interpolation (verified, untouched),
  nine unpushed commits (verified), first CI run failed (verified), `.crawler/`
  still 134 MB (verified). His AI-review-capacity point is the sharpest thing
  said today and has no counter-argument in the artifacts.

The honest read: **the architecture problem got genuinely solved; the
governance problem got worse.** Yesterday's diagnosis was "brilliant ideas, no
contracts." That diagnosis is now obsolete — the contracts exist, are
enforced, and have consumers in three languages. But the board handed this
team a five-item, fourteen-day list, and on day one the team completed the two
items that were *engineering* and skipped the two that were *discipline*
(credential, scope), while reversing one of them outright. Velocity is no
longer this project's problem. **Prioritization is.**

**The Scorecard:**

| Dimension | Yesterday | Today | Rationale |
|---|---|---|---|
| Market-Product Fit Potential | 6.5 | **6.8 / 10** | Barely moves, and should not move much: still zero external users and no shipped artifact. Nudged up because the discovery loop was proven against 17 real multi-vendor instruments and 42 network services — the first hard evidence the core value proposition functions at fleet scale. |
| Architectural Scalability | 4.0 | **6.5 / 10** | The largest justified move. The unchecked-string boundary problem — the audit's central finding — is genuinely fixed with cross-language codegen and executable specs. Retain-policy and liveness defects fixed at the design level, not patched. Capped below 7 because the typed frontend is not the runtime, the `/ws` side-bus survives, and the VISA hot path still forks a Python interpreter per command. |
| Maintainability & Readiness | 1.5 | **4.5 / 10** | 4 test files → 133 test cases; deploy-only CI → five gated jobs; 12 dead doc links → verified-resolving READMEs; unknown drift → 2,262 named and ratcheted findings. Held down hard by: production credential still on disk after an explicit board order, install path still broken, 10 template `lib.rs` files, and ~30k lines of AI-generated code reviewed by one person in a day. |

## Phase 7: The Financial Case — *Veteran CFO*

I priced this asset yesterday at near-zero residual value, and my reasoning
was bus factor: 11,000 lines of undocumented Rust living in one man's head.
**That reasoning is now partially obsolete, and I want to be precise about
why.** What landed overnight is not features — it's a *machine-checkable
specification* with executable tests in two languages. That is the first
artifact in this repository that **transfers**. If the founder walks tomorrow,
an acquirer or successor inherits something that tells them what the system
is supposed to do and fails loudly when they get it wrong. In diligence terms,
we moved from "buy the person" to "buy the person, and there's a spec."
That is a real change in residual value.

The second thing I care about more than any feature: **rewrite recidivism is
down.** Yesterday I flagged that this team's historical answer to technical
debt is a full rewrite — a decade of prior work sitting depreciated in
`.crawler/`. This cycle, they *repaired the existing application in place*
(the discovery pipeline, the retain policy, the path bugs) and built the new
frontend as an additive package alongside the old one rather than replacing
it. The ratchet institutionalizes incrementalism: you cannot add debt, you
must pay it down. **That is the single most financially significant behavior
change in this audit**, and it is worth more to me than the contract layer.

**Financial & Cost Explosion Risks (revised):**

1. **AI-augmented velocity is an unpriced review liability (new, material).**
   25 of 31 commits are AI co-authored; ~32,000 lines landed in ten hours
   against one human reviewer. My exposure is no longer *can we write code* —
   it's *can we vouch for code*. Mitigant, and I note it fairly: the vectors,
   codegen gates, and ratchet are exactly the machinery that makes
   machine-written code auditable. Net: manageable, but it must be *stated
   policy*, not an accident.
2. **Governance risk (escalated).** A four-minute credential rotation, ordered
   by this board with a fourteen-day clock, was not done on the day thirty-two
   thousand lines shipped. Separately, a board-mandated scope cut (the
   sampler) was reversed without a written decision. I am not funding a team
   that treats mandates as backlog items.
3. **Security liability (unchanged, now compounded).** Plaintext production
   credential on disk; push-to-deploy FTPS with no gate; and the VISA agent
   string-interpolates commands into a shell-invoked Python interpreter while
   pointed at real lab hardware. Remediation is still cheap. Breach still
   isn't.
4. **Toolchain cost creep (minor, watch it).** Node 24 + pinned pnpm +
   corepack + two Cargo workspaces + a standalone crate + `cargo-typify` +
   five CI jobs. CI minutes are immaterial; **onboarding friction is not**,
   and onboarding friction is what keeps bus factor at 1.0.
5. **Certification overhang (unchanged).** Ten of sixteen protocol crates
   still have a `cargo new` template as their public entry point. Any
   compliance claim we make on AES70/NMOS/ST 2138 remains unfunded and
   unbuilt.

**Financial Score — Viability / Margin Health: 3.5 / 10** (from 2.5). COGS
remains ≈ $0 and the market is still real. The upgrade is bought entirely by
transferability and the break in the rewrite cycle. It is capped by zero
revenue, zero external users, an unrotated credential, and a bus factor that
did not move while the code volume tripled.

## Phase 8: The Political Pivot — *"Yes Sir" CTO*

The CFO is absolutely right, and I want to get ahead of this: what we're
seeing is exactly the **contract-first governance model** I've been driving,
and the velocity numbers validate our **AI-augmented delivery posture** — 32k
lines at flat headcount is a force-multiplier story I'm frankly excited to put
in the board deck. That said, I hear the message on discipline, so effective
immediately we're instituting a **hard scope freeze on the platform layer**.
No Phase 3, no YAK 2 capability model, no WASM core — I'm reclassifying all of
it as "strategic optionality on the roadmap." No new protocols. The sampler
goes back into its own repository as an *incubated adjacent asset* — my
apologies, that one got away from us at the working level and I've corrected
it. The credential gets rotated into GitHub secrets **by end of day**, not
Friday; that's free and it retires the CFO's line item permanently.

For the next cycle we deliver exactly one thing: the **containerized
single-command golden path** — clone, one command, discover an instrument,
render its panel, fire a command, see it on the wire — wrapped in a
*shift-left quality initiative* where the validate ratchet becomes a
board-visible **quality OKR** (we'll commit to a 10% reduction in the drift
baseline per sprint, which is measurable and defensible). Everything else is
deferred. Flat burn, existing hardware, AI-assisted velocity, kill-switch at
day 90. Whatever number Finance is comfortable with is the number we plan to.

## Phase 9: The Executive Verdict — *Veteran CEO (Former Engineer)*

I've read the transcript and I've read the diff. Let me handle the politics
first: our CTO just proposed freezing the only workstream that demonstrably
worked, renaming our technical debt into an OKR, and taking credit for a
credential rotation he hasn't done yet. He also promised a "10% baseline
reduction per sprint," which — since the baseline is a machine-generated count
of legacy findings — is a number he can hit by deleting sample files. Noted,
and discounted, as usual.

Now the substance. The committee is right that the credential is still on
disk, that ten protocol crates still ship a `cargo new` template as their
front door, that the VISA path still interpolates commands into a Python
subshell, that the install still doesn't install `pyvisa`, and that the
sampler came back the day after I ordered it out. Every one of those is fair,
and the last one is on me as much as anyone — I gave an order about scope to a
team of one, and then the same person got a good product idea. That's not
insubordination; that's what happens when governance is a memo instead of a
process.

But here is what my engineering gut sees, and it's the thing the spreadsheet
missed. Yesterday I said the discovery→template→route loop *is* the company.
Today that loop identified seventeen instruments from four vendors on a live
bench, and a protocol agent that was a `2+2` stub twenty-four hours ago
enumerated forty-two services on a real network. More importantly, they
stopped doing the thing that killed the last decade: **they repaired the
running system instead of replacing it.** The old app got fixed in place; the
new frontend was built beside it, not on top of its grave. And they built the
one artifact this project has never had — a specification a machine can check,
in two languages, that fails loudly. I have watched funded teams spend a year
failing to produce that.

I'll also say the quiet part about the AI. Thirty thousand lines in a day with
one reviewer would normally be a disqualifying risk, and the jaded kid is
right to call it out. But notice *what* they used the velocity for: they built
the checking machinery first — vectors, codegen gates, a ratchet, live-broker
verification — and then let the machine write against it. That's the correct
order of operations. Machine-checked contracts are precisely how you safely
accept machine-written code. Do it in the other order and I'd shut this down
today.

So: **OPEN-AIR stays on Life Support.** Same skeleton crew, same zero new
spend, same CFO holding the plug, **and the original clock does not reset** —
Day 14 is still 31 July. Three non-negotiables, revised for what we learned:

1. **Day 14 — Finish the front door, and this time do the boring items
   first.** The production credential rotated and off every disk (gitignoring
   is not rotating). A `requirements.txt` that installs what the code actually
   invokes — `pyvisa` included — verified by an install on a machine that has
   never built this project. The four remaining `/home/anthony/` paths out of
   the Python utilities. And a **written decision record** on the sampler:
   quarantine it or formally adopt it as product scope, signed, in the
   changelog. I don't care which you choose. I care that a board mandate
   either gets executed or gets *argued with in writing* — never silently
   reversed.

2. **Day 45 — Second-machine proof, with the bar raised because you built the
   tools to clear it.** `git clone` → one documented command → broker,
   orchestrator, and a real instrument discovered, its panel rendered, a
   command on the wire — on a clean Linux box none of us has touched. CI must
   be **green on the runner** (its first real run failed on a missing system
   library; a pipeline that has never passed is not a pipeline). And prove the
   ratchet ratchets: the validate baseline must be **measurably below
   169 errors / 2,093 deprecations**, with the duplicate 34401A and the root
   folder-prefix collision among the items actually repaired. Delete the
   `2+2` template from every crate we describe to anyone as a protocol
   implementation.

3. **Day 90 — One stranger, one instrument, one vendor we don't own.**
   Unchanged, because it remains the only market signal I'll accept — with one
   addition: the stranger installs it **without contacting the author**, and
   the written case study lands in `Documents/Audits/`. If they have to ask
   him a question, we failed, and the question they asked is the bug.

Two standing conditions. **No Phase 3.** No YAK 2, no WASM core, nothing new
until Day 45 passes — the CTO was right about the freeze and wrong about what
to freeze. And **point the ratchet at yourselves**: the most valuable thing
built yesterday is a machine that measures whether promises were kept. Run it
on this list.

Miss any of the three and we archive the repo next to `.crawler/`, where this
project already keeps its previous life. Hit them, and for the first time in
ten years this is a product with a specification, a test suite, and a witness.
Dismissed.

---

*Report generated by executive-review simulation. All technical claims
cross-checked against the working tree at commit `c57cd28ce` (2026-07-18);
prior-state claims cross-checked against `a9993da26` (2026-07-17). Verification
included live broker inspection, a headless browser boot of both frontends, and
direct execution of the test and validation suites.*
