# Instrument panel templates

The authored control surface for each instrument FAMILY, one directory per
device type as named by the VISA knowledge base
(`BackEnd/ComProtocols/openair-visa/assets/visa_devices.json` — `34401A → DMM`).

These used to live in `FrontEnd/Gui_Frames/1_Instruments/left_50/`, where they
were a *display*: one hand-placed DMM tab regardless of how many DMMs were on
the bench, bound to no instrument in particular. A bench with eight 34401As got
one panel and a bank widget. Here they are a *template library* instead: the
panel builder stamps one instance per discovered device, so eight DMMs produce
eight tabs, each bound to its own VISA resource.

Nothing in the frontend reads this directory, which is why it carries no `#_`
ordering prefixes: those are the UI's tab-order mechanism and mean nothing here.
Generated output takes its ordering from `manifest.json` instead.

`Deployment/build_instrument_panels.py` is the only reader, and it
writes the instances into `FrontEnd/Gui_Frames/1_Instruments/left_100/`
(generated, gitignored) — `_100` because an instrument panel now takes the FULL
tab width. The `right_50` half it used to sit beside is iced at
`1_Instruments/__right_50/`; the `__` prefix is what makes the tree walkers skip
it (`BackEnd/Core/orchestrator/src/api.rs`, `Deployment/build_api_artifacts.py`),
so it stays in the repo but never reaches the UI. Rename it back to restore.

## Three kinds of file

    <Type>/<panel dir>/…    stamped ONCE PER DEVICE — the instrument's own tab
    <Type>/_unit/…          the repeating unit: one module, one channel, one meter
    <Type>/_decks/…         a header block prepended to a group view

A **unit** is an ordinary panel file — one OcaBin holding one block — so it opens
in the WYSIWYG editor like anything else. Grouping unwraps it: the block becomes
one field of a generated station block. That is the same shape the hand-authored
`psu_four.json` / `psu_eight.json` had; the difference is that it is reached by
composition instead of by copy-paste.

## manifest.json

    "<KB type>": {
      "tab":     "<folder name for the generated tab group>",
      "panel":   "<subdirectory instantiated ONCE PER DEVICE>",
      "exclude": ["<subdirectory of `panel` to skip>", ...],
      "groups":  [ <group spec>, ... ]
    }

A **group spec** declares a multi-unit view instead of authoring one:

    {
      "name":   "0_Bank_All",                      // folder under the tab
      "unit":   "Power/2_Modules/psu_module.json", // repeated per member
      "header": "Power/_decks/global_logger.json", // optional deck on top
      "over":   "devices" | "channels",
      "by":     "chassis" | "host",                // `over: devices` only
      "size":   2 | 4 | "all",                     // `over: devices` only
      "columns": 4,
      "station": "<block name>",
      "id": "<OCA id>",
      "description": { "En": …, "Fr": …, "De": …, "Es": … }
    }

`over: "devices"` repeats across instruments that belong together — the bank of
8, the quads, the pairs. `by` picks what "together" means: `chassis` for modules
sharing a mainframe (the eight 66000A modules at `gpib7,30,0-7`), `host` for
instruments that share only a bench (the eight 34401As, each at its own GPIB
primary address). A group of one is skipped; that is just the device's own panel.

`over: "channels"` repeats *within* one instrument, once per channel its model
declares. Two 54641Ds and a 4-channel Rigol are three devices whose panels differ
only in how many identical channel strips they carry.

## Device binding

The builder injects into every `yak_handler` block it copies:

    "target": "OpenAir/System/Protocols/visa/Device/<type>/<model>/Dev<n>/Write"
    "model":  "<model>"
    "params": {"chan": "<slot or channel>"}

`target` is the topic the VISA daemon executes SCPI on, so the instance drives
its own instrument instead of YAK's global (unconsumed) publish topic. `model`
makes YAK look up SCPI in that model's command table rather than falling back to
"first match in any model".

`params` are the constants that identify this instance *within* its instrument,
substituted by YAK before the widget's value (`openair-yak/src/verbs/mod.rs`,
`apply_params`). The command table is per model and four of the eight modules
here are 66104As, so the slot cannot live in the table — which is why every
module command used to read `INST:NSEL 1`, addressing slot 1 whichever module
the panel was for. The same bug existed on the scope, where `1_Channel_2/` was a
copy of `1_Channel_1/` still sending `CHAN1:SCAL`.

## Template substitution

Unit and deck templates use `${n}`, `${slot}`, `${chan}`, `${model}`,
`${resource}` and `${label}`, filled in at build time — in values *and* in key
names, because a panel's identity in the frontend tree is its top-level key.

Deliberately **not** `<name>`: panels carry SCPI fragments (`"command_value":
"VOLT <value>"`) and YAK's command tables use `<chan>`, `<n>`, `<slot>`. Two
substitution passes run over this data — the builder's at build time and YAK's
at send time — and sharing a delimiter is how a slot number ends up where a
voltage belongs.

## Limits come from YAK

A widget marked `"yak_domain": "volt"` gets `units`, `min` and `max` copied from
the model's capability sheet at
`BackEnd/openair-yak/Yak/<TYPE>_YAK/<model>/model.json`:

    { "model": "66101A", "channels": 1, "watts": 128,
      "domains": { "volt": {"units": "V", "min": 0, "max": 8},
                   "curr": {"units": "A", "min": 0, "max": 16} } }

This is what makes one template enough. The eight modules in this mainframe are
four different models spanning 8V/16A to 60V/2.5A, so a hand-authored bank of 8
has one set of widgets for instruments that do not share a range — the 8V strip
and the 60V strip were the same strip. Only the builder, which sees the
discovery table, knows which model is in which slot.

`channels` feeds `over: "channels"` the same way. Before these files existed the
ranges were English in `visa_devices.json` ("Module 8V / 16A (128W)") and the
scope's channel count was a description field reading "1, 2, 3, 4" — so the
Rigol, a 4-channel scope, was handed the 2-channel Agilent template.

## Known gaps

Only the Spectrum, Router and DMM single-instrument templates carry
`yak_handler` blocks. The Oscilloscope, Generator, Power, Load, LCR and
Distortion panels render, and are bound, but declare their commands as legacy
`message_details` / `command_value` — so their controls still send nothing, and
the `params` and `target` stamping above has nothing to attach to. The SCPI
vocabulary for those models already exists under
`BackEnd/openair-yak/Yak/<TYPE>_YAK/<model>/`; converting each widget is
per-type authoring work that has not been done.

`LCR/1_Instrument/LCR.json` is a byte-for-byte copy of `Load/1_Instrument/dc_load.json`,
down to the `Load_Instrument` root key and the `DC_Load_Station` block — an LCR
meter gets a DC electronic load's control surface. `Distortion/1_Instrument/distortion.json`
is the same panel with the labels changed. Both need authoring, not collapsing.
