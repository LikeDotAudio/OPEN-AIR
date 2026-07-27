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

Nothing in the frontend reads this directory. `Deployment/build_instrument_panels.py`
does, and writes the instances into `FrontEnd/Gui_Frames/1_Instruments/left_50/`
(generated, gitignored).

## manifest.json

    "<KB type>": {
      "tab":     "<folder name for the generated tab group>",
      "panel":   "<subdirectory instantiated ONCE PER DEVICE>",
      "exclude": ["<subdirectory of `panel` to skip>", ...]
    }

`panel` names the single-instrument variant. Everything else in a type directory
is library: bank panels (`1_Instrument_Bank_4`), multi-device views (`2_All_8`),
model-specific alternatives (`2_Instrument_Rigol`). They are kept because they
are authored work worth not losing, and because a future model→template map can
select them; they are simply never instantiated per device.

`exclude` exists because some single-instrument folders contain a multi-device
child (the DMM's `1_Instrument_Bank_8_ctrl`), which would otherwise appear as a
sub-tab under every one of the eight generated DMMs.

## Device binding

The builder injects two keys into every `yak_handler` block it copies:

    "target": "OpenAir/System/Protocols/visa/Device/<type>/<model>/Dev<n>/Write"
    "model":  "<model>"

`target` is the topic the VISA daemon executes SCPI on, so the instance drives
its own instrument instead of YAK's global (unconsumed) publish topic. `model`
makes YAK look up SCPI in that model's command table rather than falling back to
"first match in any model".

## Known gap

Only the Spectrum and Router templates currently carry `yak_handler` blocks. The
DMM, Oscilloscope, Generator, Power, Load, LCR and Distortion panels render, and
are bound, but declare no commands — so their controls still send nothing. The
SCPI vocabulary for those models already exists under
`BackEnd/ComProtocols/openair-yak/10_Yak/<n>_<TYPE>_YAK/<model>/`; wiring each
widget to a command is per-type authoring work that has not been done.
