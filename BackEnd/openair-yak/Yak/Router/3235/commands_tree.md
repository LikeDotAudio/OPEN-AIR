<!-- BEGIN GENERATED — Deployment/build_yak_command_trees.py -->

# Router/3235 — command tree

Generated from `commands.json` by `Deployment/build_yak_command_trees.py`. Edit the table, not this file.

**8 commands** — SET 2 · RIG 0 · NAB 2 · DO 4 · 0 unverified (0%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Tree

- `CLOSE` — **SET** `Close_Channels` · `<channel_list>` · args: `channel_list`
- `OPEN` — **SET** `Open_Channels` · `<channel_list>` · args: `channel_list`
- `CLOSE?` — **NAB** `Query_Channel_State` · `<chan>` · per-instance: `chan` · → 1 value
- `ID?` — **NAB** `Query_Slot_ID` · `<slot>` · per-instance: `slot` · → 1 value
- `CRESET` — **DO** `Card_Reset` · `<slot>` · per-instance: `slot`
- `CLR` — **DO** `Clear_State`
- `RESET` — **DO** `Reset_System`
- `SELECT` — **DO** `Select_Channel` · `<chan>` · per-instance: `chan`

<!-- END GENERATED -->
