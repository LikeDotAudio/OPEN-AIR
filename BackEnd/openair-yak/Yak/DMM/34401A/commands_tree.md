<!-- BEGIN GENERATED — Deployment/build_yak_command_trees.py -->

# DMM/34401A — command tree

Generated from `commands.json` by `Deployment/build_yak_command_trees.py`. Edit the table, not this file.

**155 commands** — SET 43 · RIG 5 · NAB 72 · DO 35 · 106 unverified (68%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Compound commands

Several statements in one message, so they hang off no single branch. Every statement after the first carries a leading colon — without it the parser reads it relative to the previous header's path and the instrument answers `-113`.

- **NAB** `Get_Math_Stats` · → minimum, maximum, average · †<br>Read min, max and average in one transaction
  - `:CALCulate:AVERage:MINimum?;:CALCulate:AVERage:MAXimum?;:CALCulate:AVERage:AVERage?`
- **RIG** `Setup_Limits` · args: `lower`, `upper` · †<br>Set both comparator limits in one transaction
  - `:CALCulate:LIMit:LOWer <lower>;:CALCulate:LIMit:UPPer <upper>`

## Tree

- `FETCh?` — **NAB** `Fetch_Existing` · → 1 value
- `READ?` — **NAB** `Read_Next` · → 1 value
- `ABORt` — **DO** `Abort`
- `INITiate` — **DO** `Initiate`
- **`AVERage`**
  - `AVERage?` — **NAB** `Get_Average_Average` · → NR1 · †<br>Math Operation Commands
  - `COUNt?` — **NAB** `Get_Average_Count` · → NR1 · †<br>Math Operation Commands
- **`BACK`**
  - `GOTO` — **DO** `Do_Back_Goto` · †<br>Using the Status Registers
- **`BEEPer`**
  - `STATe` — **SET** `Set_Beeper_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>System-Related Commands
  - `STATe?` — **NAB** `Get_Beeper_State` · → BOOL · †<br>System-Related Commands
- **`CALCulate`**
  - `STATe` — **SET** `Enable_Math` · `<state>` · args: `state` · bool: `OFF` | `ON`
  - `FUNCtion` — **SET** `Set_Math_Function` · `<function>` · args: `function` · enum: `NULL` | `DB` | `DBM` | `AVER` | `LIM`
  - `FUNCtion?` — **NAB** `Get_Calculate_Function` · → CRD · †
  - `STATe?` — **NAB** `Get_Calculate_State` · → BOOL · †
  - **`AVERage`**
    - `COUNt?` — **NAB** `Get_Calculate_Average_Count` · → NR1 · †<br>Math Operations
    - `AVERage?` — **NAB** `Query_Average` · → NR1
    - `MAXimum?` — **NAB** `Query_Max` · → 1 value
    - `MINimum?` — **NAB** `Query_Min` · → 1 value
  - **`DB`**
    - `REFerence` — **SET** `Set_dB_Ref` · `<value>` · args: `value` · enum
    - `REFerence?` — **NAB** `Get_Calculate_Db_Reference` · → CRD · †
  - **`DBM`**
    - `REFerence` — **SET** `Set_dBm_Ref` · `<value>` · args: `value` · enum
  - **`LIMit`**
    - `LOWer?` — **NAB** `Get_Calculate_Limit_Lower` · → 1 value · †<br>Math Operations
    - `UPPer?` — **NAB** `Get_Calculate_Limit_Upper` · → 1 value · †<br>Math Operations
  - **`NULL`**
    - `OFFSet` — **SET** `Set_Null_Offset` · `<value>` · args: `value` · numeric
    - `OFFSet?` — **NAB** `Get_Calculate_Null_Offset` · → NR3 · †
- **`CALibration`**
  - `STRing` — **SET** `Set_Calibration_String` · `<value>` · args: `value` · †<br>Calibration Message
  - `VALue` — **SET** `Set_Calibration_Value` · `<value>` · args: `value` · numeric · †<br>Calibration Commands
  - `COUNt?` — **NAB** `Get_Calibration_Count` · → NR1 · †<br>Calibration Count
  - `STRing?` — **NAB** `Get_Calibration_String` · → 1 value · †<br>Calibration Message
  - `VALue?` — **NAB** `Get_Calibration_Value` · → NR3 · †<br>Calibration Commands
  - `SECure` — **DO** `Do_Calibration_Secure` · †
  - **`SECure`**
    - `STATe` — **SET** `Set_Calibration_Secure_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Calibration Overview
    - `STATe?` — **NAB** `Get_Calibration_Secure_State` · → BOOL · †<br>Calibration Overview
    - `CODE` — **DO** `Do_Calibration_Secure_Code` · †<br>Calibration Overview
- **`CONF`**
  - `FREQ` — **DO** `Do_Configure_Frequency` · †<br>Measurement Configuration
  - `VOLT` — **DO** `Do_Configure_Voltage` · †
- **`CONFigure`**
  - `FRESistance` — **RIG** `Config_Resistance_4Wire` · `<range>,<resolution>` · args: `range`, `resolution`
  - `TEMPerature` — **RIG** `Config_Temperature` · `<probe_type>,<sensor_type>` · args: `probe_type`, `sensor_type`
  - `PERiod` — **DO** `Do_Configure_Period` · †
  - `CONTinuity` — **DO** `Select_Continuity`<br>Fixed 1 kOhm range, beeper on threshold — no range argument exists for this function
  - `DIODe` — **DO** `Select_Diode`<br>Fixed 1 mA / 1 V test, likewise argument-free
  - `RESistance` — **DO** `Select_Resistance_2W`
  - `FRESistance` — **DO** `Select_Resistance_4W`
  - **`CURRent`**
    - `AC` — **DO** `Select_AC_Current`
    - `DC` — **DO** `Select_DC_Current`
  - **`VOLTage`**
    - `AC` — **RIG** `Config_AC_Volts` · `<range>,<resolution>` · args: `range`, `resolution` · numeric (V)
    - `DC` — **RIG** `Config_DC_Volts` · `<range>,<resolution>` · args: `range`, `resolution` · numeric (V)
    - `AC` — **DO** `Select_AC_Volts`
    - `DC` — **DO** `Select_DC_Volts`
- **`DATA`**
  - `FEED` — **SET** `Set_Data_Feed` · `<value>` · args: `value` · †<br>Math Operations
  - `FEED?` — **NAB** `Get_Data_Feed` · → 1 value · †<br>Math Operations
  - `POINts?` — **NAB** `Get_Data_Points` · → NR1 · †
- **`DB`**
  - `REFerence` — **SET** `Set_Db_Reference` · `<value>` · args: `value` · enum · †<br>Math Operation Commands
  - `REFerence?` — **NAB** `Get_Db_Reference` · → CRD · †<br>Math Operation Commands
- **`DCV`**
  - `DCV` — **DO** `Do_Dcv_Dcv` · †
- **`DETector`**
  - `BANDwidth` — **SET** `Set_Detector_Bandwidth` · `<value>` · args: `value` · †
  - `BANDwidth?` — **NAB** `Get_Detector_Bandwidth` · → 1 value · †
- **`DISPlay`**
  - `TEXT` — **SET** `Display_Text` · `<string>` · args: `string`
  - `TEXT?` — **NAB** `Get_Display_Text` · → 1 value · †
  - **`TEXT`**
    - `CLEar` — **DO** `Clear_Display`
- **`FREQuency`**
  - `APERture` — **SET** `Set_Frequency_Aperture` · `<value>` · args: `value` · †<br>Measurement Configuration
  - `APERture?` — **NAB** `Get_Frequency_Aperture` · → 1 value · †<br>Measurement Configuration
  - `VOLTage` — **DO** `Do_Frequency_Voltage` · †
  - **`VOLTage`**
    - `RANGe` — **SET** `Set_Frequency_Voltage_Range` · `<value>` · args: `value` · numeric (V) · †
    - `RANGe?` — **NAB** `Get_Frequency_Voltage_Range` · → NR3 V · †
- **`FRESistance`**
  - `NPLCycles` — **SET** `Set_Fresistance_Nplcycles` · `<value>` · args: `value` · integer · †
  - `RANGe` — **SET** `Set_Fresistance_Range` · `<value>` · args: `value` · numeric · †
  - `RESolution` — **SET** `Set_Fresistance_Resolution` · `<value>` · args: `value` · †<br>Measurement Configuration Commands
  - `NPLCycles?` — **NAB** `Get_Fresistance_Nplcycles` · → NR1 · †
  - `RANGe?` — **NAB** `Get_Fresistance_Range` · → NR3 · †
  - `RESolution?` — **NAB** `Get_Fresistance_Resolution` · → 1 value · †<br>Measurement Configuration Commands
- **`INPut`**
  - **`IMPedance`**
    - `AUTO` — **SET** `Set_Input_Impedance` · `<state>` · args: `state` · bool: `OFF` | `ON`
- **`LIMit`**
  - `LOWer` — **SET** `Set_Limit_Lower` · `<value>` · args: `value` · †
  - `UPPer` — **SET** `Set_Limit_Upper` · `<value>` · args: `value` · †
  - `LOWer?` — **NAB** `Get_Limit_Lower` · → 1 value · †
  - `UPPer?` — **NAB** `Get_Limit_Upper` · → 1 value · †
- **`MEASure`**
  - `CONTinuity?` — **NAB** `Get_Measure_Continuity` · → BOOL · †<br>The MEASure? and CONFigure Commands
  - `DIODe?` — **NAB** `Get_Measure_Diode` · → 1 value · †
  - `FRESistance?` — **NAB** `Get_Measure_Fresistance` · → 1 value · †
  - `PERiod?` — **NAB** `Get_Measure_Period` · → NR3 s · †
  - `RESistance?` — **NAB** `MEASure_Resistance` · → 1 value
  - `FREQuency?` — **NAB** `Measure_Frequency` · `<range>,<resolution>` · args: `range`, `resolution` · → 1 value
  - `RESistance?` — **NAB** `Measure_Resistance_2Wire` · `<range>,<resolution>` · args: `range`, `resolution` · → 1 value<br>Measure Resistance (2W)
  - **`CURRent`**
    - `DC?` — **NAB** `Measure_DC_Current` · `<range>,<resolution>` · args: `range`, `resolution` · → NR3
  - **`VOLTage`**
    - `AC?` — **NAB** `MEASure_Voltage_AC` · → NR3 V
    - `DC?` — **NAB** `MEASure_Voltage_DC` · → NR3 V
    - `AC?` — **NAB** `Measure_AC_Voltage` · `<range>,<resolution>` · args: `range`, `resolution` · → NR3 V
    - `DC?` — **NAB** `Measure_DC_Voltage` · `<range>,<resolution>` · args: `range`, `resolution` · → NR3 V
- **`NULL`**
  - `OFFSet` — **SET** `Set_Null_Offset_Alt` · `<value>` · args: `value` · numeric · †<br>Math Operation Commands
  - `OFFSet?` — **NAB** `Get_Null_Offset` · → NR3 · †<br>Math Operation Commands
- **`PERiod`**
  - `APERture` — **SET** `Set_Period_Aperture` · `<value>` · args: `value` · numeric (s) · †<br>Measurement Configuration
  - `APERture?` — **NAB** `Get_Period_Aperture` · → NR3 s · †<br>Measurement Configuration
  - `VOLTage` — **DO** `Do_Period_Voltage` · †
  - **`VOLTage`**
    - `RANGe` — **SET** `Set_Period_Voltage_Range` · `<value>` · args: `value` · numeric (V) · †
    - `RANGe?` — **NAB** `Get_Period_Voltage_Range` · → NR3 V · †
- **`QUEStionable`**
  - `ENABle` — **SET** `Set_Questionable_Enable` · `<value>` · args: `value` · integer · †<br>Status Reporting Commands
  - `ENABle?` — **NAB** `Get_Questionable_Enable` · → NR1 · †<br>Status Reporting Commands
  - `EVENt?` — **NAB** `Get_Questionable_Event` · → NR1 · †<br>Status Reporting Commands
- **`RESistance`**
  - `NPLCycles` — **SET** `Set_Resolution_Nplcycles` · `<value>` · args: `value` · integer · †
  - `RANGe` — **SET** `Set_Resolution_Range` · `<value>` · args: `value` · numeric · †
  - `RESolution` — **SET** `Set_Resolution_Resolution` · `<value>` · args: `value` · †<br>Measurement Configuration Commands
  - `NPLCycles?` — **NAB** `Get_Resolution_Nplcycles` · → NR1 · †
  - `RANGe?` — **NAB** `Get_Resolution_Range` · → NR3 · †
  - `RESolution?` — **NAB** `Get_Resolution_Resolution` · → 1 value · †<br>Measurement Configuration Commands
- **`ROUTe`**
  - `TERMinals?` — **NAB** `Get_Route_Terminals` · → CRD · †<br>Front / Rear Input Terminal Switching
- **`SAMP`**
  - `COUN?` — **NAB** `Get_Sample_Count` · → NR1 · †
- **`SAMPle`**
  - `COUNt` — **SET** `Set_Sample_Count` · `<count>` · args: `count` · integer
- **`SECure`**
  - `STATe` — **SET** `Set_Secure_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Calibration Commands
  - `STATe?` — **NAB** `Get_Secure_State` · → BOOL · †<br>Calibration Commands
  - `CODE` — **DO** `Do_Secure_Code` · †<br>Calibration Commands
- **`SENSe`**
  - `FUNCtion` — **DO** `Do_Sense_Function` · †<br>Using the CONFigure Command
  - **`VOLTage`**
    - **`AC`**
      - `BANDwidth` — **SET** `Set_AC_Bandwidth` · `<filter>` · args: `filter` · numeric (V)
    - **`DC`**
      - `RANGe` — **SET** `Set_DCV_Range` · `<range>` · args: `range` · numeric (V)
      - `NPLC` — **SET** `Set_Integration_NPLC` · `<nplc>` · args: `nplc` · integer (V)
      - **`RANGe`**
        - `AUTO` — **SET** `Set_Autorange` · `<state>` · args: `state` · bool: `OFF` | `ON`
  - **`ZERO`**
    - `AUTO` — **DO** `Auto_Zero_OFF` · `OFF`
    - `AUTO` — **DO** `Auto_Zero_ON` · `ON`
- **`STATus`**
  - `PRESet` — **DO** `Do_State_Preset` · †<br>Status Reporting Commands
  - **`QUEStionable`**
    - `ENABle` — **SET** `Set_State_Questionable_Enable` · `<value>` · args: `value` · integer · †<br>The SCPI Status Model
    - `ENABle?` — **NAB** `Get_State_Questionable_Enable` · → NR1 · †<br>The SCPI Status Model
    - `EVENt?` — **NAB** `Get_State_Questionable_Event` · → NR1 · †
- **`SYSTem`**
  - `VERSion?` — **NAB** `Get_System_Version` · → 1 value · †<br>SCPI Language Version Query
  - `ERRor?` — **NAB** `Read_Error` · → NR2
  - `BEEPer` — **DO** `Do_System_Beeper` · †
  - `LOCal` — **DO** `Do_System_Local` · †<br>RS-232 Interface Commands
  - `REMote` — **DO** `Do_System_Remote` · †<br>RS-232 Interface Commands
  - `RWLock` — **DO** `Do_System_Rwlock` · †<br>RS-232 Interface Commands
  - **`BEEPer`**
    - `STATe` — **SET** `Set_System_Beeper_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>System-Related Commands
    - `STATe?` — **NAB** `Get_System_Beeper_State` · → BOOL · †<br>System-Related Commands
- **`TEXT`**
  - `CLEar` — **DO** `Do_Text_Clear` · †<br>System-Related Commands
- **`TRIGger`**
  - `COUNt` — **SET** `Set_Trigger_Count` · `<count>` · args: `count` · integer
  - `DELay` — **SET** `Set_Trigger_Delay` · `<delay>` · args: `delay` · numeric (s)
  - `SOURce` — **SET** `Set_Trigger_Source` · `<source>` · args: `source` · enum: `BUS` | `IMM` | `EXT`
  - `COUNt?` — **NAB** `Get_Trigger_Count` · → NR1 · †
  - `DELay?` — **NAB** `Get_Trigger_Delay` · → NR3 s · †
  - `SOURce?` — **NAB** `Get_Trigger_Source` · → CRD · †<br>Trigger Source Choices
  - **`SOURce`**
    - `IMMediate` — **DO** `Do_Trigger_Source_Immediate` · †<br>How to Use the Message Available Bit (MAV)
- **`VOLTage`**
  - `RANGe` — **SET** `Set_Voltage_Range` · `<value>` · args: `value` · numeric (V) · †<br>An Introduction to the SCPI Language
  - `RANGe?` — **NAB** `Get_Voltage_Range` · → NR3 V · †<br>An Introduction to the SCPI Language

## Common commands (IEEE 488.2)

- `*CLS` — **DO** `Clear_Status`
- `*OPC` — **DO** `Do_Opc` · †
- `*TRG` — **DO** `Do_Trg` · †
- `*ESE?` — **NAB** `Get_Ese` · → NR1 · †
- `*ESR?` — **NAB** `Get_Esr` · → NR1 · †
- `*OPC?` — **NAB** `Get_Opc` · → NR1 · †
- `*PSC?` — **NAB** `Get_Psc` · → NR1 · †
- `*SRE?` — **NAB** `Get_Sre` · → NR1 · †
- `*STB?` — **NAB** `Get_Stb` · → NR1 · †
- `*TST?` — **NAB** `Get_Tst` · → NR1 · †
- `*IDN?` — **NAB** `Read_IDN` · → AARD
- `*RST` — **DO** `Reset_Device`
- `*ESE <value>` — **SET** `Set_Ese` · `<value>` · args: `value` · integer · †
- `*PSC <value>` — **SET** `Set_Psc` · `<value>` · args: `value` · †
- `*SRE <value>` — **SET** `Set_Sre` · `<value>` · args: `value` · integer · †

<!-- END GENERATED -->

---

## Notes carried over

The SCPI (Standard Commands for Programmable Instruments) language for the Keysight (formerly Agilent/HP) 34401A is organized into a hierarchical tree. You start at the "root" and move down through subsystems to reach specific parameters.

Here is the breakdown of the 34401A command tree, separated by subsystem, along with how to distinguish between **Settings** (telling the DMM what to do) and **Queries** (asking the DMM for data).

---

### **The Golden Rule: Settings vs. Queries**

* **Setting:** You send the command with a parameter.
* *Example:* `VOLT:DC:RANG 10` (Sets the range to 10V).


* **Query:** You add a question mark (`?`) to the end.
* *Example:* `VOLT:DC:RANG?` (Asks "What is the current range?").
* *Note:* Most commands work as both. Commands that **only** work as queries are marked `[Query Only]` below.



---

### **1. The Measurement Root (High-Level)**

These are the easiest commands to use. They automatically configure the device (preset) and take a reading immediately. They sit at the very top of the tree.

* **`MEASure`**
* `:VOLTage`
* `:DC?`  Measures DC Voltage
* `:AC?`  Measures AC Voltage


* `:CURRent`
* `:DC?`  Measures DC Current
* `:AC?`  Measures AC Current


* `:RESistance?`  Measures 2-wire Resistance
* `:FRESistance?`  Measures 4-wire Resistance
* `:FREQuency?`  Measures Frequency
* `:PERiod?`  Measures Period



> **Usage:** `MEAS:VOLT:DC? 10, 0.001`
> (Measures DC voltage using the 10V range with 0.001V resolution).

---

### **2. The `SENSe` Subsystem (Detailed Configuration)**

If you want to change settings *without* immediately triggering a measurement (e.g., changing the integration time or range), you use the `[SENSe:]` tree. Note that the keyword `SENSe` is optional and often omitted.

* **`[SENSe:]`**
* **`VOLTage`** (Applies to DC or AC)
* `:DC:RANGe` `<range>`  Set specific range (0.1, 1, 10, 100, 1000).
* `:DC:RANGe:AUTO` `ON|OFF`  Turn auto-ranging on or off.
* `:DC:NPLC` `<number>`  Set integration time in Power Line Cycles (0.02 to 100).


* **`CURRent`**
* `:DC:RANGe` `<range>`
* `:DC:TERMinals?`  Query which terminals are active (Front/Rear).


* **`RESistance`**
* `:OCOMpensated` `ON|OFF`  Turn Offset Compensation on/off.


* **`DETector:BANDwidth`** `3|20|200`  Set the filter for AC measurements (Slow/Med/Fast).
* **`ZERO:AUTO`** `ON|OFF|ONCE`  Controls the internal autozero function.



---

### **3. The `TRIGger` Subsystem (Timing)**

This branch controls *when* the DMM takes a reading.

* **`TRIGger`**
* `:SOURce` `BUS|IMM|EXT`
* `BUS`: Waits for a software command (`*TRG`).
* `IMM`: Immediate (Scan constantly).
* `EXT`: Waits for hardware pulse on the rear BNC connector.


* `:DELay` `<seconds>`  Time to wait after trigger before measuring.
* `:DELay:AUTO` `ON|OFF`
* `:COUNt` `<number>`  How many readings to take per trigger.



---

### **4. The `CALCulate` Subsystem (Math)**

The 34401A can do math on the readings before sending them to you.

* **`CALCulate`**
* `:FUNCtion` `NULL|DB|DBM|LIMit|AVERage`  Select the math function.
* `:STATe` `ON|OFF`  Turn the math processing on or off.
* **`:NULL`** (Relative measurements)
* `:OFFSet` `<value>`  The value to subtract from readings.


* **`:DB`**
* `:REFerence` `<value>`


* **`:AVERage`**
* `:MINimum?`  Returns lowest reading recorded.
* `:MAXimum?`  Returns highest reading recorded.
* `:AVERage?`  Returns the average.





---

### **5. The `SYSTem` Subsystem (Utility)**

Global settings for the instrument itself.

* **`SYSTem`**
* `:BEEPer`
* `:STATe` `ON|OFF`  Silence the annoyingly loud beep.
* `[Immediate]`  `SYST:BEEP` makes the unit beep once.


* `:ERRor?`  **Critical:** Reads the next error from the queue (e.g., "+0, No Error").
* `:VERSion?`  Query the SCPI version.
* `:LOCal`  Returns control to the front panel buttons.
* `:REMote`  Locks front panel, enables remote control.



---

### **Common Shortcuts**

SCPI allows you to abbreviate commands. You only need the uppercase letters shown in the documentation.

* **Full:** `CONF:VOLTAGE:DC:RANGE 10`
* **Short:** `CONF:VOLT:DC:RANG 10`

### **Summary of Command Syntax**

| Syntax Symbol | Meaning | Example |
| --- | --- | --- |
| **Colon (`:`)** | Moves down the tree | `VOLT:DC:RANG` |
| **Question (`?`)** | Queries the value | `VOLT:DC:RANG?` |
| **Space** | Separates command from parameter | `RANG 10` |
| **`MIN | MAX`** | Special parameters |
