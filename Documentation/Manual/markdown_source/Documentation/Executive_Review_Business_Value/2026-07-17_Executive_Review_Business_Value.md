# OPEN-AIR — Executive Review Committee: Business Value Audit

**Date:** 2026-07-17
**Subject:** Repository audit of `OPEN-AIR` (branch `main`, 339 commits, first commit 2026-03-14)
**Context:** Project is approximately **10 years behind schedule**. This is the first document ever placed in `Documents/Audits` — the folder was empty until today.

**Grounding facts used by the committee** (verified against the tree, not the marketing):

- Actual architecture: a 103-line Python launcher (`openair.py`) that builds and `exec`s a **Rust orchestrator** (port 8000) plus a Rust `openair-yak` agent, speaking **MQTT**, with a **CDN-React/Babel in-browser JSX** frontend (no npm build step) deployed over FTPS.
- Scale: ~10,954 lines of Rust (168 files, ~45 `oa_*_rs` crates + 16 protocol crates), ~21,503 lines of JSX (142 files), 549 JSON GUI-frame definitions, and only 3,389 lines of Python. Python is glue, not the product.
- All **12 documentation links in `README.md` are dead** (`oaGui/`, `oaTranslator/`, `oaDocumentation/`, `oaComBroker/`, `../SchemWeb/`, the Patent, all of them). The README Quick Start references a `requirements.txt` that **does not exist**.
- The `openair-smpte2138` crate ships real `.proto` schemas and a 78-line codec — but its `src/lib.rs` is still the `cargo new` template: `pub fn add(left, right)` with a test asserting `2+2==4`.
- Recent git history (July 9–17) is a pivot into an **audio drum-sampler / sample renamer** (`pad browser`, `drum buffers`, `pads with notes now`, default startup path `/home/anthony/Documents/Music Samples`). `CHANGELOG.md` stops on 2026-07-06 and never mentions it.
- `.crawler/OPEN-AIR/` contains a **vendored 15 MB, 365-file Tkinter-era copy of the entire previous generation of this same project** (`current_version = 20251225`), plus six zipped snapshots.
- Red flags: a plaintext FTP password in `FrontEnd/.env` (untracked, but sitting in the working tree); hardcoded `/home/anthony/...` paths inside shipping Rust source (`openair-visa/src/oa_visa_scanner/mod.rs:36`, `openair-yak/src/main.rs:32` — one of them pointing at a path that isn't even this repo); six dead Rust modules disabled by `XXX` filename prefixes; startup code that comments itself as *"Bullying port 8000"* while running `kill -9 $(lsof -t -i:8000)`.
- Quality infrastructure: **4 Python test files total** (all in one CSV-import module), Rust tests mostly default stubs, **CI is deploy-only** (FTPS upload; no build, no test, no lint). 9.9 GB of local, gitignored Cargo `target/` artifacts.

---

## Phase 1: The Eager Pitch — *Jr. Business Analyst*

I want everyone in this room to understand what we're sitting on. Laboratory and broadcast instrument software is *exactly* what the README says it is: rigid, vendor-locked, and visually stuck in 2009. Every test bench, every broadcast truck, every RF coordination cart at a stadium show runs a pile of single-vendor apps that don't talk to each other. OPEN-AIR's pitch — one photorealistic web cockpit orchestrating a *fleet* of instruments from any vendor through the YAK command abstraction — is the pitch every audio-over-IP and test-and-measurement integrator has been begging for. And this isn't vaporware: there are **sixteen real protocol crates** in `BackEnd/ComProtocols/` — VISA, SCPI-over-YAK, AES70/OCA, Ember+, NMOS, PTP, SNMP, OSC, MIDI, mDNS, SAP, SMPTE ST 2138. Nobody ships that breadth. Companies pay six figures per seat for fragments of this.

And look at the delivery model! The frontend is a PWA that deploys to the web — a technician pulls it up on a phone at front-of-house, taps the logo, and gets a live MQTT-driven command router with syntax-highlighted SCPI traffic. The `Gui_Frames/` system means the interface is 549 JSON files — customers can re-skin their entire cockpit without touching code. "Your folders are your interface" is a genuinely differentiated UX story. The 2026-07-06 changelog entry shows model-aware SCPI template routing driven by live VISA discovery — that's the hard part, and it's *working*.

The market timing is perfect: ST 2110/2138 adoption is forcing every broadcast facility to modernize control, and the test-equipment world still has no open, cross-vendor answer. First mover with an MIT license builds the community moat, then we monetize support, fleet features, and certified device profiles. We need to fund this *now* — every quarter we wait, someone at a vendor reads the same tea leaves.

## Phase 2: The Geek-Out — *Excited Nerd Engineer*

Okay but can we talk about the *architecture* for a second, because it's honestly beautiful? The Python "launcher" is 103 lines and then it **`os.execv`s straight into a Rust orchestrator** — no interpreter lingering, no GIL, the process *becomes* Rust. And it's not one crate, it's a whole workspace of ~45 micro-crates — `oa_layout_engine_rs`, `oa_metering_engine_rs`, `oa_needle_engine_rs` — each engine isolated, all glued to Python via **maturin/pyo3** where needed and to the browser via a compiled **WASM bundle** in `libControl/Panels/wasm/pkg/`. Rust on the backend, Rust in the browser, MQTT as the nervous system in between. That's the exact topology every "modern control-plane" conference talk describes and nobody actually builds.

And the frontend runs **JSX with in-browser Babel and no build step at all** — 142 components, zero webpack, zero node_modules, deployed as flat files over FTP like it's gloriously 1999, except it's a service-workered PWA with a splash screen that secretly mounts the `LoaderOrchestrator` in the background while the boot GIF plays. The GUI isn't even code — it's 549 declarative JSON frames rendered by a widget registry. If we finish this, you could describe *any* instrument's face as JSON and have it live on a phone in seconds. The `openair-smpte2138` crate already has the full protobuf schema set — `device.proto`, `param.proto`, `constraint.proto`. The bones here are genuinely ahead of the industry.

## Phase 3: The Path of Least Resistance — *Lazy/Fickle Engineer*

I came in ready to love this, because a tool that auto-discovers instruments and auto-builds SCPI templates from `*IDN?` responses would mean I never write another driver shim again. The YAK model-aware routing in the July 6 changelog is legitimately the "does my job for me" feature.

Then I tried to imagine actually *running* it, and I'm out. The README says `pip install -r requirements.txt` — **there is no `requirements.txt`**. Every single documentation link is dead, so "just read the docs" means reading 11,000 lines of Rust. Starting the app requires a full Rust toolchain, `cargo build` of three packages, and it only runs on Linux because it force-frees its port with `fuser -k -9` and `pkill`. The VISA scanner won't even find its own config unless my home directory is literally `/home/anthony` — the path is hardcoded in `oa_visa_scanner/mod.rs:36`, and it's hardcoded *wrong* (points at `Documents/OPEN-AIR`, which isn't even where this repo lives). So the tool that was supposed to save me work cannot be started by anyone except its author, on one specific machine, after a Rust compile. Garbage. Wake me when `git clone && run` works.

## Phase 4: The Wall of Resistance — *Resistant Engineer*

Why are we even discussing this? We already *have* instrument control — the previous system is literally sitting inside this repo at `.crawler/OPEN-AIR/`, 365 Python files of Tkinter that presumably worked as of version `20251225`. Instead of maintaining that, someone rewrote everything in Rust plus browser-Babel React plus MQTT plus WASM plus protobuf, and now we're being asked to adopt a stack that needs a Rust toolchain, an MQTT broker, a web server on port 8000, and an FTP deploy pipeline to a personal domain. That's not a product, that's a hobby with sixteen protocol crates.

And who maintains this? Four test files. Deploy-only CI — the pipeline uploads files, it doesn't build or test anything, so every merge is a prayer. Six Rust modules are disabled by renaming them with an `XXX` prefix, which tells you exactly how changes get "managed" here. The project is ten years behind schedule and the last two weeks of commits are about **drum pads**. The old way — one language, one toolkit, no broker — was fine. Adopting this means every one of us learns Rust, MQTT topic trees, and a bespoke JSON GUI format just to fix a button. No thank you.

## Phase 5: The Teardown — *Jaded Jr. Engineer*

Let me be specific about how this dies, since everyone else is being polite. **The README is fiction.** All twelve navigation links point at directories that do not exist — `oaGui/`, `oaTranslator/`, `oaDocumentation/`, a "Patent" that appears nowhere in the tree except its own dead link, and three links into `../SchemWeb/`, a sibling repo that isn't there. The documented "12-subfolder, 7-Pillar module standard" describes a codebase that was never built or no longer exists. When a project's front door lies this comprehensively, assume the interior does too.

The interior obliges. The flagship standards-compliance story, SMPTE ST 2138, is a crate whose `lib.rs` is the untouched `cargo new` template — the shipping test suite of our "standards bridge" asserts that **2 + 2 = 4** — with the actual 78-line codec hidden behind a feature flag. Process hygiene is `kill -9` everything on port 8000 at boot, self-described in the source as *"Bullying port 8000."* There's a **plaintext FTP password for the production website sitting in `FrontEnd/.env`** in the working tree of the repo we were handed for audit. Hardcoded `/home/anthony/` paths are compiled into release binaries. The frontend transpiles JSX in the browser on every page load, which is a performance and supply-chain joke at 21,000 lines. And the repo contains its own corpse — the entire previous generation vendored in `.crawler/` — which is what the *next* rewrite of this project will look like too.

But the real kill-shot is focus. This mission is "orchestrate laboratory instruments," the project is a decade late, and the July commit log is `drum buffers`, `pads with notes now`, `pad browser`, and a sample renamer that defaults to the author's personal music folder. The CHANGELOG hasn't been updated since July 6 because the honest entry would read "spent the sprint building a drum machine." One contributor, 59 commits in a single day, zero tests worth the name, deploy-on-push to production. This isn't a product trajectory; it's a very talented person's browser history. It will crash and burn the first time anyone other than the author tries to run it — which, per the hardcoded paths, has never happened.

## Phase 6: The Pragmatic Synthesis — *Logical Mid-Level BA*

Fact-checking both sides against the tree:

- **The Jr. BA is right** that the protocol breadth is real and unusual: 16 crates under `BackEnd/ComProtocols/` exist and several (VISA scanner, YAK agent, MIDI) contain genuine logic, and the 2026-07-05/06 CHANGELOG entries document a working discovery → SCPI-template → MQTT-routing loop. The 549-JSON-frame declarative GUI also genuinely exists. The *value proposition* is not invented.
- **The Jr. BA is wrong** to present it as near-market: there is no installable artifact, no `requirements.txt`, no working docs (12/12 links dead), no test coverage (4 files, one module), and Linux-only single-machine assumptions compiled into binaries.
- **The Jaded Jr. is right** on every specific: SMPTE stub, credentials on disk, hardcoded paths, deploy-only CI, mission drift into a sampler, vendored prior rewrite. These all verified.
- **The Resistant Engineer is wrong** that the old Tkinter system is a fallback — it's abandoned at version `20251225`, unmaintained, and lives in a gitignored folder. There is no status quo to defend; there is only forward or off.
- The honest read: this is a **one-person R&D prototype with real, differentiated core technology and zero productization**, whose recent energy went to an unrelated (though technically impressive) audio tool. The immediate pivot required is not technical — it's *editorial*: make the README true, make it run on a second machine, and quarantine the sampler.

**The Scorecard:**

| Dimension | Score | Rationale |
|---|---|---|
| Market-Product Fit Potential | **6.5 / 10** | Vendor-neutral, web-native instrument orchestration is a real unserved gap; 16-protocol breadth is a genuine moat *if finished*. Score capped because no external user has ever run it. |
| Architectural Scalability | **4.0 / 10** | Rust core + MQTT + declarative JSON GUI is a sound topology; but in-browser Babel transpilation, hardcoded absolute paths, `kill -9` process management, and feature-flag-buried codecs are prototype-grade choices that must be unwound before any scale. |
| Maintainability & Readiness | **1.5 / 10** | 4 test files, deploy-only CI, all documentation links dead, `XXX`-prefix module disabling, single contributor, secrets in the working tree, self-vendored previous rewrite. Ten years behind schedule and currently drifting off-mission. |

## Phase 7: The Financial Case — *Veteran CFO*

Strip the romance out. **Burn:** one engineer-founder, ~4 months of commit history in this generation (2026-03-14 to today), preceded by — per the schedule variance — roughly a decade of predecessor work now written off in a gitignored folder. That prior investment is a **sunk cost**; I price it at zero and I note the pattern: this team's historical response to technical debt is a full rewrite, which is the most expensive maneuver in software.

**Unit economics as-built:** favorable, almost accidentally. There is no cloud bill — the product is self-hosted on the customer's LAN, the frontend is static files on shared FTP hosting, and the "no npm build" pipeline means near-zero build infrastructure. COGS ≈ $0. The margin story is therefore entirely a **labor and liability story**: every dollar goes to one irreplaceable engineer (bus factor = 1.0), and the license is already MIT, which forecloses simple license revenue and pushes us to support/services — a head-count-scaling, low-margin model that this codebase's zero-test, no-docs state makes *expensive* to deliver. Every support incident on an undocumented 11k-line Rust core is a founder interrupt.

**Financial & Cost Explosion Risks:**
1. **Key-person risk (severe):** 339 commits, one author, hardcoded to one home directory. If this person walks, residual asset value rounds to the git history.
2. **Security liability:** production FTP credentials in plaintext on disk and push-to-deploy CI with no gate. One compromised laptop = defaced customer-facing domain. Remediation is cheap *today*; breach cost is not.
3. **Rewrite recidivism:** the `.crawler/` folder is documentary evidence of a ~10-year, fully-depreciated prior build. Probability-weighted, a third rewrite is a material risk and I will not fund one.
4. **Scope leakage:** measurable diversion of the only engineer into an audio sampler during the most recent two weeks. At a skeleton budget, focus *is* the budget.
5. **Certification cost overhang:** the moment a real customer appears, "supports AES70/NMOS/ST 2138" becomes a compliance-testing bill we have not scoped, and the current ST 2138 deliverable computes 2+2.

**Financial Score — Viability / Margin Health: 2.5 / 10.** Near-zero infrastructure cost and a real market keep it off the floor; bus factor, zero revenue instrumentation, MIT-foreclosed licensing, and demonstrated schedule risk (10 years) keep it near it.

## Phase 8: The Political Pivot — *"Yes Sir" CTO*

CFO's points are entirely fair, and frankly I've been saying the same internally. Here's what we're going to do, and I think you'll like it: we **halt all net-new feature development immediately** — no more protocols, no more sampler, nothing — and execute a 90-day *"Stabilize-to-Demonstrate"* program on a skeleton crew. We de-scope from sixteen protocols to the **two that already work** (VISA discovery + YAK/SCPI routing over MQTT), we treat the remaining fourteen crates as "roadmap-visible strategic optionality" rather than deliverables, and we park the sampler in a separate repository as — and I want to be careful with language here — an *incubated adjacent asset* with demonstrated velocity. Zero new spend. Existing hardware. The FTP credential gets rotated into GitHub secrets by Friday; that's free and it retires the CFO's liability line.

For the next review cycle we'll deliver a **containerized, single-command "golden path" demo** — clone, run, discover an instrument, click a button on the phone PWA, watch the SCPI fire — wrapped in what I'd call a *lean DevSecOps hardening sprint*: CI that actually builds and tests, secrets hygiene, path portability. It's a minimal, capital-efficient, AI-assisted-velocity story that proves the orchestration kernel without betting the quarter. We keep the MIT community narrative for the board deck, we keep burn flat, and we give Finance a kill-switch at day 90. Whatever number the CFO is comfortable with — that's the number we'll plan to.

## Phase 9: The Executive Verdict — *Veteran CEO (Former Engineer)*

I've read the audit, and I've read the code the way I used to read my own. The committee is right about everything: the README is aspirational fiction, the flagship standards crate still contains the cargo template, we are ten years late, and our CTO just tried to sell me the same de-scope he'd have proposed for any project, wrapped in "DevSecOps." Noted, and discounted.

But here's what my gut sees that the spreadsheet doesn't. One engineer, in four months, stood up a Rust orchestration kernel, sixteen protocol scaffolds of which the *hard two* — VISA fleet discovery and model-aware SCPI templating over MQTT — demonstrably function, plus a declarative 549-frame GUI system that renders on a phone. I have watched fully-staffed vendor teams fail to ship the discovery→template→route loop for years. That loop is the company, if there is one. Even the drum-machine detour, which infuriates the room, tells me the underlying engine is general enough that its author got bored and built a *second product* on it in two weeks. That's not a red flag on the technology; it's a red flag on the management — and management is our job, not the engineer's.

So: **OPEN-AIR goes on Life Support.** Not funded, not killed. One engineer, 90 days, zero new spend, and the CFO holds the plug. Life Support means exactly three non-negotiable milestones, verified against the repository, not against a slide:

1. **Day 14 — Tell the truth and lock the doors.** Every dead link in `README.md` fixed or deleted; a `requirements.txt`/install path that works; the FTP credential rotated out of `FrontEnd/.env` and off every disk; every hardcoded `/home/anthony/` path removed from Rust source; the sampler code moved to its own repository. If we can't make the front door honest in two weeks, nothing behind it matters.
2. **Day 45 — Second-machine proof.** `git clone` → one command → running system on a clean Linux box that none of us has touched before, with CI that builds the Rust workspace and runs a real test suite (the CSV-import tests plus new coverage on the VISA→YAK→MQTT path; the `2+2==4` stub is deleted or replaced). The demo is the loop: discover a real instrument, render its panel from JSON, fire a command from the phone, see it on the wire.
3. **Day 90 — One stranger, one instrument, one vendor we don't own.** A person outside this room installs OPEN-AIR unassisted from the public repo and controls a second-vendor instrument through YAK, documented in a written case study committed to `Documents/Audits/`. That's the first evidence in ten years of anyone else running this software — and it's the only market signal I'll accept.
Executive_Review_Business_ValueExecutive_Review_Business_Value
Miss any one of the three and we archive the repo next to `.crawler/`, where this project already keeps its previous life. Hit all three, and we're not ten years behind anymore — we're ninety days in. Dismissed.

---

*Report generated by executive-review simulation; all technical claims cross-checked against the working tree at commit `a9993da26` on 2026-07-17.*
