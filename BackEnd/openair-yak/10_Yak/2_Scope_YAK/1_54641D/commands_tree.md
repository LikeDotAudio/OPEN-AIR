Based on the provided Programmer's Guide (Agilent 54621A/22A/24A/41A/42A and 54621D/22D/41D/42D), here are the augmented notes for the **54641D Mixed Signal Oscilloscope**.

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
