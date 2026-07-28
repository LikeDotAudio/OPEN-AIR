<!-- BEGIN GENERATED — Deployment/build_yak_command_trees.py -->

# Generator/33220A — command tree

Generated from `commands.json` by `Deployment/build_yak_command_trees.py`. Edit the table, not this file.

**254 commands** — SET 77 · RIG 4 · NAB 114 · DO 59 · 229 unverified (90%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Compound commands

Several statements in one message, so they hang off no single branch. Every statement after the first carries a leading colon — without it the parser reads it relative to the previous header's path and the instrument answers `-113`.

- **RIG** `Setup_AM` · args: `shape`, `freq`, `depth` · enum
  - `AM:INTernal:FUNCtion <shape>;AM:INTernal:FREQuency <freq>;AM:DEPTh <depth>`

## Tree

- `VOLTage` — **SET** `Set_Amplitude` · `<amp>` · args: `amp` · numeric (V)
- `FREQuency` — **SET** `Set_Frequency` · `<freq>` · args: `freq`
- `FUNCtion` — **SET** `Set_Function_Shape` · `<shape>` · args: `shape` · enum
- `APPLy?` — **NAB** `Get_Apply_String` · → 1 value
- `OUTPut?` — **NAB** `Get_Output_State` · → 1 value
- `OUTPut` — **DO** `Output_OFF` · `OFF`
- `OUTPut` — **DO** `Output_ON` · `ON`
- **`AM`**
  - `SOUR` — **SET** `Set_Am_Source` · `<value>` · args: `value` · enum: `INT` | `EXT` · †<br>AM Commands
  - `DEPTh?` — **NAB** `Get_Am_Depth` · → 1 value · †<br>AM Commands
  - `SOURce?` — **NAB** `Get_Am_Source` · → CRD · †<br>AM Commands
  - `STATe?` — **NAB** `Get_Am_State` · → BOOL · †<br>AM Commands
  - `STATe` — **DO** `AM_State_OFF` · `OFF`
  - `STATe` — **DO** `AM_State_ON` · `ON`
  - `INTernal` — **DO** `Do_Am_Internal` · †<br>AM Commands
  - **`INTernal`**
    - `FREQuency?` — **NAB** `Get_Am_Internal_Frequency` · → 1 value · †<br>Amplitude Modulation (AM) Commands
- **`APPL`**
  - `RAMP` — **DO** `Do_Apply_Ramp` · †<br>Output Frequency
  - `USER` — **DO** `Do_Apply_User` · †
- **`APPLy`**
  - `PULSe` — **RIG** `Apply_Pulse` · `<freq>, <amp>, <offset>` · args: `freq`, `amp`, `offset`
  - `SINusoid` — **RIG** `Apply_Sine` · `<freq>, <amp>, <offset>` · args: `freq`, `amp`, `offset`
  - `SQUare` — **RIG** `Apply_Square` · `<freq>, <amp>, <offset>` · args: `freq`, `amp`, `offset`
  - `NOISe` — **DO** `Do_Apply_Noise` · †<br>Using the APPLy Command
- **`ATTRibute`**
  - `AVERage?` — **NAB** `Get_Attribute_Average` · → NR1 dB · †<br>Arbitrary Waveform Commands
  - `CFACtor?` — **NAB** `Get_Attribute_Cfactor` · → NR3 dB · †<br>Arbitrary Waveform Commands
  - `POINts?` — **NAB** `Get_Attribute_Points` · → NR1 dB · †<br>Arbitrary Waveform Commands
  - `PTPeak?` — **NAB** `Get_Attribute_Ptpeak` · → NR3 dB · †<br>Arbitrary Waveform Commands
- **`BEEPer`**
  - `STATe` — **SET** `Set_Beeper_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>System-Related Commands
  - `STATe?` — **NAB** `Get_Beeper_State` · → BOOL · †<br>System-Related Commands
- **`BURS`**
  - `MODE` — **SET** `Set_Burst_Mode` · `<value>` · args: `value` · enum: `TRIG` | `GAT` · †<br>Burst Commands
  - `NCYC` — **SET** `Set_Burst_Ncycles` · `<value>` · args: `value` · †<br>Burst Commands
  - `PHAS` — **SET** `Set_Burst_Phase` · `<value>` · args: `value` · numeric (deg) · †<br>Burst Commands
  - **`INT`**
    - `PER` — **SET** `Set_Burst_Internal_Period` · `<value>` · args: `value` · numeric (s) · †<br>Burst Commands
- **`BURSt`**
  - `STATe` — **SET** `Set_Burst_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Burst Commands
  - `MODE?` — **NAB** `Get_Burst_Mode` · → CRD · †<br>Burst Commands
  - `NCYCles?` — **NAB** `Get_Burst_Ncycles` · → 1 value · †<br>Burst Commands
  - `PHASe?` — **NAB** `Get_Burst_Phase` · → 1 value · †<br>Burst Commands
  - `STATe?` — **NAB** `Get_Burst_State` · → BOOL · †<br>Burst Commands
  - **`GATE`**
    - `POLarity` — **SET** `Set_Burst_Gate_Polarity` · `<value>` · args: `value` · enum: `NORM` | `INV` · †<br>Burst Commands
    - `POLarity?` — **NAB** `Get_Burst_Gate_Polarity` · → CRD · †<br>Burst Commands
  - **`INTernal`**
    - `PERiod?` — **NAB** `Get_Burst_Internal_Period` · → NR3 s · †<br>Burst Commands
- **`CAL`**
  - `STR` — **SET** `Set_Calibration_String` · `<value>` · args: `value` · †<br>Calibration Message
  - `VAL` — **SET** `Set_Calibration_Value` · `<value>` · args: `value` · numeric · †
  - `COUNt?` — **NAB** `Get_Calibration_Count` · → NR1 · †<br>Calibration Count
  - `STRing?` — **NAB** `Get_Calibration_String` · → 1 value · †<br>Calibration Message
  - `VALue?` — **NAB** `Get_Calibration_Value` · → NR3 · †
  - **`SEC`**
    - `STAT` — **SET** `Set_Calibration_Secure_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
  - **`SECure`**
    - `STATe?` — **NAB** `Get_Calibration_Secure_State` · → BOOL · †
    - `CODE` — **DO** `Do_Calibration_Secure_Code` · †<br>Calibration Commands
- **`DATA`**
  - `CAT?` — **NAB** `Get_Data_Catalog` · → 1 value · †
  - `COPY` — **DO** `Do_Data_Copy` · †<br>Arbitrary Waveform Commands
  - `DAC` — **DO** `Do_Data_Dac` · †<br>Arbitrary Waveform Commands
  - `DEL` — **DO** `Do_Data_Delete` · †<br>Arbitrary Waveform Commands
  - **`ATTRibute`**
    - `AVERage?` — **NAB** `Get_Data_Attribute_Average` · → NR1 dB · †<br>Arbitrary Waveform Commands
    - `CFACtor?` — **NAB** `Get_Data_Attribute_Cfactor` · → NR3 dB · †<br>Arbitrary Waveform Commands
    - `POINts?` — **NAB** `Get_Data_Attribute_Points` · → NR1 dB · †<br>Arbitrary Waveform Commands
    - `PTPeak?` — **NAB** `Get_Data_Attribute_Ptpeak` · → NR3 dB · †<br>Arbitrary Waveform Commands
  - **`NVOLatile`**
    - `CATalog?` — **NAB** `Get_Data_Nvolatile_Catalog` · → 1 value · †
    - `FREE?` — **NAB** `Get_Data_Nvolatile_Free` · → 1 value · †
- **`DEV`**
  - `DCYC?` — **NAB** `Get_Deviation_Dcycle` · → NR3 % · †<br>Pulse Width Modulation (PWM) Commands
- **`DEViation`**
  - `DCYCle` — **SET** `Set_Deviation_Dcycle` · `<value>` · args: `value` · numeric (%) · †<br>Pulse Width Modulation (PWM) Commands
- **`DISP`**
  - `TEXT` — **SET** `Set_Display_Text` · `<value>` · args: `value` · †<br>System-Related Operations
- **`DISPlay`**
  - `TEXT?` — **NAB** `Get_Display_Text` · → 1 value · †<br>System-Related Operations
  - **`TEXT`**
    - `CLEar` — **DO** `Clear_Text`
- **`FM`**
  - `DEViation` — **SET** `Set_Fm_Deviation` · `<value>` · args: `value` · †<br>FM Commands
  - `SOUR` — **SET** `Set_Fm_Source` · `<value>` · args: `value` · enum: `INT` | `EXT` · †<br>FM Commands
  - `DEViation?` — **NAB** `Get_Fm_Deviation` · → 1 value · †<br>FM Commands
  - `SOURce?` — **NAB** `Get_Fm_Source` · → CRD · †<br>FM Commands
  - `STATe?` — **NAB** `Get_Fm_State` · → BOOL · †<br>FM Commands
  - `INTernal` — **DO** `Do_Fm_Internal` · †<br>FM Commands
  - `STATe` — **DO** `FM_State_OFF` · `OFF`
  - `STATe` — **DO** `FM_State_ON` · `ON`
  - **`INTernal`**
    - `FREQuency` — **SET** `Set_Fm_Internal_Frequency` · `<value>` · args: `value` · †<br>Modulating Waveform Frequency
    - `FREQuency?` — **NAB** `Get_Fm_Internal_Frequency` · → 1 value · †<br>Frequency Modulation (FM) Commands
    - `FUNCtion` — **DO** `Do_Fm_Internal_Function` · †<br>Modulating Waveform Shape
- **`FORMat`**
  - `BORDer` — **SET** `Set_Format_Border` · `<value>` · args: `value` · †<br>Arbitrary Waveform Commands
  - `BORDer?` — **NAB** `Get_Format_Border` · → 1 value · †<br>Arbitrary Waveform Commands
- **`FREQuency`**
  - `CENTer` — **SET** `Set_Frequency_Center` · `<value>` · args: `value` · numeric · †<br>Frequency Sweep Commands
  - `SPAN` — **SET** `Set_Frequency_Span` · `<value>` · args: `value` · numeric · †
  - `STARt` — **SET** `Set_Frequency_Start` · `<value>` · args: `value` · numeric · †<br>Start Frequency and Stop Frequency
  - `STOP` — **SET** `Set_Frequency_Stop` · `<value>` · args: `value` · numeric · †<br>Start Frequency and Stop Frequency
  - `CENTer?` — **NAB** `Get_Frequency_Center` · → NR3 · †<br>Frequency Sweep Commands
  - `SPAN?` — **NAB** `Get_Frequency_Span` · → NR3 · †
  - `STARt?` — **NAB** `Get_Frequency_Start` · → NR3 · †<br>Sweep Commands
  - `STOP?` — **NAB** `Get_Frequency_Stop` · → NR3 · †<br>Sweep Commands
- **`FSK`**
  - `SOUR` — **SET** `Set_Fskey_Source` · `<value>` · args: `value` · enum: `INT` | `EXT` · †<br>FSK Commands
- **`FSKey`**
  - `FREQuency` — **SET** `Set_Fskey_Frequency` · `<value>` · args: `value` · †<br>FSK Commands
  - `STATe` — **SET** `Set_Fskey_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>FSK Commands
  - `FREQuency?` — **NAB** `Get_Fskey_Frequency` · → 1 value · †<br>FSK Commands
  - `SOURce?` — **NAB** `Get_Fskey_Source` · → CRD · †<br>FSK Commands
  - `STATe?` — **NAB** `Get_Fskey_State` · → BOOL · †<br>FSK Commands
  - **`INTernal`**
    - `RATE` — **SET** `Set_Fskey_Internal_Rate` · `<value>` · args: `value` · numeric · †<br>FSK Commands
    - `RATE?` — **NAB** `Get_Fskey_Internal_Rate` · → NR3 · †<br>FSK Commands
- **`FUNC`**
  - `USER` — **SET** `Set_Function_User` · `<value>` · args: `value` · †<br>Arbitrary Waveform Commands
  - `PULS` — **DO** `Do_Function_Pulse` · †<br>Pulse Configuration Commands
  - `RAMP` — **DO** `Do_Function_Ramp` · †<br>frequency reduced for ramp function
  - **`PULS`**
    - `HOLD` — **SET** `Set_Function_Pulse_Hold` · `<value>` · args: `value` · enum: `WIDT` | `DCYC` · †<br>Using the APPLy Command
- **`FUNCtion`**
  - `USER?` — **NAB** `Get_Function_User` · → 1 value · †<br>Arbitrary Waveform Commands
  - `SHAPe` — **DO** `Do_Function_Shape` · †
  - **`PULSe`**
    - `DCYCle` — **SET** `Set_Function_Pulse_Dcycle` · `<value>` · args: `value` · numeric (%) · †<br>Pulse Configuration Commands
    - `TRANsition` — **SET** `Set_Function_Pulse_Transition` · `<value>` · args: `value` · †<br>Edge Time
    - `WIDTh` — **SET** `Setup_Pulse_Width` · `<width_sec>` · args: `width_sec` · numeric
    - `DCYCle?` — **NAB** `Get_Function_Pulse_Dcycle` · → NR3 % · †<br>Pulse Configuration Commands
    - `HOLD?` — **NAB** `Get_Function_Pulse_Hold` · → NR3 · †<br>Using the APPLy Command
    - `TRANsition?` — **NAB** `Get_Function_Pulse_Transition` · → 1 value · †<br>Pulse Configuration Commands
    - `WIDTh?` — **NAB** `Get_Function_Pulse_Width` · → NR3 · †<br>Pulse Configuration Commands
  - **`RAMP`**
    - `SYMMetry` — **SET** `Set_Function_Ramp_Symmetry` · `<value>` · args: `value` · †<br>Output Configuration Commands
    - `SYMMetry?` — **NAB** `Get_Function_Ramp_Symmetry` · → 1 value · †<br>Output Configuration Commands
  - **`SQUare`**
    - `DCYCle` — **SET** `Set_Function_Square_Dcycle` · `<value>` · args: `value` · numeric (%) · †<br>Output Configuration Commands
    - `DCYCle?` — **NAB** `Get_Function_Square_Dcycle` · → NR3 % · †<br>Output Configuration Commands
- **`GATE`**
  - `POLarity` — **DO** `Do_Gate_Polarity` · †
- **`INTernal`**
  - `PERiod` — **DO** `Do_Internal_Period` · †
- **`KLOCk`**
  - `EXCLude` — **SET** `Set_Klock_Exclude` · `<value>` · args: `value` · †<br>System-Related Commands
  - `EXCLude?` — **NAB** `Get_Klock_Exclude` · → 1 value · †<br>System-Related Commands
  - `STATe` — **DO** `Do_Klock_State` · †<br>System-Related Commands
- **`LAN`**
  - `LIPaddress?` — **NAB** `Get_Lan_Lipaddress` · → 1 value · †
  - `MAC?` — **NAB** `Get_Lan_Mac` · → 1 value · †
  - `IPADdress` — **DO** `Do_Lan_Ipaddress` · †
  - `MEDiasense` — **DO** `Do_Lan_Mediasense` · †
  - `NETBios` — **DO** `Do_Lan_Netbios` · †
  - **`TELNet`**
    - `PROM` — **DO** `Do_Lan_Telnet_Prompt` · †
    - `WMES` — **DO** `Do_Lan_Telnet_Wmessage` · †
- **`MARKer`**
  - `FREQuency` — **SET** `Set_Marker_Frequency` · `<value>` · args: `value` · †<br>Marker Frequency
  - `FREQuency?` — **NAB** `Get_Marker_Frequency` · → 1 value · †<br>Frequency Sweep Commands
- **`MEMory`**
  - `NSTates?` — **NAB** `Get_Memory_Nstates` · → 1 value · †<br>State Storage Commands
  - `STATe` — **DO** `Do_Memory_State` · †<br>State Storage Commands
  - **`STATe`**
    - `NAME` — **SET** `Set_Memory_State_Name` · `<value>` · args: `value` · †<br>State Storage Commands
    - `CATalog?` — **NAB** `Get_Memory_State_Catalog` · → 1 value · †
    - `NAME?` — **NAB** `Get_Memory_State_Name` · → 1 value · †<br>State Storage Commands
    - `VALid?` — **NAB** `Get_Memory_State_Value` · → NR3 · †<br>State Storage Commands
    - `DELete` — **DO** `Do_Memory_State_Delete` · †
- **`NVOLatile`**
  - `CATalog?` — **NAB** `Get_Nvolatile_Catalog` · → 1 value · †<br>Arbitrary Waveform Commands
  - `FREE?` — **NAB** `Get_Nvolatile_Free` · → 1 value · †<br>Arbitrary Waveform Commands
- **`OUTPut`**
  - `LOAD` — **SET** `Set_Output_Load` · `<ohms>` · args: `ohms`
  - `POLarity` — **SET** `Set_Output_Polarity` · `<value>` · args: `value` · enum: `NORM` | `INV` · †
  - `TRIGger` — **SET** `Set_Output_Trigger` · `<value>` · args: `value` · †<br>Trigger Out Signal
  - `LOAD?` — **NAB** `Get_Output_Load` · → 1 value · †
  - `POLarity?` — **NAB** `Get_Output_Polarity` · → CRD · †
  - `SYNC?` — **NAB** `Get_Output_Sync` · → BOOL · †<br>Output Configuration
  - `TRIGger?` — **NAB** `Get_Output_Trigger` · → 1 value · †<br>Trigger Out Signal
  - `SYNC` — **DO** `Sync_OFF` · `OFF`
  - `SYNC` — **DO** `Sync_ON` · `ON`
  - **`TRIGger`**
    - `SLOPe` — **SET** `Set_Output_Trigger_Slope` · `<value>` · args: `value` · enum: `POS` | `NEG` · †<br>Trigger Out Signal
    - `SLOPe?` — **NAB** `Get_Output_Trigger_Slope` · → CRD · †<br>Trigger Out Signal
- **`PHASe`**
  - `REFerence` — **DO** `Do_Phase_Reference` · †<br>Phase-Lock Commands
  - **`UNLock`**
    - **`ERRor`**
      - `STATe` — **SET** `Set_Phase_Unlock_Error_State` · `<value>` · args: `value` · †<br>Phase-Lock Commands
      - `STATe?` — **NAB** `Get_Phase_Unlock_Error_State` · → ERROR · †<br>Phase-Lock Commands
- **`PM`**
  - `DEViation` — **SET** `Set_Pm_Deviation` · `<value>` · args: `value` · †<br>PM Commands
  - `SOUR` — **SET** `Set_Pm_Source` · `<value>` · args: `value` · enum: `INT` | `EXT` · †<br>PM Commands
  - `STATe` — **SET** `Set_Pm_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>PM Commands
  - `DEViation?` — **NAB** `Get_Pm_Deviation` · → 1 value · †<br>PM Commands
  - `SOURce?` — **NAB** `Get_Pm_Source` · → CRD · †<br>PM Commands
  - `STATe?` — **NAB** `Get_Pm_State` · → BOOL · †<br>PM Commands
  - `INTernal` — **DO** `Do_Pm_Internal` · †<br>PM Commands
  - **`INTernal`**
    - `FREQuency` — **SET** `Set_Pm_Internal_Frequency` · `<value>` · args: `value` · †<br>Modulating Waveform Frequency
    - `FREQuency?` — **NAB** `Get_Pm_Internal_Frequency` · → 1 value · †<br>Phase Modulation (PM) Commands
    - `FUNCtion` — **DO** `Do_Pm_Internal_Function` · †<br>Modulating Waveform Shape
- **`PULSe`**
  - `PERiod` — **SET** `Set_Pulse_Period` · `<value>` · args: `value` · numeric (s) · †<br>Pulse Configuration Commands
  - `PERiod?` — **NAB** `Get_Pulse_Period` · → NR3 s · †<br>Pulse Configuration Commands
  - `TRANsition` — **DO** `Do_Pulse_Transition` · †
  - `WIDTh` — **DO** `Do_Pulse_Width` · †
- **`PWM`**
  - `DEV` — **SET** `Set_Pwm_Deviation` · `<value>` · args: `value` · †<br>PWM Commands
  - `SOURce` — **SET** `Set_Pwm_Source` · `<value>` · args: `value` · enum: `INT` | `EXT` · †<br>PWM Commands
  - `STATe` — **SET** `Set_Pwm_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>PWM Commands
  - `DEViation?` — **NAB** `Get_Pwm_Deviation` · → 1 value · †<br>PWM Commands
  - `SOURce?` — **NAB** `Get_Pwm_Source` · → CRD · †<br>PWM Commands
  - `STATe?` — **NAB** `Get_Pwm_State` · → BOOL · †<br>PWM Commands
  - `INTernal` — **DO** `Do_Pwm_Internal` · †<br>PWM Commands
  - **`DEViation`**
    - `DCYCle` — **SET** `Set_Pwm_Deviation_Dcycle` · `<value>` · args: `value` · numeric (%) · †<br>PWM Commands
    - `DCYCle?` — **NAB** `Get_Pwm_Deviation_Dcycle` · → NR3 % · †<br>PWM Commands
  - **`INTernal`**
    - `FREQuency` — **SET** `Set_Pwm_Internal_Frequency` · `<value>` · args: `value` · †<br>Modulating Waveform Frequency
    - `FREQuency?` — **NAB** `Get_Pwm_Internal_Frequency` · → 1 value · †<br>Pulse Width Modulation (PWM) Commands
    - `FUNCtion` — **DO** `Do_Pwm_Internal_Function` · †<br>Modulating Waveform Shape
- **`QUEStionable`**
  - `ENABle` — **SET** `Set_Questionable_Enable` · `<value>` · args: `value` · integer · †<br>Status Reporting Commands
  - `CONDition?` — **NAB** `Get_Questionable_Condition` · → NR1 · †<br>Status Reporting Commands
  - `ENABle?` — **NAB** `Get_Questionable_Enable` · → NR1 · †<br>Status Reporting Commands
  - `EVENt?` — **NAB** `Get_Questionable_Event` · → NR1 · †<br>Status Reporting Commands
- **`SECure`**
  - `STATe` — **SET** `Set_Secure_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Calibration Commands
  - `STATe?` — **NAB** `Get_Secure_State` · → BOOL · †<br>Calibration Commands
  - `CODE` — **DO** `Do_Secure_Code` · †<br>Calibration Commands
- **`SQUare`**
  - `DCYCle?` — **NAB** `Get_Square_Dcycle` · → NR3 % · †<br>Output Configuration Commands
- **`STAT`**
  - **`QUES`**
    - `ENAB` — **SET** `Set_State_Questionable_Enable` · `<value>` · args: `value` · integer · †<br>The Questionable Data Register
    - `EVEN?` — **NAB** `Get_State_Questionable_Event` · → NR1 · †<br>What is an Event Register?
- **`STATus`**
  - `PRESet` — **DO** `Do_State_Preset` · †<br>Status Reporting Commands
  - `QUEStionable` — **DO** `Do_State_Questionable` · †
  - **`QUEStionable`**
    - `CONDition?` — **NAB** `Get_State_Questionable_Condition` · → NR1 · †
    - `ENABle?` — **NAB** `Get_State_Questionable_Enable` · → NR1 · †<br>The Questionable Data Register
- **`SWE`**
  - `TIME` — **SET** `Set_Sweep_Time` · `<value>` · args: `value` · numeric (s) · †<br>Sweep Time
- **`SWEep`**
  - `SPACing` — **SET** `Set_Sweep_Spacing` · `<value>` · args: `value` · enum: `LIN` | `LOG` · †<br>Sweep Mode
  - `STATe` — **SET** `Set_Sweep_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Sweep Commands
  - `SPACing?` — **NAB** `Get_Sweep_Spacing` · → 1 value · †<br>Sweep Mode
  - `STATe?` — **NAB** `Get_Sweep_State` · → BOOL · †<br>Sweep Commands
  - `TIME?` — **NAB** `Get_Sweep_Time` · → NR3 s · †<br>Frequency Sweep Commands
- **`SYST`**
  - **`BEEP`**
    - `STAT` — **SET** `Set_System_Beeper_State` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>System-Related Commands
- **`SYSTem`**
  - `ERRor?` — **NAB** `Get_Error_Queue` · → NR2
  - `VERSion?` — **NAB** `Get_System_Version` · → 1 value · †<br>System-Related Commands
  - `BEEPer` — **DO** `Do_System_Beeper` · †
  - `LOCal` — **DO** `Do_System_Local` · †<br>Interface Configuration Commands
  - `REMote` — **DO** `Do_System_Remote` · †<br>Interface Configuration Commands
  - `RWLock` — **DO** `Do_System_Rwlock` · †<br>Interface Configuration Commands
  - **`BEEPer`**
    - `STATe?` — **NAB** `Get_System_Beeper_State` · → BOOL · †<br>System-Related Commands
  - **`COMMunicate`**
    - `LAN` — **DO** `Do_System_Communicate_Lan` · †<br>Interface Configuration Commands
    - `RLSTate` — **DO** `Do_System_Communicate_Rlstate` · †<br>Interface Configuration Commands
    - **`LAN`**
      - `IPADdress` — **SET** `Set_System_Communicate_Lan_Ipaddress` · `<value>` · args: `value` · †<br>Remote Interface Configuration
      - `MEDiasense` — **SET** `Set_System_Communicate_Lan_Mediasense` · `<value>` · args: `value` · †
      - `NETBios` — **SET** `Set_System_Communicate_Lan_Netbios` · `<value>` · args: `value` · †
      - `IPADdress?` — **NAB** `Get_System_Communicate_Lan_Ipaddress` · → 1 value · †<br>Remote Interface Configuration
      - `LIPaddress?` — **NAB** `Get_System_Communicate_Lan_Lipaddress` · → 1 value · †
      - `MAC?` — **NAB** `Get_System_Communicate_Lan_Mac` · → 1 value · †
      - `MEDiasense?` — **NAB** `Get_System_Communicate_Lan_Mediasense` · → 1 value · †
      - `NETBios?` — **NAB** `Get_System_Communicate_Lan_Netbios` · → 1 value · †
      - **`TELNet`**
        - `PROMpt` — **SET** `Set_System_Communicate_Lan_Telnet_Prompt` · `<value>` · args: `value` · †
        - `WMESsage` — **SET** `Set_System_Communicate_Lan_Telnet_Wmessage` · `<value>` · args: `value` · †
        - `PROMpt?` — **NAB** `Get_System_Communicate_Lan_Telnet_Prompt` · → 1 value · †
        - `WMESsage?` — **NAB** `Get_System_Communicate_Lan_Telnet_Wmessage` · → 1 value · †
  - **`KLOCk`**
    - `EXCLude?` — **NAB** `Get_System_Klock_Exclude` · → 1 value · †
    - `STATe` — **DO** `Do_System_Klock_State` · †
  - **`SECurity`**
    - `IMMediate` — **DO** `Do_System_Secure_Immediate` · †<br>System-Related Commands
- **`TELNet`**
  - `PROMpt` — **SET** `Set_Telnet_Prompt` · `<value>` · args: `value` · †<br>Interface Configuration Commands
  - `WMESsage` — **SET** `Set_Telnet_Wmessage` · `<value>` · args: `value` · †<br>Interface Configuration Commands
  - `PROMpt?` — **NAB** `Get_Telnet_Prompt` · → 1 value · †<br>Interface Configuration Commands
  - `WMESsage?` — **NAB** `Get_Telnet_Wmessage` · → 1 value · †<br>Interface Configuration Commands
- **`TEXT`**
  - `CLEar` — **DO** `Do_Text_Clear` · †<br>System-Related Commands
- **`TRIG`**
  - `SOUR` — **SET** `Set_Trigger_Source` · `<value>` · args: `value` · enum: `IMM` | `EXT` | `BUS` · †<br>Burst Commands
- **`TRIGger`**
  - `SLOPe` — **SET** `Set_Trigger_Slope` · `<value>` · args: `value` · enum: `POS` | `NEG` · †<br>Burst Commands
  - `SLOPe?` — **NAB** `Get_Trigger_Slope` · → CRD · †<br>Burst Commands
  - `SOURce?` — **NAB** `Get_Trigger_Source` · → CRD · †<br>Burst Commands
- **`UNIT`**
  - `ANGLe` — **SET** `Set_Unit_Angle` · `<value>` · args: `value` · †<br>Burst Commands
  - `ANGLe?` — **NAB** `Get_Unit_Angle` · → 1 value · †<br>Burst Commands
- **`UNLock`**
  - **`ERRor`**
    - `STATe` — **DO** `Do_Unlock_Error_State` · †
- **`VOLTage`**
  - `OFFSet` — **SET** `Set_Offset` · `<offset>` · args: `offset` · numeric (V)
  - `UNIT` — **SET** `Set_Voltage_Unit` · `<unit>` · args: `unit` · enum: `VPP` | `VRMS` | `DBM`
  - `OFFSet?` — **NAB** `Get_Voltage_Offset` · → NR3 V · †<br>Output Configuration Commands
  - `UNIT?` — **NAB** `Get_Voltage_Unit` · → CRD V · †<br>Output Configuration Commands
  - `HIGH` — **DO** `Do_Voltage_High` · †<br>Output Configuration
  - `LOW` — **DO** `Do_Voltage_Low` · †<br>Output Configuration

## Common commands (IEEE 488.2)

- `*CLS` — **DO** `Do_Cls` · †
- `*OPC` — **DO** `Do_Opc` · †
- `*WAI` — **DO** `Do_Wai` · †
- `*ESE?` — **NAB** `Get_Ese` · → NR1 · †
- `*ESR?` — **NAB** `Get_Esr` · → NR1 · †
- `*IDN?` — **NAB** `Get_Idn` · → AARD · †
- `*LRN?` — **NAB** `Get_Lrn` · → AARD · †
- `*OPC?` — **NAB** `Get_Opc` · → NR1 · †
- `*PSC?` — **NAB** `Get_Psc` · → NR1 · †
- `*SRE?` — **NAB** `Get_Sre` · → NR1 · †
- `*STB?` — **NAB** `Get_Stb` · → NR1 · †
- `*TST?` — **NAB** `Get_Tst` · → NR1 · †
- `*RST` — **DO** `Reset_Device`
- `*ESE <value>` — **SET** `Set_Ese` · `<value>` · args: `value` · integer · †
- `*PSC <value>` — **SET** `Set_Psc` · `<value>` · args: `value` · †
- `*RCL <value>` — **SET** `Set_Rcl` · `<value>` · args: `value` · †
- `*SAV <value>` — **SET** `Set_Sav` · `<value>` · args: `value` · †
- `*SRE <value>` — **SET** `Set_Sre` · `<value>` · args: `value` · integer · †
- `*TRG` — **DO** `Trigger_Immediate`

<!-- END GENERATED -->

---

## Notes carried over

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
