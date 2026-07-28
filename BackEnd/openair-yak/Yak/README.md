# YAK command tables

The SCPI vocabulary, one file per instrument model:

    <Family>/<Model>/commands.json    what the model ACCEPTS — the command table
    <Family>/<Model>/model.json       what the model IS — channels, V/A ranges
    <Family>/<Model>/commands_tree.md the model's SCPI tree, generated

## A folder per known device

`knownDevices.json` lists 181 instruments this bench might meet, and every one of
them has a `<Type>/<Model>/` folder here — vocabulary or not. 16 have a command
table; the other 165 carry a `model.json` reading `"vocabulary": "none"`.

That is the point of them. A directory listing is now the inventory: a model with
no table is a *known* gap with a name, a manufacturer and a one-line description,
rather than an instrument nobody thought about. Five families exist here only as
folders — Counter, DAQ, SMU, VNA and most of Oscilloscope — and none of them had
anywhere to put a command table before.

Seeded sheets carry nothing invented: `model`, `manufacturer`, `type` and `notes`,
straight out of the list. Channel counts and domains are absent until someone
reads a manual, because a guessed clamp is worse than an unclamped widget.

The list points back. A device with a table gains a path to it, relative to this
directory, so the pair travels together:

    "34401A": { "manufacturer": "HP / Agilent / Keysight", "type": "DMM",
                "notes": "6.5 Digit Benchtop Standard (Legacy)",
                "commands": "DMM/34401A/commands.json" }

Only the 16 populated models carry the key. Every one of the 181 has a
`model.json`, so a link to *that* would be present on all of them and tell a
reader nothing; `commands` is present exactly where there is something to read.

Generated, never hand-kept — an index of 181 entries against a tree that gains
tables one instrument at a time is wrong by the second commit:

    openair-yak build-links            # rewrite the links
    openair-yak build-links --check    # exit 1 if stale

A dead link is worse than no link, because it reads as coverage, so
`validate_yak_tables.py` fails on one that resolves to nothing, on one pointing
somewhere other than where the table actually is, on a table with no link, and on
a table whose model has no entry at all — that last one is a full vocabulary that
discovery can never reach, since `*IDN?` yields a model and a model absent from
the list answers "Unknown Instrument".

`Scope/` was renamed `Oscilloscope/` to match: `manifest.json`,
`BackEnd/Instruments/` and `knownDevices.json` all use the long name, and this
tree was the only place that did not. The two tables that moved had their
declared `family` updated with the path.

`commands.json` buckets every command under the YAK verb that handles it
(`src/verbs/`), so a panel author picks `yak_type` by reading the file:

    { "model": "66104A", "family": "Power",
      "set": { … one value from one widget … },
      "do":  { "Output_ON": { "scpi": "INST:NSEL <chan>;OUTP ON",
                              "description": "Output ON",
                              "group": "Output Control",
                              "subsystem": "OUTPut" } },
      "rig": { "Set_Levels": { "scpi": "INST:NSEL <chan>;VOLT <volt>;CURR <curr>",
                               "args": ["volt", "curr"], … } },
      "nab": { … queries … } }

| field | |
|---|---|
| `scpi` | the template. **The only field YAK reads.** |
| `description` | what the command does |
| `group` | the category it was authored under ("Output Control") |
| `subsystem` | its SCPI subsystem (`OUTPut`, `MEASure`, `CALCulate`) |
| `args` | values the operator supplies, in the order the SCPI wants them |
| `returns` | what a NAB answers with — see below. Absent on SET/DO/RIG. |
| `unverified` | swept out of the instrument's manual, never sent to the instrument |

## What a question answers

Every NAB entry carries a `returns` block, because a query's reply is half its
contract and nothing recorded it:

    "Get_Meas_Volt_Dc": {
      "scpi": "MEAS:VOLT:DC?",
      "returns": { "count": 1, "type": "NR3", "unit": "V" } }

**A NAB can be several questions in a row**, and 30 of them are. Those get one
named field per answer, in wire order:

    "Measure_All": {
      "scpi": "MODE?;MEAS:VOLT?;MEAS:CURR?;MEAS:POW?",
      "returns": { "count": 4, "separator": ";", "fields": [
        {"name": "mode",    "type": "CRD"},
        {"name": "voltage", "type": "NR3", "unit": "V"},
        {"name": "current", "type": "NR3", "unit": "A"},
        {"name": "power",   "type": "NR3", "unit": "W"} ] } }

That is the field a `yak_readout` widget needs and has never had. Bound to
`Measure_All` today a meter receives one semicolon-joined string with no rule for
splitting it, and `NAB_all_marker_settings` on the spectrum analyser returns
**twelve** values the same way.

`count` is exact — the number of `?` in the template, which also correctly
ignores the leading setter in `INST:NSEL <chan>;MEAS:VOLT?;MEAS:CURR?` (two
answers, not three).

Types are the SCPI response forms the 6060B manual's Tables 2-1 and 2-4 define:

| | |
|---|---|
| `NR1` | integer — 242, mostly status registers and counts |
| `NR2` / `NR3` | decimal / exponential — 454, the measurements |
| `BOOL` | `0` or `1` — 103 |
| `CRD` | character response, ≤12 chars, i.e. one of an enum — 253 |
| `AARD` | arbitrary ASCII, e.g. `*IDN?` — 19 |
| `BLOCK` | definite-length binary, e.g. `:WAVeform:DATA?` — 19 |
| `ERROR` | `<NR1>,"<message>"` from the error queue — 5 |

43 of these are the type the 66000A dictionary states outright; the rest are
derived from the mnemonic. **427 are left without a `type`** rather than guessed —
that is the honest gap, and a live query answers it immediately.

**3141 of the 3646 commands carry `unverified: true`.** They came from a sweep of
the manuals (`Documents/Audits/Yak commands missing.md`), so the SCPI is what the
manual prints but nothing has watched an instrument answer it. The flag is the
honest bit of bookkeeping here — `grep -c unverified` per model says how much of
a table is still unproven, and `sed -i '/"unverified"/d'` retires it a model at a
time as the commands get exercised. The 515 without the flag are the originally
authored ones.

Two things the sweep could not decide and a human still has to:

* **Verb for a write-only parameter.** The rule was: a node with a `?` sibling is
  a readable parameter (SET), one without is an action (DO). A parameter the
  instrument will not read back therefore lands in DO. That is why some models
  carry more DO than looks right.
* **RIG.** No `args` names were recoverable from the manuals, so every swept
  parameter is a one-value SET; the sweep added nothing to RIG. The multi-argument
  commands — the ones RIG exists for — are still mostly sitting in SET. Four have
  been grouped by hand so far (`Setup_Trigger_Edge`, `Setup_Burst`,
  `Setup_Transient_Profile`, `Setup_Limits`), and the single-parameter SETs they
  subsume were deleted rather than left beside them: one way to set a thing, so a
  panel author cannot wire the trigger level through a path that leaves source and
  slope stale. Readback NABs for the same parameters stay — you write together,
  you read individually.

`<chan>` and `<slot>` are **not** arguments. They identify the instance and are
stamped per panel by `BackEnd/Core/orchestrator/gui/build_instrument_panels.py`, then substituted by
`verbs::apply_params` before the widget's value goes in.

## Compound commands: colonise every statement after the first

SCPI resets the command path to root at the start of a program message, but a `;`
does not — the parser stays at the previous header's path minus its last mnemonic.
So this is wrong:

    TRIGger:EDGE:SOURce <source>;TRIGger:EDGE:SLOPe <slope>

The second statement is read relative to `TRIGger:EDGE` and reaches the instrument
as `TRIGger:EDGE:TRIGger:EDGE:SLOPe` — `-113 Undefined header`. Write it with a
leading colon on every continuation, which is valid from any path:

    :TRIGger:EDGE:SOURce <source>;:TRIGger:EDGE:SLOPe <slope>

(The compact `:TRIGger:EDGE:SOURce <source>;SLOPe <slope>` is equally correct and
is what the path rule is *for*, but it breaks the moment someone reorders the
statements, so the tables use the explicit form.)

Older compound entries predate this rule and repeat the full path with no colon —
`INST:NSEL <chan>;OUTP ON`, `MODE?;MEAS:VOLT?;MEAS:CURR?`, `AM:INTernal:FUNCtion
<shape>;AM:INTernal:FREQuency <freq>`. Whether a given instrument tolerates it is
a question for the instrument, not the spec; the Power ones are reportedly
exercised on the bench, so this is a list to verify rather than a list of known
breakage. `grep '";.*[A-Z]' */*/commands.json` finds them.

## Which verb

Mechanical, from what the handlers actually do:

    nab   the SCPI is a query (`?`)            — no widget value
    do    no argument placeholders             — a fixed action (`*RST`, `OUTP ON`)
    set   exactly one argument                 — one component parameter
    rig   two or more arguments                — configured in one statement

`rig` and `set` run the same code; the split is about how many sibling widgets
have to be folded in before the command is complete.

## Why it looks like this

These were 176 files shaped like GUI panels — `OcaBin` → `blocks` → `fields` →
`Execute Command`.`message`, with `Input` widgets carrying argument defaults.
`repository.rs` pattern-matched a command table out of that tree at load, and
the mismatch cost three things:

* **`fields` was a command.** The matcher fired on any key with an
  `Execute Command` child, and every widget wraps its own in a `fields` object.
  555 of 1367 loaded "commands" were that key name.
* **The model came from the directory, not the file.** It was read off the
  file's grandparent, so anything nested deeper than `<Model>/<Subsystem>/` was
  filed under a folder name — `_Legacy_Commands`, `CHANnel`, `Commands` — and
  391 commands were reachable only through `get_scpi`'s search-every-model
  fallback.
* **Nothing enforced one definition per name.** 460 rows collided; the winner
  was whichever file `read_dir` returned last. On the Power modules that decided
  between `INST:NSEL <chan>` and `INST:NSEL 1` — between addressing your slot
  and addressing slot 1 whichever module you clicked.

Dict keys make the third impossible, a declared `model` field removes the
second, and there is no key that isn't a command, so the first cannot recur.

One spelling fix came with the move: `<channel>` → `<chan>`. Only `<chan>` is
ever stamped, so a template spelled the long way reached `fill_placeholders`
unfilled, matched no payload key, and the verb refused to send — the module
silently never switched on. The two spellings were split across the modern and
legacy trees, so half the Power commands were dead this way.

`Multimeter/34401A` folded into `DMM/34401A`: same model, two family folders, and
two files declaring model `34401A` would collide at load.

## Regenerating the sheet

`CommandList.csv` / `.xlsx` is a generated view of these tables — one row per
command, with verb, description, arguments, reply shape and subsystem. It is a
report, not a source: edit `commands.json` and regenerate.

    openair-yak build-list             # rewrite both files
    openair-yak build-list --check     # exit 1 if stale

Rows are sorted by family, model, verb, command, so a regeneration after an edit
diffs as the edit rather than as whatever order the dict happened to be written
in. `--check` is the form worth wiring into a pre-commit hook: a sheet that
silently lags the tables is worse than no sheet, because it still reads as an
inventory.

The `Unverified` column is the one to read first — 86% of the rows carry it. A
sheet without it looks like 3646 working commands.

## Regenerating the trees

`<Family>/<Model>/commands_tree.md` is the other generated view: the same
vocabulary drawn as the SCPI tree it actually is, mnemonic by mnemonic, with the
verb, arguments and reply shape on each leaf. The table is a flat dict of command
names because that is what the runtime wants; this is the shape a human needs to
see what a panel can address.

    openair-yak build-trees            # rewrite every tree
    openair-yak build-trees --check    # exit 1 if stale

Only the block between the `BEGIN GENERATED` / `END GENERATED` markers is
rewritten. Everything below them is left alone — five of these files were written
by hand and carry knowledge no generator has, like the fact that a 66000A module
is unreachable until you select its slot. Write prose under the markers, not
above them.

Where a family has hand-written notes (`Load/`, `Power/`), each model's tree links
up to them. `LCR/commands_tree.md` gets no link from `LCR/4263A`: it is
byte-identical to `Load/commands_tree.md` and describes the 6060B electronic load,
so there is nothing in it about an LCR meter to link to.

## Where the vocabulary came from

| | commands | source |
|---|--:|---|
| Scope/DS1104Z | 760 | `MSO1000Z_DS1000Z_ProgrammingGuide_EN.md` |
| Distortion/Porta_one | 608 | `P1PA-DD_GPIB_Programming_Ref_Manual_rev2.pdf` — the PDF's font is offset by a constant 29, which is why its markdown conversion is mojibake; shifting back recovers it |
| Scope/54641D | 437 | `54621_Programmers guide.md` |
| Generator/33210A, 33220A | 254 | `33220_Quick command guide.md` + user guide |
| Spectrum/N9340B | 223 | `N9340B_Programming Guide.md` |
| Power/66101A–66104A | 187–192 | `66000A - 5959-3362 Programming guide.md` |
| DMM/34401A | 155 | `HP 34401A user_s guide.md` |
| Load/6060B | 123 | `06060-90005 - Programming.pdf` Table 4-1 — a 93-page scan with no text layer, read visually |
| Spectrum/HPE4411A, N9342CN | 28 | authored; no manual swept |
| Router/3235 | 8 | authored; manual is PDF-only and unread |
| LCR/4263A | 28 | `4263A/Raw Commands.txt` — a subsystem table someone typed up, not the manual |

## Gaps

`Distortion/HP_8903B` has no table at all and no source material next to it; its
manual is PDF-only.

`LCR/4263A` now has one, built from the `Raw Commands.txt` sitting beside it —
every row `unverified`, since that file is a hand-typed subsystem summary and
nothing has been sent to the meter. Two liberties the source forced: the optional
nodes it prints in brackets are dropped to their short form
(`:SOURce:VOLTage[:LEVel][:IMMediate]` → `:SOURce:VOLTage <level>`), and it lists
parameters without naming their arguments, so every one is a single-argument SET
with an argument named after what it sets. Same caveat as the manual sweep: no
RIG, because "these arguments are atomic" was not recoverable.

That table binds nothing yet. `BackEnd/Instruments/LCR/LCR.json` is not an LCR
panel — it is a copy of the DC load panel, every actuator carrying
`message_details/DC_LOAD_MODEL`, and `LCR/commands_tree.md` here is byte-identical
to `Load/commands_tree.md` and describes the 6060B. The 4263A has a vocabulary
and no front panel.

`Spectrum/HPE4411A` and `N9342CN` were never swept; both have a programming guide
in markdown. So does the 8712ES/8714ES network analyzer, which has no model here
at all.

The audit also lists the **ESA-L1500A** as an instrument with no YAK model. It
almost certainly has one: its programmer's guide is filed as `HP - E441190003` —
part number E4411-90003 — and `Spectrum/HPE4411A` is that instrument. Sweeping
that guide would settle both the 28-command vocabulary and the limits its
`model.json` currently carries on assumption.

All three Spectrum models now have a `model.json`, and all three declare
`"unverified": true`. Their frequency coverage is solid and is the number the
sheet exists for — one panel over a 1.5 GHz, a 3 GHz and a 7 GHz analyzer, where
the template today hardcodes 6000 MHz for all of them. The RBW/VBW/attenuation
and sweep bounds are datasheet recall and want a manual before a widget is clamped
to them. Nothing reads them yet: no Spectrum command carries an `arg.domain`, so
wiring them means naming the domain on the frequency and amplitude SETs. Mind the
units when you do — the Spectrum panel's widgets are authored in MHz and kHz,
these sheets are in Hz like every other `model.json`.

The Router panels bind `Set_Relay_Card4` … `Set_Relay_Card9`, 24 bindings, and
**no such commands exist** in `Router/3235` — its vocabulary is
`Close_Channels` / `Open_Channels` / `Select_Channel`. Those bindings have never
resolved; they predate this conversion. ``openair-yak crossref`` counts a
widget as BOUND when it carries a `yak_handler`, without checking the command
resolves, which is why it reports the Router as finished.
