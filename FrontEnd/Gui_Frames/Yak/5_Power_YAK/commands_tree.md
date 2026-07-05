The **Keysight (Agilent) 66101A – 66104A** series are **DC Power Modules**.

**Crucial Distinction:** Unlike the other devices you listed, these are **not standalone**. They are modules that slide into a mainframe (typically the **66000A MPS Mainframe**). A single mainframe can hold up to 8 of these modules.

Because of this, the SCPI tree has a vital extra layer: **`INSTrument`**. You must tell the mainframe *which* module you are talking to before you set a voltage.

```json
"6610xA": {
  "type": "DC Power Module", 
  "notes": "Requires 66000 Mainframe. Precision low-power (approx 150W)."
}

```

Here is the command tree, emphasizing the multi-channel workflow.

---

### **1. The `INSTrument` Subsystem (The Router)**

This is the most important step. If you don't select a channel, the mainframe might apply settings to the wrong module (or the last one accessed).

* **`INSTrument`**
* `:SELect` `1|2|3|4...`  Selects the active slot number (1–8).
* `:NSELect` `<number>`  Same as above, but strictly numeric (easier for code).
* `:COUPle` `ALL|NONE`  Allows you to send one command (like `OUTP ON`) to *all* modules simultaneously.



> **Usage:** `INST:SEL 2`
> (Now, all subsequent commands like `VOLT 5` apply *only* to the module in Slot 2).

---

### **2. The `SOURce` Subsystem (Setting V & I)**

Controls what the power supply generates. The keyword `SOURce` is optional.

* **`[SOURce:]`**
* **`VOLTage`**
* `[:LEVel]` `<volts>`  Set the output voltage.
* `:PROTection` `<volts>`  Set the **OVP** (Over Voltage Protection) trip point.


* **`CURRent`**
* `[:LEVel]` `<amps>`  Set the current limit.


* **`FUNCtion`** `VOLT|CURR`  Selects which mode is prioritized (CV vs CC), though usually handled automatically by the limits.



---

### **3. The `OUTPut` Subsystem (On/Off & Safety)**

Controls the physical connection to the load.

* **`OUTPut`**
* `:STATe` `ON|OFF`  Turns the output for the *selected* channel On or Off.
* `:PROTection`
* `:CLEar`  Resets the module if OVP or Over-Temp protection tripped.
* `:DELay` `<seconds>`  Delay before protection kicks in (for capacitive loads).


* `:PON` `RST|RCL0`  Power On state (Reset to zero, or Recall state 0).



---

### **4. The `MEASure` Subsystem (Readback)**

Asks the module: "What is physically coming out right now?"

* **`MEASure`**
* `:VOLTage?`  Reads the actual voltage at the terminals.
* `:CURRent?`  Reads the actual current flowing.
* **Note:** You can often combine these: `MEAS:VOLT?;CURR?` to get both in one line.



---

### **5. The `SYSTem` Subsystem (Global Mainframe)**

These commands apply to the entire chassis, not just one module.

* **`SYSTem`**
* `:ERRor?`  Read error queue.
* `:LANGuage` `SCPI|COMP`  Switch between SCPI and legacy Compatibility modes.



---

### **Typical Workflow (Script Example)**

Unlike the DMM or Scope, you almost always follow a "Select  Set  Turn On" pattern.

**Goal:** Set Module #3 (a 66102A 20V module) to 12V, 1A limit, and measure the result.

**1. Select the Module:**
`INST:SEL 3`

**2. Configure Settings:**
`VOLT 12.0`
`VOLT:PROT 14.0`  (Set OVP to 14V to protect the DUT)
`CURR 1.0`

**3. Turn On:**
`OUTP ON`

**4. Verify (Query):**
`MEAS:VOLT?`  (Returns: `+11.998`)
`MEAS:CURR?`  (Returns: `+0.450`)

### **Comparison: Setting vs. Query**

| Action | Command | Explanation |
| --- | --- | --- |
| **Set** Module | `INST:NSEL 1` | Focus on Slot 1. |
| **Ask** Module | `INST:NSEL?` | Returns `1`. |
| **Set** OVP | `VOLT:PROT 5.5` | Set Over-Voltage trip to 5.5V. |
| **Ask** OVP | `VOLT:PROT?` | Returns `5.500`. |
| **Set** Current | `CURR 2.0` | Set current limit to 2A. |
| **Ask** Current | `MEAS:CURR?` | Returns actual current flowing (e.g., `0.12A`). |

### **Special Feature: Output Coupling**

If you have multiple rails (e.g., +5V on Slot 1, +12V on Slot 2), you often want them to turn on at the exact same time.

* **Command:** `INST:COUP ALL`
* **Action:** Now, if you send `OUTP ON`, **all** coupled modules turn on simultaneously. This prevents "race conditions" where one voltage rail comes up before another, potentially damaging complex chips.

Based on the **Agilent 66000A Modular Power System Programming Guide** (for the **66101A–66106A** modules), here is the comprehensive SCPI command tree.

The 66000A system is unique because it is a **mainframe** holding up to 8 modules. The command tree relies heavily on the `INSTrument` subsystem to direct commands to specific power modules.

### **1. The `INSTrument` Subsystem (Channel Selection)**

This is the "router" of the system. You must select a channel before sending voltage/current commands.

* **`INSTrument`**
* `[:SELect] <channel>`  Selects a channel by name (e.g., "OUT1").
* `:NSELect <number>`  Selects a channel by slot number (1–8).
* `:COUPle`
* `[:TRIGger]` `<list>`  Groups channels to trigger simultaneously (e.g., `INST:COUP 1,2`).
* `:DO`  Executes the coupled trigger immediately.





### **2. The `SOURce` Subsystem (Setting Output)**

Controls the voltage and current generated by the selected module. The keyword `SOURce` is optional.

* **`[SOURce:]`**
* **`VOLTage`**
* `[:LEVel]` `<voltage>`  Set immediate output voltage.
* `:TRIGgered` `<voltage>`  Set voltage level to apply *after* a trigger occurs.
* `:PROTection`
* `[:LEVel]` `<voltage>`  Set Over-Voltage Protection (OVP) trip point.
* `:STATe` `0|1`  Enable/Disable OVP (Fixed at ON for some modules).




* **`CURRent`**
* `[:LEVel]` `<current>`  Set current limit.
* `:TRIGgered` `<current>`  Set current limit to apply *after* a trigger occurs.


* **`FUNCtion`**
* `:VOLTage:DC`  Sets module to Constant Voltage (CV) priority.
* `:CURRent:DC`  Sets module to Constant Current (CC) priority.





### **3. The `OUTPut` Subsystem (Safety & Relays)**

Controls the physical output state and protection features.

* **`OUTPut`**
* `[:STATe]` `0|1`  Turn the selected output ON or OFF.
* `:PROTection`
* `:CLEar`  Resets a tripped protection (OVP, OC, or Over-Temp).
* `:DELay` `<seconds>`  Time to ignore protection faults (to allow capacitive inrush).


* `:PON`
* `:STATe` `RST|RCL0`  Power-On State (Reset to safe zero, or Recall state 0).


* `:RELay`
* `[:STATe]` `0|1`  Open/Close the physical disconnect relay (if equipped).
* `:POLarity` `NORMal|REVerse`  Reverses polarity relays (if equipped).





### **4. The `MEASure` Subsystem (Readback)**

Returns the actual values measured at the output terminals.

* **`MEASure`**
* `[:SCALar]`
* `:VOLTage[:DC]?`  Measure actual DC Voltage.
* `:CURRent[:DC]?`  Measure actual DC Current.





### **5. The `TRIGger` Subsystem (Synchronization)**

Used to synchronize voltage steps across multiple modules.

* **`TRIGger`**
* `[:SEQuence]`
* `:SOURce` `BUS|IMM|EXT|HOLD|TTLTrg<n>`  Define what causes the trigger (e.g., `BUS` command or `EXT` hardware line).
* `:DELay` `<seconds>`  Time to wait after receiving a trigger before updating the output.


* **`INITiate`**
* `[:IMMediate]`  Arm the trigger system (wait for the event).


* **`ABORt`**  Stop the trigger system and return to idle.



### **6. The `SYSTem` Subsystem (Mainframe Utility)**

Commands that affect the entire chassis frame.

* **`SYSTem`**
* `:ERRor?`  Read the oldest error from the queue.
* `:VERSion?`  Query SCPI version.
* `:LANGuage` `COMPatibility|SCPI`  Switch between legacy HP 662x mode and native SCPI.



### **7. The `STATus` Subsystem (Diagnostics)**

Monitors the health of the power modules.

* **`STATus`**
* **`:QUEStionable`**
* `:CONDition?`  Real-time status (Is OVP tripped? Is it Over-Temp?).
* `:EVENt?`  Latched status (Did an error occur since last read?).
* `:ENABle` `<mask>`  Mask bits to generate an SRQ.


* **`:OPERation`**
* `:CONDition?`  Is the unit in CV or CC mode? (WTG bit, CV bit, CC bit).





---

### **Specific 66000A "Gotchas"**

* **Trigger Model:** Unlike the DMM or Scope, the Power Supply trigger system (`INIT` -> `TRIG`) is used to change voltage/current levels synchronously. You set the "Next" level using `VOLT:TRIG 5`, then send `INIT` and `*TRG` to jump to 5V.
* **Coupling:** To turn on multiple outputs at the exact same time:
1. `INST:COUP:TRIG 1,2,3` (Couple channels 1, 2, and 3).
2. `OUTP ON` (Sent to channel 1 will also turn on 2 and 3).
3. `INST:COUP:DO` can be used to force trigger coupled updates.
