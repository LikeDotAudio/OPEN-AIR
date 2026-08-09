# Audit — GUI ↔ YAK Binding Across `Instruments/`

**Date:** 2026-08-07
**Scope:** every control in `Instruments/*/*.json`, cross-referenced against the vocabulary in `Instruments/<Family>/<Model>/<Model>.yak`.
**Definitions** (per [`Instruments/TALKER_LISTENER.md`](../../../Instruments/TALKER_LISTENER.md)):

- **Talker** — a GUI element that changes something: a `yak_handler` naming a command.
- **Listener** — the NAB (or compound NAB) it hears back from once set: `readback` on the talker, `yak_listen` on whatever displays the result.

---

## 1. Headline

| | Controls | Share |
|---|---:|---:|
| Total controls audited | **350** | |
| **Talkers** (carry a `yak_handler`) | **105 → 212** | 61% |
| ├ command resolves in that family's vocabulary | 81 → **187** | |
| └ **names a command that does not exist** | **24** (all Router) | |
| **Inline `command_value`, no handler** — inert, reached nothing | **97 → 1** | resolved |
| No binding of any kind | 136 | 39% |
| **Talkers declaring a `readback`** | **24** | **23% of talkers** |
| **Controls declaring a `yak_listen`** | **14** | **4% of controls** |

**Every readback and every listener in the entire tree is in `Spectrum/`** — the panel wired during this session. Twelve other instrument families have no listening half at all: they command hardware and never ask what happened.

---

## 2. Per family

| Family | Controls | Talkers | Resolve | **Missing** | **Inline** | Unbound | Readback | Listen | Models |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Spectrum | 64 | 41 | 39 † | 2 † | 0 | 18 | **24** | **14** | 3 |
| Oscilloscope | 71 | 2 | 2 | 0 | **34** | 34 | 0 | 0 | 2 |
| Generator | 50 | 16 | 16 | 0 | 0 | 33 | 0 | 0 | 2 |
| DMM | 40 | 14 | 14 | 0 | **18** | 6 | 0 | 0 | 1 |
| LCR | 33 | 2 | 2 | 0 | **15** | 15 | 0 | 0 | 1 |
| Load | 33 | 2 | 2 | 0 | **15** | 15 | 0 | 0 | 1 |
| Power | 27 | 2 | 2 | 0 | **12** | 12 | 0 | 0 | 4 |
| **Router** | 25 | 25 | **1** | **24** | 0 | 0 | 0 | 0 | 1 |
| Distortion | 7 | 1 | 1 | 0 | 3 | 3 | 0 | 0 | 1 |
| Counter, DAQ, SMU, VNA | 0 | — | — | — | — | — | — | — | 0 |

† Both Spectrum "missing" entries are explained, not broken:
`Set_Power_Gain` resolves at runtime through the SET verb's ON/OFF-pair fallback (`Set_Power_Gain_ON` / `_OFF`), and `Set_High_Sensitivity` is deliberately `enable: false` — no such SCPI exists on N9340B firmware A.02.07 (probed, 11 spellings). **A naive name check reports both as missing; they are not.** Any tooling built on this audit must model the pair fallback or it will chase two ghosts forever.

---

## 3. Finding 1 — the Router panel cannot work

**24 of its 25 controls name a command that does not exist.**

```
panel asks for : Set_Relay_Card4 ×8, Set_Relay_Card5 ×4, Set_Relay_Card7 ×4,
                 Set_Relay_Card8 ×4, Set_Relay_Card9 ×4, Reset_Device ×1
vocabulary has : 8 commands total; the only relay-ish one is `Card_Reset`
MISSING        : Set_Relay_Card4, 5, 7, 8, 9
```

Only `Reset_Device` resolves. Every routing button on that panel logs `Command '…' not found in YAK repository` and moves no relay — the same failure mode as this session's `Set_Power_Gain`, but across a whole instrument rather than one button.

This is the highest-severity finding in the audit: the panel *looks* wired, and a router that silently does not switch is worse than one that visibly fails.

**Action:** author `Set_Relay_Card{4,5,7,8,9}` into the Router `.yak`, or correct the panel to the names that exist. Deciding which requires the router's manual — the names suggest a card/relay addressing scheme the vocabulary never received.

## 4. Finding 2 — 97 controls were inert  ✅ RESOLVED

**Correction to the first draft of this audit.** It said these controls "bypass YAK entirely",
which implied they drove hardware by another path. They did not. `command_value` has **no consumer
anywhere in the tree** — not one line of frontend or backend code reads it; the only occurrence
outside the panels was a doc comment. These controls did not bypass YAK to reach the instrument,
they reached **nothing**. Pressing them did nothing at all.

Worse in one way (97 dead controls shipped looking functional), far safer in another: converting
them could not regress a working path, because there was none.

**Resolved 2026-08-07** — all 97 now route through a `yak_handler`:

| | |
|---|---:|
| Reused an existing command (matched by SCPI text) | **39** |
| Command authored from the literal, marked `unverified` | **57** |
| Not mechanically convertible | **1** |

The exception is Distortion's `"<current_mode_command> <value>"` — a template whose *command name*
is itself a placeholder. That needs a design decision, not a rename.

⚠ **The 57 authored commands are live but unverified.** The literal was the only specification
available and it had never executed, so each entry carries `"unverified": true`. This is real SCPI
reaching real instruments the first time someone presses those buttons. Spot-check per family;
`openair-yak check-tables` lists them.

Every one of these formerly carried an inline SCPI literal and **no** `yak_handler`:

```
Oscilloscope 34 · DMM 18 · Load 15 · LCR 15 · Power 12 · Distortion 3
```

```jsonc
"trigger": false,
"command_value": "FUNC '<value>'"        // DMM
"command_value": "VOLT <value>"          // Power
"command_value": "SENS:VOLT:NPLC <value>"// DMM
```

Because they never reach YAK, **none** of the machinery applies to them:

- no unit declaration or conversion — the panel asserts the scale silently
- no readback, so nothing verifies the write landed
- no ON/OFF pair resolution, no converter, no command-table validation
- invisible to `crossref`, `check-tables` and every other audit tool

Both instrument bugs found this session were exactly this class — a panel asserting something the vocabulary should own. The RBW button that set 0.3 Hz instead of 0.3 MHz, and `bool_to_int` matching no converter. These 97 controls are the same hazard, unaudited.

**Action:** convert to `yak_handler` naming a real command. The SCPI already exists in the literal, so where the command is absent from the `.yak` the literal *is* the specification for authoring it.

## 5. Finding 3 — the listening half is one family deep

24 readbacks and 14 listeners, all in Spectrum. Everywhere else, a panel's controls show whatever the operator last typed rather than what the instrument is doing — the drift this session's work was built to end.

The vocabulary is more ready than the panels are:

| Family | NAB commands | Compound (named fields) | Declaring a unit |
|---|---:|---:|---:|
| Oscilloscope | 521 | 9 | 66 |
| Distortion | 289 | 1 | 66 |
| Power | 288 | 2 | 84 |
| Generator | 224 | 1 | 36 |
| Spectrum | 105 | 5 | 29 |
| DMM | 72 | 1 | 10 |
| Load | 46 | 2 | 22 |
| LCR | 6 | 0 | 0 |
| Router | 2 | 0 | 0 |

**Compound queries are the unlock.** One `*_settings` query returns every value a panel needs in a single round trip, and its `returns.fields` give each one a name and a unit — which is exactly what a listener binds to. Spectrum had four ready-made (`Frequency_settings`, `amplitude_settings`, `bandwidth_settings`, `all_marker_settings`) and that is why it wired up in an afternoon. Oscilloscope already has **9**; Load and Power have 2 each.

Where a family has none, one should be authored per panel rather than wiring N single-value queries — N queries means N round trips and N uncorrelated replies landing on one topic.

---

## 6. Recommended order

1. **Router** — 24 dead controls. Correctness, and the panel currently lies about what it does.
2. **Power (12 inline)** — smallest inline family, 288 NABs and 84 units already declared, 2 compound queries. The cleanest proof that the conversion generalises past Spectrum.
3. **DMM (18 inline, 14 talkers)** — highest control density after Oscilloscope, only 1 compound query and 10 units: expect to author a `dmm_settings` NAB.
4. **Oscilloscope (34 inline)** — largest, but 9 compound queries already exist.
5. **LCR / Load (15 each)** — LCR has 6 NABs and no units; it needs vocabulary before it needs panel work.
6. **Backfill units** on NAB fields per family as each is wired. A listener without a unit can display a number but cannot convert or verify it.

## 7. How to re-run this

The audit walks `Instruments/*/*.json` for controls and `Instruments/<Family>/<Model>/<Model>.yak` for vocabulary. Two rules matter for anyone rebuilding it:

- **Model the ON/OFF pair fallback**, or `Set_Power_Gain`-style talkers read as missing (§2 †).
- **Count `command_value` separately from unbound.** A control with an inline literal is not unbound — it is bound to something nothing can see, which is worse and needs its own column.

Existing tooling covers part of this already: `openair-yak crossref <Family>` reports BOUND / MATCH / CONTROL-ONLY / COMMAND-ONLY per instrument, and `openair-yak check-tables` validates the vocabulary itself (currently 234 findings across 3,656 commands, chiefly enums with no choice list).


---

## 8. State after the 2026-08-07 conversion

| Family | Talkers | Resolve | Missing | Inline |
|---|---:|---:|---:|---:|
| Spectrum | 41 | 40 † | 1 † | 0 |
| Oscilloscope | 36 | 36 | 0 | 0 |
| DMM | 32 | 32 | 0 | 0 |
| Generator | 27 | 27 | 0 | 0 |
| **Router** | 25 | **1** | **24** | 0 |
| LCR | 17 | 17 | 0 | 0 |
| Load | 17 | 17 | 0 | 0 |
| Power | 14 | 14 | 0 | 0 |
| Distortion | 3 | 3 | 0 | **1** |
| **Total** | **212** | **187** | **25** | **1** |

Vocabulary grew 3,656 → **3,758** commands across the same 16 models; YAK reloads clean.

† `Set_High_Sensitivity` is deliberately disabled (no such SCPI on that firmware). `Set_Power_Gain`
now resolves because this re-audit models the ON/OFF-pair fallback, as §7 requires.

**Remaining:**

1. **Router — 24 controls still dead.** Unchangeable without the manual: `Set_Relay_Card{4,5,7,8,9}`
   describe a card/relay addressing scheme the vocabulary never received. Inventing it means
   guessing at hardware that switches signal paths.
2. **Distortion — 1 control** whose command name is a runtime placeholder.
3. **Verify the 57 authored commands** on real instruments, family by family.
4. **The listening half is still Spectrum-only** — every control now talks, 14 of 350 listen.
   §5's compound-query table is the map for that tranche.
