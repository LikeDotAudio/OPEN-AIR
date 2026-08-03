<!-- BEGIN GENERATED — openair-yak build-trees -->

# Load/6060B — command tree

Generated from `commands.json` by `openair-yak build-trees`. Edit the table, not this file.

**122 commands** — SET 35 · RIG 1 · NAB 46 · DO 40 · 94 unverified (77%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Compound commands

Several statements in one message, so they hang off no single branch. Every statement after the first carries a leading colon — without it the parser reads it relative to the previous header's path and the instrument answers `-113`.

- **NAB** `Get_OCP_Config` · → stat, lev, del · †<br>Read overcurrent protection state, level and delay in one transaction
  - `:CURR:PROT:STAT?;:CURR:PROT:LEV?;:CURR:PROT:DEL?`
- **NAB** `Measure_All` · → mode, voltage, current, power
  - `MODE?;MEAS:VOLT?;MEAS:CURR?;MEAS:POW?`
- **RIG** `Setup_Transient_Profile` · args: `level_a`, `level_b`, `duty`, `freq` · numeric (V) · †<br>Set both transient levels, duty and frequency together
  - `:CURR:LEV <level_a>;:CURR:TLEV <level_b>;:TRAN:DCYC <duty>;:TRAN:FREQ <freq>`

## Tree

- `CHAN` — **SET** `Set_Chan` · `<value>` · args: `value` · enum · †<br>Select the electronic load channel this command stream addresses (INST is an alias)
- `CURR` — **SET** `Set_Current_Level` · `<value>` · args: `value` · numeric (A)
- `PORT0` — **SET** `Set_Port0` · `<value>` · args: `value` · †<br>Set the state of the rear-panel digital port 0 output
- `RES` — **SET** `Set_Resistance_Level` · `<value>` · args: `value` · numeric (Ohm)
- `VOLT` — **SET** `Set_Voltage_Level` · `<value>` · args: `value` · numeric (V)
- `CHAN?` — **NAB** `Get_Chan` · → CRD · †<br>Query the selected channel
- `CURR?` — **NAB** `Get_Curr` · → NR3 A · †<br>Query the programmed main current level
- `MODE?` — **NAB** `Get_Mode` · → CRD · †<br>Query the operating mode — CURR, RES or VOLT (FUNC is an alias)
- `RES?` — **NAB** `Get_Res` · → NR3 Ohm · †<br>Query the programmed main resistance level
- `VOLT?` — **NAB** `Get_Volt` · → NR3 V · †<br>Query the programmed main voltage level
- `ABOR` — **DO** `Do_Abor` · †<br>Abort the transient or trigger operation in progress
- `INP` — **DO** `Input_OFF` · `OFF`
- `INP` — **DO** `Input_ON` · `ON`
- **`CAL`**
  - `INIT` — **DO** `Do_Calib_Init` · †<br>EEPROM Initialization
  - `MEAS` — **DO** `Do_Calib_Meas` · †
  - `MODE` — **DO** `Do_Calib_Mode` · †<br>Table 3-2. Selftest Error Code
  - `SAV` — **DO** `Do_Calib_Sav` · †<br>Program Listing
  - `TLEV` — **DO** `Do_Calib_Tlev` · †
  - **`LEV`**
    - `HIGH` — **DO** `Do_Calib_Lev_High` · †
    - `LOW` — **DO** `Do_Calib_Lev_Low` · †
  - **`MEAS`**
    - `HIGH` — **DO** `Do_Calib_Meas_High` · †<br>Calibration Flowcharts
    - `LOW` — **DO** `Do_Calib_Meas_Low` · †
- **`CURR`**
  - `RANG` — **SET** `Set_Current_Range` · `<value>` · args: `value` · numeric (A)
  - `SLEW` — **SET** `Set_Current_Slew` · `<value>` · args: `value` · numeric (A)
  - `LEV` — **SET** `Set_Transient_Level_A` · `<value>` · args: `value` · numeric (V)
  - `TLEV` — **SET** `Set_Transient_Level_B` · `<value>` · args: `value` · numeric (V)
  - `RANG?` — **NAB** `Get_Curr_Rang` · → NR3 A · †<br>Query the current range
  - `SLEW?` — **NAB** `Get_Curr_Slew` · → NR3 A · †<br>Query the current slew rate
  - `TLEV?` — **NAB** `Get_Curr_Tlev` · → NR3 V · †<br>Query the transient current level
  - `PROT` — **DO** `Do_Curr_Prot` · †<br>Software Current Limit
  - `TRIG` — **DO** `Do_Curr_Trig` · †<br>Triggered Current Level
  - **`LEV`**
    - `TRIG` — **SET** `Set_Curr_Lev_Trig` · `<value>` · args: `value` · numeric (V) · †<br>Set the current level the load takes on when triggered
    - `TRIG?` — **NAB** `Get_Curr_Lev_Trig` · → NR3 V · †<br>Query the triggered current level
    - `TRIG` — **DO** `Do_Curr_Lev_Trig` · †<br>PROGRAM 2
  - **`PROT`**
    - `DEL` — **SET** `Set_Curr_Prot_Del` · `<value>` · args: `value` · numeric (A) · †<br>Set how long an overcurrent may persist before the input is turned off
    - `LEV` — **SET** `Set_Curr_Prot_Lev` · `<value>` · args: `value` · numeric (V) · †<br>Set the overcurrent protection level
    - `STAT` — **SET** `Set_Curr_Prot_Stat` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable overcurrent protection
    - `DEL` — **DO** `Do_Curr_Prot_Del` · †<br>72 Remote Operation
    - `LEV` — **DO** `Do_Curr_Prot_Lev` · †<br>CR Mode Example
    - `STAT` — **DO** `Do_Curr_Prot_Stat` · †<br>CR Mode Example
- **`DIAG`**
  - `CAL` — **DO** `Do_Diag_Calib` · †<br>EEPROM Initialization
- **`INP`**
  - `STAT?` — **NAB** `Get_Inp_Stat` · → BOOL · †<br>Query whether the load input is on (OUTP is an alias for INP)
  - **`PROT`**
    - `CLE` — **DO** `Do_Input_Prot_Cle` · †<br>Resetting Latched Protection
  - **`SHOR`**
    - `STAT` — **SET** `Set_Inp_Shor_Stat` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Close or open the input short across the load terminals
    - `STAT?` — **NAB** `Get_Inp_Shor_Stat` · → BOOL · †<br>Query the input short state
- **`INPUT`**
  - `SHORT` — **DO** `Do_Input_Short` · †<br>Short On/Off
- **`MEAS`**
  - **`CURR`**
    - `DC?` — **NAB** `Get_Meas_Curr_Dc` · → NR3 A · †<br>Measure the DC current flowing into the load
  - **`POW`**
    - `DC?` — **NAB** `Get_Meas_Pow_Dc` · → NR3 W · †<br>Measure the DC power being dissipated
  - **`VOLT`**
    - `DC?` — **NAB** `Get_Meas_Volt_Dc` · → NR3 V · †<br>Measure the DC voltage across the load input
- **`MODE`**
  - `CURR` — **DO** `Set_Mode_Current`
  - `RES` — **DO** `Set_Mode_Resistance`
  - `VOLT` — **DO** `Set_Mode_Voltage`
- **`PROT`**
  - `CLE` — **DO** `Clear_Protection`
- **`RES`**
  - `TLEV` — **SET** `Set_Res_Tlev` · `<value>` · args: `value` · numeric (V) · †<br>Set the transient resistance level
  - `RANG` — **SET** `Set_Resistance_Range` · `<value>` · args: `value` · numeric (Ohm)
  - `RANG?` — **NAB** `Get_Res_Rang` · → NR3 Ohm · †<br>Query the resistance range
  - `TLEV?` — **NAB** `Get_Res_Tlev` · → NR3 V · †<br>Query the transient resistance level
  - `TLEV` — **DO** `Do_Res_Tlev` · †<br>Transient Resistance Level
  - `TRIG` — **DO** `Do_Res_Trig` · †<br>Triggered Resistance Level
  - **`LEV`**
    - `TRIG` — **SET** `Set_Res_Lev_Trig` · `<value>` · args: `value` · numeric (V) · †<br>Set the resistance the load takes on when triggered
    - `TRIG?` — **NAB** `Get_Res_Lev_Trig` · → NR3 V · †<br>Query the triggered resistance level
- **`STAT`**
  - **`CHAN`**
    - `ENAB` — **SET** `Set_Stat_Chan_Enab` · `<value>` · args: `value` · integer · †<br>Set which channel status bits are summarised into Channel Summary
    - `ENAB?` — **NAB** `Get_Stat_Chan_Enab` · → NR1 · †<br>Query the Channel Status enable mask
    - `EVEN?` — **NAB** `Get_Stat_Chan_Even` · → NR1 · †<br>Read and clear the Channel Status event register
    - `COND?` — **NAB** `Get_Stat_Channel_Cond` · → NR1 · †<br>Overpower Circuit Troubleshooting (Figure 3-10)
  - **`CSUM`**
    - `ENAB` — **SET** `Set_Stat_Csum_Enab` · `<value>` · args: `value` · integer · †<br>Set which channels are summarised into the Status Byte CSUM bit
    - `ENAB?` — **NAB** `Get_Stat_Csum_Enab` · → NR1 · †<br>Query the Channel Summary enable mask
    - `EVEN?` — **NAB** `Get_Stat_Csum_Even` · → NR1 · †<br>Read and clear the Channel Summary event register
  - **`OPER`**
    - `ENAB` — **SET** `Set_Stat_Oper_Enab` · `<value>` · args: `value` · integer · †<br>Set the Operation Status enable mask
    - `NTR` — **SET** `Set_Stat_Oper_Ntr` · `<value>` · args: `value` · integer · †<br>Set the Operation Status negative-transition filter
    - `PTR` — **SET** `Set_Stat_Oper_Ptr` · `<value>` · args: `value` · integer · †<br>Set the Operation Status positive-transition filter
    - `COND?` — **NAB** `Get_Stat_Oper_Cond` · → NR1 · †<br>Read the Operation Status condition register
    - `ENAB?` — **NAB** `Get_Stat_Oper_Enab` · → NR1 · †<br>Query the Operation Status enable mask
    - `EVEN?` — **NAB** `Get_Stat_Oper_Even` · → NR1 · †<br>Read and clear the Operation Status event register
    - `NTR?` — **NAB** `Get_Stat_Oper_Ntr` · → NR1 · †<br>Query the Operation Status negative-transition filter
    - `PTR?` — **NAB** `Get_Stat_Oper_Ptr` · → NR1 · †<br>Query the Operation Status positive-transition filter
  - **`QUES`**
    - `ENAB` — **SET** `Set_Stat_Ques_Enab` · `<value>` · args: `value` · integer · †<br>Set the Questionable Status enable mask
    - `COND?` — **NAB** `Get_Stat_Ques_Cond` · → NR1 · †<br>Read the Questionable Status condition register
    - `ENAB?` — **NAB** `Get_Stat_Ques_Enab` · → NR1 · †<br>Query the Questionable Status enable mask
    - `EVEN?` — **NAB** `Get_Stat_Ques_Even` · → NR1 · †<br>Read and clear the Questionable Status event register
- **`SYST`**
  - `ERR?` — **NAB** `Error` · → NR2
- **`TRAN`**
  - `TWID` — **SET** `Set_Tran_Twid` · `<value>` · args: `value` · numeric (s) · †<br>Set the transient pulse width
  - `DCYC` — **SET** `Set_Transient_Duty` · `<value>` · args: `value` · numeric (%)
  - `FREQ` — **SET** `Set_Transient_Freq` · `<value>` · args: `value` · numeric (Hz)
  - `MODE` — **SET** `Set_Transient_Mode` · `<mode>` · args: `mode` · enum
  - `DCYC?` — **NAB** `Get_Tran_Dcyc` · → NR3 % · †<br>Query the transient duty cycle
  - `FREQ?` — **NAB** `Get_Tran_Freq` · → NR3 Hz · †<br>Query the transient frequency
  - `MODE?` — **NAB** `Get_Tran_Mode` · → CRD · †<br>Query the transient mode — CONT, PULS or TOGG
  - `STAT?` — **NAB** `Get_Tran_Stat` · → BOOL · †<br>Query whether transient operation is enabled
  - `TWID?` — **NAB** `Get_Tran_Twid` · → NR3 s · †<br>Query the transient pulse width
  - `TOGG` — **DO** `Do_Tran_Togg` · †<br>Toggled Transient Operation
  - `TWID` — **DO** `Do_Tran_Twid` · †<br>Pulsed Transient Operation
  - `STAT` — **DO** `Transient_OFF` · `OFF`
  - `STAT` — **DO** `Transient_ON` · `ON`
- **`TRIG`**
  - `SOUR` — **SET** `Set_Trig_Sour` · `<value>` · args: `value` · enum · †<br>Select the trigger source — BUS, EXT, HOLD, LINE or TIM
  - `TIM` — **SET** `Set_Trig_Tim` · `<value>` · args: `value` · numeric (s) · †<br>Set the internal trigger timer period
  - `SOUR?` — **NAB** `Get_Trig_Sour` · → CRD · †<br>Query the trigger source
  - `TIM?` — **NAB** `Get_Trig_Tim` · → NR3 s · †<br>Query the internal trigger timer period
  - `IMM` — **DO** `Do_Trig_Imm` · †<br>Trigger immediately, whatever the selected trigger source
  - `SOUR` — **DO** `Do_Trig_Sour` · †
- **`VOLT`**
  - `RANG` — **SET** `Set_Voltage_Range` · `<value>` · args: `value` · numeric (V)
  - `SLEW?` — **NAB** `Get_Volt_Slew` · → NR3 V · †<br>Query the voltage slew rate
  - `TLEV?` — **NAB** `Get_Volt_Tlev` · → NR3 V · †<br>Query the transient voltage level
  - `SLEW` — **DO** `Do_Volt_Slew` · †<br>Slew Rate
  - `TLEV` — **DO** `Do_Volt_Tlev` · †<br>Transient Voltage Level
  - `TRIG` — **DO** `Do_Volt_Trig` · †<br>Triggered Voltage Level
  - **`LEV`**
    - `TRIG` — **SET** `Set_Volt_Lev_Trig` · `<value>` · args: `value` · numeric (V) · †<br>Set the voltage level the load takes on when triggered
    - `TRIG?` — **NAB** `Get_Volt_Lev_Trig` · → NR3 V · †<br>Query the triggered voltage level

## Common commands (IEEE 488.2)

- `*CLS` — **DO** `Clear_Status`
- `*RDT?` — **NAB** `Get_Rdt` · → 1 value · †<br>Return the device identification / topology string
- `*IDN?` — **NAB** `Read_IDN` · → AARD<br>IDN
- `*RST` — **DO** `Reset_Device`
- `*ESE <value>` — **SET** `Set_Ese` · `<value>` · args: `value` · integer · †
- `*RCL <value>` — **SET** `Set_Rcl` · `<value>` · args: `value` · †
- `*SAV <value>` — **SET** `Set_Sav` · `<value>` · args: `value` · †
- `*SRE <value>` — **SET** `Set_Sre` · `<value>` · args: `value` · integer · †
- `*STB?` — **NAB** `Status_Byte` · → NR1
- `*TRG` — **DO** `Trigger`
- `*TRG` — **DO** `Trigger_Immediate`

<!-- END GENERATED -->

---

## Notes carried over

The **Agilent/Keysight 6060B** is a **DC Electronic Load**.

Think of this as a "Reverse Power Supply." Instead of *pushing* power out, it *swallows* (sinks) power to test batteries, power supplies, or solar panels. Because of this, the commands look similar to a power supply, but the physics are backwards.

```json
"6060B": {"type": "DC Electronic Load", "notes": "300W, 60V, 60A. Single Input."}

```

Here is the SCPI command tree for controlling the load.

---

### **1. The `INPut` Subsystem (The "On" Switch)**

On a power supply, this is called `OUTPut`. On a load, it is called `INPut` because power is going *in*.

* **`INPut`**
* `:STATe` `ON|OFF`  Connects the load to your device (starts drawing current).
* `:SHORt` `ON|OFF`  **Warning:** Simulates a dead short circuit across the terminals (used to test fuse blowing or OCP).
* `:PROTection:CLEar`  Resets the load if Over-Power or Over-Temp tripped.



---

### **2. The `MODE` Subsystem (Operation Type)**

You must decide how the load behaves before setting values.

* **`MODE`**
* `:CURRent`  **CC Mode:** Load keeps current constant (e.g., "Draw exactly 5A"). Best for battery discharge tests.
* `:VOLTage`  **CV Mode:** Load keeps voltage constant (acts like a massive Zener diode). Best for testing current chargers.
* `:RESistance`  **CR Mode:** Load acts like a power resistor.



---

### **3. The Control Subsystems (`CURRent`, `VOLTage`, `RESistance`)**

Once you pick a Mode (above), you use the matching branch to set the levels.

* **`CURRent`** (Use when in CC Mode)
* `[:LEVel]` `<amps>`  The main current setting (e.g., `CURR 5`).
* `:RANGe` `<amps>`  Select measurement range (Low range = more accurate for small currents).
* `:SLEW` `<amps/sec>`  How fast the current changes (prevents ringing).
* `:TLEVel` `<amps>`  **Transient Level:** The "Pulse" current value (see Transients below).


* **`VOLTage`** (Use when in CV Mode)
* `[:LEVel]` `<volts>`
* `:RANGe` `<volts>`
* `:TLEVel` `<volts>`


* **`RESistance`** (Use when in CR Mode)
* `[:LEVel]` `<ohms>`
* `:RANGe` `<ohms>`
* `:TLEVel` `<ohms>`



---

### **4. The `TRANsient` Subsystem (Dynamic Testing)**

The 6060B is famous for its ability to toggle rapidly between two levels (Level A and Level B) to test how a power supply reacts to load spikes.

* **`TRANsient`**
* `:STATe` `ON|OFF`  Turn the pulsing on.
* `:MODe` `CONTinuous|PULSe|TOGGle`  Cont (Train of pulses) or Pulse (One shot).
* `:FREQuency` `<hertz>`  How fast to switch (e.g., 1000Hz).
* `:DCYCle` `<percent>`  Duty Cycle (e.g., 50%).



> **How it works:** If you are in **CC Mode**, the load oscillates between `CURRent:LEVel` (Main) and `CURRent:TLEVel` (Transient).

---

### **5. The `MEASure` Subsystem (Readback)**

Ask the load what is actually happening.

* **`MEASure`**
* `:VOLTage?`  Measures voltage at the terminals.
* `:CURRent?`  Measures current sinking into the load.
* `:POWer?`  Calculates Watts ().



---

### **Usage Example: Battery Discharge Test**

You want to discharge a battery at exactly **2 Amps** and stop if the voltage drops.

**1. Setup:**

```text
MODE:CURR             (Set to Constant Current mode)
CURR:RANG 60          (Set range to 60A to be safe)
CURR 2.0              (Set discharge rate to 2A)
INPut ON              (Start discharging)

```

**2. Monitoring Loop (Query):**

```text
MEAS:VOLT?            (Read battery voltage)
MEAS:CURR?            (Confirm we are drawing 2A)

```

**3. Stop:**

```text
INPut OFF             (Stop discharge)

```

### **Comparison: Setting vs. Query**

| Action | Command | Explanation |
| --- | --- | --- |
| **Set** Mode | `MODE:CURR` | Sets the load to Constant Current. |
| **Ask** Mode | `MODE?` | Returns `CURR`. |
| **Set** Value | `CURR 10` | Sets the load to draw 10 Amps. |
| **Ask** Value | `CURR?` | Returns `10.000` (The *setting*, not the measurement). |
| **Measure** | `MEAS:CURR?` | Returns `9.998` (The *actual* current flowing). |
| **Set** Slew | `CURR:SLEW 5000` | Current changes at 5000 A/sec. |

### **Common "Gotcha" with Electronic Loads**

**The "Minimum Voltage" Limit:**
The 6060B needs a tiny bit of voltage (usually around 2V) to "turn on" its internal transistors.

* If you try to pull **20 Amps** from a **1V** source, the load cannot do it. It will likely saturate and the "UNR" (Unregulated) error light will turn on.
* **Query:** `STAT:QUES:COND?` can tell you if the unit is "Unregulated" (failing to hold the setpoint).


Based on the **Agilent 6060B Single-Input Electronic Load Programming Guide**, here is the complete and updated SCPI command tree.

The 6060B command set is divided into subsystems that control the "input" (which acts like a power supply's output), the operating mode (CC, CV, CR), and the dynamic transient generator.

### **1. The `MEASure` Subsystem (Readback)**

These queries read the actual voltage, current, and power at the input terminals.

* **`MEASure`**
* 
`:CURRent[:DC]?`  Returns the actual current flowing into the load.


* 
`:VOLTage[:DC]?`  Returns the actual voltage across the terminals.


* 
`:POWer[:DC]?`  Returns the calculated power ().





---

### **2. The `MODE` Subsystem (Operation Type)**

This subsystem selects which regulation loop is active. You must select the mode before setting the levels.

* **`MODE`**
* 
`:CURRent`  **CC Mode:** Load regulates current (battery discharge, power supply testing).


* 
`:VOLTage`  **CV Mode:** Load regulates voltage (shunt regulator, current source testing).


* 
`:RESistance`  **CR Mode:** Load acts like a variable resistor.


* 
`?`  Query returns `CURR`, `VOLT`, or `RES`.





---

### **3. The `INPut` Subsystem (On/Off & Safety)**

Controls the physical connection and input protection logic.

* **`INPut`**
* 
`[:STATe]` `ON|OFF`  Turns the load input on or off.


* 
`:SHORt` `ON|OFF`  Simulates a physical short circuit across the input terminals.


* `:PROTection`
* 
`:CLEar`  Clears a latched protection fault (OV, OC, OP, OT).


* *Note: If the fault condition persists, the protection will trip again immediately.*





---

### **4. The `CURRent` Subsystem (CC Mode Settings)**

Active when `MODE:CURR` is selected.

* **`CURRent`**
* `[:LEVel]`
* 
`[:IMMediate]` `<amps>`  Sets the main current level (Level A).


* 
`:TRIGgered` `<amps>`  Sets the current level to apply *after* a trigger event.




* 
`:TLEVel` `<amps>`  Sets the **Transient** current level (Level B) used during pulsing.


* 
`:RANGe` `<amps>`  Selects the measurement/setting range (e.g., 6A or 60A).


* 
`:SLEW` `<amps/sec>`  Sets the rate of change for current transitions (prevents ringing).


* `:MAXimum` / `:MINimum` can also be used.


* `:PROTection`
* 
`[:LEVel]` `<amps>`  Sets the software current limit (Over-Current Protection).


* 
`:DELay` `<seconds>`  Time to allow current spikes before tripping protection.


* 
`:STATe` `ON|OFF`  Enable or disable the OCP circuit.







---

### **5. The `VOLTage` Subsystem (CV Mode Settings)**

Active when `MODE:VOLT` is selected.

* **`VOLTage`**
* `[:LEVel]`
* 
`[:IMMediate]` `<volts>`  Sets the main voltage level (Level A).


* 
`:TRIGgered` `<volts>`  Sets voltage level for trigger events.




* 
`:TLEVel` `<volts>`  Sets the **Transient** voltage level (Level B).


* 
`:RANGe` `<volts>`  Selects voltage range.





---

### **6. The `RESistance` Subsystem (CR Mode Settings)**

Active when `MODE:RES` is selected.

* **`RESistance`**
* `[:LEVel]`
* 
`[:IMMediate]` `<ohms>`  Sets the main resistance (Level A).


* 
`:TRIGgered` `<ohms>`  Sets resistance for trigger events.




* 
`:TLEVel` `<ohms>`  Sets the **Transient** resistance (Level B).


* 
`:RANGe` `<ohms>`  Selects resistance range.





---

### **7. The `TRANsient` Subsystem (Dynamic Switching)**

Configures the internal generator that toggles between the Main Level (IMMediate) and the Transient Level (TLEVel).

* **`TRANsient`**
* 
`[:STATe]` `ON|OFF`  Enables the transient generator.


* 
`:MODE` `CONTinuous|PULSe|TOGGle`  Selects how the load switches:


* **CONT:** Oscillates continuously between A and B at the set frequency.
* **PULS:** Generates a single pulse to Level B upon a trigger.
* **TOGG:** Switches to Level B on one trigger, and back to Level A on the next.


* 
`:FREQuency` `<hertz>`  Frequency of the oscillation (0.25 Hz to 10 kHz).


* 
`:DCYCle` `<percent>`  Duty cycle (pulse width) in percent (3% to 97%).





---

### **8. The `TRIGger` Subsystem (Timing & Sync)**

Controls external or bus synchronization for buffered steps or pulses.

* **`TRIGger`**
* `[:SEQuence]`
* 
`:SOURce` `BUS|EXTernal|HOLD|IMMediate|LINE|TIMer`  Selects the trigger source.


* 
`:TIMer` `<seconds>`  Sets the internal timer interval if source is TIMer.


* 
`:DELay` `<seconds>`  Time to wait after a trigger before updating the input.






* 
**`ABORt`**  Stops any trigger sequence in progress.


* **`INITiate`**
* 
`[:IMMediate]`  Arms the trigger system to wait for an event.





---

### **9. The `STATus` Subsystem (Diagnostics)**

* **`STATus`**
* 
`:CSUMmary?`  Channel Summary (for mainframe compatibility).


* **`:QUEStionable`**
* 
`:CONDition?`  Real-time status (OT, OV, OP, Unregulated).


* 
`:EVENt?`  Latched errors since last read.


* 
`:ENABle` `<mask>`  Enable bits for SRQ generation.




* **`:OPERation`**
* 
`:CONDition?`  Current mode status (CAL, TRIG, WTG).







---

### **10. The `SYSTem` Subsystem (Utilities)**

* **`SYSTem`**
* 
`:ERRor?`  Read the error queue (e.g., "Data out of range").


* 
`:VERSion?`  Returns SCPI version (e.g., "1990.0").


* 
`:PERSona` `DEFault|L6060`  Sets the command language personality.





---

### **11. Common Commands (IEEE 488.2)**

* 
`*CLS`  Clear Status.


* 
`*RST`  Reset Instrument.


* 
`*TRG`  Trigger Command (Used when TRIG:SOUR BUS is set).


* 
`*SAV <n>` / `*RCL <n>`  Save/Recall state (0–6).


* 
`*IDN?`  Identification String.


* 
`*TST?`  Self-Test (Returns 0 if pass).
