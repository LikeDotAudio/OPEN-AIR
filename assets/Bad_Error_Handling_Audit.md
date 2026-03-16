# Bad Error Handling Audit Report

## Executive Summary
Analyzed codebase for silent failures, generic catches, and muddled error flows.
- **Files with Issues**: 113
- **Total Violations**: 165

## Top Offenders (Silent Failures & Bare Excepts)

### managers/Visa_Fleet/Prototype/cli_visa_find.py
- Line 50: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception:`
- Line 75: **Bare except block** (Severity: High)
  `except:`
- Line 86: **Bare except block** (Severity: High)
  `except:`
- Line 181: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception:`
- Line 196: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception:`
- Line 214: **Bare except block** (Severity: Medium)
  `except:`
- Line 255: **Bare except block** (Severity: Medium)
  `except:`
- Line 72: **Bare except block** (Severity: High)
  `except:`
- Line 200: **Bare except block** (Severity: High)
  `except:`

### workers/discovery_agents/agent_mdns_zeroconf.py
- Line 66: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception:`
- Line 90: **Bare except block** (Severity: High)
  `except: pass`
- Line 100: **Bare except block** (Severity: High)
  `except: pass`
- Line 88: **Bare except block** (Severity: High)
  `except: pass`
- Line 129: **Bare except block** (Severity: High)
  `except: pass`

### managers/Display/factory/button_canvas_base.py
- Line 145: **Bare except block** (Severity: Medium)
  `except: r_c, g_c, b_c = 255, 150, 0`
- Line 167: **Bare except block** (Severity: Medium)
  `except: font = ImageFont.load_default()`
- Line 204: **Bare except block** (Severity: Medium)
  `except: r_c, g_c, b_c = 255, 150, 0`
- Line 221: **Bare except block** (Severity: Medium)
  `except: font = ImageFont.load_default()`

### workers/builder/composite_horizontal_dial_value/core/state_sync.py
- Line 12: **Bare except block** (Severity: Medium)
  `except: decimal_places = 2`
- Line 38: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception: pass`
- Line 47: **Bare except block** (Severity: Medium)
  `except: return main_val`
- Line 64: **Bare except block** (Severity: High)
  `except: pass`

### workers/logic/state_mirror_engine.py
- Line 108: **Bare except block** (Severity: Medium)
  `except: return False`
- Line 134: **Bare except block** (Severity: Medium)
  `except: return`
- Line 180: **Bare except block** (Severity: High)
  `except: pass`
- Line 185: **Bare except block** (Severity: High)
  `except: pass`

### workers/Command_Router/SNMP/snmp_tester.py
- Line 122: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception as e:`
- Line 38: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception as e:`
- Line 67: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception as e:`
- Line 80: **Bare except block** (Severity: High)
  `except: pass`

### display/right_50/bottom_90/2_monitors/22_Yak_Monitor/gui_yak_monitor.py
- Line 224: **Bare except block** (Severity: Medium)
  `except:`
- Line 264: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception:`
- Line 70: **Bare except block** (Severity: Medium)
  `except:`
- Line 294: **Bare except block** (Severity: Medium)
  `except:`

### assets/Stand_Alone_Utilities/SUB_APP_CSV_to_json_APP/csvtojson.py
- Line 80: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception as e: messagebox.showerror("Error", str(e))`
- Line 90: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception as e:`
- Line 106: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception as e: messagebox.showerror("Error", str(e))`

### workers/builder/core/slicing_registry.py
- Line 44: **Bare except block** (Severity: High)
  `except: pass`
- Line 38: **Bare except block** (Severity: High)
  `except: pass`
- Line 87: **Bare except block** (Severity: High)
  `except: pass`

### display/right_50/bottom_90/2_monitors/50_MIDI/gui_midi.py
- Line 36: **Bare except block** (Severity: Medium)
  `except: break`
- Line 150: **Bare except block** (Severity: High)
  `except: pass`
- Line 125: **Bare except block** (Severity: Medium)
  `except: channel = 0`

### display/right_50/bottom_90/4_Splinker/222_Editor/gui_splinker_editor.py
- Line 138: **Bare except block** (Severity: High)
  `except: pass`
- Line 151: **Bare except block** (Severity: High)
  `except: pass`
- Line 210: **Generic Exception catch without proper logging** (Severity: Medium)
  `except Exception as e:`

### managers/Display/builder/async_grid_renderer.py
- Line 43: **Bare except block** (Severity: High)
  `except: pass`
- Line 71: **Bare except block** (Severity: Medium)
  `except: on_complete()`

### workers/wysiwyg_editor/workspaces/core/layout/overlay.py
- Line 21: **Bare except block** (Severity: High)
  `except: pass`
- Line 58: **Bare except block** (Severity: High)
  `except: pass`

### workers/builder/panels/core/utils.py
- Line 12: **Bare except block** (Severity: Medium)
  `except: return (128, 128, 128, 255)`
- Line 22: **Bare except block** (Severity: Medium)
  `except: return (128, 128, 128)`

### workers/builder/meter_bar/smart_meter.py
- Line 20: **Bare except block** (Severity: Medium)
  `except:`
- Line 111: **Bare except block** (Severity: High)
  `except:`

### workers/builder/circular_motion_displacement_potentiometer/cmdp_channel_handler.py
- Line 39: **Bare except block** (Severity: Medium)
  `except: angle = 0.0`
- Line 75: **Bare except block** (Severity: Medium)
  `except:`

### workers/builder/text_table/core/table_sync_engine.py
- Line 45: **Bare except block** (Severity: Medium)
  `except: return`
- Line 57: **Bare except block** (Severity: High)
  `except: pass`

### workers/builder/graphing/graph_styler.py
- Line 69: **Bare except block** (Severity: High)
  `except: pass`
- Line 77: **Bare except block** (Severity: High)
  `except: pass`

### workers/builder/graphing/core/graph_state_mixin.py
- Line 44: **Bare except block** (Severity: High)
  `except: pass`
- Line 58: **Bare except block** (Severity: High)
  `except: pass`

### workers/builder/graphing/core/graph_interaction_mixin.py
- Line 54: **Bare except block** (Severity: High)
  `except: pass`
- Line 61: **Bare except block** (Severity: High)
  `except: pass`

