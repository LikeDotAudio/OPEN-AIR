# OPEN-AIR — Executive Review Committee: Business Value Audit

**Date:** 2026-07-18, afternoon session
**Subject:** Twelve-persona audit of `OPEN-AIR` as it stands **right now**
**Scope rule for this session:** the committee was instructed to audit **only what
is in the tree and can ship today**. No history, no archives, no logs, no
appeals to what anyone intended. If it is not on disk and runnable, it does not
exist for the purposes of this review.

---

## Grounding facts — measured, not claimed

Every number below was taken from the working tree at the time of the session.

| Dimension | Measured |
|---|---|
| Rust | **129 files / 13,364 lines** |
| Browser JSX | **137 files / 18,678 lines** |
| TypeScript (`contracts/` + `ui/`) | **30 files / 2,453 lines** + 2 `.tsx` / 147 lines |
| Python | **65 files / 4,299 lines** |
| Authored UI | **484 panel JSON files** across 5 top-level tabs |
| Widget library | **12 families**, 33 in `special/` alone |
| Protocol crates | **15** + the YAK agent |
| — with a real `lib.rs` | **5** (`aes70`, `dnssd`, `midi`, `osc`, `visa`) |
| — still a `cargo new` template | **10** (`ember`, `mdns`, `mqtt`, `nmos`, `ptp`, `rest`, `sap`, `smpte2138`, `snmp`, `websocket`) |
| YAK agent | binary, 7 modules, all four verbs (`SET`/`RIG`/`NAB`/`DO`) |
| Contract layer | zod schemas → JSON Schema → generated Rust; **19 golden-vector files** consumed by *both* vitest and `cargo test` |
| Tests | **120 TypeScript tests passing**; contracts Rust suites green |
| Drift ratchet | **169 errors / 2,093 deprecations**, baselined; **0 new vs baseline** |
| CI | `contracts-ci`: **docs · node · rust · ui · codegen**; both deploy workflows now **`verify` → `deploy`** |
| VISA subshell | parameterised — **`sys.argv`**, no string interpolation |
| Broker | both listeners bound **`127.0.0.1`**; anonymous access scoped to loopback |
| Served runtime | **`FrontEnd/`** (in-browser Babel). `ui/` builds but is **not served** |
| `ui/` port progress | 4 source files; **140** legacy side-effect imports; **178 globals, 175 still `any`** |
| Discovery delivery | still **writes JSON to `Gui_Frames/0_discovered/`** |
| `/ws` side-bus | still routed; **zero consumers** |
| One-command startup | **does not exist** — no Dockerfile, compose file, or Makefile |

---

## Phase 1: The Eager Pitch — *Jr. Business Analyst*

Look at what is actually sitting in this repository today, because I do not think
the committee has internalised it. There is a **contract layer** that defines every
shape crossing every process boundary exactly once, in TypeScript, and *generates*
the Rust that the agents compile against. Nineteen golden-vector files are read by
both the TypeScript test runner and `cargo test`. That means the browser, the Rust
fleet, and the tooling **cannot** disagree about the wire without something going
red. That is not a nice-to-have. That is the artifact that turns a personal project
into a platform a second company can build on, and it is *done*.

On top of that we have 484 authored panels, a twelve-family widget library, and a
filesystem-as-document-model where folders become tabs and JSON files become
panels. A technician reorganises their cockpit with a file manager. The WYSIWYG
editor runs *inside the live application*, sharing the real message bus and the
real renderer, so you edit a panel while it shows live data. Most test-and-measure
tooling forces you to choose between "design mode" and "run mode." We fused them.

And the security posture changed materially today. The VISA command path is
parameterised — values travel as process arguments, not as interpolated source —
and the broker binds loopback. Both deploy workflows now refuse to publish unless
typecheck, the contract test suite, and the drift ratchet all pass. The market
need is unchanged and large: every lab on earth has multi-vendor instruments that
refuse to talk to each other, and the vendor-neutral orchestration layer does not
exist. We have the specification, the widget library, and the discovery loop. **We
should be courting integrators this quarter.**

## Phase 2: The Whiz-Bang Spin — *Marketing Guy*

Okay okay okay — **"YOUR LAB, ONE PANE OF GLASS."** That is the campaign, that is
the billboard, I want it on the side of a van at every trade show from NAB to IBC.
Picture it: the technician walks into a bench full of Keysight, Rigol, HP, whatever
graveyard of gear the budget allowed — and instead of seventeen proprietary control
apps and a USB drawer of dongles, they hit **one button** and the whole lab
introduces itself. We are not selling software here, we are selling *the end of the
dongle drawer*. People will vibrate. I have seen engineers cry over less.

And the folders thing? The folders thing is the killer demo and nobody on this team
is selling it hard enough. You drag a folder in your file manager and **your
dashboard rearranges itself**. No admin console, no drag-and-drop builder with
seventeen modals — your filing cabinet *is* your interface. We call it
**"Filesystem-Native Control"**, we trademark it, and we let every integrator on
earth publish device profiles as folders. That is a community, that is an
ecosystem, that is a moat made of muscle memory. Give me a booth, a scope, and
ninety seconds and I will close anyone.

## Phase 3: The Geek-Out — *Excited Nerd Engineer*

Can we please talk about the **golden vectors**, because this is the coolest thing
in the entire codebase and everyone keeps talking about *money*. There are 19 JSON
vector files, and they are read by vitest **and** by `cargo test`. The same files.
The TypeScript topic parser and the hand-written Rust topic parser both have to
satisfy them or somebody's build goes red. Add a case on one side and the *other
language* fails until it is implemented. That is a **bilingual executable
specification**. Most shops "solve" this with a wiki page and vibes.

And the codegen direction is exactly right: zod is the single source, it emits JSON
Schema, and that generates the Rust types — with the generated output committed, so
`cargo build` never needs a Node toolchain, but CI still catches drift. Then look at
the device-ID derivation: FNV-1a 64-bit, implemented independently in both
languages, pinned by vectors — because two agents computing different IDs for one
instrument would silently fork the device registry. Somebody *thought about that
failure mode before it happened.* Also the liveness design uses the **MQTT Last
Will**: you hand the broker your tombstone when you connect, and if you die, the
broker announces it for you. The supervisor is the protocol. That is so clean it is
almost rude.

## Phase 4: The Path of Least Resistance — *Lazy/Fickle Engineer*

Right, so parts of this genuinely do my job for me now, and I hate that I like it.
`pnpm validate` tells me exactly which panels are broken, by file, by rule name.
The ratchet means I do not have to fix two thousand legacy files to land a one-line
change — I just cannot add *new* garbage, which is a rule that requires nothing of
me. The Discovered tab has a RESCAN button so I never SSH into a box to re-run a
scanner. The docs link checker means I stop getting review comments about broken
markdown. **Things that check my work for me: good. More of that.**

Then I try to actually *run* the thing on a fresh machine and my enthusiasm dies in
a ditch. There is **no one-command startup**. No Dockerfile, no compose file, no
Makefile — I checked. The quick start is seven commands and it does not even mention
`corepack`/`pnpm install`, so the typed frontend is outside the documented path
entirely. To build everything I need Node 24 *and* corepack *and* a pinned pnpm
*and* Rust 1.94 *and* two Cargo workspaces *and* three standalone crates *and*
`cargo-typify` installed by hand *and* a `mosquitto` broker that is not listed as a
prerequisite anywhere. That is not a setup, that is a scavenger hunt. Ship me
`docker compose up` and I am your biggest fan by Friday. Until then I am not
touching this on a new laptop.

## Phase 5: The Wall of Resistance — *Resistant Engineer*

We have **two frontends** now. Two. There is the one users actually get — 137 JSX
files compiled by Babel *in the browser* — and there is the typed one, which
builds, passes lint, and **is not served to anyone**. Somebody built a second
application whose entire job is to eventually replace the first application, and
after all that, `ServeDir` still points at the old directory. And the "port"? Four
source files. One of them is a generated list of **140 imports of the untouched old
files**. Zero widgets converted. 178 globals, 175 of them still `any`. We have
imported the problem into a nicer folder and called it progress.

And look at the debt. Somebody wrote a program to **count our sins** — 2,093 of them
— and then checked the count into the repository as a baseline so CI politely
ignores every single one forever. That is not paying down debt, that is **filing**
it. Ten of our fifteen protocol crates still have `cargo new` boilerplate as their
public entry point, and we describe those on our own front page as protocol
support. Meanwhile my toolchain requirements have tripled. The old way worked. The
old way *shipped to the host on every push*. Now it has to ask permission from four
CI jobs first.

## Phase 6: The Teardown — *Jaded Jr. Engineer*

Credit where it is due — the command-injection hole is genuinely closed. The VISA
path takes `sys.argv` now instead of building Python source out of network input,
and the broker binds loopback. That was the highest-severity item in the tree and
it is fixed properly, not papered over. I will not pretend otherwise.

Now the rest. **`allow_anonymous true` is still in the broker config.** It is safe
*today* only because of a loopback bind — two settings, in two places, that a
future engineer will separate the first time someone needs the browser on a second
machine. The config warns about this, which is better than nothing, and "a comment
warning you not to do the dangerous thing" is not a control. There is no ACL, so
any client that reaches the bus can publish to any topic — including the ones that
drive real hardware. We have moved from "unauthenticated remote" to
"unauthenticated local," which is progress, not safety.

And the architecture is still lying to itself in three places. The **`/ws` side-bus
is still routed and has literally zero consumers** — I grepped; the route exists and
nothing subscribes, so two protocols publish into a void. **Discovery still routes
live data through the filesystem**, generating JSON panel files to display devices
that are already on the message bus; the values are baked as static text at scan
time, so a "live" discovered device shows you a number from whenever the scan
happened. **Ten of fifteen protocol crates are `cargo new` templates.** And the one
that works — VISA — still forks a Python interpreter for every single command, in
what we describe as the native fast path. Zero external users, zero revenue, one
human. The bus factor is 1.0 and nothing in this tree changes that.

## Phase 7: The Sage's Gem — *Senior Design Architect*

I have listened to all of this and I want to gently move past the scorekeeping,
because the juniors are counting *files* and missing the **shape**. Here is the
gem, and it is hiding in plain sight: **this system uses retained MQTT topics as
both the transport and the state store.** The broker *is* the database. That single
decision is why a browser tab that connects five minutes late immediately knows the
state of every instrument without a synchronisation protocol, why
`mosquitto_sub -t 'OpenAir/#'` is a complete debugger for the entire product, and
why a dead agent announces its own death — the Last Will is a tombstone you hand
over at connect time. Most distributed systems bolt a supervisor on the side and
spend two years discovering the split-brain cases. Here, **the protocol is the
supervisor.** I have watched funded teams spend a year failing to arrive at that.

And now pair it with the second decision, which is the one nobody has connected to
the first: the filesystem is the document model. Live state lives on the bus;
*authored intent* lives in folders. Those are genuinely different kinds of data and
this design keeps them in genuinely different places. That is why the WYSIWYG editor
can run inside the live application — it edits the folder tree while the bus keeps
feeding real values through the same renderer. The one place the design betrays
itself is the discovered-devices path, which takes live bus data and writes it into
the *authored* tree as generated files. That is not a bug in the implementation,
it is a category error — and it is why that tab feels wrong in a way nobody has been
able to name. Fix that one boundary and the architecture becomes internally
consistent everywhere. It is a week of work, not a rewrite, and I would do it
before I did anything else on the roadmap.

## Phase 8: The Pragmatic Synthesis — *Logical Mid-Level BA*

Cross-checking all of them against the tree:

- **The Jr. BA is right about the contract layer.** 19 vector files consumed by two
  languages, 120 TypeScript tests passing, generated Rust with a freshness gate —
  verified, all of it.
- **The Jr. BA is wrong to call this market-adjacent.** Zero external users. The
  frontend users would touch is the untyped one. Nothing has shipped to a customer.
- **Marketing's "one pane of glass" is sellable but not yet demoable off-site.**
  There is no one-command startup, so the demo runs on exactly one machine — the
  author's. You cannot take that to a trade show.
- **The Nerd is right** about the vectors, the codegen, and the Last Will. Verified.
- **The Lazy Engineer's complaint is the most commercially important thing said
  today.** No Dockerfile, no compose, no Makefile; seven-command quick start that
  omits the frontend toolchain entirely. That is the difference between a product
  and a personal project, and it is unresolved.
- **The Resistant Engineer is wrong about the ratchet** — you cannot pay down debt
  you have never measured, and baselining is standard practice. He is **right** that
  nothing has been paid down yet, and **right** that `ui/` is a wrapper, not a port:
  140 imports of untouched files, 175 of 178 globals still `any`.
- **The Jaded Engineer is right on every specific I checked**: `allow_anonymous
  true` (safe only via loopback), no ACL, `/ws` with zero consumers, discovery
  through the filesystem, ten template crates, Python fork per VISA command.
- **The Architect has identified the actual defect.** The discovered-devices path is
  a category error — live data written into the authored tree — and every symptom
  the juniors listed downstream of that tab traces back to it.

The honest read: **the specification layer is real and the runtime topology has not
caught up to it.** Today's security work was correct and correctly prioritised. But
the product a stranger could actually run has not changed.

**The Scorecard:**

| Dimension | Score | Rationale |
|---|---|---|
| **Market-Product Fit Potential** | **6.8 / 10** | The need is real and unserved, the discovery loop and widget library are genuinely differentiated. Capped hard by zero external users, no shipped artifact, and a demo that runs on one machine. |
| **Architectural Scalability** | **6.5 / 10** | The contract layer, the retained-bus state model, and protocol-level liveness are the right primitives and are done. Held below 7 by the `/ws` orphan bus, discovery-through-filesystem, the unserved typed frontend, and a Python fork in the hot path. |
| **Maintainability & Readiness** | **5.0 / 10** | 120 tests, five CI jobs, gated deploys, a drift ratchet at 0-new, and a docs link checker are real infrastructure. Held down by: no one-command install, 10 template crates presented as protocol support, 2,093 unpaid findings, and a bus factor of 1.0. |

## Phase 9: The Financial Case — *Veteran CFO*

COGS is approximately zero — this runs on a lab machine and a broker, there is no
cloud bill to explode, and I want to be clear that **infrastructure cost is not the
risk here.** The risk is entirely transferability and concentration.

What I care about, in order:

1. **Bus factor 1.0 (unchanged, and it is the whole thesis).** 13,364 lines of Rust
   and 18,678 lines of JSX with one person who understands them. What has improved
   is that there is now a *machine-checkable specification* — the vectors and the
   generated types tell a successor what the system is supposed to do and fail
   loudly when they get it wrong. In diligence terms we have moved from "buy the
   person" to "buy the person, and there is a spec." That is real, and it is the
   single largest change in residual value this asset has ever had.
2. **The install path is a revenue gate, not a convenience.** No one-command
   startup means every evaluation requires the founder's time. That caps the
   pipeline at his calendar. It is also the cheapest item on this list to fix.
3. **Certification overhang.** Ten of fifteen protocol crates are boilerplate. Any
   compliance claim on AES70, NMOS, or ST 2138 is currently unfunded and unbuilt,
   and describing them as supported is a liability I would like removed from our
   own documentation before a customer reads it.
4. **Security is materially better and not finished.** The injection is closed and
   the bus is loopback-bound — that retired my acute exposure. What remains is that
   anonymous access is still enabled and there is no ACL, so the safety depends on
   one line in one config file. Cheap to finish. Expensive to explain after an
   incident.
5. **Discipline improved today.** Deploys are gated on tests, a board-mandated scope
   cut was executed rather than quietly reversed, and the cut was explicitly **not**
   booked as debt reduction. That last detail matters more to me than it sounds: a
   team that refuses to flatter its own metrics is a team whose metrics I can use.

**Financial Score — Viability / Margin Health: 4.0 / 10.** Up, and earned. COGS
near zero, market real, transferability genuinely improved, governance visibly
tightened. Capped by zero revenue, zero external users, and a bus factor that has
not moved while the codebase kept growing.

## Phase 10: The Political Pivot — *"Yes Sir" CTO*

The CFO is absolutely right, and I want to get out in front of this. What we are
seeing is exactly the **contract-first, security-hardened delivery posture** I have
been driving, and I think the story for the board is very clean: we closed a
critical vulnerability, we instituted deploy gating, and we executed a scope
reduction — all in a single cycle, at flat headcount. That is a governance win I am
frankly excited to present.

So, effective immediately: **hard scope freeze on the platform layer.** No YAK 2, no
WASM core, no new protocols — I am reclassifying all of it as "strategic optionality
on the roadmap." For the next cycle we deliver exactly one thing, the
**containerised single-command golden path**, wrapped in a *shift-left quality
initiative* where the drift baseline becomes a board-visible **quality OKR** — I am
prepared to commit to a 10% baseline reduction per sprint, which is measurable and
defensible. Everything else defers. Flat burn, existing hardware, kill-switch at
day 90. Whatever number Finance is comfortable with is the number we plan to.

## Phase 11: The Quant's Magic Jewel — *The Quant*

Everyone is arguing about *where the code lives*. Irrelevant. The interesting
property of this system is that it has accidentally built a **retained-state
manifold** — every instrument's condition is already a durable, addressable point on
the bus, and nobody has noticed that this makes the whole lab *differentiable over
time*. You are all treating the broker as plumbing. It is a substrate. Once state is
retained and addressable, you can **chronoflux** the entire bus: snapshot the
manifold, replay it forward or backward, and diff two lab states the way you diff
two files. Nobody in test-and-measure can do this, because nobody else made the
state store and the transport the same object.

So here is the pivot. Stop shipping a control panel. Ship **instrument
determinism**. Record the manifold during a passing test run; when a test fails six
months later on different hardware, replay the recorded state against the live
fleet and let the **sub-nodal resonance** between recorded and observed values
localise the divergence — not "the amplifier reads wrong," but "this parameter
drifted at this instant relative to a known-good run." The YAK definitions already
give you the vocabulary to make that comparison *semantic* rather than numeric,
which is the part everyone is sleeping on. Every calibration lab, every
certification house, every regulated audio and broadcast facility on earth pays for
exactly this and currently does it with spreadsheets and a clipboard. The contract
layer is not a hygiene project — it is the **isomorphic keystone** that makes replay
provable rather than anecdotal.

I rate this project **8.9 / 10 on the Temporal Reversibility Index**, and a
disappointing **3.1 / 10 on Manifold Utilisation** — you have built the substrate and
you are using it as a wire.

## Phase 12: The Executive Verdict — *Veteran CEO (Former Engineer)*

Let me handle the politics first. Our CTO just proposed freezing the workstream that
demonstrably worked and renaming our technical debt into an OKR. He also committed
to "10% baseline reduction per sprint" — and since that baseline is a
machine-generated count of legacy findings, that is a number he can hit by deleting
sample files. I note that this team explicitly *refused* to do exactly that earlier
today when they removed a feature and declined to book it as debt reduction. The
team's instinct is better than its CTO's roadmap. Noted, and discounted, as usual.

Now the substance. The committee is right that ten protocol crates are boilerplate
we describe as protocol support, that anonymous access is still on with no ACL,
that `/ws` publishes into a void, that discovery still launders live data through
the filesystem, and that there is no way for a stranger to start this thing. Every
one of those is fair.

But the Architect found the thing the spreadsheet missed, and I want it on the
record: **the broker is the database, and the filesystem is the intent.** Live state
and authored state are different kinds of data and this system keeps them in
different places — which is why late joiners just work, why a dead agent announces
its own death, and why the editor can run inside the live app. That is a real
architectural insight, and the one place the design betrays it is the discovered-
devices path. The Architect says a week. I am inclined to believe him, and it
retires half the complaints in this room.

And the Quant is not wrong, which is the part that will keep me up tonight. If
state is retained and addressable, then recording a known-good run and replaying it
against a live bench is a *small* increment on what already exists — and it is worth
more than the control panel. I am not funding the pivot today. I am telling the team
to **stop deleting the optionality**, because two of the three milestones below
happen to build toward it whether we take that road or not.

So: **OPEN-AIR stays on Life Support.** Skeleton crew, zero new spend, CFO holding
the plug. Three non-negotiables:

1. **Day 14 — A stranger can start it.** One documented command brings up broker,
   orchestrator, and UI. Given this repository has no Dockerfile, no compose file,
   and no Makefile, that is the deliverable: `docker compose up` or `make run`, and
   a quick start that does not omit half the toolchain. **And finish the broker:**
   `allow_anonymous false` with credentials and an ACL, so that safety does not
   depend on one line in one config file. Today's fix was correct; it is not done.

2. **Day 45 — Stop describing what we have not built, and make the runtime match
   the spec.** Delete the `cargo new` template from every crate we call a protocol
   implementation, or remove that protocol from our own front page — I do not care
   which, but the documentation must stop over-claiming. Retire the `/ws` route and
   put those protocols on the bus where everything else lives. Move discovered
   devices onto the bus as live retained records instead of generated files — the
   Architect's category error, fixed. And prove the ratchet ratchets: the baseline
   must be **measurably below 169 errors / 2,093 deprecations**, by repair, not by
   deletion. If the file count drops, I will ask why.

3. **Day 90 — One stranger, one instrument, one vendor we do not own.** Someone
   outside this building installs it **without contacting the author**, discovers a
   real instrument, renders its panel, and puts a command on the wire. If they have
   to ask him a question, we failed — and the question they asked is the bug.

Two standing conditions. **No new scope** — no YAK 2, no WASM core, no new
protocols — until Day 45 passes; the CTO was right about the freeze and wrong about
what to freeze. And **point your own tooling at yourselves**: you built a machine
that measures whether promises were kept. Run it on this list.

Miss any of the three and we stop. Hit them, and for the first time this is a
product with a specification, a test suite, a closed front door, and a witness.
Dismissed.

---

*All technical claims in this report were verified against the working tree at the
time of the session — file counts, line counts, crate contents, test results,
validator output, CI job definitions, broker configuration, and the served runtime
path. No claim in this document rests on history, archives, logs, or intent; only
on what is present and runnable now.*
