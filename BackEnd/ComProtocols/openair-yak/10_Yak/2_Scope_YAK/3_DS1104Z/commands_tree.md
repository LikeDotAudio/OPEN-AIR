The **Rigol DS1104Z** is a very popular modern entry-level oscilloscope. While it mimics the SCPI structure of the Agilent/Keysight scopes, it has a few distinct "dialects," particularly in how it handles measurements and downloading deep memory data.

Here is the entry and the command tree for the Rigol DS1000Z series.

```json
"DS1104Z": {"type": "Oscilloscope", "notes": "4-Channel, 100MHz, UltraVision Tech"}

```

### **1. The Root (System State)**

Standard control over the acquisition state.

* **`:RUN`**  Starts the trigger system.
* **`:STOP`**  Stops the trigger system.
* **`:AUTO`**  The "Auto Scale" button.
* **`:SINGle`**  Single acquisition mode.
* **`:TFORce`**  Force a trigger (useful if waiting for an event that hasn't happened yet).

---

### **2. The `:CHANnel<n>` Subsystem (Vertical)**

Since this is a 4-channel scope, `<n>` can be 1, 2, 3, or 4.

* **`:CHANnel<n>`**
* `:DISPlay` `ON|OFF`  Turn channel trace on/off.
* `:BWLimit` `20M|OFF`  Turn on the 20MHz noise filter.
* `:COUPling` `AC|DC|GND`
* `:SCALe` `<volts>`  Set vertical scale (e.g., `1.0` for 1V/div).
* `:OFFSet` `<volts>`  Move the trace up or down.
* `:UNITs` `VOLTs|WATTs|AMPs|UNKNown`  Useful if using current probes.
* `:PROBe` `0.01|0.02...|1|10|...`  Set probe attenuation (usually 1X or 10X).



---

### **3. The `:TIMebase` Subsystem (Horizontal)**

Controls the X-axis for all channels.

* **`:TIMebase`**
* `:MODE` `MAIN|XY|ROLL`  Standard view, XY plot, or Roll mode (chart recorder).
* `:SCALe` `<seconds>`  Time per division (e.g., `0.001` for 1ms).
* `:OFFSet` `<seconds>`  Horizontal position (delay).



---

### **4. The `:TRIGger` Subsystem**

Rigol triggers are grouped by type. You must select the mode first.

* **`:TRIGger`**
* `:MODE` `EDGE|PULSe|SLOPE|VIDEO|PATTern...`
* **`:EDGe`**
* `:SOURce` `CHAN1|CHAN2|CHAN3|CHAN4|AC`
* `:SLOPe` `POSitive|NEGative|RFALI` (Rising/Falling/Either)
* `:LEVel` `<volts>`  The trigger threshold voltage.


* `:SWEep` `AUTO|NORMal|SINGle`  Trigger sweep mode.
* `:STATus?`  **Query:** Returns `TD` (Triggered), `WAIT` (Waiting), `RUN` (Auto), or `STOP`.



---

### **5. The `:MEASure` Subsystem (The Rigol Quirks)**

Rigol has a slightly different syntax for measurements compared to Agilent. You often have to enable the measurement on the screen before querying it, or use the `ITEM` command.

* **`:MEASure`**
* `:CLEar`  Clears measurements from the screen.
* `:SOURce` `CHAN1`  Sets the default source for calculations.
* **`:ITEM`** (The preferred method for scripts)
* `?` `<measure_type>, <channel>`
* *Example:* `:MEAS:ITEM? VPP, CHAN1`  Returns the Vpp of Ch1 immediately.
* *Types:* `VMAX, VMIN, VPP, VAVG, VRMS, FREQ, PER, RISetime, FALLtime`.


* `:STATistic`
* `:DISPlay` `ON|OFF`  Shows the statistics table (min/max/avg/dev) on screen.





---

### **6. The `:WAVeform` Subsystem (Getting Data)**

**Important Note:** The DS1104Z has "Deep Memory" (up to 24 Mpts). Downloading 24 million points over USB or LAN takes a long time. You usually want to request screen data (`NORM`) unless you really need deep analysis (`RAW`).

* **`:WAVeform`**
* `:SOURce` `CHAN1`  Select channel to read.
* `:MODE` `NORMal|MAXimum|RAW`
* `NORMal`: Screen data (1200 points). Fast.
* `RAW`: Deep memory data. **Scope must be STOPPED to read this.**


* `:FORMat` `WORD|BYTE|ASCii`
* `BYTE`: 8-bit resolution (standard).


* `:DATA?`  **The Query.** Returns the binary data block.
* `:XINC?`  X-increment (time between points).
* `:YINC?`, `:YORigin?`, `:YREFerence?`  Parameters needed to convert raw bytes to Voltage.



---

### **Command vs. Query Examples**

| Action | Command | Explanation |
| --- | --- | --- |
| **Set** Scale | `:CHAN1:SCAL 2` | Sets Ch1 to 2 Volts/Div. |
| **Ask** Scale | `:CHAN1:SCAL?` | Returns `2.000000e+00`. |
| **Stop** Scope | `:STOP` | Stops acquisition (Red light). |
| **Single** Shot | `:SING` | Scope waits for one trigger, then stops. |
| **Measure** | `:MEAS:ITEM? FREQ,CHAN1` | Returns frequency of Ch1 (e.g., `1.000000e+03`). |

### **A Critical Rigol "Gotcha"**

If you want to download the full deep memory (RAW mode), you **must** follow this strict sequence or the command will fail/timeout:

1. `:STOP` (Scope must be stopped).
2. `:WAV:SOUR CHAN1` (Select channel).
3. `:WAV:MODE RAW` (Select Raw mode).
4. `:WAV:DATA?` (Request data).

If the scope is `:RUN`ning, `RAW` mode requests are usually ignored or return an error.
