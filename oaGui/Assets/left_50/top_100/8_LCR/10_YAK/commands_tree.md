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
