# YAK Protocol Specification (v2.0)

This document defines the structure and requirements for YAK (Yet Another 
Kommander) JSON command definitions used in the OPEN-AIR translation layer. 
These definitions map high-level GUI interactions to SCPI (Standard Commands 
for Programmable Instruments) strings.

## I. Structural Standards

The YAK translation engine requires strict adherence to naming conventions 
and nesting patterns to ensure the GUI renderer correctly associates inputs 
with actuators.

### 1. Naming Conventions
- **Input Fields**: Must be named exactly `Input`.
- **Output Fields**: Must be named exactly `Outputs`.
- **Actuator Button**: Within a settings block, the button must be named 
  `Execute Command`.

### 2. Architectural Patterns

There are two primary patterns for defining commands: the **Setting Construct** 
and the **Action Construct**.

#### Pattern A: The Setting Construct
Used for commands that require parameters (Inputs) or return data (Outputs), 
such as RIG, SET, or NAB operations.

- **Structure**: A parent `OcaBlock` encapsulates all related fields.
- **Actuator**: A sibling field named `Execute Command` (type `_GuiActuator`).
- **Data**: Sibling fields named `Input` or `Outputs` containing parameter 
  definitions.

**Example:**
```json
"Set_Vertical_Scale": {
  "type": "OcaBlock",
  "fields": {
    "Execute Command": {
      "type": "_GuiActuator",
      "AES70": "OcaBooleanActuator",
      "active": true,
      "message": ":CHAN1:SCAL <scale>",
      "layout": { "height": 30, "sticky": "" }
    },
    "Input": {
      "type": "OcaBlock",
      "fields": {
        "scale": { "value": "1.0", "type": "_GuiValue" }
      }
    }
  }
}
```

#### Pattern B: The Action Construct
Used for instant triggers or toggles with no parameters (e.g., Run, Stop, 
Auto), typically mapped to DO operations.

- **Structure**: The `_GuiActuator` may be the direct object.
- **Command**: The SCPI message is nested within an `Execute Command` object.

**Example:**
```json
"Do_Run": {
  "type": "_GuiActuator",
  "AES70": "OcaBooleanActuator",
  "active": true,
  "label_inactive": "RUN",
  "Execute Command": {
    "message": ":RUN"
  }
}
```

## II. Operational Dimensions

YAK files are organized into four functional categories:

1. **NAB (Status/Observation)**: For measurements and status queries. 
   Syntax typically ends in `?`. Uses Pattern A.
2. **RIG (System Configuration)**: For global instrument settings (Timebase, 
   Trigger, Acquisition). Uses Pattern A.
3. **SET (Component Parameters)**: For channel-specific settings (Vertical 
   Scale, Offset). Uses Pattern A.
4. **DO (Execution)**: For immediate actions (Run, Stop, Clear). Uses Pattern B.

## III. Implementation Checklist

Before deployment, verify the following:
- [ ] Use `Input` and `Outputs` (Case Sensitive) instead of legacy `scpi_*` keys.
- [ ] Ensure buttons in RIG/SET are named `Execute Command`.
- [ ] Nest SCPI messages for DO actions within an `Execute Command` object.
- [ ] Hardcode all channel identifiers; dynamic variables (e.g., `<n>`) are 
      not supported.
- [ ] Include `"AES70": "OcaBooleanActuator"` for all actuator types.

## IV. Reference Implementation

```json
{
  "set": {
    "type": "OcaBlock",
    "description": "Channel Settings",
    "fields": {
      "Configure_Channel_1": {
        "type": "OcaBlock",
        "description": "Vertical Setup CH1",
        "fields": {
          "CH1_Scale": {
            "type": "OcaBlock",
            "fields": {
              "Execute Command": {
                "type": "_GuiActuator",
                "AES70": "OcaBooleanActuator",
                "active": true,
                "message": ":CHANnel1:SCALe <scale>",
                "layout": { "height": 30, "sticky": "" }
              },
              "Input": {
                "type": "OcaBlock",
                "fields": { 
                  "scale": { "value": "1.0", "type": "_GuiValue" } 
                }
              }
            }
          }
        }
      }
    }
  },
  "Do": {
    "type": "OcaBlock",
    "description": "Actions",
    "fields": {
      "Run_Control": {
        "type": "OcaBlock",
        "fields": {
          "Do_Run": {
            "type": "_GuiActuator",
            "AES70": "OcaBooleanActuator",
            "active": true,
            "label_inactive": "RUN",
            "Execute Command": { "message": ":RUN" }
          }
        }
      }
    }
  }
}
```
