# The four YAK verbs — SET, RIG, NAB, DO

> Written 2026-07-27 against the working tree at `714160d04`, from
> `BackEnd/openair-yak/src/verbs/` and the panel JSON under `BackEnd/Instruments/`.

*Companion to [yak_protocol_report.md](yak_protocol_report.md) (§1, §3) ·
[1_Design_Audit.md](1_Design_Audit.md) (§3.3, §4.3, §5.3) ·
[2_Architecture_Diagrams.md](2_Architecture_Diagrams.md) (§3, §3b)*

---

## 0. The one-line version

Every YAK command is a **command name** plus a **verb**. The name says *which*
SCPI template to look up; the verb says *what shape the traffic is* — whether a
value gets injected, whether a reply is coming back, and whether the panel had to
supply arguments at all.

| Verb | Intent | Argument source | Reply expected |
|---|---|---|---|
| **SET** | one component parameter | one widget value | no |
| **RIG** | one instrument-wide configuration, several arguments at once | several sibling widgets | no |
| **NAB** | ask the instrument something | none (query only) | **yes** |
| **DO** | make it happen now | none (parameterless) | no |

The distinction is real at authoring time and mostly real at runtime. §3 is where
that "mostly" is spelled out.

---

## 1. Where a verb is declared

A verb is a string on a `yak_handler` block attached to a `_GuiActuator` in an
instrument panel:

```json
"Execute Command": {
  "type": "_GuiActuator",
  "yak_handler": {
    "enable": true,
    "yak_type": "set",
    "sub_path": "Generator",
    "command": "Set_Frequency",
    "input_name": "freq",
    "converter": ""
  }
}
```

`yak_type` is one of exactly four values — `contracts/src/layout/yak-binding.ts:9`
enumerates them, and `mqtt.rs:166-172` dispatches on them, lowercased. Anything
else logs `Unknown yak_type` and is dropped.

`command` (`Set_Frequency`) is looked up in the model's command table, built by
`repository.rs` from the `Yak/<Class>/<Model>/<Section>/*.json` tree. That lookup
returns a **SCPI template** with `<angle-bracket>` placeholders:

| Verb | Command | Template found in `Yak/Generator/33220A/` |
|---|---|---|
| SET | `Set_Frequency` | `FREQuency <freq>` |
| RIG | `Apply_Sine` | `APPLy:SINusoid <freq>, <amp>, <offset>` |
| NAB | `Get_Apply_String` | `APPLy?` |
| DO | `Output_ON` | `OUTPut ON` |

That table is the clearest statement of the difference: **one placeholder, many
placeholders, a question mark, nothing.**

---

## 2. What each verb actually does

All four share the same spine — resolve the model, look up the template, fill the
per-instance constants, publish. They diverge on two axes only.

### SET — `verbs/set.rs`

The everyday verb, and the most common one by a wide margin (69 of the 98
handlers in `BackEnd/Instruments/`). One widget, one parameter, one instrument
component.

1. reads the primary value from the payload (`value`, else the key named by
   `input_name`)
2. runs it through `converters::apply_converter` (`mhz_to_hz`, `v_to_mv`, …)
3. `apply_params` — substitutes the instance constants the panel was stamped with
   (`<chan>` → the module's mainframe slot)
4. `fill_placeholders` — substitutes every remaining `<…>` from the payload plus
   the folded-in sibling `Input/*` widgets
5. publishes

**SET is the only verb that does not wrap its payload in a `correlation_id`
envelope** (`set.rs:45-47` — it passes the raw command as both the raw and the
enveloped form). On the per-device `target` topic this is invisible, because that
path publishes raw SCPI for all four verbs. On the legacy global topic it means a
SET is the one verb a future receiver could not correlate. Harmless today, a
loose end when §2.3 of the protocol report gets built.

### RIG — `verbs/rig.rs`

Same code as SET, line for line, plus the correlation envelope (`rig.rs:45-52`).
The difference that matters is **not in the agent, it is in the templates RIG is
put on**: the multi-argument compound commands.

`APPLy:SINusoid <freq>, <amp>, <offset>` is one button and three numbers, and the
three numbers live in three sibling widgets that each publish to their own MQTT
topic. The press that fires the command carries only its own `value: 1`. What
makes RIG work is `mqtt.rs:63` caching every GUI topic's last value and folding
`.../Input/*` siblings into the payload before dispatch, so `fill_placeholders`
sees `{value: 1, freq: 1000, amp: 2, offset: 0}`.

Two consequences worth knowing:

- **A named argument beats the press value** (`verbs/mod.rs:116-124`). The handler
  declares `input_name: "freq"` *and* sits on the actuator, so without that
  ordering every argument would read `1`.
- **A half-built command is refused, not sent.** If a placeholder resolves to
  nothing, `fill_placeholders` returns the missing names and the verb logs and
  returns. `APPLy:SINusoid 1000, <amp>, <offset>` is a syntax error the panel has
  no way to surface, so refusing is the recoverable failure.

Only 5 handlers use RIG today, all of them the Generator's `Quick_Setup_Apply`
block.

### NAB — `verbs/nab.rs`

The question verb: the SCPI ends in `?`. 4 handlers today.

NAB does **not** convert and does **not** call `fill_placeholders` — it runs
`apply_params` only (`nab.rs:26`). A query takes no widget value, but it still
needs its instance constants, or `INST:NSEL <chan>;MEAS:VOLT?` reaches the
instrument with the placeholder intact. It wraps in the `correlation_id` envelope
when the payload carries `full_id`.

**NAB is the one verb whose contract is not fulfilled.** It publishes the query
and returns. Nothing in the crate parses the reply; there is no receiver matching
on `correlation_id`, and no path from an instrument's answer back to the
`Outputs`/`_GuiValue` fields the NAB panels were authored with. That is design
audit §5.3 and protocol report §2.3 — the envelope is the missing half already on
the wire, `yak_receiver.py` is the behavioural spec for the rest.

So today NAB is architecturally distinct and behaviourally a write-only DO.

### DO — `verbs/do_cmd.rs`

Fire and forget: `:RUN`, `:STOP`, `OUTPut ON`, `*CLS`. 20 handlers, the second
most common verb.

Identical to NAB in code — `apply_params` only, correlation envelope, dispatch.
The instance constants still matter: an `INST:NSEL <chan>;OUTP ON` must know
which slot it is turning on. It reads the payload value into `_raw_val` and
discards it (`do_cmd.rs:9`), which is the honest expression of "the press is the
whole message."

The authored shape differs too. DO is the **Action Construct** — the SCPI lives
directly on the `Execute Command` actuator with no nested `Input` block, where
SET/RIG carry `Input` siblings and NAB carries `Outputs`.

---

## 3. What actually distinguishes them, at runtime

Four verbs, two behavioural axes:

| | fills placeholders from widgets | correlation envelope |
|---|:---:|:---:|
| **SET** | yes | no |
| **RIG** | yes | yes |
| **NAB** | no — `apply_params` only | yes |
| **DO** | no — `apply_params` only | yes |

Read across and the collapse is visible: **`nab.rs` and `do_cmd.rs` are the same
function with different log strings**, and **`set.rs` and `rig.rs` differ only in
the envelope**. Four verbs, two distinct code paths.

That is not an argument for merging them. The verb is a *semantic* declaration
that outlives the current implementation:

- NAB and DO diverge the moment the receiver exists — NAB gets a reply route, DO
  never will.
- SET and RIG diverge in validation and intent — RIG means "these arguments are
  atomic, apply them together," which is a real instrument-level guarantee even
  where the substitution code happens to be shared.

Design audit §3.3 calls the verb grammar "the good part" and it is explicitly a
keeper. The right reading of the table above is that the implementation has not
yet caught up to the vocabulary — not that the vocabulary is redundant.

---

## 4. Rules that follow from the distinction

- **SET and RIG require `input_name`.** Enforced as a cross-field rule in
  `contracts/src/layout/yak-binding.ts:35-41`. NAB and DO have no use for it —
  where they carry one it is vestigial.
- **NAB requires a reply parser.** Contract guideline Y6 in
  `Documents/Strategies/4_Contracts_Structural_Guidelines.md:387`. Currently
  unsatisfiable; it is a statement of what must be true before NAB is trustworthy.
- **`target` and `model` are stamped per instance, never authored.**
  `build_instrument_panels.py` writes them from the discovered device, for every
  verb equally. A hardcoded one in a template points all eight panels at the same
  instrument.
- **`params` are applied before the value, for every verb.** `verbs/mod.rs:59-65`.
  Skipping this on NAB/DO was the bug that made every 66104A module command read
  `INST:NSEL 1` — one table, eight modules, all addressing slot 1.

### The auto-classifier cannot infer RIG

`openair-yak crossref --emit` guesses a verb when emitting handler stubs:

```python
verb = "nab" if scpi.rstrip().endswith("?") else ("set" if placeholder else "do")
```

Three of four. RIG is never emitted, because "these several arguments belong to
one atomic command" is not visible in the SCPI string — `APPLy:SINusoid <freq>,
<amp>, <offset>` looks to the regex like a SET with a `<freq>` placeholder, and
would be stubbed as one. The script says the verb needs a human pass; this is
exactly why. A stub is a starting point, and RIG is the field you go back and fix.
