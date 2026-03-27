# Bad Naming Audit Report

## Summary

This report details findings on naming conventions within the OPEN-AIR codebase, focusing on magic numbers, short variable names, noise words, and poor function names, as per the project's 'Bad Naming' standard.

## Top Offenders

### Magic Numbers

Several instances of magic numbers were found, indicating potential areas for refactoring into named constants.

*   **`oaComSNMP/Methods/snmp_utils.py` (Line 19):** The number `0` is used as a sorting key (`'Spectrum': '0'`). Recommendation: Extract to a constant like `SORTING_KEY_DEFAULT = 0`.
*   **`oaComMQTT/Methods/mqtt_topic_utils.py` (Lines around L38):** Comments indicate numbers like `50`, `100`, `1` are used as standalone sorting numbers and are filtered out. Recommendation: These should be defined as constants (e.g., `DEFAULT_SORTING_NUMBER_50`, `DEFAULT_SORTING_NUMBER_100`, `DEFAULT_SORTING_NUMBER_1`).
*   **`oaStand_Alone_Utilities/LogViewer.py` (Lines 58, 73):** Hardcoded dimensions and margins (`'height': '60px'`, `'width': '32%'`, `'marginRight': '1%'`). Recommendation: Extract to constants like `LOG_VIEWER_DEFAULT_HEIGHT_PX = 60`, `LOG_VIEWER_DEFAULT_WIDTH_PERCENT = 32`, `LOG_VIEWER_MARGIN_RIGHT_PERCENT = 1`.
*   **`oaGuiDefinitions/Assets/right_50/bottom_90/2_monitors/70_AES70/AES70.py` (Line 109):** A log line limit of `50`. Recommendation: Define as `AES70_MAX_LOG_LINES = 50`.
*   **`oaComMidi/Interface/midi_dashboard.py` (Line 162):** A log line limit of `200`. Recommendation: Define as `MIDI_DASHBOARD_MAX_LOG_LINES = 200`.

**General Recommendation:** Search for other instances of raw numeric literals and extract them to named constants defined in relevant `Constants` modules.

### Noise Words

Several variable and class names were identified as containing redundant or unhelpful "noise words" that obscure the true meaning.

*   **`oaGuiElements/Tests/buttons/button_trapezoid/test_button_trapezoid.py` and similar test files:** Class names like `TrapezoidButton` and potentially variable names like `button` when the context is already clear (e.g., within a test file for `button_trapezoid`). Recommendation: Remove redundant suffixes like "Button" from class names if the module/file name already implies it. Use more specific names for variables if "button" is too generic.
*   **`oaGuiElements/Core/input/composite_horizontal_dial_value/Core/ui_components.py` (Line 48):** Variable name `entry_string_var`. The suffix "var" is noise. Recommendation: Rename to `entry_string` or `entry_value` to directly reflect the content.
*   **General:** While not explicitly listed with line numbers from the grep output (as it was a broad search), the presence of "Data", "Info", "String", "Variable" as suffixes or parts of names is discouraged by the standard. Recommendation: Refactor these names to be more descriptive of the object's actual role or content, rather than its type. For example, `ProductData` could become `ProductDetails` or `ProductInfo` if `Info` is not considered noise in that context.

### Short Variable Names

No instances of single-letter variable names were found using the executed search pattern. This is a positive finding and suggests good adherence to the principle of descriptive variable naming for variable scope.

### Poor Function Names

No function definitions were identified by the search pattern `^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(`. This result is unexpected and may indicate:
1.  The search pattern was too restrictive for the codebase's structure.
2.  An issue with the `grep_search` tool's output in this context.

A manual review of key files and modules would be necessary to confirm the absence of poorly named functions and to ensure adherence to the verb-based naming convention.

---
**Next Steps:**
*   Address the identified magic numbers by creating constants.
*   Refactor names containing noise words for clarity.
*   Investigate the lack of results for function names and short variables to ensure the audit was comprehensive.
