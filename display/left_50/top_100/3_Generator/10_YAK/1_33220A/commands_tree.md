It looks like there is a slight mix-up in the model numbers.

**Crucial Correction:** The **34401A** is strictly a Digital Multimeter (it *measures* signals). It cannot generate them.

You likely want the command tree for its classic "benchtop partner," the **Agilent/Keysight 33220A** (or the older 33120A). These are the standard Function/Arbitrary Waveform Generators used in that era of equipment.

Here is the entry and command tree for that device:

```json
"33220A": {"type": "Function Generator", "notes": "20 MHz Waveform / Arb Generator"}

```

The Signal Generator SCPI tree is distinct because it focuses on **SOURcing** (creating) rather than **SENSe** (measuring).

### **1. The `APPLy` Root (The "Easy Button")**

Just like `MEASure` on the DMM, `APPLy` is a macro. It sets the shape, frequency, amplitude, and offset all at once.

* **`APPLy`**
* `:SINusoid` `<freq>, <amp>, <offset>`  Output a Sine wave.
* `:SQUare` `<freq>, <amp>, <offset>`  Output a Square wave.
* `:RAMP` `<freq>, <amp>, <offset>`  Output a Ramp/Triangle wave.
* `:PULSe`  Output a Pulse.
* `:DC`  Output a DC voltage.
* `?`  **Query:** Returns a string describing the current setup (e.g., `"SIN 1.000000E+03..."`).



> **Usage:** `APPL:SIN 5000, 3.0, -1.0`
> (Output a 5 kHz Sine wave, 3 Vpp amplitude, with a -1V DC offset).

---

### **2. The `OUTPut` Subsystem (The Safety Switch)**

By default, the generator starts with the output **OFF** to protect your circuit. You **must** turn it on explicitly.

* **`OUTPut`**
* `ON|OFF`  Turns the BNC output on or off.
* `:LOAD` `50|INFinity`  **Critical Setting.** Tells the generator what impedance your circuit is (50$\Omega$ or High-Z).
* *Note:* If you set this wrong, the displayed voltage will be double or half of what you measure.


* `:SYNC` `ON|OFF`  Turns the "Sync" BNC port (TTL clock) on or off.



---

### **3. The `SOURce` Subsystem (Detailed Control)**

If you don't use `APPLy`, you use `SOURce` to change individual parameters (like tweaking just the frequency while leaving voltage alone).

* **`[SOURce:]`**
* **`FUNCtion`**
* `:SHAPe` `SIN|SQU|RAMP|PULS|NOIS|DC|USER`  Change waveform shape.


* **`FREQuency`**
* `<hertz>`  Set frequency (e.g., `FREQ 1000`).


* **`VOLTage`**
* `<volts>`  Set Amplitude (Vpp by default).
* `:OFFSet` `<volts>`  Set DC Offset.
* `:UNIT` `VPP|VRMS|DBM`  Change the units used for amplitude.


* **`PHASe`**
* `<degrees>`  Set phase angle relative to the Sync pulse.





---

### **4. The `PULSe` Subsystem (Square/Pulse Specifics)**

If you select `FUNCtion:SHAPe PULSe`, these commands become active.

* **`[SOURce:]PULSe`**
* `:PERiod` `<seconds>`  Alternative to Frequency (1/Freq).
* `:WIDTh` `<seconds>`  Set the "On" time (Duty Cycle).
* `:TRANsition` `<seconds>`  Set the edge time (Rise/Fall time).



---

### **5. The `BURSt` Subsystem (Advanced)**

Used to output a specific number of cycles (e.g., "Fire 5 sine waves then stop").

* **`BURSt`**
* `:STATe` `ON|OFF`  Enable burst mode.
* `:MODE` `TRIGgered|GATed`
* `:NCYCles` `<number>|INFinity`  How many cycles to fire per trigger.



---

### **Comparison: Setting vs. Query**

| Action | Command | Explanation |
| --- | --- | --- |
| **Set** Freq | `FREQ 5000` | Sets frequency to 5 kHz. |
| **Ask** Freq | `FREQ?` | Returns `+5.00000000000E+03`. |
| **Set** Output | `OUTP ON` | Relays click, signal goes live. |
| **Ask** State | `OUTP?` | Returns `1` (On) or `0` (Off). |

### **Common "Gotcha" with Signal Generators**

**The 50 Ohm vs. High Z problem:**
If you set the generator to `5V` but you measure `10V` on your oscilloscope (or the 34401A), it is because the Generator thinks you have a `50 OHM` load, but you actually have a `High Z` (Open) connection.

* **Fix:** Send command `OUTP:LOAD INF` to tell the generator you are connecting to a high-impedance input (like a multimeter or scope).

**Would you like a Python script that connects the 33220A (Gen) to the 34401A (DMM) to automatically characterize a filter (Sweeping Freq vs. Voltage)?**