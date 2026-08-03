# Contracts Debt Inventory — Day One

*Generated 2026-07-17 by `pnpm validate` (openair-validate, Phase 1 step 4).
Full machine-readable report: [2026-07-17_day-one-report.json](2026-07-17_day-one-report.json).
This list is the deliverable the plan asked for — it is not a reason to
soften the schemas. The step-5 ratchet baselines it; the number only goes
down from here.*

## Totals

**169 errors · 2,093 deprecations** across 477 panel files, the YAK subtree,
the folder tree, and every BackEnd `config.ini`.

## Errors (169) — will gate CI once the step-5 ratchet arms

| Count | Code | What it is |
|---|---|---|
| 60 | `unknown-widget-type` | Types that render as the dashed fallback box — almost all the `tv` data-set entries under `5_Samples/10_Data_sets` (data living in the panel tree; needs a data-set schema or relocation) |
| 57 | `folder-order-collision` | Sibling folders claiming the same `N_` prefix — including `5_Protocols` vs `5_Samples` at the **root**, and the predicted `4_DMM_YAK`/`4_Load_YAK` |
| 45 | `config-ini-topic` | Declared-but-dead `topic_listen/publish/ignore` triples (`{proto}/pub|sub|ignore`) that no code uses and the grammar rejects — includes the three-way YAK listen-topic divergence |
| 3 | `root-entry-not-node` | `items`-array data files posing as panels (`Fleet_Display`, `MQTT`, `file_paths`) |
| 2 | `invalid-topic-override` | Panel `topic` overrides that parse against nothing (`OpenAir/System/Protocols/midi/pub` in `Midi_In.json`) |
| 1 | `yak-duplicate-model` | **The two 34401As**: `4_DMM_YAK/1_34401A` vs `8_Multimeter_YAK/1_34401A` |
| 1 | `dead-key:widget_type` | Key read by nothing (`Sample.json`) |

## Deprecations (2,093) — named, counted, ratcheted down

| Count | Code | What it is |
|---|---|---|
| 856 | `legacy-widget-type` | `_GuiValue` v0 discovered-frame widgets still in the tree |
| 655 | `legacy-label-form` | `label:{En:...}` on legacy widgets (the build_discovered_gui generation) |
| 163 | `data-model-type` | AES70 data-model strings (`OcaProperty`, `OcaMap<...>`, …) living in the panel tree |
| 233 | `legacy-flat-key:*` | Flat `units`(94)/`label_active`(74)/`label_inactive`(36)/`value_default`(27)/`min`(2)/`max`(2) instead of the nested pillars |
| 72 | `legacy-topic-override` | Panel topics targeting v40 namespaces (CommandRouter's yak monitor reads, etc.) |
| 46 | `yak-binding-lint` | Mostly converters the YAK agent does not implement — `int`, `bool_to_int`, `float`, `string` **silently pass through today** |
| 41 | `yak-legacy-file:*` | `_Legacy_Commands/`(32) + `temp_norm_*`(9) still ingested by the v40 loader |
| 20 | `config-ini-topic-legacy` | config.ini values aimed at legacy namespaces |
| 5 | `yak-duplicate-definition` | Byte-identical definition files in multiple models (the copy-paste spectrum drivers) |

## How to reproduce

```bash
pnpm --dir contracts validate                  # pretty report, exit 1 on errors
pnpm --dir contracts validate -- --report json # the full machine-readable inventory
pnpm --dir contracts validate -- --strict      # deprecations fail too (Phase 2 editor gate)
```
