# OPEN-AIR Changelog

## [2026.03.16] - 23:00
### Fixed
- Fixed `AttributeError` in background panel generation by updating `PanelGenerator` calls to `generate_procedural_panel`.
- Fixed `NameError` in `FluxPlotter` graph initialization by correctly referencing the `graph` module.
- Resolved multiple thread failures occurring during dynamic GUI building.
