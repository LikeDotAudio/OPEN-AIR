# Instrument panel templates

The authored control surface for each instrument FAMILY, one directory per
device type as named by the VISA knowledge base
(`BackEnd/openair-yak/Yak/knownDevices.json` — `34401A → DMM`).

These used to live in `FrontEnd/Gui_Frames/1_Instruments/left_50/`, where they
were a *display*: one hand-placed DMM tab regardless of how many DMMs were on
the bench, bound to no instrument in particular. A bench with eight 34401As got
one panel and a bank widget. Here they are a *template library* instead: the
panel builder stamps one instance per discovered device, so eight DMMs produce
eight tabs, each bound to its own VISA resource.

Nothing in the frontend reads this directory, which is why it carries no `#_`
ordering prefixes: those are the UI's tab-order mechanism and mean nothing here.
Generated output takes its ordering from `manifest.json` and from key order
within the files below.

`BackEnd/Core/orchestrator/gui/build_instrument_panels.py` is the only reader, and it
writes the instances into `FrontEnd/Gui_Frames/1_Instruments/left_100/`
(generated, gitignored) — `_100` because an instrument panel now takes the FULL
tab width. The `right_50` half it used to sit beside is iced at
`1_Instruments/__right_50/`; the `__` prefix is what makes the tree walkers skip
it (`BackEnd/Core/orchestrator/src/api.rs`, `BackEnd/Core/orchestrator/gui/build_api_artifacts.py`),
so it stays in the repo but never reaches the UI. Rename it back to restore.

## Two files, no folders

    <Type>/<Type>.json      the instrument       — stamped ONCE PER DEVICE
    <Type>/<Type>_N.json    N of the instrument  — the block that repeats

That is the whole layout. A type with no group view (Spectrum, Router, LCR,
Distortion, Generator, Load today) has only the first file.

Sub-tabs used to be authored as nested folders — `Spectrum/Instrument/`
held `amplitude/`, `bandwidth/`, `frequency/`, `markers/` and `traces/`, five
directories to hold five panels, and `Power/Instrument/One_instrument/` was two
levels of folder around a single file. The frontend builds tabs from folders
(`WindowManager.TabContainer`), so the folders were doing real work — but they
were doing it in the *generated* tree, where the builder can just as well put
them. They are top-level keys now:

    Spectrum.json   {"amplitude": {…}, "bandwidth": {…}, …}
                    ->  0_amplitude/  1_bandwidth/  …   one tab each

Key order is tab order. A key whose value is a panel node (it has a `type`)
is one panel; a key holding a MAP of nodes is one tab carrying several stacked
panels — the Router's `Coax` tab is two cards that way. That either-a-node-or-a-
map test is the same one `LoaderOrchestrator` already makes on a file's own
root. **One key and one panel means no sub-tab at all**: the panel lands
straight in the device folder, which is how the single-panel types have always
rendered.

The `<i>_` prefix the builder puts on generated folder names is the UI's sort
key; `OaTopicMaker` strips it back off, so numbering the tabs never moves a
widget's MQTT topic.

### The N file

One OcaBin, and inside it the block that repeats plus any header decks as
siblings:

    Power_N.json
      Power_Unit_${n}          OcaBin
        blocks:
          PSU_Module_${n}      <- repeats, once per member
          Global_Logger_Deck   <- header, asked for by name
          Master_Override_Deck <- header, asked for by name

The repeating block is the one carrying `${n}` in its name — already the thing
that makes N copies N distinct panels rather than one panel claiming to exist
N times. Every other block is a header: a strip that commands the whole group
(`OUTP:ALL`) instead of one member, which a group spec requests by block name.
Power's bank-of-eight takes the logger and its quads take the interlock, out of
one file.

It is an ordinary panel file, so it opens in the WYSIWYG editor like anything
else. Grouping unwraps it: the repeating block becomes one field of a generated
station block. That is the same shape the hand-authored `psu_four.json` /
`psu_eight.json` had; the difference is that it is reached by composition
instead of by copy-paste.

## manifest.json

    "<KB type>": {
      "tab":    "<folder name for the generated tab group>",
      "groups": [ <group spec>, ... ]
    }

Both template paths are convention now, so the manifest names neither. A
**group spec** declares a multi-unit view instead of authoring one:

    {
      "name":   "0_Bank_All",             // folder under the tab
      "header": "Global_Logger_Deck",     // optional deck block from <Type>_N.json
      "over":   "devices" | "channels",
      "by":     "chassis" | "host",       // `over: devices` only
      "size":   2 | 4 | "all",            // `over: devices` only
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
the model's capability sheet at `BackEnd/openair-yak/Yak/<TYPE>/<model>/model.json`:

    { "model": "66101A", "channels": 1, "watts": 128,
      "domains": { "volt": {"units": "V", "min": 0, "max": 8},
                   "curr": {"units": "A", "min": 0, "max": 16} } }

This is what makes one template enough. The eight modules in this mainframe are
four different models spanning 8V/16A to 60V/2.5A, so a hand-authored bank of 8
has one set of widgets for instruments that do not share a range — the 8V strip
and the 60V strip were the same strip. Only the builder, which sees the
discovery table, knows which model is in which slot.

`channels` feeds `over: "channels"` the same way. Before these files existed the
ranges were English in the knowledge base ("Module 8V / 16A (128W)") and the
scope's channel count was a description field reading "1, 2, 3, 4" — so the
Rigol, a 4-channel scope, was handed the 2-channel Agilent template.

## Known gaps

**97 widgets still carry literal SCPI** in `message_details.*.command_value`
instead of a `yak_handler`, so they render, and are bound, and send nothing.
Three distinct cases, and only the first is a mechanical edit:

* **12 are dead duplicates** — all in `DMM.json`, where the widget already has
  a working `yak_handler` and the literal beside it is a leftover. Deleting the
  `command_value` key changes no behaviour. (Delete the key only: the sibling
  `style` in the same `message_details` block is what draws the widget's
  active/inactive states.)
* **16 map onto a YAK command that already exists** — `Load.json` is 10 of
  them (`CURR <value>` → `Set_Current_Level`, `TRAN:DCYC <value>` →
  `Set_Transient_Duty`, …), plus `INIT`/`READ?` on the DMM and `TIM:SCAL`/
  `TIM:OFFS` on the scope.
* **69 have no YAK command to point at.** The vocabulary has to be written in
  `BackEnd/openair-yak/Yak/<TYPE>/<model>/` first. Whole families are missing:
  `LCR/4263A/` and `Distortion/HP_8903B/` have zero commands, and the four
  66000A tables have no per-slot `MEAS:VOLT?` at all — only `Get_Values`, which
  is hardcoded to `INST:NSEL 1`.

Where a literal and a table both exist they frequently disagree, which is the
argument for handlers rather than an accident: the scope panels send
`CHAN1:SCAL` and `ACQ:STATE`, while the 54641D's table says
`CHANnel<n>:RANGe` and the Rigol's says `:CHANnel<n>:SCALe`. One literal cannot
be right for both instruments; a command name resolved per model can.

`LCR/LCR.json` is a byte-for-byte copy of `Load/Load.json`, down to the
`Load_Instrument` root key and the `DC_Load_Station` block — an LCR meter gets a
DC electronic load's control surface. `Distortion/Distortion.json` is the same
panel with the labels changed. Both need authoring, not collapsing.

`_datasets/spectrum_presets.json` is not a panel — its `blocks` is a list of
preset rows (station names, start/stop frequencies, RBW) rather than a widget
tree. It sat under `Spectrum/Presets/DataSet/` where nothing read it; parked
here until something does.
