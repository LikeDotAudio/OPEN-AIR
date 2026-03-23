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

**Would you like me to generate a Python or LabVIEW snippet showing how to automate a specific measurement sequence using these commands?**




Based on the provided **Programmer's Guide (Agilent 54621A/22A/24A/41A/42A and 54621D/22D/41D/42D)**, here are the augmented notes for the **54641D Mixed Signal Oscilloscope**.

The 54641D is part of the "54640-series" referenced in the manual, which supports specific features like 50$\Omega$ input impedance and deeper memory options not available on the 54620-series.

---

### **1. The Root (Action Commands) & `ACQuire**`

*Augmentation: You must configure **how** data is captured before you `DIGitize` it.*

* 
**`ACQuire`** 


* 
`:TYPE` `NORMal|AVERage|PEAK`  Set to `AVERage` to reduce noise, or `PEAK` to catch glitches.


* 
`:COUNt` `<number>`  Number of averages (e.g., 8, 64).


* `:POINts` `100|250|500|1000|2000|MAXimum`  **Crucial:** Sets the memory depth. Use `MAXimum` to use the deep memory (up to 2MB on some models).


* 
`:SRATe?`  Query the current sample rate.





---

### **2. `CHANnel<n>` (Analog Vertical)**

*Augmentation: Added Impedance (54640 specific) and Probe settings.*

* **`CHANnel<n>`**
* ... *(User's existing commands: BWLimit, COUPling, OFFSet, RANGe, SCALe, DISPlay)*
* 
`:IMPedance` `ONEMeg|FIFTy`  **54641D Specific:** Select **50$\Omega$** for high-speed RF active probes or **1M$\Omega$** for standard passive probes.


* 
`:PROBe` `<attenuation>`  Set probe ratio (1, 10, 100) so the scope math is correct.


* 
`:PROBe:SKEW` `<seconds>`  Deskew analog channels to match digital timing.


* 
`:INVert` `ON|OFF`  Invert the signal polarity.


* 
`:UNITs` `VOLTs|AMPeres`  Use Amps if a current probe is attached.





---

### **3. `DIGital<n>` & `POD<n>` (Digital Vertical)**

*Augmentation: Size and Threshold details.*

* **`DIGital<n>`**
* ... *(User's existing commands: DISPlay, POSition, LABel)*
* `:POSition`  Note: The range depends on the display size. (0–7 for Large, 0–15 for Medium, 0–31 for Small) .




* **`POD<n>`**
* `:THReshold` `TTL|CMOS|ECL|<voltage>`
* 
*Augmentation:* You can set a custom voltage (e.g., 1.5V) by sending a number instead of a standard name.







---

### **4. `TIMebase` (Horizontal)**

*Augmentation: Zoom window and Roll mode.*

* **`TIMebase`**
* ... *(User's existing commands: SCALe, POSition, REFerence)*
* 
`:MODE` `MAIN|WINDow|XY|ROLL`.


* `MAIN`: Normal Y-T view.
* `WINDow`: Split screen "Zoom" mode.
* `XY`: Lissajous mode (Voltage vs Voltage).
* `ROLL`: Strip-chart mode (for slow signals).


* 
**`:WINDow`** (Delayed Sweep / Zoom) 


* `:POSition` `<seconds>`  Scroll the zoom window.
* `:SCALe` `<seconds>`  Set zoom factor (width of the window).





---

### **5. `TRIGger` (The Brains)**

*Augmentation: Added Pulse Width (Glitch), TV, and Serial Trigger details.*

* **`TRIGger`**
* 
`:MODE` `EDGE|GLITch|PATTern|TV|IIC|SPI|USB|CAN...`.


* 
`:HOLDoff` `<seconds>`  Holdoff time before re-triggering (crucial for complex bursts).


* 
**`:GLITch` (Pulse Width Trigger)** 


* `:SOURce` `<channel>`
* `:POLarity` `POSitive|NEGative`  Trigger on High or Low pulse.
* `:QUALifier` `LESSthan|GREaterthan|RANGe`  Trigger on pulses narrower/wider than X.
* `:LESSthan` / `:GREaterthan` `<seconds>`  Set the time limits.


* 
**`:TV`** 


* `:STANdard` `NTSC|PAL|SECAM`
* `:MODE` `LINE|FIEld1|FIEld2`


* 
**`:IIC` (I2C Trigger)** 


* `:SOURce:CLOCk` `<channel>`
* `:SOURce:DATA` `<channel>`
* `:TRIGger:TYPE` `STARt|STOP|READ7|WRITe7|NACK...`


* 
**`:SPI`** 


* `:SOURce:CLOCk` `<channel>`
* `:SOURce:DATA` `<channel>`
* `:SOURce:FRAMe` `<channel>` (Chip Select)





---

### **6. `WAVeform` (Getting Data Out)**

*Augmentation: Data typing and memory depth.*

* **`WAVeform`**
* ... *(User's existing commands: SOURce, FORMat, DATA?, PREamble?)*
* 
`:POINts` `100|250|500|1000|2000|MAXimum`  **Critical:** If you don't set this, you might only get 500 screen points instead of the full memory dump.


* 
`:BYTeorder` `LSBFirst|MSBFirst`  Controls binary endianness (default is usually correct for PC).


* `:UNSigned` `ON|OFF`  If ON, returns 0..255. If OFF, returns -128..127.


* 
`:TYPE?`  Returns if data is Normal, Average, or Peak detect.





---

### **7. `MEASure` (Automated Math)**

*Augmentation: Full measurement list and Threshold definitions.*

* **`MEASure`**
* ... *(User's existing commands: VPP, FREQ, RISetime, VMAX)*
* 
**Time:** `:PERiod?`, `:DUTYcycle?`, `:FALLtime?`, `:PWIDth?` (Positive Width), `:NWIDth?` (Negative Width).


* 
**Voltage:** `:VRMS?`, `:VAVerage?` (Mean), `:VBASE?`, `:VTOP?`, `:OVERshoot?`, `:PREShoot?`.


* 
**Mixed:** `:DELay?` (Time between Ch1 and Ch2 edges), `:PHASE?`.


* 
**`:DEFine`** 


* `:THResholds` `PERCent|ABSolute`  Define if rise time is 10%/90% or specific voltages.





---

### **8. `MARKer` (Cursors)**

*Augmentation: Missing subsystem.*
*Manual usage for measurements often involves cursors. These commands control the X and Y markers.*

* 
**`MARKer`** 


* `:MODE` `MANual|MEASure|OFF`
* `:X1Position` / `:X2Position` `<seconds>`  Set time cursors.
* `:Y1Position` / `:Y2Position` `<volts>`  Set voltage cursors.
* `:XDELta?`  Query time difference ().
* `:YDELta?`  Query voltage difference ().



---

### **9. `FUNCtion` (Math Traces)**

*Augmentation: Missing subsystem.*
*Used to configure the "Math" trace (pink line).*

* 
**`FUNCtion`** 


* `:OPERation` `ADD|SUBTract|MULTiply|FFT|INTegrate`
* `:SOURce1` `<channel>`
* `:SOURce2` `<channel>`



---

### **10. `SYSTem` (Utilities)**

*Augmentation: Error checking.*

* 
**`SYSTem`** 


* `:ERRor?`  Read error queue (returns error code and string).
* `:SETup?`  Read the complete instrument setup (binary block) to save/restore state.
* `:LOCK` `ON|OFF`  Lock front panel keys.
