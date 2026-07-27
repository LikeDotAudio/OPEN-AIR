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
