# Bad File/Folder Naming & Improper Containerization Audit

**Date**: 2026-03-18  
**Architect**: Gemini Systems Architect  
**Status**: 🟡 IMPROVING (Transitional)

## Executive Summary
Since the previous audit, significant progress has been made: foundational modules have been renamed (`oaDependencies`, `oaInstallation`, `oaComBroker`) and Level 1 Infrastructure has been realigned. However, the **Root File Plague** remains critical in Level 2 and Level 3 modules. The 12-folder standard is now established as a project baseline, but manual realignment is required for the remaining 80% of the codebase.

---

## 1. Top Offenders: Bad Naming (New & Remaining)

| File/Folder | Violation | Suggested Refactor |
| :--- | :--- | :--- |
| `oaComBroker/AES70` | **Naming Inconsistency**: Folder name is all-caps, unlike `protocol_router`. | `oaComBroker/Core/aes70/` |
| `midi.py` (in `oaComMidi`) | **Intention-Blind**: General name sitting at root. | `oaComMidi/Managers/midi_manager.py` |
| `osc.py`, `osc_rx_server.py` | **Noise Word**: Sitting at root. | Move to `Managers/` and `Workers/`. |
| `snmp_utils.py`, `mqtt_topic_utils.py`| **Noise Word**: Meaningless distinction "utils". | Rename to `snmp_helpers.py` or `topic_formatter.py`. |
| `*_mixin.py` | **Pattern Encoding**: Encoding 'Mixin' in the filename. | Focus on the responsibility (e.g., `StateSync.py`). |

### Magic Numbers & Boolean Blindness
- **oaComBroker/Core/protocol_router/settle.py**: Hardcoded `0.050` (50ms) for settling logic. Should be a named constant in `Constants/`.
- **oaComBroker/Core/protocol_router/monitor.py**: Magic number `2000` for buffer size.
- **oaComMQTT/Entry.py**: Magic number `1883` for port. Should pull from `Config`.

---

## 2. Improper Containerization (Remaining Scatters)

### The "Root File" Plague (Remaining Level 2/3)
The following modules still have primary logic files sitting in the root:
- **oaComMidi**: `midi.py`
- **oaComOSC**: `osc.py`, `osc_rx_server.py`, `osc_tx_client.py`
- **oaComSNMP**: 6 files sits at root.
- **oaComVisa**: 8 files sits at root (despite having `Managers/` and `Workers/` folders).
- **oaTranslator**: 10+ `yak_*` files sitting at root.

### Scatter: GUI Definitions
`oaGuiDefinitions` remains a massive flat directory of 50+ JSON files.
- **Offender**: Mixing Agilent equipment with Yak protocols and general connection dialogs.
- **Recommendation**: Sub-group into `oaGuiDefinitions/Agilent/`, `oaGuiDefinitions/Yak/`, etc.

---

## 3. Realignment Progress (The "Clean" List)
The following modules are now **100% Compliant** with the 12-folder & Entry.py standard:
- [x] **oaConfiguration**
- [x] **oaLogging**
- [x] **oaOchestration**
- [x] **oaComBroker**
- [x] **oaComMQTT**

---

## 4. Specific Refactoring Roadmap (Next Steps)

1.  **Phase 2 Realignment**: Target `oaComVisa` and `oaComMidi`. These are high-traffic modules with cluttered roots.
2.  **Phase 3 Realignment**: Target `oaTranslator` (The Yak Engine). This is the most complex scatter.
3.  **Magic Number Consolidation**: Extract hardcoded timeouts and buffers into module-specific `Constants/` folders.
4.  **Rename Mixins**: Transition from `*_mixin.py` to responsibility-based naming (e.g., `InteractionHandler.py`).

## Conclusion
The architectural foundation is now solid. The "Root File Plague" is being systematically eradicated. Priority for the next session should be the realignment of the hardware protocol modules (`oaCom*`) to ensure they match the professional **Encapsulated Module** standard.
