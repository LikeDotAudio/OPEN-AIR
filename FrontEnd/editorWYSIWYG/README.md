# editorWYSIWYG — HTML5 WYSIWYG GUI editor

An in-browser editor for the OPEN-AIR `Gui_Frames` JSON definitions, modelled on
the Tkinter editor `oaGuiEditorWYSIWYG` from the previous generation (no longer
in this repository; an archived copy lives in `.crawler/`). It runs
inside the web frontend (`frontEnd/`) and reuses the live runtime renderer
(`LoaderOrchestrator` + `WidgetFactory`) as its WYSIWYG preview.

## Launching

Right-click any JSON-backed panel in the web UI → the editor opens full-screen
for that panel's file. `Esc` closes, `Ctrl/Cmd+S` saves.

Programmatic launch:

```js
window.launchWysiwygEditor({ filePath: "/Window_1/.../bandwidth.json", content: {...} });
```

`WindowManager` listens for the `oa-open-wysiwyg` window event and renders
`<window.WysiwygEditor>` inside the app tree (so it shares the MqttProvider
context and the live renderer).

## Folder ↔ function map (mirrors the Python editor)

| Path | Global | Role |
|------|--------|------|
| `Entry.jsx` | `launchWysiwygEditor` | Launch surface (event dispatch). |
| `Core/state.jsx` | `OaEdState`, `useEditorStore` | Central JSON state + pub/sub; path ops (get/set/delete/rename/reorder/move/insert). |
| `FileReaders/file_reader.jsx` | `OaEdFileReader` | Load a definition (via `/api/tree`). |
| `FileReaders/grab_bag_loader.jsx` | `OaEdGrabBagLoader` | Load + cache the palette (`/api/grabbag`). |
| `FileWriters/file_writer.jsx` | `OaEdFileWriter` | Save (`POST /api/save`, server writes a `.old` backup) + download fallback. |
| `Interface/layout_engine/snap_logic.jsx` | `OaEdSnap` | Grid snapping math. |
| `Interface/layout_engine/focus.jsx` | `OaEdFocus` | Screen-coord → element path (`data-oca-path`). |
| `Interface/layout_engine/overlay_manager.jsx` | `OaEdSelectionOverlay` | Selection outline over the preview. |
| `Interface/layout_engine/preview_engine.jsx` | `OaEdPreview` | Live preview via `LoaderOrchestrator`. |
| `Interface/layout_engine/ruler.jsx` | `OaEdRuler` | Pixel rulers. |
| `Methods/builder_editor_grid.jsx` | `OaEdGrid` | 100px grid backdrop. |
| `Interface/PropertyEditor/property_leaf.jsx` | `OaEdPropertyLeaf` | One editable field (bool/number/color/text). |
| `Interface/renderers/tree_renderer.jsx` | `OaEdPropertyTree` | Recursive property editor. |
| `Interface/Tabs/InteractiveLayout/interactive_layout.jsx` | `OaEdCanvas` | WYSIWYG canvas: select + drop + rulers + grid. |
| `Interface/Tabs/ElementProperties/Entry.jsx` | `OaEdProperties` | Inspector: rename/reorder/duplicate/delete + props. |
| `Interface/Tabs/JsonEditor/json_editor.jsx` | `OaEdJsonEditor` | Raw JSON, two-way synced. |
| `Interface/Tabs/TreeRefactor/Entry.jsx` | `OaEdTree` | Hierarchy: select/reorder/delete + drag-to-move. |
| `Interface/Tabs/GrabBagView/grab_bag_view.jsx` | `OaEdGrabBag` | Categorized draggable palette. |
| `Interface/Window/editor_toolbar.jsx` | `OaEdToolbar` | Save / Download / Close + dirty flag. |
| `Interface/Window/editor_layout.jsx` | `OaEdLayout` | Left tabs (Structure/JSON/Library) + canvas + properties. |
| `Managers/wysiwyg_editor.jsx` | `WysiwygEditor` | Overlay controller; wires Save + shortcuts. |

## Data model

State is the whole file object `{ rootKey: OcaBin }`. Paths are dot-strings,
e.g. `Spectrum_Instrument_bandwidth.blocks.Resolution Bandwidth.fields.RBW`
(GUI keys never contain `.`). Selection on the canvas relies on the
`data-oca-path` attribute emitted by `WidgetFactory`.

## Where the library (palette) comes from

`GET /api/grabbag` (`LauchWebserver.py → get_grab_bag()`) is the library source.
It is now **README-driven**: each `frontEnd/libControl/<category>/<Component>/Readme.md`
embeds one ```json sample block (see the "Sample (WYSIWYG library source)"
section in any component README). The server scans those READMEs first — they are
authoritative — and supplies each widget's palette entry, live preview, and
property manipulators from that block. It then falls back to
`oaGuiElements/*/sample.json` for any widget no README has provided (deduped by
sample name). `_LEGEND` arrays from either source become the property-editor
dropdowns. `Gui_Frames/Sample.json` is a generated catalog frame holding one
instance of every component — open it to see the whole library at once.

To add/change a widget in the editor: edit the JSON block in its component
README (or add a new component folder with a README) — no editor code change.

## Server requirement

The palette and save use endpoints in `frontEnd/Core/Launch/LauchWebserver.py`
(`GET /api/grabbag`, `POST /api/save`). **Restart the web server** after editing a
component README so the regenerated palette is live.

## Not yet implemented (vs. the Python editor)

Resize/drag handles on the canvas, snap-on-move, undo/redo, and MQTT "Test UI"
push. Selection, property editing, add (palette), reorder/move (tree), JSON
round-trip, and save-with-backup are functional.
