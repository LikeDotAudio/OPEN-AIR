# YAK command tables

The SCPI vocabulary, one file per instrument model:

    <Family>/<Model>/commands.json    what the model ACCEPTS — the command table
    <Family>/<Model>/model.json       what the model IS — channels, V/A ranges
    <Family>/<Model>/commands_tree.md hand-written SCPI reference for the model

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

`<chan>` and `<slot>` are **not** arguments. They identify the instance and are
stamped per panel by `Deployment/build_instrument_panels.py`, then substituted by
`verbs::apply_params` before the widget's value goes in.

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
command, with verb, description, arguments and subsystem. It is a report, not a
source: edit `commands.json` and regenerate.

## Gaps

`LCR/4263A` and `Distortion/HP_8903B` have no table at all — `Raw Commands.txt`
next to the former is the source material. Their panels therefore have nothing
to bind to, which is 15 of the controls listed in
`BackEnd/Instruments/Instrument functions.csv` as unbound.

The Router panels bind `Set_Relay_Card4` … `Set_Relay_Card9`, 24 bindings, and
**no such commands exist** in `Router/3235` — its vocabulary is
`Close_Channels` / `Open_Channels` / `Select_Channel`. Those bindings have never
resolved; they predate this conversion. `Deployment/yak_crossref.py` counts a
widget as BOUND when it carries a `yak_handler`, without checking the command
resolves, which is why it reports the Router as finished.
