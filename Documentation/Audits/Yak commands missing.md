# YAK commands missing

Every SCPI command the instrument manuals document and
`BackEnd/openair-yak/Yak/*/*/commands.json` does not, as YAK entries ready to
paste. Generated 2026-07-27 against the tables as of commit `3f23f2875`
(15 models, 515 commands).

**2483 commands are missing, 1128 of them queries.** The tables can currently
set far more than they can read back — 95 of 515 existing commands are NAB —
which is why a panel meter shows a dash while the same panel's knob works.

## What is reliable here, and what is not

| | |
|---|---|
| `scpi` | **Reliable.** Lifted verbatim from the manual, argument cut off, index parameterised. |
| verb bucket | **Mostly.** `?` → NAB. Otherwise: a node with a query sibling is a readable parameter, so SET; a node without is an action, so DO. That rule mis-files a write-only parameter as DO. |
| command name | **Derived**, from the SCPI path expanded through each manual's own long-form spellings (`VOLT` → Voltage). Correct but verbose — shorten the ones a panel will actually bind. |
| `description` | **Present on 778 of 2483.** The manual's nearest preceding heading, kept only where it reads like a description. The other 1705 are left absent rather than filled with the manual's page furniture. |
| `subsystem` | Reliable — the leading mnemonic. |

No `args` names are proposed: the manuals name arguments inconsistently and
`<value>` is what a single-widget SET needs. Multi-argument commands are
therefore all filed as SET rather than RIG — **0 RIG entries below**, and the
ones that take several arguments together have to be re-bucketed by hand.

## Coverage

| Family | Model | In manual | of which queries | In YAK | YAK NAB | Absent | Query gap |
|---|---|--:|--:|--:|--:|--:|--:|
| DMM | 34401A | 127 | 61 | 49 | 15 | **97** | 9 |
| Generator | 33210A | 246 | 112 | 25 | 3 | **220** | 9 |
| Generator | 33220A | 246 | 112 | 25 | 3 | **220** | 9 |
| Load | 6060B | 50 | 6 | 28 | 4 | **31** | 0 |
| Power | 66101A | 181 | 72 | 13 | 3 | **174** | 0 |
| Power | 66102A | 181 | 72 | 18 | 4 | **170** | 1 |
| Power | 66103A | 181 | 72 | 18 | 4 | **170** | 1 |
| Power | 66104A | 184 | 73 | 18 | 4 | **173** | 1 |
| Scope | 54641D | 381 | 163 | 113 | 14 | **292** | 32 |
| Scope | DS1104Z | 717 | 353 | 73 | 12 | **667** | 20 |
| Spectrum | N9340B | 194 | 83 | 36 | 8 | **187** | 0 |

*Absent* = neither the command nor its query is in the table. *Query gap* = the
table can set it but never read it back, so only a NAB entry is missing.

## Sources that could not be read

Only `.md` was read, as asked. That leaves real holes, and they land on exactly
the three models with the worst coverage:

| Model | YAK commands | Why nothing could be extracted |
|---|--:|---|
| `Router/3235` | 8 | `3235 - SWITCHER/` holds **only PDFs** — `HP 3235E Programming.pdf`, Installation, Quick Reference. No markdown exists. |
| `LCR/4263A` | 0 | `HP 4263A LCR meter/` is **five PDFs**. `Raw Commands.txt` in the YAK tree is the only machine-readable source. |
| `Distortion/HP_8903B` | 0 | `8903B Distorting Analyzer/` is **four PDFs**. |

Two further gaps in folders that *do* have markdown:

- **`Load/6060B`** — both of the PDFs you named are unconverted, and the
  operator manual says so itself: *"Programming Guide includes a complete
  Language Dictionary"*. That Programming Guide is
  `06060-90005 - Programming.pdf`. The 50 commands found below come from
  scattered examples in the operator and service manuals, not from a dictionary,
  so the real 6060B gap is larger than the 31 shown.
- **`Distortion/Porta_one`** — `P1PA-DD_GPIB_Programming_Ref_Manual_rev2.pdf.md`
  exists but its PDF→markdown conversion lost the character encoding; the file is
  mojibake (`##########`) with no recoverable SCPI. Not included above.

Converting those four PDFs is the single highest-value thing that could be done
for this library: it is the difference between a Router panel that has never
worked and one that can, and between an LCR meter with zero vocabulary and a
working one.

## Instruments in the manual set with no YAK model at all

Not missing commands — missing *models*. Both have a full programming guide in
markdown, so a table could be authored today:

- **8712ES / 8714ES RF Network Analyzer** — `08714-90015 - Programming guide.md` (392 KB)
- **HP ESA-L1500A Spectrum Analyzer** — `HP - E441190003 - Programmer's Guide` (392 KB)

---

## DMM — 34401A

Source: `HP 34401A user_s guide.md`

106 missing — SET 30, DO 20, NAB 56. The table has 49.

### SET — 30

```json
"set": {
  // BEEP
  "Set_Beeper_State": {"scpi": ":BEEPer:STATe <value>", "description": "System-Related Commands", "subsystem": "BEEP"},

  // CAL
  "Set_Calibration_Secure_State": {"scpi": "CALibration:SECure:STATe <value>", "description": "Calibration Overview", "subsystem": "CAL"},
  "Set_Calibration_String": {"scpi": "CALibration:STRing <value>", "description": "Calibration Message", "subsystem": "CAL"},
  "Set_Calibration_Value": {"scpi": "CALibration:VALue <value>", "description": "Calibration Commands", "subsystem": "CAL"},

  // CALC
  "Set_Calculate_Limit_Lower": {"scpi": "CALCulate:LIMit:LOWer <value>", "description": "Math Operations", "subsystem": "CALC"},
  "Set_Calculate_Limit_Upper": {"scpi": "CALCulate:LIMit:UPPer <value>", "description": "Math Operations", "subsystem": "CALC"},

  // Common
  "Set_Ese": {"scpi": "*ESE <value>", "subsystem": "Common"},
  "Set_Psc": {"scpi": "*PSC <value>", "subsystem": "Common"},
  "Set_Sre": {"scpi": "*SRE <value>", "subsystem": "Common"},

  // DATA
  "Set_Data_Feed": {"scpi": "DATA:FEED <value>", "description": "Math Operations", "subsystem": "DATA"},

  // DB
  "Set_Db_Reference": {"scpi": ":DB:REFerence <value>", "description": "Math Operation Commands", "subsystem": "DB"},

  // DET
  "Set_Detector_Bandwidth": {"scpi": "DETector:BANDwidth <value>", "subsystem": "DET"},

  // FREQ
  "Set_Frequency_Aperture": {"scpi": "FREQuency:APERture <value>", "description": "Measurement Configuration", "subsystem": "FREQ"},
  "Set_Frequency_Voltage_Range": {"scpi": "FREQuency:VOLTage:RANGe <value>", "subsystem": "FREQ"},

  // FRES
  "Set_Fresistance_Nplcycles": {"scpi": "FRESistance:NPLCycles <value>", "subsystem": "FRES"},
  "Set_Fresistance_Range": {"scpi": "FRESistance:RANGe <value>", "subsystem": "FRES"},
  "Set_Fresistance_Resolution": {"scpi": "FRESistance:RESolution <value>", "description": "Measurement Configuration Commands", "subsystem": "FRES"},

  // LIM
  "Set_Limit_Lower": {"scpi": ":LIMit:LOWer <value>", "subsystem": "LIM"},
  "Set_Limit_Upper": {"scpi": ":LIMit:UPPer <value>", "subsystem": "LIM"},

  // NULL
  "Set_Null_Offset": {"scpi": ":NULL:OFFSet <value>", "description": "Math Operation Commands", "subsystem": "NULL"},

  // PER
  "Set_Period_Aperture": {"scpi": "PERiod:APERture <value>", "description": "Measurement Configuration", "subsystem": "PER"},
  "Set_Period_Voltage_Range": {"scpi": "PERiod:VOLTage:RANGe <value>", "subsystem": "PER"},

  // QUES
  "Set_Questionable_Enable": {"scpi": ":QUEStionable:ENABle <value>", "description": "Status Reporting Commands", "subsystem": "QUES"},

  // RES
  "Set_Resolution_Nplcycles": {"scpi": "RESistance:NPLCycles <value>", "subsystem": "RES"},
  "Set_Resolution_Range": {"scpi": "RESistance:RANGe <value>", "subsystem": "RES"},
  "Set_Resolution_Resolution": {"scpi": "RESistance:RESolution <value>", "description": "Measurement Configuration Commands", "subsystem": "RES"},

  // SEC
  "Set_Secure_State": {"scpi": ":SECure:STATe <value>", "description": "Calibration Commands", "subsystem": "SEC"},

  // STAT
  "Set_State_Questionable_Enable": {"scpi": "STATus:QUEStionable:ENABle <value>", "description": "The SCPI Status Model", "subsystem": "STAT"},

  // SYST
  "Set_System_Beeper_State": {"scpi": "SYSTem:BEEPer:STATe <value>", "description": "System-Related Commands", "subsystem": "SYST"},

  // VOLT
  "Set_Voltage_Range": {"scpi": "VOLTage:RANGe <value>", "description": "An Introduction to the SCPI Language", "subsystem": "VOLT"},
}
```

### DO — 20

```json
"do": {
  // BACK
  "Do_Back_Goto": {"scpi": "BACK:GOTO", "description": "Using the Status Registers", "subsystem": "BACK"},

  // CAL
  "Do_Calibration_Secure": {"scpi": "CALibration:SECure", "subsystem": "CAL"},
  "Do_Calibration_Secure_Code": {"scpi": "CALibration:SECure:CODE", "description": "Calibration Overview", "subsystem": "CAL"},

  // CONF
  "Do_Configure_Frequency": {"scpi": "CONF:FREQ", "description": "Measurement Configuration", "subsystem": "CONF"},
  "Do_Configure_Period": {"scpi": "CONFigure:PERiod", "subsystem": "CONF"},
  "Do_Configure_Voltage": {"scpi": "CONF:VOLT", "subsystem": "CONF"},

  // Common
  "Do_Opc": {"scpi": "*OPC", "subsystem": "Common"},
  "Do_Trg": {"scpi": "*TRG", "subsystem": "Common"},

  // DCV
  "Do_Dcv_Dcv": {"scpi": "DCV:DCV", "subsystem": "DCV"},

  // FREQ
  "Do_Frequency_Voltage": {"scpi": "FREQuency:VOLTage", "subsystem": "FREQ"},

  // PER
  "Do_Period_Voltage": {"scpi": "PERiod:VOLTage", "subsystem": "PER"},

  // SEC
  "Do_Secure_Code": {"scpi": ":SECure:CODE", "description": "Calibration Commands", "subsystem": "SEC"},

  // SENS
  "Do_Sense_Function": {"scpi": "SENSe:FUNCtion", "description": "Using the CONFigure Command", "subsystem": "SENS"},

  // STAT
  "Do_State_Preset": {"scpi": "STATus:PRESet", "description": "Status Reporting Commands", "subsystem": "STAT"},

  // SYST
  "Do_System_Beeper": {"scpi": "SYSTem:BEEPer", "subsystem": "SYST"},
  "Do_System_Local": {"scpi": "SYSTem:LOCal", "description": "RS-232 Interface Commands", "subsystem": "SYST"},
  "Do_System_Remote": {"scpi": "SYSTem:REMote", "description": "RS-232 Interface Commands", "subsystem": "SYST"},
  "Do_System_Rwlock": {"scpi": "SYSTem:RWLock", "description": "RS-232 Interface Commands", "subsystem": "SYST"},

  // TEXT
  "Do_Text_Clear": {"scpi": ":TEXT:CLEar", "description": "System-Related Commands", "subsystem": "TEXT"},

  // TRIG
  "Do_Trigger_Source_Immediate": {"scpi": "TRIGger:SOURce:IMMediate", "description": "How to Use the Message Available Bit (MAV)", "subsystem": "TRIG"},
}
```

### NAB — 56

```json
"nab": {
  // AVER
  "Get_Average_Average": {"scpi": ":AVERage:AVERage?", "description": "Math Operation Commands", "subsystem": "AVER"},
  "Get_Average_Count": {"scpi": ":AVERage:COUNt?", "description": "Math Operation Commands", "subsystem": "AVER"},

  // BEEP
  "Get_Beeper_State": {"scpi": ":BEEPer:STATe?", "description": "System-Related Commands", "subsystem": "BEEP"},

  // CAL
  "Get_Calibration_Count": {"scpi": "CALibration:COUNt?", "description": "Calibration Count", "subsystem": "CAL"},
  "Get_Calibration_Secure_State": {"scpi": "CALibration:SECure:STATe?", "subsystem": "CAL"},
  "Get_Calibration_String": {"scpi": "CALibration:STRing?", "subsystem": "CAL"},
  "Get_Calibration_Value": {"scpi": "CALibration:VALue?", "subsystem": "CAL"},

  // CALC
  "Get_Calculate_Average_Count": {"scpi": "CALCulate:AVERage:COUNt?", "description": "Math Operations", "subsystem": "CALC"},
  "Get_Calculate_Db_Reference": {"scpi": "CALCulate:DB:REFerence?", "subsystem": "CALC"},
  "Get_Calculate_Function": {"scpi": "CALCulate:FUNCtion?", "subsystem": "CALC"},
  "Get_Calculate_Limit_Lower": {"scpi": "CALCulate:LIMit:LOWer?", "subsystem": "CALC"},
  "Get_Calculate_Limit_Upper": {"scpi": "CALCulate:LIMit:UPPer?", "subsystem": "CALC"},
  "Get_Calculate_Null_Offset": {"scpi": "CALCulate:NULL:OFFSet?", "subsystem": "CALC"},
  "Get_Calculate_State": {"scpi": "CALCulate:STATe?", "subsystem": "CALC"},

  // Common
  "Get_Ese": {"scpi": "*ESE?", "subsystem": "Common"},
  "Get_Esr": {"scpi": "*ESR?", "subsystem": "Common"},
  "Get_Opc": {"scpi": "*OPC?", "subsystem": "Common"},
  "Get_Psc": {"scpi": "*PSC?", "subsystem": "Common"},
  "Get_Sre": {"scpi": "*SRE?", "subsystem": "Common"},
  "Get_Stb": {"scpi": "*STB?", "subsystem": "Common"},
  "Get_Tst": {"scpi": "*TST?", "subsystem": "Common"},

  // DATA
  "Get_Data_Feed": {"scpi": "DATA:FEED?", "description": "Math Operations", "subsystem": "DATA"},
  "Get_Data_Points": {"scpi": "DATA:POINts?", "subsystem": "DATA"},

  // DB
  "Get_Db_Reference": {"scpi": ":DB:REFerence?", "description": "Math Operation Commands", "subsystem": "DB"},

  // DET
  "Get_Detector_Bandwidth": {"scpi": "DETector:BANDwidth?", "subsystem": "DET"},

  // DISP
  "Get_Display_Text": {"scpi": "DISPlay:TEXT?", "subsystem": "DISP"},

  // FREQ
  "Get_Frequency_Aperture": {"scpi": "FREQuency:APERture?", "description": "Measurement Configuration", "subsystem": "FREQ"},
  "Get_Frequency_Voltage_Range": {"scpi": "FREQuency:VOLTage:RANGe?", "subsystem": "FREQ"},

  // FRES
  "Get_Fresistance_Nplcycles": {"scpi": "FRESistance:NPLCycles?", "subsystem": "FRES"},
  "Get_Fresistance_Range": {"scpi": "FRESistance:RANGe?", "subsystem": "FRES"},
  "Get_Fresistance_Resolution": {"scpi": "FRESistance:RESolution?", "description": "Measurement Configuration Commands", "subsystem": "FRES"},

  // LIM
  "Get_Limit_Lower": {"scpi": ":LIMit:LOWer?", "subsystem": "LIM"},
  "Get_Limit_Upper": {"scpi": ":LIMit:UPPer?", "subsystem": "LIM"},

  // MEAS
  "Get_Measure_Continuity": {"scpi": "MEASure:CONTinuity?", "description": "The MEASure? and CONFigure Commands", "subsystem": "MEAS"},
  "Get_Measure_Diode": {"scpi": "MEASure:DIODe?", "subsystem": "MEAS"},
  "Get_Measure_Fresistance": {"scpi": "MEASure:FRESistance?", "subsystem": "MEAS"},
  "Get_Measure_Period": {"scpi": "MEASure:PERiod?", "subsystem": "MEAS"},

  // NULL
  "Get_Null_Offset": {"scpi": ":NULL:OFFSet?", "description": "Math Operation Commands", "subsystem": "NULL"},

  // PER
  "Get_Period_Aperture": {"scpi": "PERiod:APERture?", "description": "Measurement Configuration", "subsystem": "PER"},
  "Get_Period_Voltage_Range": {"scpi": "PERiod:VOLTage:RANGe?", "subsystem": "PER"},

  // QUES
  "Get_Questionable_Enable": {"scpi": ":QUEStionable:ENABle?", "description": "Status Reporting Commands", "subsystem": "QUES"},
  "Get_Questionable_Event": {"scpi": ":QUEStionable:EVENt?", "description": "Status Reporting Commands", "subsystem": "QUES"},

  // RES
  "Get_Resolution_Nplcycles": {"scpi": "RESistance:NPLCycles?", "subsystem": "RES"},
  "Get_Resolution_Range": {"scpi": "RESistance:RANGe?", "subsystem": "RES"},
  "Get_Resolution_Resolution": {"scpi": "RESistance:RESolution?", "description": "Measurement Configuration Commands", "subsystem": "RES"},

  // ROUT
  "Get_Route_Terminals": {"scpi": "ROUTe:TERMinals?", "description": "Front / Rear Input Terminal Switching", "subsystem": "ROUT"},

  // SAMP
  "Get_Sample_Count": {"scpi": "SAMP:COUN?", "subsystem": "SAMP"},

  // SEC
  "Get_Secure_State": {"scpi": ":SECure:STATe?", "description": "Calibration Commands", "subsystem": "SEC"},

  // STAT
  "Get_State_Questionable_Enable": {"scpi": "STATus:QUEStionable:ENABle?", "subsystem": "STAT"},
  "Get_State_Questionable_Event": {"scpi": "STATus:QUEStionable:EVENt?", "subsystem": "STAT"},

  // SYST
  "Get_System_Beeper_State": {"scpi": "SYSTem:BEEPer:STATe?", "description": "System-Related Commands", "subsystem": "SYST"},
  "Get_System_Version": {"scpi": "SYSTem:VERSion?", "description": "SCPI Language Version Query", "subsystem": "SYST"},

  // TRIG
  "Get_Trigger_Count": {"scpi": "TRIGger:COUNt?", "subsystem": "TRIG"},
  "Get_Trigger_Delay": {"scpi": "TRIGger:DELay?", "subsystem": "TRIG"},
  "Get_Trigger_Source": {"scpi": "TRIGger:SOURce?", "description": "Trigger Source Choices", "subsystem": "TRIG"},

  // VOLT
  "Get_Voltage_Range": {"scpi": "VOLTage:RANGe?", "description": "An Introduction to the SCPI Language", "subsystem": "VOLT"},
}
```

## Generator — 33210A, 33220A

Identical missing sets across 2 models (one shared manual), so
written once. Paste into each model's `commands.json`.

Source: `33220_Quick command guide.md`; `Agilent Keysight - 32220 Function Generator - User guide 9018-04437.md`

229 missing — SET 70, DO 48, NAB 111. The table has 25.

### SET — 70

```json
"set": {
  // AM
  "Set_Am_Source": {"scpi": "AM:SOUR <value>", "description": "AM Commands", "subsystem": "AM"},

  // BEEP
  "Set_Beeper_State": {"scpi": ":BEEPer:STATe <value>", "description": "System-Related Commands", "subsystem": "BEEP"},

  // BURS
  "Set_Burst_Gate_Polarity": {"scpi": "BURSt:GATE:POLarity <value>", "description": "Burst Commands", "subsystem": "BURS"},
  "Set_Burst_Internal_Period": {"scpi": "BURS:INT:PER <value>", "description": "Burst Commands", "subsystem": "BURS"},
  "Set_Burst_Mode": {"scpi": "BURS:MODE <value>", "description": "Burst Commands", "subsystem": "BURS"},
  "Set_Burst_Ncycles": {"scpi": "BURS:NCYC <value>", "description": "Burst Commands", "subsystem": "BURS"},
  "Set_Burst_Phase": {"scpi": "BURS:PHAS <value>", "description": "Burst Commands", "subsystem": "BURS"},
  "Set_Burst_State": {"scpi": "BURSt:STATe <value>", "description": "Burst Commands", "subsystem": "BURS"},

  // CAL
  "Set_Calibration_Secure_State": {"scpi": "CAL:SEC:STAT <value>", "subsystem": "CAL"},
  "Set_Calibration_String": {"scpi": "CAL:STR <value>", "description": "Calibration Message", "subsystem": "CAL"},
  "Set_Calibration_Value": {"scpi": "CAL:VAL <value>", "subsystem": "CAL"},

  // Common
  "Set_Ese": {"scpi": "*ESE <value>", "subsystem": "Common"},
  "Set_Psc": {"scpi": "*PSC <value>", "subsystem": "Common"},
  "Set_Rcl": {"scpi": "*RCL <value>", "subsystem": "Common"},
  "Set_Sav": {"scpi": "*SAV <value>", "subsystem": "Common"},
  "Set_Sre": {"scpi": "*SRE <value>", "subsystem": "Common"},

  // DEV
  "Set_Deviation_Dcycle": {"scpi": "DEViation:DCYCle <value>", "description": "Pulse Width Modulation (PWM) Commands", "subsystem": "DEV"},

  // DISP
  "Set_Display_Text": {"scpi": "DISP:TEXT <value>", "description": "System-Related Operations", "subsystem": "DISP"},

  // FM
  "Set_Fm_Deviation": {"scpi": "FM:DEViation <value>", "description": "FM Commands", "subsystem": "FM"},
  "Set_Fm_Internal_Frequency": {"scpi": "FM:INTernal:FREQuency <value>", "description": "Modulating Waveform Frequency", "subsystem": "FM"},
  "Set_Fm_Source": {"scpi": "FM:SOUR <value>", "description": "FM Commands", "subsystem": "FM"},

  // FORM
  "Set_Format_Border": {"scpi": "FORMat:BORDer <value>", "description": "Arbitrary Waveform Commands", "subsystem": "FORM"},

  // FREQ
  "Set_Frequency_Center": {"scpi": "FREQuency:CENTer <value>", "description": "Frequency Sweep Commands", "subsystem": "FREQ"},
  "Set_Frequency_Span": {"scpi": "FREQuency:SPAN <value>", "subsystem": "FREQ"},
  "Set_Frequency_Start": {"scpi": "FREQuency:STARt <value>", "description": "Start Frequency and Stop Frequency", "subsystem": "FREQ"},
  "Set_Frequency_Stop": {"scpi": "FREQuency:STOP <value>", "description": "Start Frequency and Stop Frequency", "subsystem": "FREQ"},

  // FSK
  "Set_Fskey_Frequency": {"scpi": "FSKey:FREQuency <value>", "description": "FSK Commands", "subsystem": "FSK"},
  "Set_Fskey_Internal_Rate": {"scpi": "FSKey:INTernal:RATE <value>", "description": "FSK Commands", "subsystem": "FSK"},
  "Set_Fskey_Source": {"scpi": "FSK:SOUR <value>", "description": "FSK Commands", "subsystem": "FSK"},
  "Set_Fskey_State": {"scpi": "FSKey:STATe <value>", "description": "FSK Commands", "subsystem": "FSK"},

  // FUNC
  "Set_Function_Pulse_Dcycle": {"scpi": "FUNCtion:PULSe:DCYCle <value>", "description": "Pulse Configuration Commands", "subsystem": "FUNC"},
  "Set_Function_Pulse_Hold": {"scpi": "FUNC:PULS:HOLD <value>", "description": "Using the APPLy Command", "subsystem": "FUNC"},
  "Set_Function_Pulse_Transition": {"scpi": "FUNCtion:PULSe:TRANsition <value>", "description": "Edge Time", "subsystem": "FUNC"},
  "Set_Function_Ramp_Symmetry": {"scpi": "FUNCtion:RAMP:SYMMetry <value>", "description": "Output Configuration Commands", "subsystem": "FUNC"},
  "Set_Function_Square_Dcycle": {"scpi": "FUNCtion:SQUare:DCYCle <value>", "description": "Output Configuration Commands", "subsystem": "FUNC"},
  "Set_Function_User": {"scpi": "FUNC:USER <value>", "description": "Arbitrary Waveform Commands", "subsystem": "FUNC"},

  // KLOC
  "Set_Klock_Exclude": {"scpi": ":KLOCk:EXCLude <value>", "description": "System-Related Commands", "subsystem": "KLOC"},

  // MARK
  "Set_Marker_Frequency": {"scpi": "MARKer:FREQuency <value>", "description": "Marker Frequency", "subsystem": "MARK"},

  // MEM
  "Set_Memory_State_Name": {"scpi": "MEMory:STATe:NAME <value>", "description": "State Storage Commands", "subsystem": "MEM"},

  // OUTP
  "Set_Output_Polarity": {"scpi": "OUTPut:POLarity <value>", "subsystem": "OUTP"},
  "Set_Output_Trigger": {"scpi": "OUTPut:TRIGger <value>", "description": "Trigger Out Signal", "subsystem": "OUTP"},
  "Set_Output_Trigger_Slope": {"scpi": "OUTPut:TRIGger:SLOPe <value>", "description": "Trigger Out Signal", "subsystem": "OUTP"},

  // PHAS
  "Set_Phase_Unlock_Error_State": {"scpi": "PHASe:UNLock:ERRor:STATe <value>", "description": "Phase-Lock Commands", "subsystem": "PHAS"},

  // PM
  "Set_Pm_Deviation": {"scpi": "PM:DEViation <value>", "description": "PM Commands", "subsystem": "PM"},
  "Set_Pm_Internal_Frequency": {"scpi": "PM:INTernal:FREQuency <value>", "description": "Modulating Waveform Frequency", "subsystem": "PM"},
  "Set_Pm_Source": {"scpi": "PM:SOUR <value>", "description": "PM Commands", "subsystem": "PM"},
  "Set_Pm_State": {"scpi": "PM:STATe <value>", "description": "PM Commands", "subsystem": "PM"},

  // PULS
  "Set_Pulse_Period": {"scpi": "PULSe:PERiod <value>", "description": "Pulse Configuration Commands", "subsystem": "PULS"},

  // PWM
  "Set_Pwm_Deviation": {"scpi": "PWM:DEV <value>", "description": "PWM Commands", "subsystem": "PWM"},
  "Set_Pwm_Deviation_Dcycle": {"scpi": "PWM:DEViation:DCYCle <value>", "description": "PWM Commands", "subsystem": "PWM"},
  "Set_Pwm_Internal_Frequency": {"scpi": "PWM:INTernal:FREQuency <value>", "description": "Modulating Waveform Frequency", "subsystem": "PWM"},
  "Set_Pwm_Source": {"scpi": "PWM:SOURce <value>", "description": "PWM Commands", "subsystem": "PWM"},
  "Set_Pwm_State": {"scpi": "PWM:STATe <value>", "description": "PWM Commands", "subsystem": "PWM"},

  // QUES
  "Set_Questionable_Enable": {"scpi": ":QUEStionable:ENABle <value>", "description": "Status Reporting Commands", "subsystem": "QUES"},

  // SEC
  "Set_Secure_State": {"scpi": ":SECure:STATe <value>", "description": "Calibration Commands", "subsystem": "SEC"},

  // STAT
  "Set_State_Questionable_Enable": {"scpi": "STAT:QUES:ENAB <value>", "description": "The Questionable Data Register", "subsystem": "STAT"},

  // SWE
  "Set_Sweep_Spacing": {"scpi": "SWEep:SPACing <value>", "description": "Sweep Mode", "subsystem": "SWE"},
  "Set_Sweep_State": {"scpi": "SWEep:STATe <value>", "description": "Sweep Commands", "subsystem": "SWE"},
  "Set_Sweep_Time": {"scpi": "SWE:TIME <value>", "description": "Sweep Time", "subsystem": "SWE"},

  // SYST
  "Set_System_Beeper_State": {"scpi": "SYST:BEEP:STAT <value>", "description": "System-Related Commands", "subsystem": "SYST"},
  "Set_System_Communicate_Lan_Ipaddress": {"scpi": "SYSTem:COMMunicate:LAN:IPADdress <value>", "description": "Remote Interface Configuration", "subsystem": "SYST"},
  "Set_System_Communicate_Lan_Mediasense": {"scpi": "SYSTem:COMMunicate:LAN:MEDiasense <value>", "subsystem": "SYST"},
  "Set_System_Communicate_Lan_Netbios": {"scpi": "SYSTem:COMMunicate:LAN:NETBios <value>", "subsystem": "SYST"},
  "Set_System_Communicate_Lan_Telnet_Prompt": {"scpi": "SYSTem:COMMunicate:LAN:TELNet:PROMpt <value>", "subsystem": "SYST"},
  "Set_System_Communicate_Lan_Telnet_Wmessage": {"scpi": "SYSTem:COMMunicate:LAN:TELNet:WMESsage <value>", "subsystem": "SYST"},

  // TELN
  "Set_Telnet_Prompt": {"scpi": ":TELNet:PROMpt <value>", "description": "Interface Configuration Commands", "subsystem": "TELN"},
  "Set_Telnet_Wmessage": {"scpi": ":TELNet:WMESsage <value>", "description": "Interface Configuration Commands", "subsystem": "TELN"},

  // TRIG
  "Set_Trigger_Slope": {"scpi": "TRIGger:SLOPe <value>", "description": "Burst Commands", "subsystem": "TRIG"},
  "Set_Trigger_Source": {"scpi": "TRIG:SOUR <value>", "description": "Burst Commands", "subsystem": "TRIG"},

  // UNIT
  "Set_Unit_Angle": {"scpi": "UNIT:ANGLe <value>", "description": "Burst Commands", "subsystem": "UNIT"},
}
```

### DO — 48

```json
"do": {
  // AM
  "Do_Am_Internal": {"scpi": "AM:INTernal", "description": "AM Commands", "subsystem": "AM"},

  // APPL
  "Do_Apply_Noise": {"scpi": "APPLy:NOISe", "description": "Using the APPLy Command", "subsystem": "APPL"},
  "Do_Apply_Ramp": {"scpi": "APPL:RAMP", "description": "Output Frequency", "subsystem": "APPL"},
  "Do_Apply_User": {"scpi": "APPL:USER", "subsystem": "APPL"},

  // CAL
  "Do_Calibration_Secure_Code": {"scpi": "CAL:SECure:CODE", "description": "Calibration Commands", "subsystem": "CAL"},

  // Common
  "Do_Cls": {"scpi": "*CLS", "subsystem": "Common"},
  "Do_Opc": {"scpi": "*OPC", "subsystem": "Common"},
  "Do_Wai": {"scpi": "*WAI", "subsystem": "Common"},

  // DATA
  "Do_Data_Copy": {"scpi": "DATA:COPY", "description": "Arbitrary Waveform Commands", "subsystem": "DATA"},
  "Do_Data_Dac": {"scpi": "DATA:DAC", "description": "Arbitrary Waveform Commands", "subsystem": "DATA"},
  "Do_Data_Delete": {"scpi": "DATA:DEL", "description": "Arbitrary Waveform Commands", "subsystem": "DATA"},

  // FM
  "Do_Fm_Internal": {"scpi": "FM:INTernal", "description": "FM Commands", "subsystem": "FM"},
  "Do_Fm_Internal_Function": {"scpi": "FM:INTernal:FUNCtion", "description": "Modulating Waveform Shape", "subsystem": "FM"},

  // FUNC
  "Do_Function_Pulse": {"scpi": "FUNC:PULS", "description": "Pulse Configuration Commands", "subsystem": "FUNC"},
  "Do_Function_Ramp": {"scpi": "FUNC:RAMP", "description": "frequency reduced for ramp function", "subsystem": "FUNC"},
  "Do_Function_Shape": {"scpi": "FUNCtion:SHAPe", "subsystem": "FUNC"},

  // GATE
  "Do_Gate_Polarity": {"scpi": "GATE:POLarity", "subsystem": "GATE"},

  // INT
  "Do_Internal_Period": {"scpi": "INTernal:PERiod", "subsystem": "INT"},

  // KLOC
  "Do_Klock_State": {"scpi": ":KLOCk:STATe", "description": "System-Related Commands", "subsystem": "KLOC"},

  // LAN
  "Do_Lan_Ipaddress": {"scpi": "LAN:IPADdress", "subsystem": "LAN"},
  "Do_Lan_Mediasense": {"scpi": "LAN:MEDiasense", "subsystem": "LAN"},
  "Do_Lan_Netbios": {"scpi": "LAN:NETBios", "subsystem": "LAN"},
  "Do_Lan_Telnet_Prompt": {"scpi": "LAN:TELNet:PROM", "subsystem": "LAN"},
  "Do_Lan_Telnet_Wmessage": {"scpi": "LAN:TELNet:WMES", "subsystem": "LAN"},

  // MEM
  "Do_Memory_State": {"scpi": "MEMory:STATe", "description": "State Storage Commands", "subsystem": "MEM"},
  "Do_Memory_State_Delete": {"scpi": "MEMory:STATe:DELete", "subsystem": "MEM"},

  // PHAS
  "Do_Phase_Reference": {"scpi": "PHASe:REFerence", "description": "Phase-Lock Commands", "subsystem": "PHAS"},

  // PM
  "Do_Pm_Internal": {"scpi": "PM:INTernal", "description": "PM Commands", "subsystem": "PM"},
  "Do_Pm_Internal_Function": {"scpi": "PM:INTernal:FUNCtion", "description": "Modulating Waveform Shape", "subsystem": "PM"},

  // PULS
  "Do_Pulse_Transition": {"scpi": "PULSe:TRANsition", "subsystem": "PULS"},
  "Do_Pulse_Width": {"scpi": "PULSe:WIDTh", "subsystem": "PULS"},

  // PWM
  "Do_Pwm_Internal": {"scpi": "PWM:INTernal", "description": "PWM Commands", "subsystem": "PWM"},
  "Do_Pwm_Internal_Function": {"scpi": "PWM:INTernal:FUNCtion", "description": "Modulating Waveform Shape", "subsystem": "PWM"},

  // SEC
  "Do_Secure_Code": {"scpi": ":SECure:CODE", "description": "Calibration Commands", "subsystem": "SEC"},

  // STAT
  "Do_State_Preset": {"scpi": "STATus:PRESet", "description": "Status Reporting Commands", "subsystem": "STAT"},
  "Do_State_Questionable": {"scpi": "STATus:QUEStionable", "subsystem": "STAT"},

  // SYST
  "Do_System_Beeper": {"scpi": "SYSTem:BEEPer", "subsystem": "SYST"},
  "Do_System_Communicate_Lan": {"scpi": "SYSTem:COMMunicate:LAN", "description": "Interface Configuration Commands", "subsystem": "SYST"},
  "Do_System_Communicate_Rlstate": {"scpi": "SYSTem:COMMunicate:RLSTate", "description": "Interface Configuration Commands", "subsystem": "SYST"},
  "Do_System_Klock_State": {"scpi": "SYSTem:KLOCk:STATe", "subsystem": "SYST"},
  "Do_System_Local": {"scpi": "SYSTem:LOCal", "description": "Interface Configuration Commands", "subsystem": "SYST"},
  "Do_System_Remote": {"scpi": "SYSTem:REMote", "description": "Interface Configuration Commands", "subsystem": "SYST"},
  "Do_System_Rwlock": {"scpi": "SYSTem:RWLock", "description": "Interface Configuration Commands", "subsystem": "SYST"},
  "Do_System_Secure_Immediate": {"scpi": "SYSTem:SECurity:IMMediate", "description": "System-Related Commands", "subsystem": "SYST"},

  // TEXT
  "Do_Text_Clear": {"scpi": ":TEXT:CLEar", "description": "System-Related Commands", "subsystem": "TEXT"},

  // UNL
  "Do_Unlock_Error_State": {"scpi": "UNLock:ERRor:STATe", "subsystem": "UNL"},

  // VOLT
  "Do_Voltage_High": {"scpi": "VOLTage:HIGH", "description": "Output Configuration", "subsystem": "VOLT"},
  "Do_Voltage_Low": {"scpi": "VOLTage:LOW", "description": "Output Configuration", "subsystem": "VOLT"},
}
```

### NAB — 111

```json
"nab": {
  // AM
  "Get_Am_Depth": {"scpi": "AM:DEPTh?", "description": "AM Commands", "subsystem": "AM"},
  "Get_Am_Internal_Frequency": {"scpi": "AM:INTernal:FREQuency?", "description": "Amplitude Modulation (AM) Commands", "subsystem": "AM"},
  "Get_Am_Source": {"scpi": "AM:SOURce?", "description": "AM Commands", "subsystem": "AM"},
  "Get_Am_State": {"scpi": "AM:STATe?", "description": "AM Commands", "subsystem": "AM"},

  // ATTR
  "Get_Attribute_Average": {"scpi": ":ATTRibute:AVERage?", "description": "Arbitrary Waveform Commands", "subsystem": "ATTR"},
  "Get_Attribute_Cfactor": {"scpi": ":ATTRibute:CFACtor?", "description": "Arbitrary Waveform Commands", "subsystem": "ATTR"},
  "Get_Attribute_Points": {"scpi": ":ATTRibute:POINts?", "description": "Arbitrary Waveform Commands", "subsystem": "ATTR"},
  "Get_Attribute_Ptpeak": {"scpi": ":ATTRibute:PTPeak?", "description": "Arbitrary Waveform Commands", "subsystem": "ATTR"},

  // BEEP
  "Get_Beeper_State": {"scpi": ":BEEPer:STATe?", "description": "System-Related Commands", "subsystem": "BEEP"},

  // BURS
  "Get_Burst_Gate_Polarity": {"scpi": "BURSt:GATE:POLarity?", "description": "Burst Commands", "subsystem": "BURS"},
  "Get_Burst_Internal_Period": {"scpi": "BURSt:INTernal:PERiod?", "description": "Burst Commands", "subsystem": "BURS"},
  "Get_Burst_Mode": {"scpi": "BURSt:MODE?", "description": "Burst Commands", "subsystem": "BURS"},
  "Get_Burst_Ncycles": {"scpi": "BURSt:NCYCles?", "description": "Burst Commands", "subsystem": "BURS"},
  "Get_Burst_Phase": {"scpi": "BURSt:PHASe?", "description": "Burst Commands", "subsystem": "BURS"},
  "Get_Burst_State": {"scpi": "BURSt:STATe?", "description": "Burst Commands", "subsystem": "BURS"},

  // CAL
  "Get_Calibration_Count": {"scpi": "CAL:COUNt?", "description": "Calibration Count", "subsystem": "CAL"},
  "Get_Calibration_Secure_State": {"scpi": "CAL:SECure:STATe?", "subsystem": "CAL"},
  "Get_Calibration_String": {"scpi": "CAL:STRing?", "description": "Calibration Message", "subsystem": "CAL"},
  "Get_Calibration_Value": {"scpi": "CAL:VALue?", "subsystem": "CAL"},

  // Common
  "Get_Ese": {"scpi": "*ESE?", "subsystem": "Common"},
  "Get_Esr": {"scpi": "*ESR?", "subsystem": "Common"},
  "Get_Idn": {"scpi": "*IDN?", "subsystem": "Common"},
  "Get_Lrn": {"scpi": "*LRN?", "subsystem": "Common"},
  "Get_Opc": {"scpi": "*OPC?", "subsystem": "Common"},
  "Get_Psc": {"scpi": "*PSC?", "subsystem": "Common"},
  "Get_Sre": {"scpi": "*SRE?", "subsystem": "Common"},
  "Get_Stb": {"scpi": "*STB?", "subsystem": "Common"},
  "Get_Tst": {"scpi": "*TST?", "subsystem": "Common"},

  // DATA
  "Get_Data_Attribute_Average": {"scpi": "DATA:ATTRibute:AVERage?", "description": "Arbitrary Waveform Commands", "subsystem": "DATA"},
  "Get_Data_Attribute_Cfactor": {"scpi": "DATA:ATTRibute:CFACtor?", "description": "Arbitrary Waveform Commands", "subsystem": "DATA"},
  "Get_Data_Attribute_Points": {"scpi": "DATA:ATTRibute:POINts?", "description": "Arbitrary Waveform Commands", "subsystem": "DATA"},
  "Get_Data_Attribute_Ptpeak": {"scpi": "DATA:ATTRibute:PTPeak?", "description": "Arbitrary Waveform Commands", "subsystem": "DATA"},
  "Get_Data_Catalog": {"scpi": "DATA:CAT?", "subsystem": "DATA"},
  "Get_Data_Nvolatile_Catalog": {"scpi": "DATA:NVOLatile:CATalog?", "subsystem": "DATA"},
  "Get_Data_Nvolatile_Free": {"scpi": "DATA:NVOLatile:FREE?", "subsystem": "DATA"},

  // DEV
  "Get_Deviation_Dcycle": {"scpi": ":DEV:DCYC?", "description": "Pulse Width Modulation (PWM) Commands", "subsystem": "DEV"},

  // DISP
  "Get_Display_Text": {"scpi": "DISPlay:TEXT?", "description": "System-Related Operations", "subsystem": "DISP"},

  // FM
  "Get_Fm_Deviation": {"scpi": "FM:DEViation?", "description": "FM Commands", "subsystem": "FM"},
  "Get_Fm_Internal_Frequency": {"scpi": "FM:INTernal:FREQuency?", "description": "Frequency Modulation (FM) Commands", "subsystem": "FM"},
  "Get_Fm_Source": {"scpi": "FM:SOURce?", "description": "FM Commands", "subsystem": "FM"},
  "Get_Fm_State": {"scpi": "FM:STATe?", "description": "FM Commands", "subsystem": "FM"},

  // FORM
  "Get_Format_Border": {"scpi": "FORMat:BORDer?", "description": "Arbitrary Waveform Commands", "subsystem": "FORM"},

  // FREQ
  "Get_Frequency_Center": {"scpi": "FREQuency:CENTer?", "description": "Frequency Sweep Commands", "subsystem": "FREQ"},
  "Get_Frequency_Span": {"scpi": "FREQuency:SPAN?", "subsystem": "FREQ"},
  "Get_Frequency_Start": {"scpi": "FREQuency:STARt?", "description": "Sweep Commands", "subsystem": "FREQ"},
  "Get_Frequency_Stop": {"scpi": "FREQuency:STOP?", "description": "Sweep Commands", "subsystem": "FREQ"},

  // FSK
  "Get_Fskey_Frequency": {"scpi": "FSKey:FREQuency?", "description": "FSK Commands", "subsystem": "FSK"},
  "Get_Fskey_Internal_Rate": {"scpi": "FSKey:INTernal:RATE?", "description": "FSK Commands", "subsystem": "FSK"},
  "Get_Fskey_Source": {"scpi": "FSKey:SOURce?", "description": "FSK Commands", "subsystem": "FSK"},
  "Get_Fskey_State": {"scpi": "FSKey:STATe?", "description": "FSK Commands", "subsystem": "FSK"},

  // FUNC
  "Get_Function_Pulse_Dcycle": {"scpi": "FUNCtion:PULSe:DCYCle?", "description": "Pulse Configuration Commands", "subsystem": "FUNC"},
  "Get_Function_Pulse_Hold": {"scpi": "FUNCtion:PULSe:HOLD?", "description": "Using the APPLy Command", "subsystem": "FUNC"},
  "Get_Function_Pulse_Transition": {"scpi": "FUNCtion:PULSe:TRANsition?", "description": "Pulse Configuration Commands", "subsystem": "FUNC"},
  "Get_Function_Pulse_Width": {"scpi": "FUNCtion:PULSe:WIDTh?", "description": "Pulse Configuration Commands", "subsystem": "FUNC"},
  "Get_Function_Ramp_Symmetry": {"scpi": "FUNCtion:RAMP:SYMMetry?", "description": "Output Configuration Commands", "subsystem": "FUNC"},
  "Get_Function_Square_Dcycle": {"scpi": "FUNCtion:SQUare:DCYCle?", "description": "Output Configuration Commands", "subsystem": "FUNC"},
  "Get_Function_User": {"scpi": "FUNCtion:USER?", "description": "Arbitrary Waveform Commands", "subsystem": "FUNC"},

  // KLOC
  "Get_Klock_Exclude": {"scpi": ":KLOCk:EXCLude?", "description": "System-Related Commands", "subsystem": "KLOC"},

  // LAN
  "Get_Lan_Lipaddress": {"scpi": "LAN:LIPaddress?", "subsystem": "LAN"},
  "Get_Lan_Mac": {"scpi": "LAN:MAC?", "subsystem": "LAN"},

  // MARK
  "Get_Marker_Frequency": {"scpi": "MARKer:FREQuency?", "description": "Frequency Sweep Commands", "subsystem": "MARK"},

  // MEM
  "Get_Memory_Nstates": {"scpi": "MEMory:NSTates?", "description": "State Storage Commands", "subsystem": "MEM"},
  "Get_Memory_State_Catalog": {"scpi": "MEMory:STATe:CATalog?", "subsystem": "MEM"},
  "Get_Memory_State_Name": {"scpi": "MEMory:STATe:NAME?", "description": "State Storage Commands", "subsystem": "MEM"},
  "Get_Memory_State_Value": {"scpi": "MEMory:STATe:VALid?", "description": "State Storage Commands", "subsystem": "MEM"},

  // NVOL
  "Get_Nvolatile_Catalog": {"scpi": ":NVOLatile:CATalog?", "description": "Arbitrary Waveform Commands", "subsystem": "NVOL"},
  "Get_Nvolatile_Free": {"scpi": ":NVOLatile:FREE?", "description": "Arbitrary Waveform Commands", "subsystem": "NVOL"},

  // OUTP
  "Get_Output_Load": {"scpi": "OUTPut:LOAD?", "subsystem": "OUTP"},
  "Get_Output_Polarity": {"scpi": "OUTPut:POLarity?", "subsystem": "OUTP"},
  "Get_Output_Sync": {"scpi": "OUTPut:SYNC?", "description": "Output Configuration", "subsystem": "OUTP"},
  "Get_Output_Trigger": {"scpi": "OUTPut:TRIGger?", "description": "Trigger Out Signal", "subsystem": "OUTP"},
  "Get_Output_Trigger_Slope": {"scpi": "OUTPut:TRIGger:SLOPe?", "description": "Trigger Out Signal", "subsystem": "OUTP"},

  // PHAS
  "Get_Phase_Unlock_Error_State": {"scpi": "PHASe:UNLock:ERRor:STATe?", "description": "Phase-Lock Commands", "subsystem": "PHAS"},

  // PM
  "Get_Pm_Deviation": {"scpi": "PM:DEViation?", "description": "PM Commands", "subsystem": "PM"},
  "Get_Pm_Internal_Frequency": {"scpi": "PM:INTernal:FREQuency?", "description": "Phase Modulation (PM) Commands", "subsystem": "PM"},
  "Get_Pm_Source": {"scpi": "PM:SOURce?", "description": "PM Commands", "subsystem": "PM"},
  "Get_Pm_State": {"scpi": "PM:STATe?", "description": "PM Commands", "subsystem": "PM"},

  // PULS
  "Get_Pulse_Period": {"scpi": "PULSe:PERiod?", "description": "Pulse Configuration Commands", "subsystem": "PULS"},

  // PWM
  "Get_Pwm_Deviation": {"scpi": "PWM:DEViation?", "description": "PWM Commands", "subsystem": "PWM"},
  "Get_Pwm_Deviation_Dcycle": {"scpi": "PWM:DEViation:DCYCle?", "description": "PWM Commands", "subsystem": "PWM"},
  "Get_Pwm_Internal_Frequency": {"scpi": "PWM:INTernal:FREQuency?", "description": "Pulse Width Modulation (PWM) Commands", "subsystem": "PWM"},
  "Get_Pwm_Source": {"scpi": "PWM:SOURce?", "description": "PWM Commands", "subsystem": "PWM"},
  "Get_Pwm_State": {"scpi": "PWM:STATe?", "description": "PWM Commands", "subsystem": "PWM"},

  // QUES
  "Get_Questionable_Condition": {"scpi": ":QUEStionable:CONDition?", "description": "Status Reporting Commands", "subsystem": "QUES"},
  "Get_Questionable_Enable": {"scpi": ":QUEStionable:ENABle?", "description": "Status Reporting Commands", "subsystem": "QUES"},
  "Get_Questionable_Event": {"scpi": ":QUEStionable:EVENt?", "description": "Status Reporting Commands", "subsystem": "QUES"},

  // SEC
  "Get_Secure_State": {"scpi": ":SECure:STATe?", "description": "Calibration Commands", "subsystem": "SEC"},

  // SQU
  "Get_Square_Dcycle": {"scpi": "SQUare:DCYCle?", "description": "Output Configuration Commands", "subsystem": "SQU"},

  // STAT
  "Get_State_Questionable_Condition": {"scpi": "STATus:QUEStionable:CONDition?", "subsystem": "STAT"},
  "Get_State_Questionable_Enable": {"scpi": "STATus:QUEStionable:ENABle?", "description": "The Questionable Data Register", "subsystem": "STAT"},
  "Get_State_Questionable_Event": {"scpi": "STAT:QUES:EVEN?", "description": "What is an Event Register?", "subsystem": "STAT"},

  // SWE
  "Get_Sweep_Spacing": {"scpi": "SWEep:SPACing?", "description": "Sweep Mode", "subsystem": "SWE"},
  "Get_Sweep_State": {"scpi": "SWEep:STATe?", "description": "Sweep Commands", "subsystem": "SWE"},
  "Get_Sweep_Time": {"scpi": "SWEep:TIME?", "description": "Frequency Sweep Commands", "subsystem": "SWE"},

  // SYST
  "Get_System_Beeper_State": {"scpi": "SYSTem:BEEPer:STATe?", "description": "System-Related Commands", "subsystem": "SYST"},
  "Get_System_Communicate_Lan_Ipaddress": {"scpi": "SYSTem:COMMunicate:LAN:IPADdress?", "description": "Remote Interface Configuration", "subsystem": "SYST"},
  "Get_System_Communicate_Lan_Lipaddress": {"scpi": "SYSTem:COMMunicate:LAN:LIPaddress?", "subsystem": "SYST"},
  "Get_System_Communicate_Lan_Mac": {"scpi": "SYSTem:COMMunicate:LAN:MAC?", "subsystem": "SYST"},
  "Get_System_Communicate_Lan_Mediasense": {"scpi": "SYSTem:COMMunicate:LAN:MEDiasense?", "subsystem": "SYST"},
  "Get_System_Communicate_Lan_Netbios": {"scpi": "SYSTem:COMMunicate:LAN:NETBios?", "subsystem": "SYST"},
  "Get_System_Communicate_Lan_Telnet_Prompt": {"scpi": "SYSTem:COMMunicate:LAN:TELNet:PROMpt?", "subsystem": "SYST"},
  "Get_System_Communicate_Lan_Telnet_Wmessage": {"scpi": "SYSTem:COMMunicate:LAN:TELNet:WMESsage?", "subsystem": "SYST"},
  "Get_System_Klock_Exclude": {"scpi": "SYSTem:KLOCk:EXCLude?", "subsystem": "SYST"},
  "Get_System_Version": {"scpi": "SYSTem:VERSion?", "description": "System-Related Commands", "subsystem": "SYST"},

  // TELN
  "Get_Telnet_Prompt": {"scpi": ":TELNet:PROMpt?", "description": "Interface Configuration Commands", "subsystem": "TELN"},
  "Get_Telnet_Wmessage": {"scpi": ":TELNet:WMESsage?", "description": "Interface Configuration Commands", "subsystem": "TELN"},

  // TRIG
  "Get_Trigger_Slope": {"scpi": "TRIGger:SLOPe?", "description": "Burst Commands", "subsystem": "TRIG"},
  "Get_Trigger_Source": {"scpi": "TRIGger:SOURce?", "description": "Burst Commands", "subsystem": "TRIG"},

  // UNIT
  "Get_Unit_Angle": {"scpi": "UNIT:ANGLe?", "description": "Burst Commands", "subsystem": "UNIT"},

  // VOLT
  "Get_Voltage_Offset": {"scpi": "VOLTage:OFFSet?", "description": "Output Configuration Commands", "subsystem": "VOLT"},
  "Get_Voltage_Unit": {"scpi": "VOLTage:UNIT?", "description": "Output Configuration Commands", "subsystem": "VOLT"},
}
```

## Load — 6060B

Source: `6060B - DC Load - 5951-2826 - Opperator.md`; `6060B - DC Load - 5951-2828 - Service Manual.md`

31 missing — SET 4, DO 26, NAB 1. The table has 28.

### SET — 4

```json
"set": {
  // Common
  "Set_Ese": {"scpi": "*ESE <value>", "subsystem": "Common"},
  "Set_Rcl": {"scpi": "*RCL <value>", "subsystem": "Common"},
  "Set_Sav": {"scpi": "*SAV <value>", "subsystem": "Common"},
  "Set_Sre": {"scpi": "*SRE <value>", "subsystem": "Common"},
}
```

### DO — 26

```json
"do": {
  // CAL
  "Do_Calib_Init": {"scpi": "CAL:INIT", "description": "EEPROM Initialization", "subsystem": "CAL"},
  "Do_Calib_Lev_High": {"scpi": "CAL:LEV:HIGH", "subsystem": "CAL"},
  "Do_Calib_Lev_Low": {"scpi": "CAL:LEV:LOW", "subsystem": "CAL"},
  "Do_Calib_Meas": {"scpi": "CAL:MEAS", "subsystem": "CAL"},
  "Do_Calib_Meas_High": {"scpi": "CAL:MEAS:HIGH", "description": "Calibration Flowcharts", "subsystem": "CAL"},
  "Do_Calib_Meas_Low": {"scpi": "CAL:MEAS:LOW", "subsystem": "CAL"},
  "Do_Calib_Mode": {"scpi": "CAL:MODE", "description": "Table 3-2. Selftest Error Code", "subsystem": "CAL"},
  "Do_Calib_Sav": {"scpi": "CAL:SAV", "description": "Program Listing", "subsystem": "CAL"},
  "Do_Calib_Tlev": {"scpi": "CAL:TLEV", "subsystem": "CAL"},

  // CURR
  "Do_Curr_Lev_Trig": {"scpi": "CURR:LEV:TRIG", "description": "PROGRAM 2", "subsystem": "CURR"},
  "Do_Curr_Prot": {"scpi": "CURR:PROT", "description": "Software Current Limit", "subsystem": "CURR"},
  "Do_Curr_Prot_Del": {"scpi": "CURR:PROT:DEL", "description": "72 Remote Operation", "subsystem": "CURR"},
  "Do_Curr_Prot_Lev": {"scpi": "CURR:PROT:LEV", "description": "CR Mode Example", "subsystem": "CURR"},
  "Do_Curr_Prot_Stat": {"scpi": "CURR:PROT:STAT", "description": "CR Mode Example", "subsystem": "CURR"},
  "Do_Curr_Trig": {"scpi": "CURR:TRIG", "description": "Triggered Current Level", "subsystem": "CURR"},

  // DIAG
  "Do_Diag_Calib": {"scpi": "DIAG:CAL", "description": "EEPROM Initialization", "subsystem": "DIAG"},

  // INP
  "Do_Input_Prot_Cle": {"scpi": "INP:PROT:CLE", "description": "Resetting Latched Protection", "subsystem": "INP"},

  // INPUT
  "Do_Input_Short": {"scpi": "INPUT:SHORT", "description": "Short On/Off", "subsystem": "INPUT"},

  // RES
  "Do_Res_Tlev": {"scpi": "RES:TLEV", "description": "Transient Resistance Level", "subsystem": "RES"},
  "Do_Res_Trig": {"scpi": "RES:TRIG", "description": "Triggered Resistance Level", "subsystem": "RES"},

  // TRAN
  "Do_Tran_Togg": {"scpi": "TRAN:TOGG", "description": "Toggled Transient Operation", "subsystem": "TRAN"},
  "Do_Tran_Twid": {"scpi": "TRAN:TWID", "description": "Pulsed Transient Operation", "subsystem": "TRAN"},

  // TRIG
  "Do_Trig_Sour": {"scpi": "TRIG:SOUR", "subsystem": "TRIG"},

  // VOLT
  "Do_Volt_Slew": {"scpi": "VOLT:SLEW", "description": "Slew Rate", "subsystem": "VOLT"},
  "Do_Volt_Tlev": {"scpi": "VOLT:TLEV", "description": "Transient Voltage Level", "subsystem": "VOLT"},
  "Do_Volt_Trig": {"scpi": "VOLT:TRIG", "description": "Triggered Voltage Level", "subsystem": "VOLT"},
}
```

### NAB — 1

```json
"nab": {
  // STAT
  "Get_Stat_Channel_Cond": {"scpi": "STAT:CHAN:COND?", "description": "Overpower Circuit Troubleshooting (Figure 3-10)", "subsystem": "STAT"},
}
```

## Power — 66101A

Source: `66000A - 5959-3362 Programming guide.md`

174 missing — SET 49, DO 57, NAB 68. The table has 13.

### SET — 49

```json
"set": {
  // CAL
  "Set_Calibrate_Status": {"scpi": "CAL:STAT <value>", "subsystem": "CAL"},

  // CURR
  "Set_Current_Trigger": {"scpi": "CURR:TRIG <value>", "subsystem": "CURR"},

  // Common
  "Set_Ese": {"scpi": "*ESE <value>", "subsystem": "Common"},
  "Set_Psc": {"scpi": "*PSC <value>", "subsystem": "Common"},
  "Set_Rcl": {"scpi": "*RCL <value>", "subsystem": "Common"},
  "Set_Sav": {"scpi": "*SAV <value>", "subsystem": "Common"},
  "Set_Sre": {"scpi": "*SRE <value>", "subsystem": "Common"},

  // DISP
  "Set_Display_Window_Status": {"scpi": "DISP:WIND:STAT <value>", "subsystem": "DISP"},

  // INIT
  "Set_Initiate_Continuous": {"scpi": "INIT:CONT <value>", "subsystem": "INIT"},

  // OUTP
  "Set_Output_Dfi_Link": {"scpi": "OUTP:DFI:LINK <value>", "subsystem": "OUTP"},
  "Set_Output_Dfi_Source": {"scpi": "OUTP:DFI:SOUR <value>", "subsystem": "OUTP"},
  "Set_Output_Dfi_Status": {"scpi": "OUTP:DFI:STAT <value>", "subsystem": "OUTP"},
  "Set_Output_Protection_Delay": {"scpi": "OUTP:PROT:DEL <value>", "subsystem": "OUTP"},
  "Set_Output_Relay": {"scpi": "OUTP:REL <value>", "description": "Output Subsystem", "subsystem": "OUTP"},
  "Set_Output_Relay_Polarity": {"scpi": "OUTP:REL:POL <value>", "subsystem": "OUTP"},
  "Set_Output_Relay_Status": {"scpi": "OUTP:REL:STAT <value>", "subsystem": "OUTP"},
  "Set_Output_Status": {"scpi": "OUTP:STAT <value>", "subsystem": "OUTP"},
  "Set_Output_Ttltrg_Link": {"scpi": "OUTP:TTLT:LINK <value>", "subsystem": "OUTP"},
  "Set_Output_Ttltrg_Source": {"scpi": "OUTP:TTLT:SOUR <value>", "subsystem": "OUTP"},
  "Set_Output_Ttltrg_Status": {"scpi": "OUTP:TTLT:STAT <value>", "subsystem": "OUTP"},

  // SOUR
  "Set_Source_Current_Level_Immediate_Amplitude": {"scpi": "SOUR:CURR:LEV:IMM:AMPL <value>", "subsystem": "SOUR"},
  "Set_Source_Current_Level_Trigger_Amplitude": {"scpi": "SOUR:CURR:LEV:TRIG:AMPL <value>", "subsystem": "SOUR"},
  "Set_Source_Current_Mode": {"scpi": "SOURce:CURRent:MODE <value>", "subsystem": "SOUR"},
  "Set_Source_Current_Protection_Status": {"scpi": "SOURce:CURRent:PROTection:STATe <value>", "subsystem": "SOUR"},
  "Set_Source_List_Count": {"scpi": "SOURce:LIST:COUNt <value>", "subsystem": "SOUR"},
  "Set_Source_List_Dwel": {"scpi": "SOURce:LIST:DWEL<chan> <value>", "subsystem": "SOUR"},
  "Set_Source_List_Step": {"scpi": "SOUR:LIST:STEP <value>", "subsystem": "SOUR"},
  "Set_Source_Voltage_Level_Trigger_Amplitude": {"scpi": "SOUR:VOLT:LEV:TRIG:AMPL <value>", "subsystem": "SOUR"},
  "Set_Source_Voltage_Mode": {"scpi": "SOURce:VOLTage:MODE <value>", "subsystem": "SOUR"},
  "Set_Source_Voltage_Protection_Level": {"scpi": "SOUR:VOLT:PROT:LEV <value>", "subsystem": "SOUR"},

  // STAT
  "Set_Status_Operation": {"scpi": "STAT:OPER <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Enable": {"scpi": "STAT:OPER:ENAB <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Event": {"scpi": "STAT:OPER:EVEN <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Ntransition": {"scpi": "STAT:OPER:NTR <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Ptransition": {"scpi": "STAT:OPER:PTR <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable": {"scpi": "STAT:QUES <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable_Enable": {"scpi": "STAT:QUES:ENAB <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable_Ntransition": {"scpi": "STAT:QUES:NTR <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable_Ptransition": {"scpi": "STAT:QUES:PTR <value>", "description": "Register Commands", "subsystem": "STAT"},

  // TRIG
  "Set_Trigger_Delay": {"scpi": "TRIG:DEL <value>", "subsystem": "TRIG"},
  "Set_Trigger_Link": {"scpi": "TRIG:LINK <value>", "subsystem": "TRIG"},
  "Set_Trigger_Source": {"scpi": "TRIG:SOUR <value>", "subsystem": "TRIG"},
  "Set_Trigger_Start_Delay": {"scpi": "TRIGger:STARt:DELay <value>", "subsystem": "TRIG"},
  "Set_Trigger_Start_Link": {"scpi": "TRIG:STAR:LINK <value>", "subsystem": "TRIG"},
  "Set_Trigger_Start_Source": {"scpi": "TRIGger:STARt:SOURce <value>", "subsystem": "TRIG"},

  // VOLT
  "Set_Voltage_Alc_Source": {"scpi": "VOLT:ALC:SOUR <value>", "subsystem": "VOLT"},
  "Set_Voltage_Protection": {"scpi": "VOLT:PROT <value>", "description": "Query Indicator", "subsystem": "VOLT"},
  "Set_Voltage_Sense_Source": {"scpi": "VOLT:SENS:SOUR <value>", "subsystem": "VOLT"},
  "Set_Voltage_Trigger": {"scpi": "VOLT:TRIG <value>", "subsystem": "VOLT"},
}
```

### DO — 57

```json
"do": {
  // CAL
  "Do_Calibrate_Aut": {"scpi": "CAL:AUT", "subsystem": "CAL"},
  "Do_Calibrate_Current": {"scpi": "CAL:CURR", "subsystem": "CAL"},
  "Do_Calibrate_Current_Data": {"scpi": "CAL:CURR:DATA", "subsystem": "CAL"},
  "Do_Calibrate_Current_Level": {"scpi": "CAL:CURR:LEV", "subsystem": "CAL"},
  "Do_Calibrate_Passcode": {"scpi": "CAL:PASS", "subsystem": "CAL"},
  "Do_Calibrate_Sav": {"scpi": "CAL:SAV", "subsystem": "CAL"},
  "Do_Calibrate_Voltage": {"scpi": "CAL:VOLT", "subsystem": "CAL"},
  "Do_Calibrate_Voltage_Data": {"scpi": "CAL:VOLT:DATA", "subsystem": "CAL"},
  "Do_Calibrate_Voltage_Level": {"scpi": "CAL:VOLT:LEV", "subsystem": "CAL"},
  "Do_Calibrate_Voltage_Protection": {"scpi": "CAL:VOLT:PROT", "subsystem": "CAL"},

  // CURR
  "Do_Current_Immediate": {"scpi": "CURR:IMM", "subsystem": "CURR"},
  "Do_Current_Level": {"scpi": "CURR:LEV", "subsystem": "CURR"},
  "Do_Current_Level_Immediate": {"scpi": "CURR:LEV:IMM", "subsystem": "CURR"},
  "Do_Current_Level_Trigger": {"scpi": "CURR:LEV:TRIG", "description": "Trigger Subsystem", "subsystem": "CURR"},
  "Do_Current_List": {"scpi": "CURR:LIST", "subsystem": "CURR"},
  "Do_Current_Mode": {"scpi": "CURR:MODE", "subsystem": "CURR"},
  "Do_Current_Mode_List": {"scpi": "CURR:MODE:LIST", "subsystem": "CURR"},
  "Do_Current_Protection": {"scpi": "CURRent:PROTection", "subsystem": "CURR"},
  "Do_Current_Protection_Status": {"scpi": "CURR:PROT:STAT", "subsystem": "CURR"},

  // Common
  "Do_Opc": {"scpi": "*OPC", "subsystem": "Common"},
  "Do_Wai": {"scpi": "*WAI", "subsystem": "Common"},

  // DISP
  "Do_Display_Status": {"scpi": "DISP:STAT", "subsystem": "DISP"},

  // IMM
  "Do_Immediate_Amplitude": {"scpi": ":IMMediate:AMPLitude", "subsystem": "IMM"},

  // INIT
  "Do_Initiate_Immediate": {"scpi": "INIT:IMM", "subsystem": "INIT"},

  // LIST
  "Do_List_Count": {"scpi": "LIST:COUN", "subsystem": "LIST"},
  "Do_List_Current": {"scpi": "LIST:CURR", "subsystem": "LIST"},
  "Do_List_Dwel": {"scpi": "LIST:DWEL", "subsystem": "LIST"},
  "Do_List_Step": {"scpi": "LIST:STEP", "subsystem": "LIST"},
  "Do_List_Voltage": {"scpi": "LIST:VOLT", "subsystem": "LIST"},

  // OUTP
  "Do_Output_Dfi": {"scpi": "OUTP:DFI", "subsystem": "OUTP"},
  "Do_Output_Protection": {"scpi": "OUTP:PROT", "subsystem": "OUTP"},
  "Do_Output_Protection_Clear": {"scpi": "OUTP:PROT:CLE", "subsystem": "OUTP"},
  "Do_Output_Ttltrg": {"scpi": "OUTP:TTLT", "subsystem": "OUTP"},

  // PROTECTION
  "Do_Protection_Clear": {"scpi": "PROTECTION:CLEAR", "description": "The Effect of Optional Headers", "subsystem": "PROTECTION"},

  // SOUR
  "Do_Source_Current_Level": {"scpi": "SOURce:CURRent:LEVel", "subsystem": "SOUR"},
  "Do_Source_Current_Level_Trigger": {"scpi": "SOURce:CURRent:LEVel:TRIGgered", "subsystem": "SOUR"},
  "Do_Source_Currlev_Trigger": {"scpi": "SOURce:CURRentLEVel:TRIGgered", "subsystem": "SOUR"},
  "Do_Source_List": {"scpi": "SOURce:LIST", "description": "Conventions", "subsystem": "SOUR"},
  "Do_Source_List_Current": {"scpi": "SOURce:LIST:CURRent", "subsystem": "SOUR"},
  "Do_Source_List_Voltage": {"scpi": "SOURce:LIST:VOLTage", "subsystem": "SOUR"},
  "Do_Source_Voltage_Level": {"scpi": "SOURce:VOLTage:LEVel", "subsystem": "SOUR"},
  "Do_Source_Voltage_Level_Immediate_Amplitude": {"scpi": "SOUR:VOLT:LEV:IMM:AMPL", "subsystem": "SOUR"},
  "Do_Source_Voltage_Level_Trigger": {"scpi": "SOURce:VOLTage:LEVel:TRIGgered", "subsystem": "SOUR"},
  "Do_Source_Voltage_Protection": {"scpi": "SOURce:VOLTage:PROTection", "subsystem": "SOUR"},
  "Do_Source_Voltlev_Trigger": {"scpi": "SOURce:VOLTageLEVel:TRIGgered", "subsystem": "SOUR"},

  // STAT
  "Do_Status_Pre": {"scpi": "STAT:PRE", "description": "Status Registers", "subsystem": "STAT"},

  // TRIG
  "Do_Trigger_Immediate": {"scpi": "TRIG:IMM", "subsystem": "TRIG"},
  "Do_Trigger_Start_Immediate": {"scpi": "TRIGger:STARt:IMMediate", "subsystem": "TRIG"},

  // TTLT
  "Do_Ttltrg_Link": {"scpi": "TTLT:LINK", "subsystem": "TTLT"},

  // VOLT
  "Do_Voltage_Immediate": {"scpi": "VOLT:IMM", "subsystem": "VOLT"},
  "Do_Voltage_Level": {"scpi": "VOLT:LEV", "subsystem": "VOLT"},
  "Do_Voltage_Level_Immediate": {"scpi": "VOLT:LEV:IMM", "subsystem": "VOLT"},
  "Do_Voltage_Level_Trigger": {"scpi": "VOLT:LEV:TRIG", "description": "Trigger Subsystem", "subsystem": "VOLT"},
  "Do_Voltage_List": {"scpi": "VOLT:LIST", "description": "SCPI Command Completion", "subsystem": "VOLT"},
  "Do_Voltage_Mode": {"scpi": "VOLT:MODE", "subsystem": "VOLT"},
  "Do_Voltage_Protection_Level": {"scpi": "VOLT:PROT:LEV", "subsystem": "VOLT"},
  "Do_Voltage_Tiug": {"scpi": "VOLT:TIUG", "subsystem": "VOLT"},
}
```

### NAB — 68

```json
"nab": {
  // CAL
  "Get_Calibrate_Status": {"scpi": "CALibrate:STATe?", "subsystem": "CAL"},

  // CURR
  "Get_Current_Trigger": {"scpi": "CURR:TRIG?", "subsystem": "CURR"},

  // Common
  "Get_Ese": {"scpi": "*ESE?", "subsystem": "Common"},
  "Get_Esr": {"scpi": "*ESR?", "subsystem": "Common"},
  "Get_Idn": {"scpi": "*IDN?", "subsystem": "Common"},
  "Get_Opc": {"scpi": "*OPC?", "subsystem": "Common"},
  "Get_Opt": {"scpi": "*OPT?", "subsystem": "Common"},
  "Get_Psc": {"scpi": "*PSC?", "subsystem": "Common"},
  "Get_Sre": {"scpi": "*SRE?", "subsystem": "Common"},
  "Get_Stb": {"scpi": "*STB?", "subsystem": "Common"},
  "Get_Tst": {"scpi": "*TST?", "subsystem": "Common"},

  // DISP
  "Get_Display_Window_Status": {"scpi": "DISPlay:WINDow:STAT?", "subsystem": "DISP"},

  // IMM
  "Get_Immediate_Amplitude": {"scpi": ":IMMediate:AMPlitude?", "subsystem": "IMM"},

  // INIT
  "Get_Initiate_Continuous": {"scpi": "INITiate:CONTinuous?", "subsystem": "INIT"},

  // LIST
  "Get_List_Current_Points": {"scpi": "LIST:CURR:POIN?", "subsystem": "LIST"},
  "Get_List_Dwel_Points": {"scpi": "LIST:DWEL:POIN?", "subsystem": "LIST"},
  "Get_List_Voltage_Points": {"scpi": "LIST:VOLT:POIN?", "subsystem": "LIST"},

  // OUTP
  "Get_Output_Dfi_Link": {"scpi": "OUTPut:DFI:LINK?", "subsystem": "OUTP"},
  "Get_Output_Dfi_Source": {"scpi": "OUTPut:DFI:SOUR?", "subsystem": "OUTP"},
  "Get_Output_Dfi_Status": {"scpi": "OUTPut:DFI:STATe?", "subsystem": "OUTP"},
  "Get_Output_Protection_Delay": {"scpi": "OUTPut:PROTection:DELay?", "subsystem": "OUTP"},
  "Get_Output_Relay": {"scpi": "OUTP:REL?", "description": "Output Subsystem", "subsystem": "OUTP"},
  "Get_Output_Relay_Polarity": {"scpi": "OUTPut:RELay:POLarity?", "subsystem": "OUTP"},
  "Get_Output_Relay_Status": {"scpi": "OUTP:REL:STAT?", "subsystem": "OUTP"},
  "Get_Output_Status": {"scpi": "OUTPut:STATe?", "subsystem": "OUTP"},
  "Get_Output_Ttltrg_Link": {"scpi": "OUTP:TTLT:LINK?", "subsystem": "OUTP"},
  "Get_Output_Ttltrg_Source": {"scpi": "OUTP:TTLT:SOUR?", "subsystem": "OUTP"},
  "Get_Output_Ttltrg_Status": {"scpi": "OUTP:TTLT:STAT?", "subsystem": "OUTP"},

  // QUES
  "Get_Questionable_Event": {"scpi": "QUES:EVEN?", "subsystem": "QUES"},

  // SOUR
  "Get_Source_Current_Level_Immediate_Amplitude": {"scpi": "SOUR:CURR:LEV:IMM:AMPL?", "subsystem": "SOUR"},
  "Get_Source_Current_Level_Trigger_Amplitude": {"scpi": "SOUR:CURR:LEV:TRIG:AMPL?", "subsystem": "SOUR"},
  "Get_Source_Current_Mode": {"scpi": "SOURce:CURRent:MODE?", "subsystem": "SOUR"},
  "Get_Source_Current_Protection_Status": {"scpi": "SOURce:CURRent:PROTection:STATe?", "subsystem": "SOUR"},
  "Get_Source_List_Count": {"scpi": "SOURce:LIST:COUNt?", "subsystem": "SOUR"},
  "Get_Source_List_Current_Points": {"scpi": "SOURce:LIST:CURRent:POINts?", "subsystem": "SOUR"},
  "Get_Source_List_Dwel": {"scpi": "SOUR:LIST:DWEL?", "subsystem": "SOUR"},
  "Get_Source_List_Dwel_Points": {"scpi": "SOUR:LIST:DWEL:POIN?", "subsystem": "SOUR"},
  "Get_Source_List_Dwfl_Points": {"scpi": "SOURce:LIST:DWFL1:POINts?", "subsystem": "SOUR"},
  "Get_Source_List_Step": {"scpi": "SOUR:LIST:STEP?", "subsystem": "SOUR"},
  "Get_Source_List_Voltage_Points": {"scpi": "SOURce:LIST:VOLTage:POINts?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Level_Trigger_Amplitude": {"scpi": "SOUR:VOLT:LEV:TRIG:AMPL?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Mode": {"scpi": "SOURce:VOLTage:MODE?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Protection_Level": {"scpi": "SOUR:VOLT:PROT:LEV?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Sense": {"scpi": "SOUR:VOLT:SENS?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Sense_Source": {"scpi": "SOURce:VOLTage:SENSe:SOURce?", "subsystem": "SOUR"},

  // SOURI
  "Get_Souri_Voltage_Level_Immediate_Amplitude": {"scpi": "SOURI:VOLT:LEV:IMM:AMPL?", "subsystem": "SOURI"},

  // STAT
  "Get_Status_Operation": {"scpi": "STAT:OPER?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Condition": {"scpi": "STAT:OPER:COND?", "subsystem": "STAT"},
  "Get_Status_Operation_Enable": {"scpi": "STAT:OPER:ENAB?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Event": {"scpi": "STAT:OPER:EVEN?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Ntransition": {"scpi": "STAT:OPER:NTR?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Ptransition": {"scpi": "STAT:OPER:PTR?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable": {"scpi": "STAT:QUES?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Enable": {"scpi": "STAT:QUES:ENAB?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Event": {"scpi": "STAT:QUES:EVEN?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Ntransition": {"scpi": "STATus:QUEStionable:NTRansition?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Ptransition": {"scpi": "STATus:QUEStionable:PTRansitiion?", "description": "Register Commands", "subsystem": "STAT"},

  // SYST
  "Get_System_Version": {"scpi": "SYST:VERS?", "subsystem": "SYST"},

  // TRIG
  "Get_Trigger_Delay": {"scpi": "TRIG:DEL?", "subsystem": "TRIG"},
  "Get_Trigger_Link": {"scpi": "TRIG:LINK?", "subsystem": "TRIG"},
  "Get_Trigger_Source": {"scpi": "TRIG:SOUR?", "subsystem": "TRIG"},
  "Get_Trigger_Start_Delay": {"scpi": "TRIGger:STARt:DELay?", "subsystem": "TRIG"},
  "Get_Trigger_Start_Link": {"scpi": "TRIGger:STARt:LINK?", "subsystem": "TRIG"},
  "Get_Trigger_Start_Source": {"scpi": "TRIGger:STARt:SOURce?", "subsystem": "TRIG"},

  // VOLT
  "Get_Voltage_Alc_Source": {"scpi": "VOLT:ALC:SOUR?", "subsystem": "VOLT"},
  "Get_Voltage_Protection": {"scpi": "VOLT:PROT?", "description": "Query Indicator", "subsystem": "VOLT"},
  "Get_Voltage_Sense_Source": {"scpi": "VOLT:SENS:SOUR?", "subsystem": "VOLT"},
  "Get_Voltage_Trigger": {"scpi": "VOLT:TRIG?", "subsystem": "VOLT"},
}
```

## Power — 66102A, 66103A

Identical missing sets across 2 models (one shared manual), so
written once. Paste into each model's `commands.json`.

Source: `66000A - 5959-3362 Programming guide.md`

171 missing — SET 48, DO 55, NAB 68. The table has 18.

### SET — 48

```json
"set": {
  // CAL
  "Set_Calibrate_Status": {"scpi": "CAL:STAT <value>", "subsystem": "CAL"},

  // CURR
  "Set_Current_Trigger": {"scpi": "CURR:TRIG <value>", "subsystem": "CURR"},

  // Common
  "Set_Ese": {"scpi": "*ESE <value>", "subsystem": "Common"},
  "Set_Psc": {"scpi": "*PSC <value>", "subsystem": "Common"},
  "Set_Rcl": {"scpi": "*RCL <value>", "subsystem": "Common"},
  "Set_Sav": {"scpi": "*SAV <value>", "subsystem": "Common"},
  "Set_Sre": {"scpi": "*SRE <value>", "subsystem": "Common"},

  // DISP
  "Set_Display_Window_Status": {"scpi": "DISP:WIND:STAT <value>", "subsystem": "DISP"},

  // INIT
  "Set_Initiate_Continuous": {"scpi": "INIT:CONT <value>", "subsystem": "INIT"},

  // OUTP
  "Set_Output_Dfi_Link": {"scpi": "OUTP:DFI:LINK <value>", "subsystem": "OUTP"},
  "Set_Output_Dfi_Source": {"scpi": "OUTP:DFI:SOUR <value>", "subsystem": "OUTP"},
  "Set_Output_Dfi_Status": {"scpi": "OUTP:DFI:STAT <value>", "subsystem": "OUTP"},
  "Set_Output_Protection_Delay": {"scpi": "OUTP:PROT:DEL <value>", "subsystem": "OUTP"},
  "Set_Output_Relay": {"scpi": "OUTP:REL <value>", "description": "Output Subsystem", "subsystem": "OUTP"},
  "Set_Output_Relay_Polarity": {"scpi": "OUTP:REL:POL <value>", "subsystem": "OUTP"},
  "Set_Output_Relay_Status": {"scpi": "OUTP:REL:STAT <value>", "subsystem": "OUTP"},
  "Set_Output_Status": {"scpi": "OUTP:STAT <value>", "subsystem": "OUTP"},
  "Set_Output_Ttltrg_Link": {"scpi": "OUTP:TTLT:LINK <value>", "subsystem": "OUTP"},
  "Set_Output_Ttltrg_Source": {"scpi": "OUTP:TTLT:SOUR <value>", "subsystem": "OUTP"},
  "Set_Output_Ttltrg_Status": {"scpi": "OUTP:TTLT:STAT <value>", "subsystem": "OUTP"},

  // SOUR
  "Set_Source_Current_Level_Immediate_Amplitude": {"scpi": "SOUR:CURR:LEV:IMM:AMPL <value>", "subsystem": "SOUR"},
  "Set_Source_Current_Level_Trigger_Amplitude": {"scpi": "SOUR:CURR:LEV:TRIG:AMPL <value>", "subsystem": "SOUR"},
  "Set_Source_Current_Mode": {"scpi": "SOURce:CURRent:MODE <value>", "subsystem": "SOUR"},
  "Set_Source_Current_Protection_Status": {"scpi": "SOURce:CURRent:PROTection:STATe <value>", "subsystem": "SOUR"},
  "Set_Source_List_Count": {"scpi": "SOURce:LIST:COUNt <value>", "subsystem": "SOUR"},
  "Set_Source_List_Dwel": {"scpi": "SOURce:LIST:DWEL<chan> <value>", "subsystem": "SOUR"},
  "Set_Source_List_Step": {"scpi": "SOUR:LIST:STEP <value>", "subsystem": "SOUR"},
  "Set_Source_Voltage_Level_Trigger_Amplitude": {"scpi": "SOUR:VOLT:LEV:TRIG:AMPL <value>", "subsystem": "SOUR"},
  "Set_Source_Voltage_Mode": {"scpi": "SOURce:VOLTage:MODE <value>", "subsystem": "SOUR"},
  "Set_Source_Voltage_Protection_Level": {"scpi": "SOUR:VOLT:PROT:LEV <value>", "subsystem": "SOUR"},

  // STAT
  "Set_Status_Operation": {"scpi": "STAT:OPER <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Enable": {"scpi": "STAT:OPER:ENAB <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Event": {"scpi": "STAT:OPER:EVEN <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Ntransition": {"scpi": "STAT:OPER:NTR <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Ptransition": {"scpi": "STAT:OPER:PTR <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable": {"scpi": "STAT:QUES <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable_Enable": {"scpi": "STAT:QUES:ENAB <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable_Ntransition": {"scpi": "STAT:QUES:NTR <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable_Ptransition": {"scpi": "STAT:QUES:PTR <value>", "description": "Register Commands", "subsystem": "STAT"},

  // TRIG
  "Set_Trigger_Delay": {"scpi": "TRIG:DEL <value>", "subsystem": "TRIG"},
  "Set_Trigger_Link": {"scpi": "TRIG:LINK <value>", "subsystem": "TRIG"},
  "Set_Trigger_Source": {"scpi": "TRIG:SOUR <value>", "subsystem": "TRIG"},
  "Set_Trigger_Start_Delay": {"scpi": "TRIGger:STARt:DELay <value>", "subsystem": "TRIG"},
  "Set_Trigger_Start_Link": {"scpi": "TRIG:STAR:LINK <value>", "subsystem": "TRIG"},
  "Set_Trigger_Start_Source": {"scpi": "TRIGger:STARt:SOURce <value>", "subsystem": "TRIG"},

  // VOLT
  "Set_Voltage_Alc_Source": {"scpi": "VOLT:ALC:SOUR <value>", "subsystem": "VOLT"},
  "Set_Voltage_Sense_Source": {"scpi": "VOLT:SENS:SOUR <value>", "subsystem": "VOLT"},
  "Set_Voltage_Trigger": {"scpi": "VOLT:TRIG <value>", "subsystem": "VOLT"},
}
```

### DO — 55

```json
"do": {
  // CAL
  "Do_Calibrate_Aut": {"scpi": "CAL:AUT", "subsystem": "CAL"},
  "Do_Calibrate_Current": {"scpi": "CAL:CURR", "subsystem": "CAL"},
  "Do_Calibrate_Current_Data": {"scpi": "CAL:CURR:DATA", "subsystem": "CAL"},
  "Do_Calibrate_Current_Level": {"scpi": "CAL:CURR:LEV", "subsystem": "CAL"},
  "Do_Calibrate_Passcode": {"scpi": "CAL:PASS", "subsystem": "CAL"},
  "Do_Calibrate_Sav": {"scpi": "CAL:SAV", "subsystem": "CAL"},
  "Do_Calibrate_Voltage": {"scpi": "CAL:VOLT", "subsystem": "CAL"},
  "Do_Calibrate_Voltage_Data": {"scpi": "CAL:VOLT:DATA", "subsystem": "CAL"},
  "Do_Calibrate_Voltage_Level": {"scpi": "CAL:VOLT:LEV", "subsystem": "CAL"},
  "Do_Calibrate_Voltage_Protection": {"scpi": "CAL:VOLT:PROT", "subsystem": "CAL"},

  // CURR
  "Do_Current_Immediate": {"scpi": "CURR:IMM", "subsystem": "CURR"},
  "Do_Current_Level": {"scpi": "CURR:LEV", "subsystem": "CURR"},
  "Do_Current_Level_Immediate": {"scpi": "CURR:LEV:IMM", "subsystem": "CURR"},
  "Do_Current_Level_Trigger": {"scpi": "CURR:LEV:TRIG", "description": "Trigger Subsystem", "subsystem": "CURR"},
  "Do_Current_List": {"scpi": "CURR:LIST", "subsystem": "CURR"},
  "Do_Current_Mode": {"scpi": "CURR:MODE", "subsystem": "CURR"},
  "Do_Current_Mode_List": {"scpi": "CURR:MODE:LIST", "subsystem": "CURR"},
  "Do_Current_Protection": {"scpi": "CURRent:PROTection", "subsystem": "CURR"},

  // Common
  "Do_Opc": {"scpi": "*OPC", "subsystem": "Common"},
  "Do_Wai": {"scpi": "*WAI", "subsystem": "Common"},

  // DISP
  "Do_Display_Status": {"scpi": "DISP:STAT", "subsystem": "DISP"},

  // IMM
  "Do_Immediate_Amplitude": {"scpi": ":IMMediate:AMPLitude", "subsystem": "IMM"},

  // INIT
  "Do_Initiate_Immediate": {"scpi": "INIT:IMM", "subsystem": "INIT"},

  // LIST
  "Do_List_Count": {"scpi": "LIST:COUN", "subsystem": "LIST"},
  "Do_List_Current": {"scpi": "LIST:CURR", "subsystem": "LIST"},
  "Do_List_Dwel": {"scpi": "LIST:DWEL", "subsystem": "LIST"},
  "Do_List_Step": {"scpi": "LIST:STEP", "subsystem": "LIST"},
  "Do_List_Voltage": {"scpi": "LIST:VOLT", "subsystem": "LIST"},

  // OUTP
  "Do_Output_Dfi": {"scpi": "OUTP:DFI", "subsystem": "OUTP"},
  "Do_Output_Protection": {"scpi": "OUTP:PROT", "subsystem": "OUTP"},
  "Do_Output_Ttltrg": {"scpi": "OUTP:TTLT", "subsystem": "OUTP"},

  // PROTECTION
  "Do_Protection_Clear": {"scpi": "PROTECTION:CLEAR", "description": "The Effect of Optional Headers", "subsystem": "PROTECTION"},

  // SOUR
  "Do_Source_Current_Level": {"scpi": "SOURce:CURRent:LEVel", "subsystem": "SOUR"},
  "Do_Source_Current_Level_Trigger": {"scpi": "SOURce:CURRent:LEVel:TRIGgered", "subsystem": "SOUR"},
  "Do_Source_Currlev_Trigger": {"scpi": "SOURce:CURRentLEVel:TRIGgered", "subsystem": "SOUR"},
  "Do_Source_List": {"scpi": "SOURce:LIST", "description": "Conventions", "subsystem": "SOUR"},
  "Do_Source_List_Current": {"scpi": "SOURce:LIST:CURRent", "subsystem": "SOUR"},
  "Do_Source_List_Voltage": {"scpi": "SOURce:LIST:VOLTage", "subsystem": "SOUR"},
  "Do_Source_Voltage_Level": {"scpi": "SOURce:VOLTage:LEVel", "subsystem": "SOUR"},
  "Do_Source_Voltage_Level_Immediate_Amplitude": {"scpi": "SOUR:VOLT:LEV:IMM:AMPL", "subsystem": "SOUR"},
  "Do_Source_Voltage_Level_Trigger": {"scpi": "SOURce:VOLTage:LEVel:TRIGgered", "subsystem": "SOUR"},
  "Do_Source_Voltage_Protection": {"scpi": "SOURce:VOLTage:PROTection", "subsystem": "SOUR"},
  "Do_Source_Voltlev_Trigger": {"scpi": "SOURce:VOLTageLEVel:TRIGgered", "subsystem": "SOUR"},

  // STAT
  "Do_Status_Pre": {"scpi": "STAT:PRE", "description": "Status Registers", "subsystem": "STAT"},

  // TRIG
  "Do_Trigger_Immediate": {"scpi": "TRIG:IMM", "subsystem": "TRIG"},
  "Do_Trigger_Start_Immediate": {"scpi": "TRIGger:STARt:IMMediate", "subsystem": "TRIG"},

  // TTLT
  "Do_Ttltrg_Link": {"scpi": "TTLT:LINK", "subsystem": "TTLT"},

  // VOLT
  "Do_Voltage_Immediate": {"scpi": "VOLT:IMM", "subsystem": "VOLT"},
  "Do_Voltage_Level": {"scpi": "VOLT:LEV", "subsystem": "VOLT"},
  "Do_Voltage_Level_Immediate": {"scpi": "VOLT:LEV:IMM", "subsystem": "VOLT"},
  "Do_Voltage_Level_Trigger": {"scpi": "VOLT:LEV:TRIG", "description": "Trigger Subsystem", "subsystem": "VOLT"},
  "Do_Voltage_List": {"scpi": "VOLT:LIST", "description": "SCPI Command Completion", "subsystem": "VOLT"},
  "Do_Voltage_Mode": {"scpi": "VOLT:MODE", "subsystem": "VOLT"},
  "Do_Voltage_Protection_Level": {"scpi": "VOLT:PROT:LEV", "subsystem": "VOLT"},
  "Do_Voltage_Tiug": {"scpi": "VOLT:TIUG", "subsystem": "VOLT"},
}
```

### NAB — 68

```json
"nab": {
  // CAL
  "Get_Calibrate_Status": {"scpi": "CALibrate:STATe?", "subsystem": "CAL"},

  // CURR
  "Get_Current_Trigger": {"scpi": "CURR:TRIG?", "subsystem": "CURR"},

  // Common
  "Get_Ese": {"scpi": "*ESE?", "subsystem": "Common"},
  "Get_Esr": {"scpi": "*ESR?", "subsystem": "Common"},
  "Get_Idn": {"scpi": "*IDN?", "subsystem": "Common"},
  "Get_Opc": {"scpi": "*OPC?", "subsystem": "Common"},
  "Get_Opt": {"scpi": "*OPT?", "subsystem": "Common"},
  "Get_Psc": {"scpi": "*PSC?", "subsystem": "Common"},
  "Get_Sre": {"scpi": "*SRE?", "subsystem": "Common"},
  "Get_Stb": {"scpi": "*STB?", "subsystem": "Common"},
  "Get_Tst": {"scpi": "*TST?", "subsystem": "Common"},

  // DISP
  "Get_Display_Window_Status": {"scpi": "DISPlay:WINDow:STAT?", "subsystem": "DISP"},

  // IMM
  "Get_Immediate_Amplitude": {"scpi": ":IMMediate:AMPlitude?", "subsystem": "IMM"},

  // INIT
  "Get_Initiate_Continuous": {"scpi": "INITiate:CONTinuous?", "subsystem": "INIT"},

  // LIST
  "Get_List_Current_Points": {"scpi": "LIST:CURR:POIN?", "subsystem": "LIST"},
  "Get_List_Dwel_Points": {"scpi": "LIST:DWEL:POIN?", "subsystem": "LIST"},
  "Get_List_Voltage_Points": {"scpi": "LIST:VOLT:POIN?", "subsystem": "LIST"},

  // OUTP
  "Get_Output_Dfi_Link": {"scpi": "OUTPut:DFI:LINK?", "subsystem": "OUTP"},
  "Get_Output_Dfi_Source": {"scpi": "OUTPut:DFI:SOUR?", "subsystem": "OUTP"},
  "Get_Output_Dfi_Status": {"scpi": "OUTPut:DFI:STATe?", "subsystem": "OUTP"},
  "Get_Output_Protection_Delay": {"scpi": "OUTPut:PROTection:DELay?", "subsystem": "OUTP"},
  "Get_Output_Relay": {"scpi": "OUTP:REL?", "description": "Output Subsystem", "subsystem": "OUTP"},
  "Get_Output_Relay_Polarity": {"scpi": "OUTPut:RELay:POLarity?", "subsystem": "OUTP"},
  "Get_Output_Relay_Status": {"scpi": "OUTP:REL:STAT?", "subsystem": "OUTP"},
  "Get_Output_Status": {"scpi": "OUTPut:STATe?", "subsystem": "OUTP"},
  "Get_Output_Ttltrg_Link": {"scpi": "OUTP:TTLT:LINK?", "subsystem": "OUTP"},
  "Get_Output_Ttltrg_Source": {"scpi": "OUTP:TTLT:SOUR?", "subsystem": "OUTP"},
  "Get_Output_Ttltrg_Status": {"scpi": "OUTP:TTLT:STAT?", "subsystem": "OUTP"},

  // QUES
  "Get_Questionable_Event": {"scpi": "QUES:EVEN?", "subsystem": "QUES"},

  // SOUR
  "Get_Source_Current_Level_Immediate_Amplitude": {"scpi": "SOUR:CURR:LEV:IMM:AMPL?", "subsystem": "SOUR"},
  "Get_Source_Current_Level_Trigger_Amplitude": {"scpi": "SOUR:CURR:LEV:TRIG:AMPL?", "subsystem": "SOUR"},
  "Get_Source_Current_Mode": {"scpi": "SOURce:CURRent:MODE?", "subsystem": "SOUR"},
  "Get_Source_Current_Protection_Status": {"scpi": "SOURce:CURRent:PROTection:STATe?", "subsystem": "SOUR"},
  "Get_Source_List_Count": {"scpi": "SOURce:LIST:COUNt?", "subsystem": "SOUR"},
  "Get_Source_List_Current_Points": {"scpi": "SOURce:LIST:CURRent:POINts?", "subsystem": "SOUR"},
  "Get_Source_List_Dwel": {"scpi": "SOUR:LIST:DWEL?", "subsystem": "SOUR"},
  "Get_Source_List_Dwel_Points": {"scpi": "SOUR:LIST:DWEL:POIN?", "subsystem": "SOUR"},
  "Get_Source_List_Dwfl_Points": {"scpi": "SOURce:LIST:DWFL1:POINts?", "subsystem": "SOUR"},
  "Get_Source_List_Step": {"scpi": "SOUR:LIST:STEP?", "subsystem": "SOUR"},
  "Get_Source_List_Voltage_Points": {"scpi": "SOURce:LIST:VOLTage:POINts?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Level_Trigger_Amplitude": {"scpi": "SOUR:VOLT:LEV:TRIG:AMPL?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Mode": {"scpi": "SOURce:VOLTage:MODE?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Protection_Level": {"scpi": "SOUR:VOLT:PROT:LEV?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Sense": {"scpi": "SOUR:VOLT:SENS?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Sense_Source": {"scpi": "SOURce:VOLTage:SENSe:SOURce?", "subsystem": "SOUR"},

  // SOURI
  "Get_Souri_Voltage_Level_Immediate_Amplitude": {"scpi": "SOURI:VOLT:LEV:IMM:AMPL?", "subsystem": "SOURI"},

  // STAT
  "Get_Status_Operation": {"scpi": "STAT:OPER?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Condition": {"scpi": "STAT:OPER:COND?", "subsystem": "STAT"},
  "Get_Status_Operation_Enable": {"scpi": "STAT:OPER:ENAB?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Event": {"scpi": "STAT:OPER:EVEN?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Ntransition": {"scpi": "STAT:OPER:NTR?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Ptransition": {"scpi": "STAT:OPER:PTR?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable": {"scpi": "STAT:QUES?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Enable": {"scpi": "STAT:QUES:ENAB?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Event": {"scpi": "STAT:QUES:EVEN?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Ntransition": {"scpi": "STATus:QUEStionable:NTRansition?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Ptransition": {"scpi": "STATus:QUEStionable:PTRansitiion?", "description": "Register Commands", "subsystem": "STAT"},

  // SYST
  "Get_System_Version": {"scpi": "SYST:VERS?", "subsystem": "SYST"},

  // TRIG
  "Get_Trigger_Delay": {"scpi": "TRIG:DEL?", "subsystem": "TRIG"},
  "Get_Trigger_Link": {"scpi": "TRIG:LINK?", "subsystem": "TRIG"},
  "Get_Trigger_Source": {"scpi": "TRIG:SOUR?", "subsystem": "TRIG"},
  "Get_Trigger_Start_Delay": {"scpi": "TRIGger:STARt:DELay?", "subsystem": "TRIG"},
  "Get_Trigger_Start_Link": {"scpi": "TRIGger:STARt:LINK?", "subsystem": "TRIG"},
  "Get_Trigger_Start_Source": {"scpi": "TRIGger:STARt:SOURce?", "subsystem": "TRIG"},

  // VOLT
  "Get_Voltage_Alc_Source": {"scpi": "VOLT:ALC:SOUR?", "subsystem": "VOLT"},
  "Get_Voltage_Protection": {"scpi": "VOLT:PROT?", "description": "Query Indicator", "subsystem": "VOLT"},
  "Get_Voltage_Sense_Source": {"scpi": "VOLT:SENS:SOUR?", "subsystem": "VOLT"},
  "Get_Voltage_Trigger": {"scpi": "VOLT:TRIG?", "subsystem": "VOLT"},
}
```

## Power — 66104A

Source: `66000A - 5959-3362 Programming guide.md`; `HP 661xx A User guide.md`

174 missing — SET 49, DO 56, NAB 69. The table has 18.

### SET — 49

```json
"set": {
  // CAL
  "Set_Calibrate_Status": {"scpi": "CAL:STAT <value>", "subsystem": "CAL"},

  // CURR
  "Set_Current_Trigger": {"scpi": "CURR:TRIG <value>", "description": "Controlling Fixed-Mode Output", "subsystem": "CURR"},

  // Common
  "Set_Ese": {"scpi": "*ESE <value>", "subsystem": "Common"},
  "Set_Psc": {"scpi": "*PSC <value>", "subsystem": "Common"},
  "Set_Rcl": {"scpi": "*RCL <value>", "subsystem": "Common"},
  "Set_Sav": {"scpi": "*SAV <value>", "subsystem": "Common"},
  "Set_Sre": {"scpi": "*SRE <value>", "subsystem": "Common"},

  // DISP
  "Set_Display_Window_Status": {"scpi": "DISP:WIND:STAT <value>", "subsystem": "DISP"},

  // INIT
  "Set_Initiate_Continuous": {"scpi": "INIT:CONT <value>", "description": "Controlling Triggers", "subsystem": "INIT"},

  // LIST
  "Set_List_Dwel_Points": {"scpi": "LIST:DWEL:POIN <value>", "description": "CURR:PROT:STAT,32", "subsystem": "LIST"},

  // OUTP
  "Set_Output_Dfi_Link": {"scpi": "OUTP:DFI:LINK <value>", "subsystem": "OUTP"},
  "Set_Output_Dfi_Source": {"scpi": "OUTP:DFI:SOUR <value>", "subsystem": "OUTP"},
  "Set_Output_Dfi_Status": {"scpi": "OUTP:DFI:STAT <value>", "subsystem": "OUTP"},
  "Set_Output_Protection_Delay": {"scpi": "OUTP:PROT:DEL <value>", "description": "Controlling Protection Functions", "subsystem": "OUTP"},
  "Set_Output_Relay": {"scpi": "OUTP:REL <value>", "description": "Controlling the Output State", "subsystem": "OUTP"},
  "Set_Output_Relay_Polarity": {"scpi": "OUTP:REL:POL <value>", "description": "Controlling the Output State", "subsystem": "OUTP"},
  "Set_Output_Relay_Status": {"scpi": "OUTP:REL:STAT <value>", "subsystem": "OUTP"},
  "Set_Output_Status": {"scpi": "OUTP:STAT <value>", "subsystem": "OUTP"},
  "Set_Output_Ttltrg_Link": {"scpi": "OUTP:TTLT:LINK <value>", "description": "Controlling Triggers", "subsystem": "OUTP"},
  "Set_Output_Ttltrg_Source": {"scpi": "OUTP:TTLT:SOUR <value>", "description": "Controlling Triggers", "subsystem": "OUTP"},
  "Set_Output_Ttltrg_Status": {"scpi": "OUTP:TTLT:STAT <value>", "subsystem": "OUTP"},

  // SOUR
  "Set_Source_Current_Level_Immediate_Amplitude": {"scpi": "SOUR:CURR:LEV:IMM:AMPL <value>", "subsystem": "SOUR"},
  "Set_Source_Current_Level_Trigger_Amplitude": {"scpi": "SOUR:CURR:LEV:TRIG:AMPL <value>", "subsystem": "SOUR"},
  "Set_Source_Current_Mode": {"scpi": "SOURce:CURRent:MODE <value>", "subsystem": "SOUR"},
  "Set_Source_Current_Protection_Status": {"scpi": "SOURce:CURRent:PROTection:STATe <value>", "subsystem": "SOUR"},
  "Set_Source_List_Count": {"scpi": "SOURce:LIST:COUNt <value>", "subsystem": "SOUR"},
  "Set_Source_List_Dwel": {"scpi": "SOURce:LIST:DWEL<chan> <value>", "subsystem": "SOUR"},
  "Set_Source_List_Step": {"scpi": "SOUR:LIST:STEP <value>", "subsystem": "SOUR"},
  "Set_Source_Voltage_Level_Trigger_Amplitude": {"scpi": "SOUR:VOLT:LEV:TRIG:AMPL <value>", "subsystem": "SOUR"},
  "Set_Source_Voltage_Mode": {"scpi": "SOURce:VOLTage:MODE <value>", "subsystem": "SOUR"},
  "Set_Source_Voltage_Protection_Level": {"scpi": "SOUR:VOLT:PROT:LEV <value>", "subsystem": "SOUR"},

  // STAT
  "Set_Status_Operation": {"scpi": "STAT:OPER <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Enable": {"scpi": "STAT:OPER:ENAB <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Event": {"scpi": "STAT:OPER:EVEN <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Ntransition": {"scpi": "STAT:OPER:NTR <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Operation_Ptransition": {"scpi": "STAT:OPER:PTR <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable": {"scpi": "STAT:QUES <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable_Enable": {"scpi": "STAT:QUES:ENAB <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable_Ntransition": {"scpi": "STAT:QUES:NTR <value>", "description": "Register Commands", "subsystem": "STAT"},
  "Set_Status_Questionable_Ptransition": {"scpi": "STAT:QUES:PTR <value>", "description": "Register Commands", "subsystem": "STAT"},

  // TRIG
  "Set_Trigger_Delay": {"scpi": "TRIG:DEL <value>", "description": "Controlling Triggers", "subsystem": "TRIG"},
  "Set_Trigger_Link": {"scpi": "TRIG:LINK <value>", "description": "Controlling Triggers", "subsystem": "TRIG"},
  "Set_Trigger_Source": {"scpi": "TRIG:SOUR <value>", "description": "Controlling Triggers", "subsystem": "TRIG"},
  "Set_Trigger_Start_Delay": {"scpi": "TRIGger:STARt:DELay <value>", "subsystem": "TRIG"},
  "Set_Trigger_Start_Link": {"scpi": "TRIG:STAR:LINK <value>", "subsystem": "TRIG"},
  "Set_Trigger_Start_Source": {"scpi": "TRIGger:STARt:SOURce <value>", "subsystem": "TRIG"},

  // VOLT
  "Set_Voltage_Alc_Source": {"scpi": "VOLT:ALC:SOUR <value>", "subsystem": "VOLT"},
  "Set_Voltage_Sense_Source": {"scpi": "VOLT:SENS:SOUR <value>", "subsystem": "VOLT"},
  "Set_Voltage_Trigger": {"scpi": "VOLT:TRIG <value>", "subsystem": "VOLT"},
}
```

### DO — 56

```json
"do": {
  // CAL
  "Do_Calibrate_Aut": {"scpi": "CAL:AUT", "subsystem": "CAL"},
  "Do_Calibrate_Current": {"scpi": "CAL:CURR", "subsystem": "CAL"},
  "Do_Calibrate_Current_Data": {"scpi": "CAL:CURR:DATA", "subsystem": "CAL"},
  "Do_Calibrate_Current_Level": {"scpi": "CAL:CURR:LEV", "subsystem": "CAL"},
  "Do_Calibrate_Passcode": {"scpi": "CAL:PASS", "subsystem": "CAL"},
  "Do_Calibrate_Sav": {"scpi": "CAL:SAV", "subsystem": "CAL"},
  "Do_Calibrate_Voltage": {"scpi": "CAL:VOLT", "subsystem": "CAL"},
  "Do_Calibrate_Voltage_Data": {"scpi": "CAL:VOLT:DATA", "subsystem": "CAL"},
  "Do_Calibrate_Voltage_Level": {"scpi": "CAL:VOLT:LEV", "subsystem": "CAL"},
  "Do_Calibrate_Voltage_Protection": {"scpi": "CAL:VOLT:PROT", "description": "Calibrating Voltage", "subsystem": "CAL"},

  // CURR
  "Do_Current_Data": {"scpi": "CURR:DATA", "subsystem": "CURR"},
  "Do_Current_Immediate": {"scpi": "CURR:IMM", "subsystem": "CURR"},
  "Do_Current_Level": {"scpi": "CURR:LEV", "description": "Installation 23", "subsystem": "CURR"},
  "Do_Current_Level_Immediate": {"scpi": "CURR:LEV:IMM", "subsystem": "CURR"},
  "Do_Current_Level_Trigger": {"scpi": "CURR:LEV:TRIG", "description": "Trigger Subsystem", "subsystem": "CURR"},
  "Do_Current_List": {"scpi": "CURR:LIST", "subsystem": "CURR"},
  "Do_Current_Mode": {"scpi": "CURR:MODE", "description": "Controlling Fixed-Mode Output", "subsystem": "CURR"},
  "Do_Current_Mode_List": {"scpi": "CURR:MODE:LIST", "subsystem": "CURR"},
  "Do_Current_Protection": {"scpi": "CURRent:PROTection", "subsystem": "CURR"},

  // Common
  "Do_Opc": {"scpi": "*OPC", "subsystem": "Common"},
  "Do_Wai": {"scpi": "*WAI", "subsystem": "Common"},

  // DISP
  "Do_Display_Status": {"scpi": "DISP:STAT", "subsystem": "DISP"},

  // IMM
  "Do_Immediate_Amplitude": {"scpi": ":IMMediate:AMPLitude", "subsystem": "IMM"},

  // INIT
  "Do_Initiate_Immediate": {"scpi": "INIT:IMM", "subsystem": "INIT"},

  // LIST
  "Do_List_Count": {"scpi": "LIST:COUN", "subsystem": "LIST"},
  "Do_List_Current": {"scpi": "LIST:CURR", "description": "Controlling List-Mode Output", "subsystem": "LIST"},
  "Do_List_Dwel": {"scpi": "LIST:DWEL", "description": "Controlling List-Mode Output", "subsystem": "LIST"},
  "Do_List_Step": {"scpi": "LIST:STEP", "subsystem": "LIST"},
  "Do_List_Voltage": {"scpi": "LIST:VOLT", "description": "Controlling List-Mode Output", "subsystem": "LIST"},

  // OUTP
  "Do_Output_Dfi": {"scpi": "OUTP:DFI", "description": "DFI (Discrete Fault Indicator) Output", "subsystem": "OUTP"},
  "Do_Output_Protection": {"scpi": "OUTP:PROT", "subsystem": "OUTP"},
  "Do_Output_Ttltrg": {"scpi": "OUTP:TTLT", "description": "CURR:PROT:STAT,32", "subsystem": "OUTP"},

  // PROTECTION
  "Do_Protection_Clear": {"scpi": "PROTECTION:CLEAR", "description": "The Effect of Optional Headers", "subsystem": "PROTECTION"},

  // SOUR
  "Do_Source_Current_Level": {"scpi": "SOURce:CURRent:LEVel", "subsystem": "SOUR"},
  "Do_Source_Current_Level_Trigger": {"scpi": "SOURce:CURRent:LEVel:TRIGgered", "subsystem": "SOUR"},
  "Do_Source_Currlev_Trigger": {"scpi": "SOURce:CURRentLEVel:TRIGgered", "subsystem": "SOUR"},
  "Do_Source_List": {"scpi": "SOURce:LIST", "description": "Conventions", "subsystem": "SOUR"},
  "Do_Source_List_Current": {"scpi": "SOURce:LIST:CURRent", "subsystem": "SOUR"},
  "Do_Source_List_Voltage": {"scpi": "SOURce:LIST:VOLTage", "subsystem": "SOUR"},
  "Do_Source_Voltage_Level": {"scpi": "SOURce:VOLTage:LEVel", "subsystem": "SOUR"},
  "Do_Source_Voltage_Level_Immediate_Amplitude": {"scpi": "SOUR:VOLT:LEV:IMM:AMPL", "subsystem": "SOUR"},
  "Do_Source_Voltage_Level_Trigger": {"scpi": "SOURce:VOLTage:LEVel:TRIGgered", "subsystem": "SOUR"},
  "Do_Source_Voltage_Protection": {"scpi": "SOURce:VOLTage:PROTection", "subsystem": "SOUR"},
  "Do_Source_Voltlev_Trigger": {"scpi": "SOURce:VOLTageLEVel:TRIGgered", "subsystem": "SOUR"},

  // STAT
  "Do_Status_Pre": {"scpi": "STAT:PRE", "description": "Status Registers", "subsystem": "STAT"},

  // TRIG
  "Do_Trigger_Immediate": {"scpi": "TRIG:IMM", "subsystem": "TRIG"},
  "Do_Trigger_Start_Immediate": {"scpi": "TRIGger:STARt:IMMediate", "subsystem": "TRIG"},

  // TTLT
  "Do_Ttltrg_Link": {"scpi": "TTLT:LINK", "subsystem": "TTLT"},

  // VOLT
  "Do_Voltage_Immediate": {"scpi": "VOLT:IMM", "subsystem": "VOLT"},
  "Do_Voltage_Level": {"scpi": "VOLT:LEV", "subsystem": "VOLT"},
  "Do_Voltage_Level_Immediate": {"scpi": "VOLT:LEV:IMM", "subsystem": "VOLT"},
  "Do_Voltage_Level_Trigger": {"scpi": "VOLT:LEV:TRIG", "description": "Trigger Subsystem", "subsystem": "VOLT"},
  "Do_Voltage_List": {"scpi": "VOLT:LIST", "description": "SCPI Command Completion", "subsystem": "VOLT"},
  "Do_Voltage_Mode": {"scpi": "VOLT:MODE", "description": "Controlling Fixed-Mode Output", "subsystem": "VOLT"},
  "Do_Voltage_Protection_Level": {"scpi": "VOLT:PROT:LEV", "subsystem": "VOLT"},
  "Do_Voltage_Tiug": {"scpi": "VOLT:TIUG", "subsystem": "VOLT"},
}
```

### NAB — 69

```json
"nab": {
  // CAL
  "Get_Calibrate_Status": {"scpi": "CALibrate:STATe?", "subsystem": "CAL"},

  // CURR
  "Get_Current_Trigger": {"scpi": "CURR:TRIG?", "subsystem": "CURR"},

  // Common
  "Get_Ese": {"scpi": "*ESE?", "subsystem": "Common"},
  "Get_Esr": {"scpi": "*ESR?", "subsystem": "Common"},
  "Get_Idn": {"scpi": "*IDN?", "subsystem": "Common"},
  "Get_Opc": {"scpi": "*OPC?", "subsystem": "Common"},
  "Get_Opt": {"scpi": "*OPT?", "subsystem": "Common"},
  "Get_Psc": {"scpi": "*PSC?", "subsystem": "Common"},
  "Get_Sre": {"scpi": "*SRE?", "subsystem": "Common"},
  "Get_Stb": {"scpi": "*STB?", "subsystem": "Common"},
  "Get_Tst": {"scpi": "*TST?", "subsystem": "Common"},

  // DISP
  "Get_Display_Window_Status": {"scpi": "DISPlay:WINDow:STAT?", "subsystem": "DISP"},

  // IMM
  "Get_Immediate_Amplitude": {"scpi": ":IMMediate:AMPlitude?", "subsystem": "IMM"},

  // INIT
  "Get_Initiate_Continuous": {"scpi": "INITiate:CONTinuous?", "subsystem": "INIT"},

  // LIST
  "Get_List_Current_Points": {"scpi": "LIST:CURR:POIN?", "description": "Controlling List-Mode Output", "subsystem": "LIST"},
  "Get_List_Dwel_Points": {"scpi": "LIST:DWEL:POIN?", "description": "Controlling List-Mode Output", "subsystem": "LIST"},
  "Get_List_Voltage_Points": {"scpi": "LIST:VOLT:POIN?", "description": "Controlling List-Mode Output", "subsystem": "LIST"},

  // OUTP
  "Get_Output_Dfi_Link": {"scpi": "OUTPut:DFI:LINK?", "subsystem": "OUTP"},
  "Get_Output_Dfi_Source": {"scpi": "OUTPut:DFI:SOUR?", "subsystem": "OUTP"},
  "Get_Output_Dfi_Status": {"scpi": "OUTPut:DFI:STATe?", "subsystem": "OUTP"},
  "Get_Output_Protection_Delay": {"scpi": "OUTPut:PROTection:DELay?", "description": "Controlling Protection Functions", "subsystem": "OUTP"},
  "Get_Output_Relay": {"scpi": "OUTP:REL?", "description": "Output Subsystem", "subsystem": "OUTP"},
  "Get_Output_Relay_Polarity": {"scpi": "OUTPut:RELay:POLarity?", "description": "Controlling the Output State", "subsystem": "OUTP"},
  "Get_Output_Relay_Status": {"scpi": "OUTP:REL:STAT?", "subsystem": "OUTP"},
  "Get_Output_Status": {"scpi": "OUTPut:STATe?", "subsystem": "OUTP"},
  "Get_Output_Ttltrg_Link": {"scpi": "OUTP:TTLT:LINK?", "description": "Controlling Triggers", "subsystem": "OUTP"},
  "Get_Output_Ttltrg_Source": {"scpi": "OUTP:TTLT:SOUR?", "description": "Controlling Triggers", "subsystem": "OUTP"},
  "Get_Output_Ttltrg_Status": {"scpi": "OUTP:TTLT:STAT?", "subsystem": "OUTP"},

  // QUES
  "Get_Questionable_Event": {"scpi": "QUES:EVEN?", "subsystem": "QUES"},

  // SOUR
  "Get_Source_Current_Level_Immediate_Amplitude": {"scpi": "SOUR:CURR:LEV:IMM:AMPL?", "subsystem": "SOUR"},
  "Get_Source_Current_Level_Trigger_Amplitude": {"scpi": "SOUR:CURR:LEV:TRIG:AMPL?", "subsystem": "SOUR"},
  "Get_Source_Current_Mode": {"scpi": "SOURce:CURRent:MODE?", "subsystem": "SOUR"},
  "Get_Source_Current_Protection_Status": {"scpi": "SOURce:CURRent:PROTection:STATe?", "subsystem": "SOUR"},
  "Get_Source_List_Count": {"scpi": "SOURce:LIST:COUNt?", "subsystem": "SOUR"},
  "Get_Source_List_Current_Points": {"scpi": "SOURce:LIST:CURRent:POINts?", "subsystem": "SOUR"},
  "Get_Source_List_Dwel": {"scpi": "SOUR:LIST:DWEL?", "subsystem": "SOUR"},
  "Get_Source_List_Dwel_Points": {"scpi": "SOUR:LIST:DWEL:POIN?", "subsystem": "SOUR"},
  "Get_Source_List_Dwfl_Points": {"scpi": "SOURce:LIST:DWFL1:POINts?", "subsystem": "SOUR"},
  "Get_Source_List_Step": {"scpi": "SOUR:LIST:STEP?", "subsystem": "SOUR"},
  "Get_Source_List_Voltage_Points": {"scpi": "SOURce:LIST:VOLTage:POINts?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Level_Trigger_Amplitude": {"scpi": "SOUR:VOLT:LEV:TRIG:AMPL?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Mode": {"scpi": "SOURce:VOLTage:MODE?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Protection_Level": {"scpi": "SOUR:VOLT:PROT:LEV?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Sense": {"scpi": "SOUR:VOLT:SENS?", "subsystem": "SOUR"},
  "Get_Source_Voltage_Sense_Source": {"scpi": "SOURce:VOLTage:SENSe:SOURce?", "subsystem": "SOUR"},

  // SOURI
  "Get_Souri_Voltage_Level_Immediate_Amplitude": {"scpi": "SOURI:VOLT:LEV:IMM:AMPL?", "subsystem": "SOURI"},

  // STAT
  "Get_Status_Operation": {"scpi": "STAT:OPER?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Condition": {"scpi": "STAT:OPER:COND?", "subsystem": "STAT"},
  "Get_Status_Operation_Enable": {"scpi": "STAT:OPER:ENAB?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Event": {"scpi": "STAT:OPER:EVEN?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Ntransition": {"scpi": "STAT:OPER:NTR?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Operation_Ptransition": {"scpi": "STAT:OPER:PTR?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable": {"scpi": "STAT:QUES?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Enable": {"scpi": "STAT:QUES:ENAB?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Event": {"scpi": "STAT:QUES:EVEN?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Ntransition": {"scpi": "STATus:QUEStionable:NTRansition?", "description": "Register Commands", "subsystem": "STAT"},
  "Get_Status_Questionable_Ptransition": {"scpi": "STATus:QUEStionable:PTRansitiion?", "description": "Register Commands", "subsystem": "STAT"},

  // SYST
  "Get_System_Version": {"scpi": "SYST:VERS?", "subsystem": "SYST"},

  // TRIG
  "Get_Trigger_Delay": {"scpi": "TRIG:DEL?", "description": "Controlling Triggers", "subsystem": "TRIG"},
  "Get_Trigger_Link": {"scpi": "TRIG:LINK?", "description": "Controlling Triggers", "subsystem": "TRIG"},
  "Get_Trigger_Source": {"scpi": "TRIG:SOUR?", "description": "Controlling Triggers", "subsystem": "TRIG"},
  "Get_Trigger_Start_Delay": {"scpi": "TRIGger:STARt:DELay?", "subsystem": "TRIG"},
  "Get_Trigger_Start_Link": {"scpi": "TRIGger:STARt:LINK?", "subsystem": "TRIG"},
  "Get_Trigger_Start_Source": {"scpi": "TRIGger:STARt:SOURce?", "subsystem": "TRIG"},

  // VOLT
  "Get_Voltage_Alc_Source": {"scpi": "VOLT:ALC:SOUR?", "subsystem": "VOLT"},
  "Get_Voltage_Protection": {"scpi": "VOLT:PROT?", "description": "Query Indicator", "subsystem": "VOLT"},
  "Get_Voltage_Sense": {"scpi": "VOLT:SENS?", "description": "Controlling Fixed-Mode Output", "subsystem": "VOLT"},
  "Get_Voltage_Sense_Source": {"scpi": "VOLT:SENS:SOUR?", "description": "Local Voltage Sensing", "subsystem": "VOLT"},
  "Get_Voltage_Trigger": {"scpi": "VOLT:TRIG?", "subsystem": "VOLT"},
}
```

## Scope — 54641D

Source: `54621_Programmers guide.md`

324 missing — SET 90, DO 85, NAB 149. The table has 113.

### SET — 90

```json
"set": {
  // ACQ
  "Set_Acquire_Complete": {"scpi": ":ACQuire:COMPlete <value>", "subsystem": "ACQ"},
  "Set_Acquire_Mode": {"scpi": ":ACQuire:MODE <value>", "subsystem": "ACQ"},

  // CAL
  "Set_Calibrate_Label": {"scpi": ":CALibrate:LABel <value>", "subsystem": "CAL"},

  // CHANNEL
  "Set_Channel_Coupling": {"scpi": ":CHANNEL1:COUPLING <value>", "subsystem": "CHANNEL"},

  // Common
  "Set_Ese": {"scpi": "*ESE <value>", "subsystem": "Common"},
  "Set_Rcl": {"scpi": "*RCL <value>", "subsystem": "Common"},
  "Set_Sav": {"scpi": "*SAV <value>", "subsystem": "Common"},
  "Set_Sre": {"scpi": "*SRE <value>", "subsystem": "Common"},

  // DISP
  "Set_Display_Data": {"scpi": ":DISPlay:DATA <value>", "subsystem": "DISP"},
  "Set_Display_Label": {"scpi": ":DISPlay:LABel <value>", "subsystem": "DISP"},
  "Set_Display_Persistence": {"scpi": "DISPlay:PERSistence <value>", "subsystem": "DISP"},
  "Set_Display_Source": {"scpi": ":DISPlay:SOURce <value>", "subsystem": "DISP"},
  "Set_Display_Vectors": {"scpi": "DISPlay:VECTors <value>", "subsystem": "DISP"},

  // EXT
  "Set_External_Bwlimit": {"scpi": ":EXTernal:BWLimit <value>", "subsystem": "EXT"},
  "Set_External_Impedance": {"scpi": "EXTernal:IMPedance <value>", "subsystem": "EXT"},
  "Set_External_Probe": {"scpi": ":EXTernal:PROBe <value>", "subsystem": "EXT"},
  "Set_External_Range": {"scpi": ":EXTernal:RANGe <value>", "subsystem": "EXT"},
  "Set_External_Units": {"scpi": ":EXTernal:UNITs <value>", "subsystem": "EXT"},

  // FUNC
  "Set_Function_Reference": {"scpi": ":FUNCtion:REFerence <value>", "subsystem": "FUNC"},

  // HARD
  "Set_Hardcopy_Factors": {"scpi": ":HARDcopy:FACTors <value>", "subsystem": "HARD"},
  "Set_Hardcopy_Ffeed": {"scpi": ":HARDcopy:FFEed <value>", "subsystem": "HARD"},
  "Set_Hardcopy_Format": {"scpi": "HARDcopy:FORMat <value>", "description": "Obsolete and Discontinued Commands", "subsystem": "HARD"},
  "Set_Hardcopy_Grayscale": {"scpi": ":HARDcopy:GRAYscale <value>", "subsystem": "HARD"},

  // MEAS
  "Set_Measure_Count": {"scpi": ":MEASure:COUNter <value>", "subsystem": "MEAS"},
  "Set_Measure_Delay": {"scpi": ":MEASure:DELay <value>", "subsystem": "MEAS"},
  "Set_Measure_Falltime": {"scpi": ":MEASure:FALLtime <value>", "subsystem": "MEAS"},
  "Set_Measure_Nwidth": {"scpi": ":MEASure:NWIDth <value>", "subsystem": "MEAS"},
  "Set_Measure_Overshoot": {"scpi": ":MEASure:OVERshoot <value>", "subsystem": "MEAS"},
  "Set_Measure_Phase": {"scpi": ":MEASure:PHASe <value>", "subsystem": "MEAS"},
  "Set_Measure_Preshoot": {"scpi": ":MEASure:PREShoot <value>", "subsystem": "MEAS"},
  "Set_Measure_Pwidth": {"scpi": ":MEASure:PWIDth <value>", "subsystem": "MEAS"},
  "Set_Measure_Show": {"scpi": ":MEASure:SHOW <value>", "subsystem": "MEAS"},
  "Set_Measure_Tedge": {"scpi": ":MEASure:TEDGe <value>", "subsystem": "MEAS"},
  "Set_Measure_Tvalue": {"scpi": "MEASure:TVALue <value>", "subsystem": "MEAS"},
  "Set_Measure_Vamplitude": {"scpi": ":MEASure:VAMPlitude <value>", "subsystem": "MEAS"},
  "Set_Measure_Vbase": {"scpi": ":MEASure:VBASe <value>", "subsystem": "MEAS"},
  "Set_Measure_Vtop": {"scpi": ":MEASure:VTOP <value>", "subsystem": "MEAS"},
  "Set_Measure_Xmax": {"scpi": "MEASure:XMAX <value>", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},
  "Set_Measure_Xmin": {"scpi": "MEASure:XMIN <value>", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},

  // PROB
  "Set_Probe_Skew": {"scpi": ":PROBe:SKEW <value>", "subsystem": "PROB"},

  // SYST
  "Set_System_Date": {"scpi": ":SYSTem:DATE <value>", "subsystem": "SYST"},
  "Set_System_Time": {"scpi": ":SYSTem:TIME <value>", "subsystem": "SYST"},

  // TIM
  "Set_Timebase_Range": {"scpi": ":TIMebase:RANGe <value>", "subsystem": "TIM"},
  "Set_Timebase_Window_Range": {"scpi": ":TIMebase:WINDow:RANGe <value>", "subsystem": "TIM"},

  // TRIG
  "Set_Trigger_Can_Acknowledge": {"scpi": ":TRIGger:CAN:ACKNowledge <value>", "subsystem": "TRIG"},
  "Set_Trigger_Can_Pattern_Data": {"scpi": ":TRIGger:CAN:PATTern:DATA <value>", "description": "Table 5-1", "subsystem": "TRIG"},
  "Set_Trigger_Can_Pattern_Id": {"scpi": "TRIGger:CAN:PATTern:ID <value>", "description": "Table 5-1", "subsystem": "TRIG"},
  "Set_Trigger_Can_Pattern_Id_Mode": {"scpi": ":TRIGger:CAN:PATTern:ID:MODE <value>", "subsystem": "TRIG"},
  "Set_Trigger_Can_Samplepoint": {"scpi": ":TRIGger:CAN:SAMPlepoint <value>", "subsystem": "TRIG"},
  "Set_Trigger_Can_Signal_Baudrate": {"scpi": ":TRIGger:CAN:SIGNal:BAUDrate <value>", "subsystem": "TRIG"},
  "Set_Trigger_Can_Source": {"scpi": ":TRIGger:CAN:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Can_Trigger": {"scpi": ":TRIGger:CAN:TRIGger <value>", "subsystem": "TRIG"},
  "Set_Trigger_Duration_Pattern": {"scpi": ":TRIGger:DURation:PATTern <value>", "subsystem": "TRIG"},
  "Set_Trigger_Duration_Qualifier": {"scpi": ":TRIGger:DURation:QUALifier <value>", "subsystem": "TRIG"},
  "Set_Trigger_Duration_Range": {"scpi": ":TRIGger:DURation:RANGe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Glitch_Level": {"scpi": ":TRIGger:GLITch:LEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Glitch_Polarity": {"scpi": ":TRIGger:GLITch:POLarity <value>", "subsystem": "TRIG"},
  "Set_Trigger_Glitch_Range": {"scpi": ":TRIGger:GLITch:RANGe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Hfreject": {"scpi": ":TRIGger:HFReject <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Pattern_Address": {"scpi": ":TRIGger:IIC:PATTern:ADDRess <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Pattern_Data": {"scpi": ":TRIGger:IIC:PATTern:DATA <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Trigger_Qualifier": {"scpi": ":TRIGger:IIC:TRIGger:QUALifier <value>", "subsystem": "TRIG"},
  "Set_Trigger_Lin_Signal_Baudrate": {"scpi": ":TRIGger:LIN:SIGNal:BAUDrate <value>", "subsystem": "TRIG"},
  "Set_Trigger_Lin_Source": {"scpi": ":TRIGger:LIN:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Lin_Trigger": {"scpi": ":TRIGger:LIN:TRIGger <value>", "subsystem": "TRIG"},
  "Set_Trigger_Nreject": {"scpi": ":TRIGger:NREJect <value>", "subsystem": "TRIG"},
  "Set_Trigger_Pattern": {"scpi": ":TRIGger:PATTern <value>", "subsystem": "TRIG"},
  "Set_Trigger_Sequence_Count": {"scpi": ":TRIGger:SEQuence:COUNt <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Clock_Slope": {"scpi": ":TRIGger:SPI:CLOCk:SLOPe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Clock_Timebase": {"scpi": ":TRIGger:SPI:CLOCk:TIMeout <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Frame": {"scpi": ":TRIGger:SPI:FRAMing <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Pattern_Data": {"scpi": ":TRIGger:SPI:PATTern:DATA <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Pattern_Width": {"scpi": "TRIGger:SPI:PATTern:WIDth <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Source_Clock": {"scpi": ":TRIGger:SPI:SOURce:CLOCk <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Source_Data": {"scpi": ":TRIGger:SPI:SOURce:DATA <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Source_Frame": {"scpi": ":TRIGger:SPI:SOURce:FRAMe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Tv_Line": {"scpi": ":TRIGger:TV:LINE <value>", "subsystem": "TRIG"},
  "Set_Trigger_Tv_Mode": {"scpi": "TRIGger:TV:MODE <value>", "subsystem": "TRIG"},
  "Set_Trigger_Tv_Polarity": {"scpi": ":TRIGger:TV:POLarity <value>", "subsystem": "TRIG"},
  "Set_Trigger_Tv_Source": {"scpi": ":TRIGger:TV:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Tv_Standard": {"scpi": ":TRIGger:TV:STANdard <value>", "subsystem": "TRIG"},
  "Set_Trigger_Usb_Source_Dminus": {"scpi": ":TRIGger:USB:SOURce:DMINus <value>", "subsystem": "TRIG"},
  "Set_Trigger_Usb_Source_Dplus": {"scpi": ":TRIGger:USB:SOURce:DPLus <value>", "subsystem": "TRIG"},
  "Set_Trigger_Usb_Speed": {"scpi": ":TRIGger:USB:SPEed <value>", "subsystem": "TRIG"},
  "Set_Trigger_Usb_Trigger": {"scpi": ":TRIGger:USB:TRIGer <value>", "subsystem": "TRIG"},

  // TRIGGER
  "Set_Trigger_Sequence_Find": {"scpi": ":TRIGGER:SEQuence:FIND <value>", "subsystem": "TRIGGER"},
  "Set_Trigger_Sequence_Reset": {"scpi": ":TRIGGER:SEQuence:RESet <value>", "subsystem": "TRIGGER"},
  "Set_Trigger_Sequence_Timebase": {"scpi": ":TRIGGER:SEQuence:TIMer <value>", "subsystem": "TRIGGER"},
  "Set_Trigger_Sequence_Trigger": {"scpi": ":TRIGGER:SEQuence:TRIGger <value>", "subsystem": "TRIGGER"},

  // WAV
  "Set_Waveform_View": {"scpi": ":WAVeform:VIEW <value>", "subsystem": "WAV"},
}
```

### DO — 85

```json
"do": {
  // CHAN
  "Do_Channel_Activity": {"scpi": "CHANnel:ACTivity", "subsystem": "CHAN"},
  "Do_Channel_Math": {"scpi": "CHANnel:MATH", "subsystem": "CHAN"},
  "Do_Channel_Skew": {"scpi": "CHANnel2:SKEW", "subsystem": "CHAN"},
  "Do_Channel_Threshold": {"scpi": "CHANnel:THReshold", "subsystem": "CHAN"},

  // CHANNEL
  "Do_Channel_Bwlimit": {"scpi": ":CHANNEL1:BWLIMIT", "subsystem": "CHANNEL"},
  "Do_Channel_Offset": {"scpi": ":CHANNEL1:OFFSET", "subsystem": "CHANNEL"},
  "Do_Channel_Probe": {"scpi": ":CHANNEL1:PROBE", "description": "Setting Up the Instrument", "subsystem": "CHANNEL"},

  // Common
  "Do_Opc": {"scpi": "*OPC", "subsystem": "Common"},
  "Do_Trg": {"scpi": "*TRG", "subsystem": "Common"},
  "Do_Wai": {"scpi": "*WAI", "subsystem": "Common"},

  // DISP
  "Do_Display_Column": {"scpi": "DISPlay:COLumn", "subsystem": "DISP"},
  "Do_Display_Connect": {"scpi": "DISPlay:CONNect", "subsystem": "DISP"},
  "Do_Display_Grid": {"scpi": "DISPlay:GRID", "subsystem": "DISP"},
  "Do_Display_Invert": {"scpi": "DISPlay:INVerse", "subsystem": "DISP"},
  "Do_Display_Order": {"scpi": "DISPlay:ORDer", "subsystem": "DISP"},
  "Do_Display_Pixel": {"scpi": "DISPlay:PIXel", "subsystem": "DISP"},
  "Do_Display_Position": {"scpi": "DISPlay:POSition", "subsystem": "DISP"},
  "Do_Display_Row": {"scpi": "DISPlay:ROW", "subsystem": "DISP"},
  "Do_Display_Text": {"scpi": "DISPlay:TEXT", "subsystem": "DISP"},

  // DISPL
  "Do_Display_Line": {"scpi": "DISPLay:LINE", "subsystem": "DISPL"},

  // EXT
  "Do_External_Input": {"scpi": "EXTernal:INPut", "subsystem": "EXT"},
  "Do_External_Pmode": {"scpi": "EXTernal:PMODe", "subsystem": "EXT"},
  "Do_External_Protection_Clear": {"scpi": ":EXTernal:PROTection:CLEAR", "subsystem": "EXT"},

  // FUNC
  "Do_Function_Move": {"scpi": "FUNCtion:MOVE", "subsystem": "FUNC"},
  "Do_Function_Peaks": {"scpi": "FUNCtion:PEAKs", "subsystem": "FUNC"},
  "Do_Function_View": {"scpi": "FUNCtion:VIEW", "description": "Obsolete and Discontinued Commands", "subsystem": "FUNC"},

  // HARD
  "Do_Hardcopy_Address": {"scpi": "HARDcopy:ADDRess", "subsystem": "HARD"},
  "Do_Hardcopy_Destination": {"scpi": ":HARDcopy:DESTination", "subsystem": "HARD"},
  "Do_Hardcopy_Device": {"scpi": "HARDcopy:DEVice", "description": "Obsolete and Discontinued Commands", "subsystem": "HARD"},

  // MARK
  "Do_Marker_Tdelta": {"scpi": "MARKer:TDELta", "description": "Obsolete and Discontinued Commands", "subsystem": "MARK"},
  "Do_Marker_Vdelta": {"scpi": "MARKer:VDELta", "subsystem": "MARK"},

  // MEAS
  "Do_Measure_Clear": {"scpi": "MEASure:CLEar", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},
  "Do_Measure_Lower": {"scpi": "MEASure:LOWer", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},
  "Do_Measure_Risetime": {"scpi": ":MEASure:RISEtime", "subsystem": "MEAS"},
  "Do_Measure_Scratch": {"scpi": "MEASure:SCRatch", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},
  "Do_Measure_Tdelta": {"scpi": "MEASure:TDELta", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},
  "Do_Measure_Threshold": {"scpi": "MEASure:THResholds", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},
  "Do_Measure_Tmax": {"scpi": "MEASure:TMAX", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},
  "Do_Measure_Tmin": {"scpi": "MEASure:TMIN", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},
  "Do_Measure_Tstart": {"scpi": "MEASure:TSTArt", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},
  "Do_Measure_Tstop": {"scpi": "MEASure:TSTOp", "description": "Obsolete and Discontinued Commands", "subsystem": "MEAS"},
  "Do_Measure_Tvolt": {"scpi": "MEASure:TVOLt", "subsystem": "MEAS"},
  "Do_Measure_Upper": {"scpi": "MEASure:UPPer", "subsystem": "MEAS"},
  "Do_Measure_Vdelta": {"scpi": "MEASure:VDELta", "subsystem": "MEAS"},
  "Do_Measure_Vstart": {"scpi": "MEASure:VSTArt", "subsystem": "MEAS"},
  "Do_Measure_Vstop": {"scpi": "MEASure:VSTOp", "subsystem": "MEAS"},

  // PROT
  "Do_Protection_Clear": {"scpi": ":PROTection:CLEAR", "subsystem": "PROT"},

  // SYST
  "Do_System_Dsp": {"scpi": "SYSTem:DSP", "description": "Message Queue", "subsystem": "SYST"},
  "Do_System_Key": {"scpi": "SYSTem:KEY", "subsystem": "SYST"},

  // TIM
  "Do_Timebase_Delay": {"scpi": "TIM:DEL", "description": "Program Header Options", "subsystem": "TIM"},
  "Do_Timebase_Window": {"scpi": "TIMebase:WINDow", "description": "Command Set Organization", "subsystem": "TIM"},

  // TRIG
  "Do_Trigger_Advanced": {"scpi": "TRIGger:ADVanced", "subsystem": "TRIG"},
  "Do_Trigger_Can": {"scpi": "TRIGger:CAN", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Can_Pattern": {"scpi": "TRIGger:CAN:PATTern", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Can_Signal": {"scpi": "TRIGger:CAN:SIGNal", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Duration": {"scpi": "TRIGger:DURation", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Edge": {"scpi": "TRIGger:EDGE", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Glitch": {"scpi": "TRIGger:GLITch", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Iic": {"scpi": "TRIGger:IIC", "description": "Command Set Organization", "subsystem": "TRIG"},
  "Do_Trigger_Iic_Pattern": {"scpi": "TRIGger:IIC:PATTern", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Iic_Source": {"scpi": ":TRIGger:IIC:SOURce", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Iic_Trigger": {"scpi": "TRIGger:IIC:TRIGger", "description": "Command Set Organization", "subsystem": "TRIG"},
  "Do_Trigger_Lin": {"scpi": "TRIGger:LIN", "description": "Command Set Organization", "subsystem": "TRIG"},
  "Do_Trigger_Lin_Signal": {"scpi": "TRIGger:LIN:SIGNal", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Sequence": {"scpi": "TRIGger:SEQuence", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Sequence_Edge": {"scpi": ":TRIGger:SEQuence:EDGE", "subsystem": "TRIG"},
  "Do_Trigger_Sequence_Pattern": {"scpi": ":TRIGger:SEQuence:PATTern", "subsystem": "TRIG"},
  "Do_Trigger_Spi": {"scpi": "TRIGger:SPI", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Spi_Clock": {"scpi": "TRIGger:SPI:CLOCk", "description": "Command Set Organization", "subsystem": "TRIG"},
  "Do_Trigger_Spi_Pattern": {"scpi": "TRIGger:SPI:PATTERN", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Spi_Source": {"scpi": "TRIGger:SPI:SOURce", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Threshold": {"scpi": "TRIGger:THReshold", "subsystem": "TRIG"},
  "Do_Trigger_Tv": {"scpi": "TRIGger:TV", "description": "Table 5-1", "subsystem": "TRIG"},
  "Do_Trigger_Tv_Field": {"scpi": "TRIGger:TV:FIELd", "subsystem": "TRIG"},
  "Do_Trigger_Tv_Tvhfrej": {"scpi": "TRIGger:TV:TVHFrej", "subsystem": "TRIG"},
  "Do_Trigger_Tv_Tvmode": {"scpi": "TRIGger:TV:TVMode", "subsystem": "TRIG"},
  "Do_Trigger_Tv_Vir": {"scpi": "TRIGger:TV:VIR", "subsystem": "TRIG"},
  "Do_Trigger_Usb": {"scpi": "TRIGger:USB", "description": "Command Set Organization", "subsystem": "TRIG"},
  "Do_Trigger_Usb_Source": {"scpi": "TRIGger:USB:SOURce", "description": "Table 5-1", "subsystem": "TRIG"},

  // TRIGGER
  "Do_Trigger_Duration_Greaterthan": {"scpi": ":TRIGGER:DURation:GREaterthan", "subsystem": "TRIGGER"},
  "Do_Trigger_Duration_Lessthan": {"scpi": ":TRIGGER:DURation:LESSthan", "subsystem": "TRIGGER"},
  "Do_Trigger_Glitch_Greaterthan": {"scpi": ":TRIGGER:GLITch:GREaterthan", "subsystem": "TRIGGER"},
  "Do_Trigger_Glitch_Lessthan": {"scpi": ":TRIGGER:GLITch:LESSthan", "subsystem": "TRIGGER"},
  "Do_Trigger_Level": {"scpi": ":TRIGGER:LEVEL", "subsystem": "TRIGGER"},
  "Do_Trigger_Slope": {"scpi": ":TRIGGER:SLOPE", "subsystem": "TRIGGER"},
}
```

### NAB — 149

```json
"nab": {
  // ACQ
  "Get_Acquire_Complete": {"scpi": ":ACQuire:COMPlete?", "subsystem": "ACQ"},
  "Get_Acquire_Count": {"scpi": ":ACQuire:COUNT?", "subsystem": "ACQ"},
  "Get_Acquire_Mode": {"scpi": ":ACQuire:MODE?", "subsystem": "ACQ"},
  "Get_Acquire_Points": {"scpi": ":ACQuire:POINts?", "subsystem": "ACQ"},

  // CAL
  "Get_Calibrate_Date": {"scpi": ":CALibrate:DATE?", "subsystem": "CAL"},
  "Get_Calibrate_Label": {"scpi": ":CALibrate:LABel?", "subsystem": "CAL"},
  "Get_Calibrate_Switch": {"scpi": ":CALibrate:SWITch?", "subsystem": "CAL"},
  "Get_Calibrate_Time": {"scpi": ":CALibrate:TIME?", "subsystem": "CAL"},

  // CHANNEL
  "Get_Channel_Coupling": {"scpi": ":CHANNEL1:COUPLING?", "description": "Receiving Information from the Instrument", "subsystem": "CHANNEL"},
  "Get_Channel_Range": {"scpi": ":CHANNEL1:RANGE?", "description": "Address Varies According to Configuration", "subsystem": "CHANNEL"},

  // Common
  "Get_Ese": {"scpi": "*ESE?", "subsystem": "Common"},
  "Get_Esr": {"scpi": "*ESR?", "subsystem": "Common"},
  "Get_Lrn": {"scpi": "*LRN?", "subsystem": "Common"},
  "Get_Opc": {"scpi": "*OPC?", "subsystem": "Common"},
  "Get_Opt": {"scpi": "*OPT?", "subsystem": "Common"},
  "Get_Sre": {"scpi": "*SRE?", "subsystem": "Common"},
  "Get_Stb": {"scpi": "*STB?", "subsystem": "Common"},
  "Get_Tst": {"scpi": "*TST?", "subsystem": "Common"},

  // DISP
  "Get_Display_Data": {"scpi": ":DISPlay:DATA?", "subsystem": "DISP"},
  "Get_Display_Label": {"scpi": ":DISPlay:LABel?", "subsystem": "DISP"},
  "Get_Display_Persistence": {"scpi": ":DISPlay:PERSistence?", "subsystem": "DISP"},
  "Get_Display_Source": {"scpi": ":DISPlay:SOURce?", "subsystem": "DISP"},
  "Get_Display_Vectors": {"scpi": ":DISPlay:VECTors?", "subsystem": "DISP"},

  // EXT
  "Get_External_Bwlimit": {"scpi": ":EXTernal:BWLimit?", "subsystem": "EXT"},
  "Get_External_Impedance": {"scpi": ":EXTernal:IMPedance?", "subsystem": "EXT"},
  "Get_External_Probe": {"scpi": ":EXTernal:PROBe?", "subsystem": "EXT"},
  "Get_External_Protection": {"scpi": ":EXTernal:PROTection?", "subsystem": "EXT"},
  "Get_External_Range": {"scpi": ":EXTernal:RANGe?", "subsystem": "EXT"},
  "Get_External_Units": {"scpi": ":EXTernal:UNITs?", "subsystem": "EXT"},

  // FUNC
  "Get_Function_Center": {"scpi": ":FUNCtion:CENTer?", "subsystem": "FUNC"},
  "Get_Function_Display": {"scpi": ":FUNCtion:DISPlay?", "description": "Obsolete and Discontinued Commands", "subsystem": "FUNC"},
  "Get_Function_Offset": {"scpi": ":FUNCtion:OFFSet?", "subsystem": "FUNC"},
  "Get_Function_Operation": {"scpi": ":FUNCtion:OPERation?", "subsystem": "FUNC"},
  "Get_Function_Range": {"scpi": ":FUNCtion:RANGe?", "subsystem": "FUNC"},
  "Get_Function_Reference": {"scpi": ":FUNCtion:REFerence?", "subsystem": "FUNC"},
  "Get_Function_Source": {"scpi": ":FUNCtion:SOURce?", "subsystem": "FUNC"},
  "Get_Function_Span": {"scpi": ":FUNCtion:SPAN?", "subsystem": "FUNC"},
  "Get_Function_Window": {"scpi": ":FUNCtion:WINDow?", "subsystem": "FUNC"},

  // HARD
  "Get_Hardcopy_Factors": {"scpi": ":HARDcopy:FACTors?", "subsystem": "HARD"},
  "Get_Hardcopy_Ffeed": {"scpi": ":HARDcopy:FFEed?", "subsystem": "HARD"},
  "Get_Hardcopy_Format": {"scpi": ":HARDcopy:FORMat?", "description": "Obsolete and Discontinued Commands", "subsystem": "HARD"},
  "Get_Hardcopy_Grayscale": {"scpi": ":HARDcopy:GRAYscale?", "subsystem": "HARD"},

  // MAR
  "Get_Marker_Xdelta": {"scpi": ":MARker:XDELta?", "subsystem": "MAR"},

  // MARK
  "Get_Marker_Mode": {"scpi": ":MARKer:MODE?", "subsystem": "MARK"},

  // MEAS
  "Get_Measure_Count": {"scpi": "MEASure:COUNter?", "subsystem": "MEAS"},
  "Get_Measure_Delay": {"scpi": ":MEASure:DELay?", "subsystem": "MEAS"},
  "Get_Measure_Falltime": {"scpi": ":MEASure:FALLtime?", "subsystem": "MEAS"},
  "Get_Measure_Nwidth": {"scpi": ":MEASure:NWIDth?", "subsystem": "MEAS"},
  "Get_Measure_Overshoot": {"scpi": ":MEASure:OVERshoot?", "subsystem": "MEAS"},
  "Get_Measure_Phase": {"scpi": ":MEASure:PHASe?", "subsystem": "MEAS"},
  "Get_Measure_Preshoot": {"scpi": ":MEASure:PREShoot?", "subsystem": "MEAS"},
  "Get_Measure_Pwidth": {"scpi": ":MEASure:PWIDth?", "subsystem": "MEAS"},
  "Get_Measure_Show": {"scpi": ":MEASure:SHOW?", "subsystem": "MEAS"},
  "Get_Measure_Source": {"scpi": ":MEASure:SOURce?", "subsystem": "MEAS"},
  "Get_Measure_Tedge": {"scpi": ":MEASure:TEDGe?", "subsystem": "MEAS"},
  "Get_Measure_Tvalue": {"scpi": ":MEASure:TVALue?", "subsystem": "MEAS"},
  "Get_Measure_Vamplitude": {"scpi": ":MEASure:VAMPlitude?", "subsystem": "MEAS"},
  "Get_Measure_Vbase": {"scpi": ":MEASure:VBASe?", "subsystem": "MEAS"},
  "Get_Measure_Vtime": {"scpi": ":MEASure:VTIMe?", "subsystem": "MEAS"},
  "Get_Measure_Vtop": {"scpi": ":MEASure:VTOP?", "subsystem": "MEAS"},
  "Get_Measure_Xmax": {"scpi": ":MEASure:XMAX?", "subsystem": "MEAS"},
  "Get_Measure_Xmin": {"scpi": ":MEASure:XMIN?", "subsystem": "MEAS"},

  // MEASURE
  "Get_Measure_Risetime": {"scpi": ":MEASURE:RISETIME?", "description": "Query Command", "subsystem": "MEASURE"},

  // PROB
  "Get_Probe_Skew": {"scpi": "PROBe:SKEW?", "subsystem": "PROB"},

  // SYST
  "Get_System_Date": {"scpi": ":SYSTem:DATE?", "subsystem": "SYST"},
  "Get_System_Lock": {"scpi": ":SYSTem:LOCK?", "subsystem": "SYST"},
  "Get_System_Time": {"scpi": ":SYSTem:TIME?", "subsystem": "SYST"},

  // SYSTEM
  "Get_System_Dsp": {"scpi": "SYSTEM:DSP?", "description": "Message Queue", "subsystem": "SYSTEM"},

  // TIM
  "Get_Timebase_Mode": {"scpi": ":TIMebase:MODE?", "subsystem": "TIM"},
  "Get_Timebase_Position": {"scpi": ":TIMebase:POSition?", "subsystem": "TIM"},
  "Get_Timebase_Range": {"scpi": ":TIMebase:RANGe?", "subsystem": "TIM"},
  "Get_Timebase_Reference": {"scpi": ":TIMebase:REFerence?", "subsystem": "TIM"},
  "Get_Timebase_Scale": {"scpi": ":TIMebase:SCALe?", "subsystem": "TIM"},
  "Get_Timebase_Window_Position": {"scpi": ":TIMebase:WINDow:POSition?", "subsystem": "TIM"},
  "Get_Timebase_Window_Range": {"scpi": ":TIMebase:WINDow:RANGe?", "subsystem": "TIM"},
  "Get_Timebase_Window_Scale": {"scpi": ":TIMebase:WINDow:SCALe?", "subsystem": "TIM"},

  // TRIG
  "Get_Trigger_Can_Acknowledge": {"scpi": ":TRIGger:CAN:ACKNowledge?", "subsystem": "TRIG"},
  "Get_Trigger_Can_Pattern_Data": {"scpi": ":TRIGger:CAN:PATTern:DATA?", "subsystem": "TRIG"},
  "Get_Trigger_Can_Pattern_Id": {"scpi": ":TRIGger:CAN:PATTern:ID?", "description": "Table 5-1", "subsystem": "TRIG"},
  "Get_Trigger_Can_Pattern_Id_Mode": {"scpi": ":TRIGger:CAN:PATTern:ID:MODE?", "subsystem": "TRIG"},
  "Get_Trigger_Can_Samplepoint": {"scpi": ":TRIGger:CAN:SAMPlepoint?", "subsystem": "TRIG"},
  "Get_Trigger_Can_Signal_Baudrate": {"scpi": ":TRIGger:CAN:SIGNal:BAUDrate?", "subsystem": "TRIG"},
  "Get_Trigger_Can_Source": {"scpi": ":TRIGger:CAN:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Can_Trigger": {"scpi": ":TRIGger:CAN:TRIGer?", "subsystem": "TRIG"},
  "Get_Trigger_Coupling": {"scpi": ":TRIGger:COUPling?", "subsystem": "TRIG"},
  "Get_Trigger_Duration_Greaterthan": {"scpi": ":TRIGger:DURation:GREaterthan?", "subsystem": "TRIG"},
  "Get_Trigger_Duration_Lessthan": {"scpi": ":TRIGger:DURation:LESSthan?", "subsystem": "TRIG"},
  "Get_Trigger_Duration_Pattern": {"scpi": ":TRIGger:DURation:PATTern?", "subsystem": "TRIG"},
  "Get_Trigger_Duration_Qualifier": {"scpi": ":TRIGger:DURation:QUALifier?", "subsystem": "TRIG"},
  "Get_Trigger_Duration_Range": {"scpi": ":TRIGger:DURation:RANGe?", "subsystem": "TRIG"},
  "Get_Trigger_Edge_Level": {"scpi": ":TRIGger:EDGE:LEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Edge_Slope": {"scpi": ":TRIGger:EDGE:SLOPe?", "subsystem": "TRIG"},
  "Get_Trigger_Edge_Source": {"scpi": ":TRIGger:EDGE:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Glitch_Greaterthan": {"scpi": ":TRIGger:GLITch:GREaterthan?", "subsystem": "TRIG"},
  "Get_Trigger_Glitch_Lessthan": {"scpi": ":TRIGger:GLITch:LESSthan?", "subsystem": "TRIG"},
  "Get_Trigger_Glitch_Level": {"scpi": ":TRIGger:GLITch:LEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Glitch_Polarity": {"scpi": ":TRIGger:GLITch:POLarity?", "subsystem": "TRIG"},
  "Get_Trigger_Glitch_Qualifier": {"scpi": ":TRIGger:GLITch:QUALifier?", "subsystem": "TRIG"},
  "Get_Trigger_Glitch_Range": {"scpi": ":TRIGger:GLITch:RANGe?", "subsystem": "TRIG"},
  "Get_Trigger_Glitch_Source": {"scpi": ":TRIGger:GLITch:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Hfreject": {"scpi": ":TRIGger:HFReject?", "subsystem": "TRIG"},
  "Get_Trigger_Holdoff": {"scpi": ":TRIGger:HOLDoff?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Pattern_Address": {"scpi": ":TRIGger:IIC:PATTern:ADDRess?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Pattern_Data": {"scpi": ":TRIGger:IIC:PATTern:DATA?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Trigger_Qualifier": {"scpi": ":TRIGger:IIC:TRIGger:QUALifer?", "subsystem": "TRIG"},
  "Get_Trigger_Lin_Signal_Baudrate": {"scpi": ":TRIGger:LIN:SIGNal:BAUDrate?", "subsystem": "TRIG"},
  "Get_Trigger_Lin_Source": {"scpi": ":TRIGger:LIN:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Lin_Trigger": {"scpi": ":TRIGger:LIN:TRIGger?", "subsystem": "TRIG"},
  "Get_Trigger_Mode": {"scpi": ":TRIGger:MODE?", "subsystem": "TRIG"},
  "Get_Trigger_Nreject": {"scpi": ":TRIGger:NREJect?", "subsystem": "TRIG"},
  "Get_Trigger_Pattern": {"scpi": ":TRIGger:PATTern?", "subsystem": "TRIG"},
  "Get_Trigger_Reject": {"scpi": ":TRIGger:REJect?", "subsystem": "TRIG"},
  "Get_Trigger_Sequence_Count": {"scpi": ":TRIGger:SEQuence:COUNt?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Clock_Slope": {"scpi": ":TRIGger:SPI:CLOCk:SLOPe?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Clock_Timebase": {"scpi": ":TRIGger:SPI:CLOCk:TIMeout?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Frame": {"scpi": ":TRIGger:SPI:FRAMing?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Pattern_Data": {"scpi": ":TRIGger:SPI:PATTern:DATA?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Pattern_Width": {"scpi": ":TRIGger:SPI:PATTern:WIDth?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Source_Clock": {"scpi": ":TRIGger:SPI:SOURce:CLOCk?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Source_Data": {"scpi": ":TRIGger:SPI:SOURce:DATA?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Source_Frame": {"scpi": ":TRIGger:SPI:SOURce:FRAMe?", "subsystem": "TRIG"},
  "Get_Trigger_Sweep": {"scpi": ":TRIGger:SWEep?", "subsystem": "TRIG"},
  "Get_Trigger_Tv_Line": {"scpi": ":TRIGger:TV:LINE?", "subsystem": "TRIG"},
  "Get_Trigger_Tv_Mode": {"scpi": ":TRIGger:TV:MODE?", "subsystem": "TRIG"},
  "Get_Trigger_Tv_Polarity": {"scpi": ":TRIGger:TV:POLarity?", "subsystem": "TRIG"},
  "Get_Trigger_Tv_Source": {"scpi": ":TRIGger:TV:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Tv_Standard": {"scpi": ":TRIGger:TV:STANdard?", "subsystem": "TRIG"},
  "Get_Trigger_Tv_Tvmode": {"scpi": ":TRIGger:TV:TVMODE?", "subsystem": "TRIG"},
  "Get_Trigger_Usb_Source_Dminus": {"scpi": ":TRIGger:USB:SOURce:DMINus?", "subsystem": "TRIG"},
  "Get_Trigger_Usb_Source_Dplus": {"scpi": ":TRIGger:USB:SOURce:DPLus?", "subsystem": "TRIG"},
  "Get_Trigger_Usb_Speed": {"scpi": ":TRIGger:USB:SPEed?", "subsystem": "TRIG"},
  "Get_Trigger_Usb_Trigger": {"scpi": ":TRIGger:USB:TRIGger?", "subsystem": "TRIG"},

  // TRIGGER
  "Get_Trigger_Sequence_Find": {"scpi": ":TRIGGER:SEQuence:FIND?", "subsystem": "TRIGGER"},
  "Get_Trigger_Sequence_Reset": {"scpi": ":TRIGGER:SEQuence:RESet?", "subsystem": "TRIGGER"},
  "Get_Trigger_Sequence_Timebase": {"scpi": ":TRIGGER:SEQuence:TIMer?", "subsystem": "TRIGGER"},
  "Get_Trigger_Sequence_Trigger": {"scpi": ":TRIGGER:SEQuence:TRIGger?", "subsystem": "TRIGGER"},

  // WAV
  "Get_Waveform_Byteorder": {"scpi": ":WAVeform:BYTeorder?", "subsystem": "WAV"},
  "Get_Waveform_Count": {"scpi": ":WAVeform:COUNt?", "subsystem": "WAV"},
  "Get_Waveform_Format": {"scpi": ":WAVeform:FORMat?", "subsystem": "WAV"},
  "Get_Waveform_Points": {"scpi": ":WAVeform:POINts?", "subsystem": "WAV"},
  "Get_Waveform_Source": {"scpi": ":WAVeform:SOURce?", "subsystem": "WAV"},
  "Get_Waveform_Unsigned": {"scpi": ":WAVeform:UNSigned?", "subsystem": "WAV"},
  "Get_Waveform_View": {"scpi": ":WAVeform:VIEW?", "subsystem": "WAV"},
  "Get_Waveform_Xincrement": {"scpi": ":WAVeform:XINCrement?", "subsystem": "WAV"},
  "Get_Waveform_Xorigin": {"scpi": ":WAVeform:XORigin?", "subsystem": "WAV"},
  "Get_Waveform_Xreference": {"scpi": ":WAVeform:XREFerence?", "subsystem": "WAV"},
  "Get_Waveform_Yincrement": {"scpi": ":WAVeform:YINCrement?", "subsystem": "WAV"},
  "Get_Waveform_Yorigin": {"scpi": ":WAVeform:YORigin?", "subsystem": "WAV"},
  "Get_Waveform_Yreference": {"scpi": ":WAVeform:YREFerence?", "subsystem": "WAV"},
}
```

## Scope — DS1104Z

Source: `MSO1000Z_DS1000Z_ProgrammingGuide_EN.md`; `DS1000Z_ProgrammingGuide_EN.md`

687 missing — SET 294, DO 47, NAB 346. The table has 73.

### SET — 294

```json
"set": {
  // ACQ
  "Set_Acquire_Averages": {"scpi": ":ACQuire:AVERages <value>", "subsystem": "ACQ"},
  "Set_Acquire_Mdepth": {"scpi": ":ACQuire:MDEPth <value>", "subsystem": "ACQ"},

  // CHAN
  "Set_Channel_Invert": {"scpi": ":CHANnel1:INVert <value>", "subsystem": "CHAN"},
  "Set_Channel_Range": {"scpi": ":CHANnel1:RANGe <value>", "subsystem": "CHAN"},
  "Set_Channel_Tcalibrate": {"scpi": ":CHANnel1:TCAL <value>", "subsystem": "CHAN"},
  "Set_Channel_Vernier": {"scpi": ":CHANnel1:VERNier <value>", "subsystem": "CHAN"},

  // CONF
  "Set_Config_Endian": {"scpi": ":CONFig:ENDian <value>", "subsystem": "CONF"},
  "Set_Config_Format": {"scpi": ":CONFig:FORMat <value>", "subsystem": "CONF"},
  "Set_Config_Label": {"scpi": ":CONFig:LABel <value>", "description": "Commands", "subsystem": "CONF"},
  "Set_Config_Line": {"scpi": ":CONFig:LINE <value>", "subsystem": "CONF"},
  "Set_Config_Width": {"scpi": ":CONFig:WIDth <value>", "subsystem": "CONF"},

  // CURS
  "Set_Cursor_Manual_Ax": {"scpi": ":CURSor:MANual:AX <value>", "subsystem": "CURS"},
  "Set_Cursor_Manual_Ay": {"scpi": ":CURSor:MANual:AY <value>", "subsystem": "CURS"},
  "Set_Cursor_Manual_Bx": {"scpi": ":CURSor:MANual:BX <value>", "subsystem": "CURS"},
  "Set_Cursor_Manual_By": {"scpi": ":CURSor:MANual:BY <value>", "subsystem": "CURS"},
  "Set_Cursor_Manual_Source": {"scpi": ":CURSor:MANual:SOURce <value>", "subsystem": "CURS"},
  "Set_Cursor_Manual_Tunit": {"scpi": ":CURSor:MANual:TUNit <value>", "subsystem": "CURS"},
  "Set_Cursor_Manual_Vunit": {"scpi": ":CURSor:MANual:VUNit <value>", "subsystem": "CURS"},
  "Set_Cursor_Mode": {"scpi": ":CURSor:MODE <value>", "subsystem": "CURS"},
  "Set_Cursor_Track_Ax": {"scpi": ":CURSor:TRACk:AX <value>", "subsystem": "CURS"},
  "Set_Cursor_Track_Bx": {"scpi": ":CURSor:TRACk:BX <value>", "subsystem": "CURS"},
  "Set_Cursor_Track_Source": {"scpi": ":CURSor:TRACk:SOURce<chan> <value>", "subsystem": "CURS"},
  "Set_Cursor_Xy_Ax": {"scpi": ":CURSor:XY:AX <value>", "subsystem": "CURS"},
  "Set_Cursor_Xy_Ay": {"scpi": ":CURSor:XY:AY <value>", "subsystem": "CURS"},
  "Set_Cursor_Xy_Bx": {"scpi": ":CURSor:XY:BX <value>", "subsystem": "CURS"},
  "Set_Cursor_Xy_By": {"scpi": ":CURSor:XY:BY <value>", "subsystem": "CURS"},

  // Common
  "Set_Ese": {"scpi": "*ESE <value>", "subsystem": "Common"},
  "Set_Sre": {"scpi": "*SRE <value>", "subsystem": "Common"},

  // DATA
  "Set_Data_Points": {"scpi": ":DATA:POINts <value>", "subsystem": "DATA"},
  "Set_Data_Points_Internal": {"scpi": ":DATA:POINts:INTerpolate <value>", "subsystem": "DATA"},
  "Set_Data_Value": {"scpi": ":DATA:VALue <value>", "subsystem": "DATA"},

  // DEC
  "Set_Decoder_Config_Endian": {"scpi": ":DECoder1:CONFig:ENDian <value>", "subsystem": "DEC"},
  "Set_Decoder_Config_Format": {"scpi": ":DECoder1:CONFig:FORMat <value>", "subsystem": "DEC"},
  "Set_Decoder_Config_Label": {"scpi": ":DECoder1:CONFig:LABel <value>", "subsystem": "DEC"},
  "Set_Decoder_Config_Line": {"scpi": ":DECoder1:CONFig:LINE <value>", "subsystem": "DEC"},
  "Set_Decoder_Config_Width": {"scpi": ":DECoder1:CONFig:WIDth <value>", "subsystem": "DEC"},
  "Set_Decoder_Display": {"scpi": ":DECoder1:DISPlay <value>", "subsystem": "DEC"},
  "Set_Decoder_Format": {"scpi": ":DECoder1:FORMat <value>", "subsystem": "DEC"},
  "Set_Decoder_Iic_Address": {"scpi": ":DECoder1:IIC:ADDRess <value>", "subsystem": "DEC"},
  "Set_Decoder_Iic_Clk": {"scpi": ":DECoder1:IIC:CLK <value>", "subsystem": "DEC"},
  "Set_Decoder_Iic_Data": {"scpi": ":DECoder1:IIC:DATA <value>", "subsystem": "DEC"},
  "Set_Decoder_Mode": {"scpi": ":DECoder1:MODE <value>", "subsystem": "DEC"},
  "Set_Decoder_Parallel_Bitx": {"scpi": ":DECoder1:PARallel:BITX <value>", "subsystem": "DEC"},
  "Set_Decoder_Parallel_Ccompensation": {"scpi": ":DECoder1:PARallel:CCOMpensation <value>", "subsystem": "DEC"},
  "Set_Decoder_Parallel_Clk": {"scpi": ":DECoder1:PARallel:CLK <value>", "subsystem": "DEC"},
  "Set_Decoder_Parallel_Edge": {"scpi": ":DECoder1:PARallel:EDGE <value>", "subsystem": "DEC"},
  "Set_Decoder_Parallel_Nreject": {"scpi": ":DECoder1:PARallel:NREJect <value>", "subsystem": "DEC"},
  "Set_Decoder_Parallel_Nrtime": {"scpi": ":DECoder1:PARallel:NRTime <value>", "subsystem": "DEC"},
  "Set_Decoder_Parallel_Plot": {"scpi": ":DECoder1:PARallel:PLOT <value>", "subsystem": "DEC"},
  "Set_Decoder_Parallel_Polarity": {"scpi": ":DECoder1:PARallel:POLarity <value>", "subsystem": "DEC"},
  "Set_Decoder_Parallel_Source": {"scpi": ":DECoder1:PARallel:SOURce <value>", "subsystem": "DEC"},
  "Set_Decoder_Parallel_Width": {"scpi": ":DECoder1:PARallel:WIDTh <value>", "subsystem": "DEC"},
  "Set_Decoder_Positive": {"scpi": ":DECoder1:POSition <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Clk": {"scpi": ":DECoder1:SPI:CLK <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Csrc": {"scpi": ":DECoder1:SPI:CS <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Edge": {"scpi": ":DECoder1:SPI:EDGE <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Endian": {"scpi": ":DECoder1:SPI:ENDian <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Miso": {"scpi": ":DECoder1:SPI:MISO <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Mode": {"scpi": ":DECoder1:SPI:MODE <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Mosi": {"scpi": ":DECoder1:SPI:MOSI <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Polarity": {"scpi": ":DECoder1:SPI:POLarity <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Select": {"scpi": ":DECoder1:SPI:SELect <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Timebase": {"scpi": ":DECoder1:SPI:TIMeout <value>", "subsystem": "DEC"},
  "Set_Decoder_Spi_Width": {"scpi": ":DECoder1:SPI:WIDTh <value>", "subsystem": "DEC"},
  "Set_Decoder_Threshold_Channel": {"scpi": ":DECoder1:THREshold:CHANnel<chan> <value>", "subsystem": "DEC"},
  "Set_Decoder_Uart_Baud": {"scpi": ":DECoder1:UART:BAUD <value>", "subsystem": "DEC"},
  "Set_Decoder_Uart_Endian": {"scpi": ":DECoder1:UART:ENDian <value>", "subsystem": "DEC"},
  "Set_Decoder_Uart_Parallel": {"scpi": ":DECoder1:UART:PARity <value>", "subsystem": "DEC"},
  "Set_Decoder_Uart_Polarity": {"scpi": ":DECoder1:UART:POLarity <value>", "subsystem": "DEC"},
  "Set_Decoder_Uart_Rx": {"scpi": ":DECoder1:UART:RX <value>", "subsystem": "DEC"},
  "Set_Decoder_Uart_Stop": {"scpi": ":DECoder1:UART:STOP <value>", "subsystem": "DEC"},
  "Set_Decoder_Uart_Tx": {"scpi": ":DECoder1:UART:TX <value>", "subsystem": "DEC"},
  "Set_Decoder_Uart_Width": {"scpi": ":DECoder1:UART:WIDTh <value>", "subsystem": "DEC"},

  // DISP
  "Set_Display_Gbrightness": {"scpi": ":DISPlay:GBRightness <value>", "subsystem": "DISP"},
  "Set_Display_Grading_Time": {"scpi": ":DISPlay:GRADing:TIME <value>", "subsystem": "DISP"},
  "Set_Display_Grid": {"scpi": ":DISPlay:GRID <value>", "subsystem": "DISP"},
  "Set_Display_Wbrightness": {"scpi": ":DISPlay:WBRightness <value>", "subsystem": "DISP"},

  // ETAB
  "Set_Etable_Color": {"scpi": ":ETABle1:COLumn <value>", "subsystem": "ETAB"},
  "Set_Etable_Display": {"scpi": ":ETABle1:DISP <value>", "subsystem": "ETAB"},
  "Set_Etable_Format": {"scpi": ":ETABle1:FORMat <value>", "subsystem": "ETAB"},
  "Set_Etable_Row": {"scpi": ":ETABle1:ROW <value>", "subsystem": "ETAB"},
  "Set_Etable_Sort": {"scpi": ":ETABle1:SORT <value>", "subsystem": "ETAB"},
  "Set_Etable_View": {"scpi": ":ETABle1:VIEW <value>", "subsystem": "ETAB"},

  // FREQ
  "Set_Frequency_Fixed": {"scpi": ":FREQuency:FIXed <value>", "subsystem": "FREQ"},

  // FUNC
  "Set_Function_Ramp_Symmetry": {"scpi": ":FUNCtion:RAMP:SYMMetry <value>", "subsystem": "FUNC"},
  "Set_Function_Shape": {"scpi": ":FUNCtion:SHAPe <value>", "subsystem": "FUNC"},
  "Set_Function_Wrecord_Enable": {"scpi": ":FUNCtion:WRECord:ENABle <value>", "subsystem": "FUNC"},
  "Set_Function_Wrecord_Fend": {"scpi": ":FUNCtion:WRECord:FEND <value>", "subsystem": "FUNC"},
  "Set_Function_Wrecord_Finterval": {"scpi": ":FUNCtion:WRECord:FINTerval <value>", "subsystem": "FUNC"},
  "Set_Function_Wrecord_Operator": {"scpi": ":FUNCtion:WRECord:OPERate <value>", "subsystem": "FUNC"},
  "Set_Function_Wrecord_Prompt": {"scpi": ":FUNCtion:WRECord:PROMpt <value>", "subsystem": "FUNC"},
  "Set_Function_Wreplay_Direction": {"scpi": ":FUNCtion:WREPlay:DIRection <value>", "subsystem": "FUNC"},
  "Set_Function_Wreplay_Fcurrent": {"scpi": ":FUNCtion:WREPlay:FCURrent <value>", "subsystem": "FUNC"},
  "Set_Function_Wreplay_Fend": {"scpi": ":FUNCtion:WREPlay:FEND <value>", "subsystem": "FUNC"},
  "Set_Function_Wreplay_Finterval": {"scpi": ":FUNCtion:WREPlay:FINTerval <value>", "subsystem": "FUNC"},
  "Set_Function_Wreplay_Fstart": {"scpi": ":FUNCtion:WREPlay:FSTart <value>", "subsystem": "FUNC"},
  "Set_Function_Wreplay_Mode": {"scpi": ":FUNCtion:WREPlay:MODE <value>", "subsystem": "FUNC"},
  "Set_Function_Wreplay_Operator": {"scpi": ":FUNCtion:WREPlay:OPERate <value>", "subsystem": "FUNC"},

  // IIC
  "Set_Iic_Address": {"scpi": ":IIC:ADDRess <value>", "subsystem": "IIC"},
  "Set_Iic_Clk": {"scpi": ":IIC:CLK <value>", "subsystem": "IIC"},
  "Set_Iic_Data": {"scpi": ":IIC:DATA <value>", "subsystem": "IIC"},

  // IMM
  "Set_Immediate_Offset": {"scpi": ":IMMediate:OFFSet <value>", "subsystem": "IMM"},

  // LA
  "Set_La_Active": {"scpi": ":LA:ACTive <value>", "subsystem": "LA"},
  "Set_La_Digital_Display": {"scpi": ":LA:DIGital3:DISPlay <value>", "subsystem": "LA"},
  "Set_La_Digital_Positive": {"scpi": ":LA:DIGital1:POSition <value>", "subsystem": "LA"},
  "Set_La_Display": {"scpi": ":LA:DISPlay <value>", "subsystem": "LA"},
  "Set_La_Pod_Display": {"scpi": ":LA:POD1:DISPlay <value>", "subsystem": "LA"},
  "Set_La_Pod_Threshold": {"scpi": ":LA:POD1:THReshold <value>", "subsystem": "LA"},
  "Set_La_Size": {"scpi": ":LA:SIZE <value>", "subsystem": "LA"},
  "Set_La_Statistic": {"scpi": ":LA:STATe <value>", "subsystem": "LA"},
  "Set_La_Tcalibrate": {"scpi": ":LA:TCALibrate <value>", "subsystem": "LA"},

  // MASK
  "Set_Mask_Enable": {"scpi": ":MASK:ENABle <value>", "subsystem": "MASK"},
  "Set_Mask_Mdisplay": {"scpi": ":MASK:MDISplay <value>", "subsystem": "MASK"},
  "Set_Mask_Operator": {"scpi": ":MASK:OPERate <value>", "subsystem": "MASK"},
  "Set_Mask_Output": {"scpi": ":MASK:OUTPut <value>", "subsystem": "MASK"},
  "Set_Mask_Sooutput": {"scpi": ":MASK:SOOutput <value>", "subsystem": "MASK"},
  "Set_Mask_Source": {"scpi": ":MASK:SOURce <value>", "subsystem": "MASK"},

  // MATH
  "Set_Math_Display": {"scpi": ":MATH:DISPlay <value>", "subsystem": "MATH"},
  "Set_Math_Fft_Hcenter": {"scpi": ":MATH:FFT:HCENter <value>", "subsystem": "MATH"},
  "Set_Math_Fft_Hscale": {"scpi": ":MATH:FFT:HSCale <value>", "subsystem": "MATH"},
  "Set_Math_Fft_Mode": {"scpi": ":MATH:FFT:MODE <value>", "description": "Commands", "subsystem": "MATH"},
  "Set_Math_Fft_Source": {"scpi": ":MATH:FFT:SOURce <value>", "description": "Commands", "subsystem": "MATH"},
  "Set_Math_Fft_Split": {"scpi": ":MATH:FFT:SPLit <value>", "subsystem": "MATH"},
  "Set_Math_Fft_Units": {"scpi": ":MATH:FFT:UNIT <value>", "subsystem": "MATH"},
  "Set_Math_Fft_Windows": {"scpi": ":MATH:FFT:WINDow <value>", "subsystem": "MATH"},
  "Set_Math_Invert": {"scpi": ":MATH:INVert <value>", "subsystem": "MATH"},
  "Set_Math_Lsou": {"scpi": ":MATH:LSOUrce<chan> <value>", "subsystem": "MATH"},
  "Set_Math_Offset": {"scpi": ":MATH:OFFSet <value>", "subsystem": "MATH"},
  "Set_Math_Operator": {"scpi": ":MATH:OPERator <value>", "subsystem": "MATH"},
  "Set_Math_Option_Ascale": {"scpi": ":MATH:OPTion:ASCale <value>", "subsystem": "MATH"},
  "Set_Math_Option_Distance": {"scpi": ":MATH:OPTion:DIStance <value>", "subsystem": "MATH"},
  "Set_Math_Option_Endian": {"scpi": ":MATH:OPTion:END <value>", "subsystem": "MATH"},
  "Set_Math_Option_Fx_Operator": {"scpi": ":MATH:OPTion:FX:OPERator <value>", "subsystem": "MATH"},
  "Set_Math_Option_Fx_Source": {"scpi": ":MATH:OPTion:FX:SOURce<chan> <value>", "description": "Commands", "subsystem": "MATH"},
  "Set_Math_Option_Invert": {"scpi": ":MATH:OPTion:INVert <value>", "subsystem": "MATH"},
  "Set_Math_Option_Sensitivity": {"scpi": ":MATH:OPTion:SENSitivity <value>", "subsystem": "MATH"},
  "Set_Math_Option_Start": {"scpi": ":MATH:OPTion:STARt <value>", "subsystem": "MATH"},
  "Set_Math_Option_Threshold": {"scpi": ":MATH:OPTion:THReshold<chan> <value>", "subsystem": "MATH"},
  "Set_Math_Scale": {"scpi": ":MATH:SCALe <value>", "subsystem": "MATH"},
  "Set_Math_Source": {"scpi": ":MATH:SOURce<chan> <value>", "subsystem": "MATH"},

  // MEAS
  "Set_Measure_Adisplay": {"scpi": ":MEASure:ADISplay <value>", "subsystem": "MEAS"},
  "Set_Measure_Amsource": {"scpi": ":MEASure:AMSource <value>", "subsystem": "MEAS"},
  "Set_Measure_Counter_Source": {"scpi": ":MEASure:COUNter:SOURce <value>", "subsystem": "MEAS"},
  "Set_Measure_Statistic_Item": {"scpi": ":MEASure:STATistic:ITEM <value>", "description": "Commands", "subsystem": "MEAS"},
  "Set_Measure_Statistic_Mode": {"scpi": ":MEASure:STATistic:MODE <value>", "description": "Commands", "subsystem": "MEAS"},

  // MOD
  "Set_Mod_Am": {"scpi": ":MOD:AM <value>", "subsystem": "MOD"},
  "Set_Mod_Am_Depth": {"scpi": ":MOD:AM:DEPTh <value>", "subsystem": "MOD"},
  "Set_Mod_Am_Internal_Frequency": {"scpi": ":MOD:AM:INTernal:FREQuency <value>", "subsystem": "MOD"},
  "Set_Mod_Am_Internal_Function": {"scpi": ":MOD:AM:INTernal:FUNCtion <value>", "subsystem": "MOD"},
  "Set_Mod_Fm": {"scpi": ":MOD:FM <value>", "subsystem": "MOD"},
  "Set_Mod_Fm_Deviation": {"scpi": ":MOD:FM:DEVIation <value>", "subsystem": "MOD"},
  "Set_Mod_Fm_Internal_Frequency": {"scpi": ":MOD:FM:INTernal:FREQuency <value>", "subsystem": "MOD"},
  "Set_Mod_Fm_Internal_Function": {"scpi": ":MOD:FM:INTernal:FUNCtion <value>", "subsystem": "MOD"},
  "Set_Mod_Statistic": {"scpi": ":MOD:STATe <value>", "subsystem": "MOD"},
  "Set_Mod_Type": {"scpi": ":MOD:TYPe <value>", "subsystem": "MOD"},

  // OUTP
  "Set_Output_Impedance": {"scpi": ":OUTPut:IMPedance <value>", "subsystem": "OUTP"},

  // PAR
  "Set_Parallel_Bitx": {"scpi": ":PARallel:BITX <value>", "subsystem": "PAR"},
  "Set_Parallel_Ccompensation": {"scpi": ":PARallel:CCOMpensation <value>", "subsystem": "PAR"},
  "Set_Parallel_Clk": {"scpi": ":PARallel:CLK <value>", "subsystem": "PAR"},
  "Set_Parallel_Edge": {"scpi": ":PARallel:EDGE <value>", "subsystem": "PAR"},
  "Set_Parallel_Nreject": {"scpi": ":PARallel:NREJect <value>", "subsystem": "PAR"},
  "Set_Parallel_Nrtime": {"scpi": ":PARallel:NRTime <value>", "subsystem": "PAR"},
  "Set_Parallel_Plot": {"scpi": ":PARallel:PLOT <value>", "subsystem": "PAR"},
  "Set_Parallel_Polarity": {"scpi": ":PARallel:POLarity <value>", "subsystem": "PAR"},
  "Set_Parallel_Source": {"scpi": ":PARallel:SOURce <value>", "subsystem": "PAR"},
  "Set_Parallel_Width": {"scpi": ":PARallel:WIDTh <value>", "subsystem": "PAR"},

  // PHAS
  "Set_Phase_Adjust": {"scpi": ":PHASe:ADJust <value>", "subsystem": "PHAS"},

  // PULS
  "Set_Pulse_Dcycle": {"scpi": ":PULSe:DCYCle <value>", "subsystem": "PULS"},

  // REF
  "Set_Reference_Color": {"scpi": ":REFerence1:COLor <value>", "subsystem": "REF"},
  "Set_Reference_Display": {"scpi": ":REFerence:DISPlay <value>", "subsystem": "REF"},
  "Set_Reference_Enable": {"scpi": ":REFerence1:ENABle <value>", "subsystem": "REF"},
  "Set_Reference_Source": {"scpi": ":REFerence1:SOURce <value>", "subsystem": "REF"},
  "Set_Reference_Voffset": {"scpi": ":REFerence1:VOFFset <value>", "description": "Commands", "subsystem": "REF"},
  "Set_Reference_Vscale": {"scpi": ":REFerence1:VSCale <value>", "subsystem": "REF"},

  // SPI
  "Set_Spi_Clk": {"scpi": ":SPI:CLK <value>", "subsystem": "SPI"},
  "Set_Spi_Csrc": {"scpi": ":SPI:CS <value>", "subsystem": "SPI"},
  "Set_Spi_Edge": {"scpi": ":SPI:EDGE <value>", "subsystem": "SPI"},
  "Set_Spi_Endian": {"scpi": ":SPI:ENDian <value>", "subsystem": "SPI"},
  "Set_Spi_Miso": {"scpi": ":SPI:MISO <value>", "subsystem": "SPI"},
  "Set_Spi_Mode": {"scpi": ":SPI:MODE <value>", "subsystem": "SPI"},
  "Set_Spi_Mosi": {"scpi": ":SPI:MOSI <value>", "subsystem": "SPI"},
  "Set_Spi_Polarity": {"scpi": ":SPI:POLarity <value>", "subsystem": "SPI"},
  "Set_Spi_Select": {"scpi": ":SPI:SELect <value>", "subsystem": "SPI"},
  "Set_Spi_Timebase": {"scpi": ":SPI:TIMeout <value>", "subsystem": "SPI"},
  "Set_Spi_Width": {"scpi": ":SPI:WIDTh <value>", "subsystem": "SPI"},

  // STOR
  "Set_Storage_Image_Color": {"scpi": ":STORage:IMAGe:COLor <value>", "subsystem": "STOR"},
  "Set_Storage_Image_Invert": {"scpi": ":STORage:IMAGe:INVERT <value>", "subsystem": "STOR"},

  // SYST
  "Set_System_Autoscale": {"scpi": ":SYSTem:AUToscale <value>", "subsystem": "SYST"},
  "Set_System_Beeper": {"scpi": ":SYSTem:BEEPer <value>", "subsystem": "SYST"},
  "Set_System_Language": {"scpi": ":SYSTem:LANGuage <value>", "subsystem": "SYST"},
  "Set_System_Locked": {"scpi": ":SYSTem:LOCKed <value>", "subsystem": "SYST"},
  "Set_System_Pon": {"scpi": ":SYSTem:PON <value>", "subsystem": "SYST"},

  // THRE
  "Set_Threshold_Channel": {"scpi": ":THREshold:CHANnel<chan> <value>", "subsystem": "THRE"},

  // TIM
  "Set_Timebase_Delay_Enable": {"scpi": ":TIMebase:DELay:ENABle <value>", "subsystem": "TIM"},
  "Set_Timebase_Delay_Offset": {"scpi": ":TIMebase:DELay:OFFSet <value>", "subsystem": "TIM"},
  "Set_Timebase_Delay_Scale": {"scpi": ":TIMebase:DELay:SCALe <value>", "description": "Commands", "subsystem": "TIM"},

  // TRIG
  "Set_Trigger_Coupling": {"scpi": ":TRIGger:COUPling <value>", "subsystem": "TRIG"},
  "Set_Trigger_Delay_Sa": {"scpi": ":TRIGger:DELay:SA <value>", "subsystem": "TRIG"},
  "Set_Trigger_Delay_Sb": {"scpi": ":TRIGger:DELay:SB <value>", "subsystem": "TRIG"},
  "Set_Trigger_Delay_Slopa": {"scpi": ":TRIGger:DELay:SLOPA <value>", "subsystem": "TRIG"},
  "Set_Trigger_Delay_Slopb": {"scpi": ":TRIGger:DELay:SLOPB <value>", "subsystem": "TRIG"},
  "Set_Trigger_Delay_Tlower": {"scpi": ":TRIGger:DELay:TLOWer <value>", "subsystem": "TRIG"},
  "Set_Trigger_Delay_Tupper": {"scpi": ":TRIGger:DELay:TUPPer <value>", "subsystem": "TRIG"},
  "Set_Trigger_Delay_Type": {"scpi": ":TRIGger:DELay:TYPe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Duration_Source": {"scpi": ":TRIGger:DURATion:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Duration_Tlower": {"scpi": ":TRIGger:DURATion:TLOWer <value>", "subsystem": "TRIG"},
  "Set_Trigger_Duration_Tupper": {"scpi": ":TRIGger:DURATion:TUPPer <value>", "subsystem": "TRIG"},
  "Set_Trigger_Duration_Type": {"scpi": ":TRIGger:DURATion:TYPe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Duration_When": {"scpi": ":TRIGger:DURATion:WHEN <value>", "subsystem": "TRIG"},
  "Set_Trigger_Holdoff": {"scpi": ":TRIGger:HOLDoff <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Address": {"scpi": ":TRIGger:IIC:ADDRess <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Awidth": {"scpi": ":TRIGger:IIC:AWIDth <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Clevel": {"scpi": ":TRIGger:IIC:CLEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Data": {"scpi": ":TRIGger:IIC:DATA <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Direction": {"scpi": ":TRIGger:IIC:DIRection <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Dlevel": {"scpi": ":TRIGger:IIC:DLEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Scl": {"scpi": ":TRIGger:IIC:SCL <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_Sda": {"scpi": ":TRIGger:IIC:SDA <value>", "subsystem": "TRIG"},
  "Set_Trigger_Iic_When": {"scpi": ":TRIGger:IIC:WHEN <value>", "subsystem": "TRIG"},
  "Set_Trigger_Nedge_Edge": {"scpi": ":TRIGger:NEDGe:EDGE <value>", "subsystem": "TRIG"},
  "Set_Trigger_Nedge_Idle": {"scpi": ":TRIGger:NEDGe:IDLE <value>", "subsystem": "TRIG"},
  "Set_Trigger_Nedge_Level": {"scpi": ":TRIGger:NEDGe:LEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Nedge_Slope": {"scpi": ":TRIGger:NEDGe:SLOPe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Nedge_Source": {"scpi": ":TRIGger:NEDGe:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Nreject": {"scpi": ":TRIGger:NREJect <value>", "subsystem": "TRIG"},
  "Set_Trigger_Pattern_Level": {"scpi": ":TRIGger:PATTern:LEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Pattern_Pattern": {"scpi": ":TRIGger:PATTern:PATTern <value>", "subsystem": "TRIG"},
  "Set_Trigger_Pulse_Level": {"scpi": ":TRIGger:PULSe:LEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Pulse_Lwidth": {"scpi": ":TRIGger:PULSe:LWIDth <value>", "subsystem": "TRIG"},
  "Set_Trigger_Pulse_Source": {"scpi": ":TRIGger:PULSe:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Pulse_Uwidth": {"scpi": ":TRIGger:PULSe:UWIDth <value>", "subsystem": "TRIG"},
  "Set_Trigger_Pulse_When": {"scpi": ":TRIGger:PULSe:WHEN <value>", "subsystem": "TRIG"},
  "Set_Trigger_Pulse_Width": {"scpi": ":TRIGger:PULSe:WIDTh <value>", "subsystem": "TRIG"},
  "Set_Trigger_Runt_Alevel": {"scpi": ":TRIGger:RUNT:ALEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Runt_Blevel": {"scpi": ":TRIGger:RUNT:BLEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Runt_Polarity": {"scpi": ":TRIGger:RUNT:POLarity <value>", "subsystem": "TRIG"},
  "Set_Trigger_Runt_Source": {"scpi": ":TRIGger:RUNT:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Runt_When": {"scpi": ":TRIGger:RUNT:WHEN <value>", "subsystem": "TRIG"},
  "Set_Trigger_Runt_Wlower": {"scpi": ":TRIGger:RUNT:WLOWer <value>", "subsystem": "TRIG"},
  "Set_Trigger_Runt_Wupper": {"scpi": ":TRIGger:RUNT:WUPPer <value>", "subsystem": "TRIG"},
  "Set_Trigger_Shold_Csrc": {"scpi": ":TRIGger:SHOLd:CSrc <value>", "subsystem": "TRIG"},
  "Set_Trigger_Shold_Dsrc": {"scpi": ":TRIGger:SHOLd:DSrc <value>", "subsystem": "TRIG"},
  "Set_Trigger_Shold_Htime": {"scpi": ":TRIGger:SHOLd:HTIMe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Shold_Pattern": {"scpi": ":TRIGger:SHOLd:PATTern <value>", "subsystem": "TRIG"},
  "Set_Trigger_Shold_Slope": {"scpi": ":TRIGger:SHOLd:SLOPe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Shold_Stime": {"scpi": ":TRIGger:SHOLd:STIMe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Shold_Type": {"scpi": ":TRIGger:SHOLd:TYPe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Slope_Alevel": {"scpi": ":TRIGger:SLOPe:ALEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Slope_Blevel": {"scpi": ":TRIGger:SLOPe:BLEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Slope_Source": {"scpi": ":TRIGger:SLOPe:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Slope_Time": {"scpi": ":TRIGger:SLOPe:TIME <value>", "subsystem": "TRIG"},
  "Set_Trigger_Slope_Tlower": {"scpi": ":TRIGger:SLOPe:TLOWer <value>", "subsystem": "TRIG"},
  "Set_Trigger_Slope_Tupper": {"scpi": ":TRIGger:SLOPe:TUPPer <value>", "subsystem": "TRIG"},
  "Set_Trigger_Slope_When": {"scpi": ":TRIGger:SLOPe:WHEN <value>", "subsystem": "TRIG"},
  "Set_Trigger_Slope_Windows": {"scpi": ":TRIGger:SLOPe:WINDow <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Clevel": {"scpi": ":TRIGger:SPI:CLEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Csrc": {"scpi": ":TRIGger:SPI:CS <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Data": {"scpi": ":TRIGger:SPI:DATA <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Dlevel": {"scpi": ":TRIGger:SPI:DLEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Mode": {"scpi": ":TRIGger:SPI:MODE <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Scl": {"scpi": ":TRIGger:SPI:SCL <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Sda": {"scpi": ":TRIGger:SPI:SDA <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Slevel": {"scpi": ":TRIGger:SPI:SLEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Slope": {"scpi": ":TRIGger:SPI:SLOPe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Timebase": {"scpi": ":TRIGger:SPI:TIMeout <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_When": {"scpi": ":TRIGger:SPI:WHEN <value>", "subsystem": "TRIG"},
  "Set_Trigger_Spi_Width": {"scpi": ":TRIGger:SPI:WIDTh <value>", "subsystem": "TRIG"},
  "Set_Trigger_Timebase_Slope": {"scpi": ":TRIGger:TIMeout:SLOPe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Timebase_Source": {"scpi": ":TRIGger:TIMeout:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Timebase_Timebase": {"scpi": ":TRIGger:TIMeout:TIMe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Video_Level": {"scpi": ":TRIGger:VIDeo:LEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Video_Line": {"scpi": ":TRIGger:VIDeo:LINE <value>", "subsystem": "TRIG"},
  "Set_Trigger_Video_Mode": {"scpi": ":TRIGger:VIDeo:MODE <value>", "subsystem": "TRIG"},
  "Set_Trigger_Video_Polarity": {"scpi": ":TRIGger:VIDeo:POLarity <value>", "subsystem": "TRIG"},
  "Set_Trigger_Video_Source": {"scpi": ":TRIGger:VIDeo:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Video_Standard": {"scpi": ":TRIGger:VIDeo:STANdard <value>", "subsystem": "TRIG"},
  "Set_Trigger_Windows_Alevel": {"scpi": ":TRIGger:WINDows:ALEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Windows_Blevel": {"scpi": ":TRIGger:WINDows:BLEVel <value>", "subsystem": "TRIG"},
  "Set_Trigger_Windows_Positive": {"scpi": ":TRIGger:WINDows:POSition <value>", "subsystem": "TRIG"},
  "Set_Trigger_Windows_Slope": {"scpi": ":TRIGger:WINDows:SLOPe <value>", "subsystem": "TRIG"},
  "Set_Trigger_Windows_Source": {"scpi": ":TRIGger:WINDows:SOURce <value>", "subsystem": "TRIG"},
  "Set_Trigger_Windows_Timebase": {"scpi": ":TRIGger:WINDows:TIMe <value>", "subsystem": "TRIG"},

  // UART
  "Set_Uart_Baud": {"scpi": ":UART:BAUD <value>", "subsystem": "UART"},
  "Set_Uart_Endian": {"scpi": ":UART:ENDian <value>", "subsystem": "UART"},
  "Set_Uart_Parallel": {"scpi": ":UART:PARity <value>", "subsystem": "UART"},
  "Set_Uart_Polarity": {"scpi": ":UART:POLarity <value>", "subsystem": "UART"},
  "Set_Uart_Rx": {"scpi": ":UART:RX <value>", "subsystem": "UART"},
  "Set_Uart_Stop": {"scpi": ":UART:STOP <value>", "subsystem": "UART"},
  "Set_Uart_Tx": {"scpi": ":UART:TX <value>", "subsystem": "UART"},
  "Set_Uart_Width": {"scpi": ":UART:WIDTh <value>", "subsystem": "UART"},

  // VOLT
  "Set_Voltage_Level_Immediate_Amplitude": {"scpi": ":VOLTage:LEVel:IMMediate:AMPLitude <value>", "subsystem": "VOLT"},
  "Set_Voltage_Offset": {"scpi": ":VOLTage:OFFSet <value>", "subsystem": "VOLT"},

  // WAV
  "Set_Waveform_Start": {"scpi": ":WAVeform:STARt <value>", "subsystem": "WAV"},
  "Set_Waveform_Stop": {"scpi": ":WAVeform:STOP <value>", "subsystem": "WAV"},
}
```

### DO — 47

```json
"do": {
  // APPL
  "Do_Apply_Noise": {"scpi": ":APPLy:NOISe", "subsystem": "APPL"},
  "Do_Apply_Pulse": {"scpi": ":APPLy:PULSe", "subsystem": "APPL"},
  "Do_Apply_Ramp": {"scpi": ":APPLy:RAMP", "subsystem": "APPL"},
  "Do_Apply_Sinusoid": {"scpi": ":APPLy:SINusoid", "subsystem": "APPL"},
  "Do_Apply_Square": {"scpi": ":APPLy:SQUare", "subsystem": "APPL"},
  "Do_Apply_User": {"scpi": ":APPLy:USER", "subsystem": "APPL"},

  // CAL
  "Do_Calibrate_Quit": {"scpi": ":CALibrate:QUIT", "subsystem": "CAL"},
  "Do_Calibrate_Start": {"scpi": ":CALibrate:STARt", "subsystem": "CAL"},

  // CURS
  "Do_Cursor_Manual": {"scpi": ":CURSor:MANual", "subsystem": "CURS"},
  "Do_Cursor_Track": {"scpi": ":CURSor:TRACk", "subsystem": "CURS"},
  "Do_Cursor_Xy": {"scpi": ":CURSor:XY", "subsystem": "CURS"},

  // Common
  "Do_Cls": {"scpi": "*CLS", "subsystem": "Common"},
  "Do_Opc": {"scpi": "*OPC", "subsystem": "Common"},
  "Do_Rst": {"scpi": "*RST", "subsystem": "Common"},
  "Do_Wai": {"scpi": "*WAI", "subsystem": "Common"},

  // DATA
  "Do_Data_Dac": {"scpi": ":DATA:DAC<chan>", "subsystem": "DATA"},

  // DISP
  "Do_Display_Clear": {"scpi": ":DISPlay:CLEar", "subsystem": "DISP"},

  // LA
  "Do_La_Autoscale": {"scpi": ":LA:AUTosort", "subsystem": "LA"},
  "Do_La_Digital": {"scpi": ":LA:DIGital", "subsystem": "LA"},
  "Do_La_Pod": {"scpi": ":LA:POD", "subsystem": "LA"},

  // MASK
  "Do_Mask_Create": {"scpi": ":MASK:CREate", "subsystem": "MASK"},
  "Do_Mask_Reset": {"scpi": ":MASK:RESet", "subsystem": "MASK"},

  // MATH
  "Do_Math_Filter": {"scpi": ":MATH:FILTer", "subsystem": "MATH"},
  "Do_Math_Reset": {"scpi": ":MATH:RESet", "subsystem": "MATH"},

  // MEAS
  "Do_Measure_Recover": {"scpi": ":MEASure:RECover", "subsystem": "MEAS"},
  "Do_Measure_Statistic_Reset": {"scpi": ":MEASure:STATistic:RESet", "subsystem": "MEAS"},

  // PHAS
  "Do_Phase_Initiate": {"scpi": ":PHASe:INITiate", "subsystem": "PHAS"},

  // SYST
  "Do_System_Option_Install": {"scpi": ":SYSTem:OPTion:INSTall", "subsystem": "SYST"},
  "Do_System_Option_Uninstall": {"scpi": ":SYSTem:OPTion:UNINSTall", "subsystem": "SYST"},

  // TRIG
  "Do_Trigger_Delay": {"scpi": ":TRIGger:DELay", "subsystem": "TRIG"},
  "Do_Trigger_Duration": {"scpi": ":TRIGger:DURATion", "subsystem": "TRIG"},
  "Do_Trigger_Edge": {"scpi": ":TRIGger:EDGe", "subsystem": "TRIG"},
  "Do_Trigger_Iic": {"scpi": ":TRIGger:IIC", "subsystem": "TRIG"},
  "Do_Trigger_Nedge": {"scpi": ":TRIGger:NEDGe", "subsystem": "TRIG"},
  "Do_Trigger_Pattern": {"scpi": ":TRIGger:PATTern", "subsystem": "TRIG"},
  "Do_Trigger_Pulse": {"scpi": ":TRIGger:PULSe", "subsystem": "TRIG"},
  "Do_Trigger_Rs": {"scpi": ":TRIGger:RS<chan>", "subsystem": "TRIG"},
  "Do_Trigger_Runt": {"scpi": ":TRIGger:RUNT", "subsystem": "TRIG"},
  "Do_Trigger_Shold": {"scpi": ":TRIGger:SHOLd", "subsystem": "TRIG"},
  "Do_Trigger_Slope": {"scpi": ":TRIGger:SLOPe", "subsystem": "TRIG"},
  "Do_Trigger_Spi": {"scpi": ":TRIGger:SPI", "subsystem": "TRIG"},
  "Do_Trigger_Timebase": {"scpi": ":TRIGger:TIMeout", "subsystem": "TRIG"},
  "Do_Trigger_Video": {"scpi": ":TRIGger:VIDeo", "subsystem": "TRIG"},
  "Do_Trigger_Windows": {"scpi": ":TRIGger:WINDows", "subsystem": "TRIG"},

  // VOLT
  "Do_Voltage_Level": {"scpi": ":VOLTage:LEVel", "subsystem": "VOLT"},
  "Do_Voltage_Level_Immediate_Offset": {"scpi": ":VOLTage:LEVel:IMMediate:OFFSet", "subsystem": "VOLT"},

  // WAV
  "Do_Waveform_Sor": {"scpi": ":WAV:SOR", "description": "LabVIEW Programming Demo", "subsystem": "WAV"},
}
```

### NAB — 346

```json
"nab": {
  // ACQ
  "Get_Acquire_Averages": {"scpi": ":ACQuire:AVERages?", "subsystem": "ACQ"},
  "Get_Acquire_Mdepth": {"scpi": ":ACQuire:MDEPth?", "subsystem": "ACQ"},
  "Get_Acquire_Srate": {"scpi": ":ACQuire:SRATe?", "subsystem": "ACQ"},

  // CHAN
  "Get_Channel_Bwlimit": {"scpi": ":CHANnel1:BWLimit?", "subsystem": "CHAN"},
  "Get_Channel_Coupling": {"scpi": ":CHANnel1:COUPling?", "subsystem": "CHAN"},
  "Get_Channel_Display": {"scpi": ":CHAN1:DISP?", "subsystem": "CHAN"},
  "Get_Channel_Invert": {"scpi": ":CHANnel1:INVert?", "subsystem": "CHAN"},
  "Get_Channel_Offset": {"scpi": ":CHANnel1:OFFSet?", "subsystem": "CHAN"},
  "Get_Channel_Probe": {"scpi": ":CHANnel1:PROBe?", "subsystem": "CHAN"},
  "Get_Channel_Range": {"scpi": ":CHANnel1:RANGe?", "subsystem": "CHAN"},
  "Get_Channel_Scale": {"scpi": ":CHANnel1:SCALe?", "subsystem": "CHAN"},
  "Get_Channel_Tcalibrate": {"scpi": ":CHANnel1:TCAL?", "subsystem": "CHAN"},
  "Get_Channel_Units": {"scpi": ":CHANnel1:UNITs?", "subsystem": "CHAN"},
  "Get_Channel_Vernier": {"scpi": ":CHANnel1:VERNier?", "subsystem": "CHAN"},

  // CONF
  "Get_Config_Endian": {"scpi": ":CONFig:ENDian?", "subsystem": "CONF"},
  "Get_Config_Format": {"scpi": ":CONFig:FORMat?", "subsystem": "CONF"},
  "Get_Config_Label": {"scpi": ":CONFig:LABel?", "description": "Commands", "subsystem": "CONF"},
  "Get_Config_Line": {"scpi": ":CONFig:LINE?", "subsystem": "CONF"},
  "Get_Config_Srate": {"scpi": ":CONFig:SRATe?", "subsystem": "CONF"},
  "Get_Config_Width": {"scpi": ":CONFig:WIDth?", "subsystem": "CONF"},

  // CURS
  "Get_Cursor_Manual_Ax": {"scpi": ":CURSor:MANual:AX?", "subsystem": "CURS"},
  "Get_Cursor_Manual_Ay": {"scpi": ":CURSor:MANual:AY?", "subsystem": "CURS"},
  "Get_Cursor_Manual_Bx": {"scpi": ":CURSor:MANual:BX?", "subsystem": "CURS"},
  "Get_Cursor_Manual_By": {"scpi": ":CURSor:MANual:BY?", "subsystem": "CURS"},
  "Get_Cursor_Manual_Ixdelta": {"scpi": ":CURSor:MANual:IXDELta?", "subsystem": "CURS"},
  "Get_Cursor_Manual_Source": {"scpi": ":CURSor:MANual:SOURce?", "subsystem": "CURS"},
  "Get_Cursor_Manual_Tunit": {"scpi": ":CURSor:MANual:TUNit?", "subsystem": "CURS"},
  "Get_Cursor_Manual_Vunit": {"scpi": ":CURSor:MANual:VUNit?", "subsystem": "CURS"},
  "Get_Cursor_Manual_Xdelta": {"scpi": ":CURSor:MANual:XDELta?", "subsystem": "CURS"},
  "Get_Cursor_Manual_Ydelta": {"scpi": ":CURSor:MANual:YDELta?", "subsystem": "CURS"},
  "Get_Cursor_Mode": {"scpi": ":CURSor:MODE?", "subsystem": "CURS"},
  "Get_Cursor_Track_Ax": {"scpi": ":CURSor:TRACk:AX?", "subsystem": "CURS"},
  "Get_Cursor_Track_Ay": {"scpi": ":CURSor:TRACk:AY?", "subsystem": "CURS"},
  "Get_Cursor_Track_Bx": {"scpi": ":CURSor:TRACk:BX?", "subsystem": "CURS"},
  "Get_Cursor_Track_By": {"scpi": ":CURSor:TRACk:BY?", "subsystem": "CURS"},
  "Get_Cursor_Track_Ixdelta": {"scpi": ":CURSor:TRACk:IXDELTA?", "subsystem": "CURS"},
  "Get_Cursor_Track_Source": {"scpi": ":CURSor:TRACk:SOURce<chan>?", "subsystem": "CURS"},
  "Get_Cursor_Track_Xdelta": {"scpi": ":CURSor:TRACk:XDELta?", "subsystem": "CURS"},
  "Get_Cursor_Track_Ydelta": {"scpi": ":CURSor:TRACk:YDELta?", "subsystem": "CURS"},
  "Get_Cursor_Xy_Ax": {"scpi": ":CURSor:XY:AX?", "subsystem": "CURS"},
  "Get_Cursor_Xy_Ay": {"scpi": ":CURSor:XY:AY?", "subsystem": "CURS"},
  "Get_Cursor_Xy_Bx": {"scpi": ":CURSor:XY:BX?", "subsystem": "CURS"},
  "Get_Cursor_Xy_By": {"scpi": ":CURSor:XY:BY?", "subsystem": "CURS"},

  // Common
  "Get_Ese": {"scpi": "*ESE?", "subsystem": "Common"},
  "Get_Esr": {"scpi": "*ESR?", "subsystem": "Common"},
  "Get_Idn": {"scpi": "*IDN?", "subsystem": "Common"},
  "Get_Opc": {"scpi": "*OPC?", "subsystem": "Common"},
  "Get_Sre": {"scpi": "*SRE?", "subsystem": "Common"},
  "Get_Stb": {"scpi": "*STB?", "subsystem": "Common"},
  "Get_Tst": {"scpi": "*TST?", "subsystem": "Common"},

  // DATA
  "Get_Data_Load": {"scpi": ":DATA:LOAD?", "subsystem": "DATA"},
  "Get_Data_Points": {"scpi": ":DATA:POINts?", "subsystem": "DATA"},
  "Get_Data_Points_Internal": {"scpi": ":DATA:POINts:INTerpolate?", "subsystem": "DATA"},
  "Get_Data_Value": {"scpi": ":DATA:VALue?", "subsystem": "DATA"},

  // DEC
  "Get_Decoder_Config_Endian": {"scpi": ":DECoder1:CONFig:ENDian?", "subsystem": "DEC"},
  "Get_Decoder_Config_Format": {"scpi": ":DECoder1:CONFig:FORMat?", "subsystem": "DEC"},
  "Get_Decoder_Config_Label": {"scpi": ":DECoder1:CONFig:LABel?", "subsystem": "DEC"},
  "Get_Decoder_Config_Line": {"scpi": ":DECoder1:CONFig:LINE?", "subsystem": "DEC"},
  "Get_Decoder_Config_Srate": {"scpi": ":DECoder1:CONFig:SRATe?", "subsystem": "DEC"},
  "Get_Decoder_Config_Width": {"scpi": ":DECoder1:CONFig:WIDth?", "subsystem": "DEC"},
  "Get_Decoder_Display": {"scpi": ":DECoder1:DISPlay?", "subsystem": "DEC"},
  "Get_Decoder_Format": {"scpi": ":DECoder1:FORMat?", "subsystem": "DEC"},
  "Get_Decoder_Iic_Address": {"scpi": ":DECoder1:IIC:ADDRess?", "subsystem": "DEC"},
  "Get_Decoder_Iic_Clk": {"scpi": ":DECoder1:IIC:CLK?", "subsystem": "DEC"},
  "Get_Decoder_Iic_Data": {"scpi": ":DECoder1:IIC:DATA?", "subsystem": "DEC"},
  "Get_Decoder_Mode": {"scpi": ":DECoder1:MODE?", "subsystem": "DEC"},
  "Get_Decoder_Parallel_Bitx": {"scpi": ":DECoder1:PARallel:BITX?", "subsystem": "DEC"},
  "Get_Decoder_Parallel_Ccompensation": {"scpi": ":DECoder1:PARallel:CCOMpensation?", "subsystem": "DEC"},
  "Get_Decoder_Parallel_Clk": {"scpi": ":DECoder1:PARallel:CLK?", "subsystem": "DEC"},
  "Get_Decoder_Parallel_Edge": {"scpi": ":DECoder1:PARallel:EDGE?", "subsystem": "DEC"},
  "Get_Decoder_Parallel_Nreject": {"scpi": ":DECoder1:PARallel:NREJect?", "subsystem": "DEC"},
  "Get_Decoder_Parallel_Nrtime": {"scpi": ":DECoder1:PARallel:NRTime?", "subsystem": "DEC"},
  "Get_Decoder_Parallel_Plot": {"scpi": ":DECoder1:PARallel:PLOT?", "subsystem": "DEC"},
  "Get_Decoder_Parallel_Polarity": {"scpi": ":DECoder1:PARallel:POLarity?", "subsystem": "DEC"},
  "Get_Decoder_Parallel_Source": {"scpi": ":DECoder1:PARallel:SOURce?", "subsystem": "DEC"},
  "Get_Decoder_Parallel_Width": {"scpi": ":DECoder1:PARallel:WIDTh?", "subsystem": "DEC"},
  "Get_Decoder_Positive": {"scpi": ":DECoder1:POSition?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Clk": {"scpi": ":DECoder1:SPI:CLK?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Csrc": {"scpi": ":DECoder1:SPI:CS?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Edge": {"scpi": ":DECoder1:SPI:EDGE?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Endian": {"scpi": ":DECoder1:SPI:ENDian?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Miso": {"scpi": ":DECoder1:SPI:MISO?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Mode": {"scpi": ":DECoder1:SPI:MODE?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Mosi": {"scpi": ":DECoder1:SPI:MOSI?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Polarity": {"scpi": ":DECoder1:SPI:POLarity?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Select": {"scpi": ":DECoder1:SPI:SELect?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Timebase": {"scpi": ":DECoder1:SPI:TIMeout?", "subsystem": "DEC"},
  "Get_Decoder_Spi_Width": {"scpi": ":DECoder1:SPI:WIDTh?", "subsystem": "DEC"},
  "Get_Decoder_Threshold_Channel": {"scpi": ":DECoder1:THREshold:CHANnel<chan>?", "subsystem": "DEC"},
  "Get_Decoder_Uart_Baud": {"scpi": ":DECoder1:UART:BAUD?", "subsystem": "DEC"},
  "Get_Decoder_Uart_Endian": {"scpi": ":DECoder1:UART:ENDian?", "subsystem": "DEC"},
  "Get_Decoder_Uart_Parallel": {"scpi": ":DECoder1:UART:PARity?", "subsystem": "DEC"},
  "Get_Decoder_Uart_Polarity": {"scpi": ":DECoder1:UART:POLarity?", "subsystem": "DEC"},
  "Get_Decoder_Uart_Rx": {"scpi": ":DECoder1:UART:RX?", "subsystem": "DEC"},
  "Get_Decoder_Uart_Stop": {"scpi": ":DECoder1:UART:STOP?", "subsystem": "DEC"},
  "Get_Decoder_Uart_Tx": {"scpi": ":DECoder1:UART:TX?", "subsystem": "DEC"},
  "Get_Decoder_Uart_Width": {"scpi": ":DECoder1:UART:WIDTh?", "subsystem": "DEC"},

  // DISP
  "Get_Display_Data": {"scpi": ":DISPlay:DATA?", "subsystem": "DISP"},
  "Get_Display_Gbrightness": {"scpi": ":DISPlay:GBRightness?", "subsystem": "DISP"},
  "Get_Display_Grading_Time": {"scpi": ":DISPlay:GRADing:TIME?", "subsystem": "DISP"},
  "Get_Display_Grid": {"scpi": ":DISPlay:GRID?", "subsystem": "DISP"},
  "Get_Display_Wbrightness": {"scpi": ":DISPlay:WBRightness?", "subsystem": "DISP"},

  // ETAB
  "Get_Etable_Color": {"scpi": ":ETABle1:COLumn?", "subsystem": "ETAB"},
  "Get_Etable_Data": {"scpi": ":ETABle1:DATA?", "subsystem": "ETAB"},
  "Get_Etable_Display": {"scpi": ":ETABle1:DISP?", "subsystem": "ETAB"},
  "Get_Etable_Format": {"scpi": ":ETABle1:FORMat?", "subsystem": "ETAB"},
  "Get_Etable_Row": {"scpi": ":ETABle1:ROW?", "subsystem": "ETAB"},
  "Get_Etable_Sort": {"scpi": ":ETABle1:SORT?", "subsystem": "ETAB"},
  "Get_Etable_View": {"scpi": ":ETABle1:VIEW?", "subsystem": "ETAB"},

  // FREQ
  "Get_Frequency_Fixed": {"scpi": ":FREQuency:FIXed?", "subsystem": "FREQ"},

  // FUNC
  "Get_Function_Ramp_Symmetry": {"scpi": ":FUNCtion:RAMP:SYMMetry?", "subsystem": "FUNC"},
  "Get_Function_Shape": {"scpi": ":FUNCtion:SHAPe?", "subsystem": "FUNC"},
  "Get_Function_Wrecord_Enable": {"scpi": ":FUNCtion:WRECord:ENABle?", "subsystem": "FUNC"},
  "Get_Function_Wrecord_Fend": {"scpi": ":FUNCtion:WRECord:FEND?", "subsystem": "FUNC"},
  "Get_Function_Wrecord_Finterval": {"scpi": ":FUNCtion:WRECord:FINTerval?", "subsystem": "FUNC"},
  "Get_Function_Wrecord_Fmax": {"scpi": ":FUNCtion:WRECord:FMAX?", "subsystem": "FUNC"},
  "Get_Function_Wrecord_Operator": {"scpi": ":FUNCtion:WRECord:OPERate?", "subsystem": "FUNC"},
  "Get_Function_Wrecord_Prompt": {"scpi": ":FUNCtion:WRECord:PROMpt?", "subsystem": "FUNC"},
  "Get_Function_Wreplay_Direction": {"scpi": ":FUNCtion:WREPlay:DIRection?", "subsystem": "FUNC"},
  "Get_Function_Wreplay_Fcurrent": {"scpi": ":FUNCtion:WREPlay:FCURrent?", "subsystem": "FUNC"},
  "Get_Function_Wreplay_Fend": {"scpi": ":FUNCtion:WREPlay:FEND?", "subsystem": "FUNC"},
  "Get_Function_Wreplay_Finterval": {"scpi": ":FUNCtion:WREPlay:FINTerval?", "subsystem": "FUNC"},
  "Get_Function_Wreplay_Fmax": {"scpi": ":FUNCtion:WREPlay:FMAX?", "subsystem": "FUNC"},
  "Get_Function_Wreplay_Fstart": {"scpi": ":FUNCtion:WREPlay:FSTart?", "subsystem": "FUNC"},
  "Get_Function_Wreplay_Mode": {"scpi": ":FUNCtion:WREPlay:MODE?", "subsystem": "FUNC"},
  "Get_Function_Wreplay_Operator": {"scpi": ":FUNCtion:WREPlay:OPERate?", "subsystem": "FUNC"},

  // IIC
  "Get_Iic_Address": {"scpi": ":IIC:ADDRess?", "subsystem": "IIC"},
  "Get_Iic_Clk": {"scpi": ":IIC:CLK?", "subsystem": "IIC"},
  "Get_Iic_Data": {"scpi": ":IIC:DATA?", "subsystem": "IIC"},

  // IMM
  "Get_Immediate_Offset": {"scpi": ":IMMediate:OFFSet?", "subsystem": "IMM"},

  // LA
  "Get_La_Active": {"scpi": ":LA:ACTive?", "subsystem": "LA"},
  "Get_La_Digital_Display": {"scpi": ":LA:DIGital3:DISPlay?", "subsystem": "LA"},
  "Get_La_Digital_Positive": {"scpi": ":LA:DIGital1:POSition?", "subsystem": "LA"},
  "Get_La_Display": {"scpi": ":LA:DISPlay?", "subsystem": "LA"},
  "Get_La_Pod_Display": {"scpi": ":LA:POD1:DISPlay?", "subsystem": "LA"},
  "Get_La_Pod_Threshold": {"scpi": ":LA:POD1:THReshold?", "subsystem": "LA"},
  "Get_La_Size": {"scpi": ":LA:SIZE?", "subsystem": "LA"},
  "Get_La_Statistic": {"scpi": ":LA:STATe?", "subsystem": "LA"},
  "Get_La_Tcalibrate": {"scpi": ":LA:TCALibrate?", "subsystem": "LA"},

  // MASK
  "Get_Mask_Enable": {"scpi": ":MASK:ENABle?", "subsystem": "MASK"},
  "Get_Mask_Failed": {"scpi": ":MASK:FAILed?", "subsystem": "MASK"},
  "Get_Mask_Mdisplay": {"scpi": ":MASK:MDISplay?", "subsystem": "MASK"},
  "Get_Mask_Operator": {"scpi": ":MASK:OPERate?", "subsystem": "MASK"},
  "Get_Mask_Output": {"scpi": ":MASK:OUTPut?", "subsystem": "MASK"},
  "Get_Mask_Passed": {"scpi": ":MASK:PASSed?", "subsystem": "MASK"},
  "Get_Mask_Sooutput": {"scpi": ":MASK:SOOutput?", "subsystem": "MASK"},
  "Get_Mask_Source": {"scpi": ":MASK:SOURce?", "subsystem": "MASK"},
  "Get_Mask_Total": {"scpi": ":MASK:TOTal?", "subsystem": "MASK"},

  // MATH
  "Get_Math_Display": {"scpi": ":MATH:DISPlay?", "subsystem": "MATH"},
  "Get_Math_Fft_Hcenter": {"scpi": ":MATH:FFT:HCENter?", "description": "Commands", "subsystem": "MATH"},
  "Get_Math_Fft_Hscale": {"scpi": ":MATH:FFT:HSCale?", "subsystem": "MATH"},
  "Get_Math_Fft_Mode": {"scpi": ":MATH:FFT:MODE?", "description": "Commands", "subsystem": "MATH"},
  "Get_Math_Fft_Source": {"scpi": ":MATH:FFT:SOURce?", "description": "Commands", "subsystem": "MATH"},
  "Get_Math_Fft_Split": {"scpi": ":MATH:FFT:SPLit?", "subsystem": "MATH"},
  "Get_Math_Fft_Units": {"scpi": ":MATH:FFT:UNIT?", "subsystem": "MATH"},
  "Get_Math_Fft_Windows": {"scpi": ":MATH:FFT:WINDow?", "subsystem": "MATH"},
  "Get_Math_Invert": {"scpi": ":MATH:INVert?", "description": "Commands", "subsystem": "MATH"},
  "Get_Math_Lsou": {"scpi": ":MATH:LSOUrce<chan>?", "subsystem": "MATH"},
  "Get_Math_Offset": {"scpi": ":MATH:OFFSet?", "description": "Commands", "subsystem": "MATH"},
  "Get_Math_Operator": {"scpi": ":MATH:OPERator?", "subsystem": "MATH"},
  "Get_Math_Option_Ascale": {"scpi": ":MATH:OPTion:ASCale?", "subsystem": "MATH"},
  "Get_Math_Option_Distance": {"scpi": ":MATH:OPTion:DIStance?", "description": "Commands", "subsystem": "MATH"},
  "Get_Math_Option_Endian": {"scpi": ":MATH:OPTion:END?", "subsystem": "MATH"},
  "Get_Math_Option_Fx_Operator": {"scpi": ":MATH:OPTion:FX:OPERator?", "subsystem": "MATH"},
  "Get_Math_Option_Fx_Source": {"scpi": ":MATH:OPTion:FX:SOURce<chan>?", "description": "Commands", "subsystem": "MATH"},
  "Get_Math_Option_Invert": {"scpi": ":MATH:OPTion:INVert?", "subsystem": "MATH"},
  "Get_Math_Option_Sensitivity": {"scpi": ":MATH:OPTion:SENSitivity?", "subsystem": "MATH"},
  "Get_Math_Option_Start": {"scpi": ":MATH:OPTion:STARt?", "description": "Commands", "subsystem": "MATH"},
  "Get_Math_Option_Threshold": {"scpi": ":MATH:OPTion:THReshold<chan>?", "subsystem": "MATH"},
  "Get_Math_Scale": {"scpi": ":MATH:SCALe?", "subsystem": "MATH"},
  "Get_Math_Source": {"scpi": ":MATH:SOURce<chan>?", "subsystem": "MATH"},

  // MEAS
  "Get_Measure_Adisplay": {"scpi": ":MEASure:ADISplay?", "subsystem": "MEAS"},
  "Get_Measure_Amsource": {"scpi": ":MEASure:AMSource?", "subsystem": "MEAS"},
  "Get_Measure_Counter_Source": {"scpi": ":MEASure:COUNter:SOURce?", "subsystem": "MEAS"},
  "Get_Measure_Counter_Value": {"scpi": ":MEASure:COUNter:VALue?", "subsystem": "MEAS"},
  "Get_Measure_Source": {"scpi": ":MEASure:SOURce?", "subsystem": "MEAS"},
  "Get_Measure_Statistic_Display": {"scpi": ":MEASure:STATistic:DISPlay?", "subsystem": "MEAS"},
  "Get_Measure_Statistic_Item": {"scpi": ":MEASure:STATistic:ITEM?", "description": "Commands", "subsystem": "MEAS"},
  "Get_Measure_Statistic_Mode": {"scpi": ":MEASure:STATistic:MODE?", "description": "Commands", "subsystem": "MEAS"},

  // MOD
  "Get_Mod_Am": {"scpi": ":MOD:AM?", "subsystem": "MOD"},
  "Get_Mod_Am_Depth": {"scpi": ":MOD:AM:DEPTh?", "subsystem": "MOD"},
  "Get_Mod_Am_Internal_Frequency": {"scpi": ":MOD:AM:INTernal:FREQuency?", "subsystem": "MOD"},
  "Get_Mod_Am_Internal_Function": {"scpi": ":MOD:AM:INTernal:FUNCtion?", "subsystem": "MOD"},
  "Get_Mod_Fm": {"scpi": ":MOD:FM?", "subsystem": "MOD"},
  "Get_Mod_Fm_Deviation": {"scpi": ":MOD:FM:DEVIation?", "subsystem": "MOD"},
  "Get_Mod_Fm_Internal_Frequency": {"scpi": ":MOD:FM:INTernal:FREQuency?", "subsystem": "MOD"},
  "Get_Mod_Fm_Internal_Function": {"scpi": ":MOD:FM:INTernal:FUNCtion?", "subsystem": "MOD"},
  "Get_Mod_Statistic": {"scpi": ":MOD:STATe?", "subsystem": "MOD"},
  "Get_Mod_Type": {"scpi": ":MOD:TYPe?", "subsystem": "MOD"},

  // OUTP
  "Get_Output_Impedance": {"scpi": ":OUTPut:IMPedance?", "subsystem": "OUTP"},

  // PAR
  "Get_Parallel_Bitx": {"scpi": ":PARallel:BITX?", "subsystem": "PAR"},
  "Get_Parallel_Ccompensation": {"scpi": ":PARallel:CCOMpensation?", "subsystem": "PAR"},
  "Get_Parallel_Clk": {"scpi": ":PARallel:CLK?", "subsystem": "PAR"},
  "Get_Parallel_Edge": {"scpi": ":PARallel:EDGE?", "subsystem": "PAR"},
  "Get_Parallel_Nreject": {"scpi": ":PARallel:NREJect?", "subsystem": "PAR"},
  "Get_Parallel_Nrtime": {"scpi": ":PARallel:NRTime?", "subsystem": "PAR"},
  "Get_Parallel_Plot": {"scpi": ":PARallel:PLOT?", "subsystem": "PAR"},
  "Get_Parallel_Polarity": {"scpi": ":PARallel:POLarity?", "subsystem": "PAR"},
  "Get_Parallel_Source": {"scpi": ":PARallel:SOURce?", "subsystem": "PAR"},
  "Get_Parallel_Width": {"scpi": ":PARallel:WIDTh?", "subsystem": "PAR"},

  // PHAS
  "Get_Phase_Adjust": {"scpi": ":PHASe:ADJust?", "subsystem": "PHAS"},

  // PULS
  "Get_Pulse_Dcycle": {"scpi": ":PULSe:DCYCle?", "subsystem": "PULS"},

  // REF
  "Get_Reference_Color": {"scpi": ":REFerence1:COLor?", "subsystem": "REF"},
  "Get_Reference_Display": {"scpi": ":REFerence:DISPlay?", "subsystem": "REF"},
  "Get_Reference_Enable": {"scpi": ":REFerence1:ENABle?", "subsystem": "REF"},
  "Get_Reference_Source": {"scpi": ":REFerence1:SOURce?", "subsystem": "REF"},
  "Get_Reference_Voffset": {"scpi": ":REFerence1:VOFFset?", "description": "Commands", "subsystem": "REF"},
  "Get_Reference_Vscale": {"scpi": ":REFerence1:VSCale?", "subsystem": "REF"},

  // SPI
  "Get_Spi_Clk": {"scpi": ":SPI:CLK?", "subsystem": "SPI"},
  "Get_Spi_Csrc": {"scpi": ":SPI:CS?", "subsystem": "SPI"},
  "Get_Spi_Edge": {"scpi": ":SPI:EDGE?", "subsystem": "SPI"},
  "Get_Spi_Endian": {"scpi": ":SPI:ENDian?", "subsystem": "SPI"},
  "Get_Spi_Miso": {"scpi": ":SPI:MISO?", "subsystem": "SPI"},
  "Get_Spi_Mode": {"scpi": ":SPI:MODE?", "subsystem": "SPI"},
  "Get_Spi_Mosi": {"scpi": ":SPI:MOSI?", "subsystem": "SPI"},
  "Get_Spi_Polarity": {"scpi": ":SPI:POLarity?", "subsystem": "SPI"},
  "Get_Spi_Select": {"scpi": ":SPI:SELect?", "subsystem": "SPI"},
  "Get_Spi_Timebase": {"scpi": ":SPI:TIMeout?", "subsystem": "SPI"},
  "Get_Spi_Width": {"scpi": ":SPI:WIDTh?", "subsystem": "SPI"},

  // STOR
  "Get_Storage_Image_Color": {"scpi": ":STORage:IMAGe:COLor?", "subsystem": "STOR"},
  "Get_Storage_Image_Invert": {"scpi": ":STORage:IMAGe:INVERT?", "subsystem": "STOR"},

  // SYST
  "Get_System_Autoscale": {"scpi": ":SYSTem:AUToscale?", "subsystem": "SYST"},
  "Get_System_Beeper": {"scpi": ":SYSTem:BEEPer?", "subsystem": "SYST"},
  "Get_System_Error_Next": {"scpi": ":SYSTem:ERRor:NEXT?", "subsystem": "SYST"},
  "Get_System_Gam": {"scpi": ":SYSTem:GAM?", "subsystem": "SYST"},
  "Get_System_Language": {"scpi": ":SYSTem:LANGuage?", "subsystem": "SYST"},
  "Get_System_Locked": {"scpi": ":SYSTem:LOCKed?", "subsystem": "SYST"},
  "Get_System_Pon": {"scpi": ":SYSTem:PON?", "subsystem": "SYST"},
  "Get_System_Ram": {"scpi": ":SYSTem:RAM?", "subsystem": "SYST"},

  // THRE
  "Get_Threshold_Channel": {"scpi": ":THREshold:CHANnel<chan>?", "subsystem": "THRE"},

  // TIM
  "Get_Timebase_Delay_Enable": {"scpi": ":TIMebase:DELay:ENABle?", "subsystem": "TIM"},
  "Get_Timebase_Delay_Offset": {"scpi": ":TIMebase:DELay:OFFSet?", "subsystem": "TIM"},
  "Get_Timebase_Delay_Scale": {"scpi": ":TIMebase:DELay:SCALe?", "description": "Commands", "subsystem": "TIM"},
  "Get_Timebase_Main_Offset": {"scpi": ":TIMebase:MAIN:OFFSet?", "description": "Commands", "subsystem": "TIM"},
  "Get_Timebase_Main_Scale": {"scpi": ":TIMebase:MAIN:SCALe?", "description": "Commands", "subsystem": "TIM"},
  "Get_Timebase_Mode": {"scpi": ":TIMebase:MODE?", "subsystem": "TIM"},

  // TRIG
  "Get_Trigger_Coupling": {"scpi": ":TRIGger:COUPling?", "subsystem": "TRIG"},
  "Get_Trigger_Delay_Sa": {"scpi": ":TRIGger:DELay:SA?", "subsystem": "TRIG"},
  "Get_Trigger_Delay_Sb": {"scpi": ":TRIGger:DELay:SB?", "subsystem": "TRIG"},
  "Get_Trigger_Delay_Slopa": {"scpi": ":TRIGger:DELay:SLOPA?", "subsystem": "TRIG"},
  "Get_Trigger_Delay_Slopb": {"scpi": ":TRIGger:DELay:SLOPB?", "subsystem": "TRIG"},
  "Get_Trigger_Delay_Tlower": {"scpi": ":TRIGger:DELay:TLOWer?", "subsystem": "TRIG"},
  "Get_Trigger_Delay_Tupper": {"scpi": ":TRIGger:DELay:TUPPer?", "description": "Commands", "subsystem": "TRIG"},
  "Get_Trigger_Delay_Type": {"scpi": ":TRIGger:DELay:TYPe?", "subsystem": "TRIG"},
  "Get_Trigger_Duration_Source": {"scpi": ":TRIGger:DURATion:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Duration_Tlower": {"scpi": ":TRIGger:DURATion:TLOWer?", "subsystem": "TRIG"},
  "Get_Trigger_Duration_Tupper": {"scpi": ":TRIGger:DURATion:TUPPer?", "subsystem": "TRIG"},
  "Get_Trigger_Duration_Type": {"scpi": ":TRIGger:DURATion:TYPe?", "subsystem": "TRIG"},
  "Get_Trigger_Duration_When": {"scpi": ":TRIGger:DURATion:WHEN?", "subsystem": "TRIG"},
  "Get_Trigger_Edge_Level": {"scpi": ":TRIGger:EDGe:LEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Edge_Slope": {"scpi": ":TRIGger:EDGe:SLOPe?", "subsystem": "TRIG"},
  "Get_Trigger_Edge_Source": {"scpi": ":TRIGger:EDGe:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Holdoff": {"scpi": ":TRIGger:HOLDoff?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Address": {"scpi": ":TRIGger:IIC:ADDRess?", "description": "Commands", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Awidth": {"scpi": ":TRIGger:IIC:AWIDth?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Clevel": {"scpi": ":TRIGger:IIC:CLEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Data": {"scpi": ":TRIGger:IIC:DATA?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Direction": {"scpi": ":TRIGger:IIC:DIRection?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Dlevel": {"scpi": ":TRIGger:IIC:DLEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Scl": {"scpi": ":TRIGger:IIC:SCL?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_Sda": {"scpi": ":TRIGger:IIC:SDA?", "subsystem": "TRIG"},
  "Get_Trigger_Iic_When": {"scpi": ":TRIGger:IIC:WHEN?", "subsystem": "TRIG"},
  "Get_Trigger_Mode": {"scpi": ":TRIGger:MODE?", "subsystem": "TRIG"},
  "Get_Trigger_Nedge_Edge": {"scpi": ":TRIGger:NEDGe:EDGE?", "subsystem": "TRIG"},
  "Get_Trigger_Nedge_Idle": {"scpi": ":TRIGger:NEDGe:IDLE?", "subsystem": "TRIG"},
  "Get_Trigger_Nedge_Level": {"scpi": ":TRIGger:NEDGe:LEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Nedge_Slope": {"scpi": ":TRIGger:NEDGe:SLOPe?", "subsystem": "TRIG"},
  "Get_Trigger_Nedge_Source": {"scpi": ":TRIGger:NEDGe:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Nreject": {"scpi": ":TRIGger:NREJect?", "subsystem": "TRIG"},
  "Get_Trigger_Pattern_Level": {"scpi": ":TRIGger:PATTern:LEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Pattern_Pattern": {"scpi": ":TRIGger:PATTern:PATTern?", "subsystem": "TRIG"},
  "Get_Trigger_Positive": {"scpi": ":TRIGger:POSition?", "subsystem": "TRIG"},
  "Get_Trigger_Pulse_Level": {"scpi": ":TRIGger:PULSe:LEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Pulse_Lwidth": {"scpi": ":TRIGger:PULSe:LWIDth?", "subsystem": "TRIG"},
  "Get_Trigger_Pulse_Source": {"scpi": ":TRIGger:PULSe:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Pulse_Uwidth": {"scpi": ":TRIGger:PULSe:UWIDth?", "subsystem": "TRIG"},
  "Get_Trigger_Pulse_When": {"scpi": ":TRIGger:PULSe:WHEN?", "subsystem": "TRIG"},
  "Get_Trigger_Pulse_Width": {"scpi": ":TRIGger:PULSe:WIDTh?", "subsystem": "TRIG"},
  "Get_Trigger_Runt_Alevel": {"scpi": ":TRIGger:RUNT:ALEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Runt_Blevel": {"scpi": ":TRIGger:RUNT:BLEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Runt_Polarity": {"scpi": ":TRIGger:RUNT:POLarity?", "subsystem": "TRIG"},
  "Get_Trigger_Runt_Source": {"scpi": ":TRIGger:RUNT:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Runt_When": {"scpi": ":TRIGger:RUNT:WHEN?", "subsystem": "TRIG"},
  "Get_Trigger_Runt_Wlower": {"scpi": ":TRIGger:RUNT:WLOWer?", "subsystem": "TRIG"},
  "Get_Trigger_Runt_Wupper": {"scpi": ":TRIGger:RUNT:WUPPer?", "subsystem": "TRIG"},
  "Get_Trigger_Shold_Csrc": {"scpi": ":TRIGger:SHOLd:CSrc?", "subsystem": "TRIG"},
  "Get_Trigger_Shold_Dsrc": {"scpi": ":TRIGger:SHOLd:DSrc?", "subsystem": "TRIG"},
  "Get_Trigger_Shold_Htime": {"scpi": ":TRIGger:SHOLd:HTIMe?", "subsystem": "TRIG"},
  "Get_Trigger_Shold_Pattern": {"scpi": ":TRIGger:SHOLd:PATTern?", "subsystem": "TRIG"},
  "Get_Trigger_Shold_Slope": {"scpi": ":TRIGger:SHOLd:SLOPe?", "subsystem": "TRIG"},
  "Get_Trigger_Shold_Stime": {"scpi": ":TRIGger:SHOLd:STIMe?", "subsystem": "TRIG"},
  "Get_Trigger_Shold_Type": {"scpi": ":TRIGger:SHOLd:TYPe?", "subsystem": "TRIG"},
  "Get_Trigger_Slope_Alevel": {"scpi": ":TRIGger:SLOPe:ALEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Slope_Blevel": {"scpi": ":TRIGger:SLOPe:BLEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Slope_Source": {"scpi": ":TRIGger:SLOPe:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Slope_Time": {"scpi": ":TRIGger:SLOPe:TIME?", "subsystem": "TRIG"},
  "Get_Trigger_Slope_Tlower": {"scpi": ":TRIGger:SLOPe:TLOWer?", "subsystem": "TRIG"},
  "Get_Trigger_Slope_Tupper": {"scpi": ":TRIGger:SLOPe:TUPPer?", "subsystem": "TRIG"},
  "Get_Trigger_Slope_When": {"scpi": ":TRIGger:SLOPe:WHEN?", "subsystem": "TRIG"},
  "Get_Trigger_Slope_Windows": {"scpi": ":TRIGger:SLOPe:WINDow?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Clevel": {"scpi": ":TRIGger:SPI:CLEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Csrc": {"scpi": ":TRIGger:SPI:CS?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Data": {"scpi": ":TRIGger:SPI:DATA?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Dlevel": {"scpi": ":TRIGger:SPI:DLEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Mode": {"scpi": ":TRIGger:SPI:MODE?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Scl": {"scpi": ":TRIGger:SPI:SCL?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Sda": {"scpi": ":TRIGger:SPI:SDA?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Slevel": {"scpi": ":TRIGger:SPI:SLEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Slope": {"scpi": ":TRIGger:SPI:SLOPe?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Timebase": {"scpi": ":TRIGger:SPI:TIMeout?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_When": {"scpi": ":TRIGger:SPI:WHEN?", "subsystem": "TRIG"},
  "Get_Trigger_Spi_Width": {"scpi": ":TRIGger:SPI:WIDTh?", "subsystem": "TRIG"},
  "Get_Trigger_Sweep": {"scpi": ":TRIGger:SWEep?", "subsystem": "TRIG"},
  "Get_Trigger_Timebase_Slope": {"scpi": ":TRIGger:TIMeout:SLOPe?", "subsystem": "TRIG"},
  "Get_Trigger_Timebase_Source": {"scpi": ":TRIGger:TIMeout:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Timebase_Timebase": {"scpi": ":TRIGger:TIMeout:TIMe?", "subsystem": "TRIG"},
  "Get_Trigger_Video_Level": {"scpi": ":TRIGger:VIDeo:LEVel?", "description": "Commands", "subsystem": "TRIG"},
  "Get_Trigger_Video_Line": {"scpi": ":TRIGger:VIDeo:LINE?", "description": "Commands", "subsystem": "TRIG"},
  "Get_Trigger_Video_Mode": {"scpi": ":TRIGger:VIDeo:MODE?", "subsystem": "TRIG"},
  "Get_Trigger_Video_Polarity": {"scpi": ":TRIGger:VIDeo:POLarity?", "subsystem": "TRIG"},
  "Get_Trigger_Video_Source": {"scpi": ":TRIGger:VIDeo:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Video_Standard": {"scpi": ":TRIGger:VIDeo:STANdard?", "subsystem": "TRIG"},
  "Get_Trigger_Windows_Alevel": {"scpi": ":TRIGger:WINDows:ALEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Windows_Blevel": {"scpi": ":TRIGger:WINDows:BLEVel?", "subsystem": "TRIG"},
  "Get_Trigger_Windows_Positive": {"scpi": ":TRIGger:WINDows:POSition?", "subsystem": "TRIG"},
  "Get_Trigger_Windows_Slope": {"scpi": ":TRIGger:WINDows:SLOPe?", "subsystem": "TRIG"},
  "Get_Trigger_Windows_Source": {"scpi": ":TRIGger:WINDows:SOURce?", "subsystem": "TRIG"},
  "Get_Trigger_Windows_Timebase": {"scpi": ":TRIGger:WINDows:TIMe?", "subsystem": "TRIG"},

  // UART
  "Get_Uart_Baud": {"scpi": ":UART:BAUD?", "subsystem": "UART"},
  "Get_Uart_Endian": {"scpi": ":UART:ENDian?", "subsystem": "UART"},
  "Get_Uart_Parallel": {"scpi": ":UART:PARity?", "subsystem": "UART"},
  "Get_Uart_Polarity": {"scpi": ":UART:POLarity?", "subsystem": "UART"},
  "Get_Uart_Rx": {"scpi": ":UART:RX?", "subsystem": "UART"},
  "Get_Uart_Stop": {"scpi": ":UART:STOP?", "subsystem": "UART"},
  "Get_Uart_Tx": {"scpi": ":UART:TX?", "subsystem": "UART"},
  "Get_Uart_Width": {"scpi": ":UART:WIDTh?", "subsystem": "UART"},

  // VOLT
  "Get_Voltage_Level_Immediate_Amplitude": {"scpi": ":VOLTage:LEVel:IMMediate:AMPLitude?", "subsystem": "VOLT"},
  "Get_Voltage_Offset": {"scpi": ":VOLTage:OFFSet?", "subsystem": "VOLT"},

  // WAV
  "Get_Waveform_Format": {"scpi": ":WAVeform:FORMat?", "subsystem": "WAV"},
  "Get_Waveform_Mode": {"scpi": ":WAVeform:MODE?", "subsystem": "WAV"},
  "Get_Waveform_Preamble": {"scpi": ":WAVeform:PREamble?", "subsystem": "WAV"},
  "Get_Waveform_Source": {"scpi": ":WAVeform:SOURce?", "subsystem": "WAV"},
  "Get_Waveform_Start": {"scpi": ":WAVeform:STARt?", "subsystem": "WAV"},
  "Get_Waveform_Stop": {"scpi": ":WAVeform:STOP?", "description": "Commands", "subsystem": "WAV"},
  "Get_Waveform_Xorigin": {"scpi": ":WAVeform:XORigin?", "subsystem": "WAV"},
  "Get_Waveform_Xreference": {"scpi": ":WAVeform:XREFerence?", "subsystem": "WAV"},
}
```

## Spectrum — N9340B

Source: `N9340B_Programming Guide.md`

187 missing — SET 64, DO 42, NAB 81. The table has 36.

### SET — 64

```json
"set": {
  // BWID
  "Set_Bwidth_Integration": {"scpi": "BWIDth:INTegration <value>", "description": "Set the Chan Integ BW", "subsystem": "BWID"},
  "Set_Bwidth_Resolution": {"scpi": "BWIDth:RESolution <value>", "description": "Set the Channel Res BW", "subsystem": "BWID"},
  "Set_Bwidth_Video": {"scpi": "BWIDth:VIDeo <value>", "description": "Video Bandwidth", "subsystem": "BWID"},
  "Set_Bwidth_Video_Ratio": {"scpi": "BWIDth:VIDeo:RATio <value>", "description": "Video to Resolution Bandwidth Ratio", "subsystem": "BWID"},

  // CALC
  "Set_Calculate_Lline_State": {"scpi": ":CALCulate:LLINe1:STATe <value>", "description": "Limit Line Testing", "subsystem": "CALC"},

  // Common
  "Set_Ese": {"scpi": "*ESE <value>", "subsystem": "Common"},
  "Set_Sre": {"scpi": "*SRE <value>", "subsystem": "Common"},

  // DEM
  "Set_Demod_Am_State": {"scpi": ":DEMod:AM:STATe <value>", "description": "AM Demodulation", "subsystem": "DEM"},
  "Set_Demod_Fm_State": {"scpi": ":DEMod:FM:STATe <value>", "description": "FM Demodulation", "subsystem": "DEM"},

  // DISP
  "Set_Display_Mode_Brightness": {"scpi": ":DISPlay:MODE:BRIGhtness <value>", "description": "Brightness", "subsystem": "DISP"},

  // FCO
  "Set_Fcount_State": {"scpi": "FCOunt:STATe <value>", "description": "Frequency Counter Marker", "subsystem": "FCO"},

  // INST
  "Set_Instrument_Measure": {"scpi": ":INSTrument:MEASure <value>", "description": "Power Measurement", "subsystem": "INST"},
  "Set_Instrument_Select": {"scpi": ":INSTrument:SELect <value>", "description": "Instrument Mode", "subsystem": "INST"},

  // MEAS
  "Set_Measure_Acpr_Adjacent": {"scpi": ":MEASure:ACPR:ADJacent <value>", "description": "Adjacent channel", "subsystem": "MEAS"},
  "Set_Measure_Acpr_Center": {"scpi": ":MEASure:ACPR:CENTer <value>", "description": "Center Freq", "subsystem": "MEAS"},
  "Set_Measure_Acpr_Main": {"scpi": ":MEASure:ACPR:MAIN <value>", "description": "Main channel", "subsystem": "MEAS"},
  "Set_Measure_Acpr_Spacing": {"scpi": ":MEASure:ACPR:SPACe <value>", "description": "Channel space", "subsystem": "MEAS"},
  "Set_Measure_Chpower_Center": {"scpi": ":MEASure:CHPower:CENTer <value>", "description": "Center Freq", "subsystem": "MEAS"},
  "Set_Measure_Chpower_Ibw": {"scpi": ":MEASure:CHPower:IBW <value>", "subsystem": "MEAS"},
  "Set_Measure_Chpower_Span": {"scpi": ":MEASure:CHPower:SPAN <value>", "description": "Channel Span", "subsystem": "MEAS"},
  "Set_Measure_Obw_Method": {"scpi": ":MEASure:OBW:METHod <value>", "description": "Select the measurement method of OBW", "subsystem": "MEAS"},
  "Set_Measure_Obw_Percent": {"scpi": ":MEASure:OBW:PERCent <value>", "description": "Set percentage (%) method of OBW", "subsystem": "MEAS"},
  "Set_Measure_Obw_Xdb": {"scpi": ":MEASure:OBW:XDB <value>", "description": "Set dBc method of OBW", "subsystem": "MEAS"},
  "Set_Measure_Semask_Average_Count": {"scpi": ":MEASure:SEMask:AVERage:COUNt <value>", "description": "Set the Average", "subsystem": "MEAS"},
  "Set_Measure_Semask_Average_State": {"scpi": ":MEASure:SEMask:AVERage:STATe <value>", "description": "Set the Average", "subsystem": "MEAS"},
  "Set_Measure_Semask_Carrier_Power": {"scpi": ":MEASure:SEMask:CARRier:POWer <value>", "description": "Set Total Power Reference", "subsystem": "MEAS"},
  "Set_Measure_Semask_Frequency_Center": {"scpi": "MEASure:SEMask:FREQuency:CENTer <value>", "description": "Set Center Frequency", "subsystem": "MEAS"},
  "Set_Measure_Semask_Frequency_Span": {"scpi": ":MEASure:SEMask:FREQuency:SPAN <value>", "description": "Set Chan Span", "subsystem": "MEAS"},
  "Set_Measure_Semask_Offset_List_Frequency_Start": {"scpi": ":MEASure:SEMask:OFFSet:LIST:FREQuency:STARt <value>", "description": "Set the Start Freq", "subsystem": "MEAS"},
  "Set_Measure_Semask_Offset_List_Start_Absolute": {"scpi": ":MEASure:SEMask:OFFSet:LIST:STARt:ABSolute <value>", "description": "Set the Abs Start", "subsystem": "MEAS"},
  "Set_Measure_Semask_Offset_List_Start_Rcarrier": {"scpi": ":MEASure:SEMask:OFFSet:LIST:STARt:RCARrier <value>", "description": "Set the Rel Start", "subsystem": "MEAS"},
  "Set_Measure_Semask_Offset_List_State": {"scpi": ":MEASure:SEMask:OFFSet:LIST:STATe <value>", "description": "Set the Start Freq", "subsystem": "MEAS"},
  "Set_Measure_Semask_Offset_List_Sweep": {"scpi": ":MEASure:SEMask:OFFSet:LIST:SWEeptime <value>", "description": "Set the Sweep Time", "subsystem": "MEAS"},
  "Set_Measure_Semask_Offset_List_Test": {"scpi": ":MEASure:SEMask:OFFSet:LIST:TEST <value>", "description": "Set the Fail Mask", "subsystem": "MEAS"},
  "Set_Measure_Semask_Sweep": {"scpi": ":MEASure:SEMask:SWEeptime <value>", "description": "Set the Sweep Time", "subsystem": "MEAS"},

  // SCAL
  "Set_Scale_Pdivision": {"scpi": ":SCALe:PDIVision <value>", "description": "Trace Y-Axis Scaling", "subsystem": "SCAL"},
  "Set_Scale_Rlevel_Offset": {"scpi": ":SCALe:RLEVel:OFFSet <value>", "description": "Trace Y-Axis Reference Level", "subsystem": "SCAL"},
  "Set_Scale_Spacing": {"scpi": ":SCALe:SPACing <value>", "description": "Vertical Axis Scaling", "subsystem": "SCAL"},

  // SENS
  "Set_Sense_Frequency_Center": {"scpi": "SENS:FREQ:CENT <value>", "description": "Using C with Marker Peak Search and Peak Excursion", "subsystem": "SENS"},
  "Set_Sense_Frequency_Center_Step_Increment": {"scpi": ":SENSe:FREQuency:CENTer:STEP:INCRement <value>", "description": "Center Frequency Step Size", "subsystem": "SENS"},
  "Set_Sense_Frequency_Span": {"scpi": "SENS:FREQ:SPAN <value>", "description": "Using C with Marker Peak Search and Peak Excursion", "subsystem": "SENS"},
  "Set_Sense_Frequency_Start": {"scpi": "SENS:FREQ:STAR <value>", "subsystem": "SENS"},
  "Set_Sense_Frequency_Stop": {"scpi": ":SENS:FREQ:STOP <value>", "description": "Stop Frequency", "subsystem": "SENS"},
  "Set_Sense_Power_Rf_Attenuation": {"scpi": ":SENSe:POWer:RF:ATTenuation <value>", "description": "Input Attenuation", "subsystem": "SENS"},
  "Set_Sense_Power_Rf_Gain_State": {"scpi": ":SENSe:POWer:RF:GAIN:STATe <value>", "description": "Input Port Power Gain", "subsystem": "SENS"},
  "Set_Sense_Sweep_Tdmode": {"scpi": ":SENSe:SWEep:TDMode <value>", "subsystem": "SENS"},

  // SYST
  "Set_System_Channel": {"scpi": ":SYSTem:CHANnel <value>", "description": "Low Frequency Channel", "subsystem": "SYST"},
  "Set_System_Configure_Port": {"scpi": ":SYSTem:CONFigure:PORT <value>", "description": "Power on Type", "subsystem": "SYST"},
  "Set_System_Date": {"scpi": ":SYSTem:DATE <value>", "description": "Set Date", "subsystem": "SYST"},
  "Set_System_Time": {"scpi": ":SYSTem:TIME <value>", "description": "Set Time", "subsystem": "SYST"},

  // TGEN
  "Set_Tgenerator_Amplitude": {"scpi": ":TGENerator:AMPLitude <value>", "description": "Output Amplitdue", "subsystem": "TGEN"},
  "Set_Tgenerator_Amplitude_State": {"scpi": ":TGENerator:AMPLitude:STATe <value>", "description": "Amplitude On/Off", "subsystem": "TGEN"},
  "Set_Tgenerator_Amplitude_Step": {"scpi": ":TGENerator:AMPLitude:STEP <value>", "description": "Amplitude Step", "subsystem": "TGEN"},
  "Set_Tgenerator_Normalize_Level": {"scpi": ":TGENerator:NORMalize:LEVel <value>", "description": "Normalization Reference Level", "subsystem": "TGEN"},
  "Set_Tgenerator_Normalize_Posn": {"scpi": ":TGENerator:NORMalize:POSN <value>", "description": "Normalization Reference Position", "subsystem": "TGEN"},
  "Set_Tgenerator_Normalize_State": {"scpi": ":TGENerator:NORMalize:STATe <value>", "description": "Normalization", "subsystem": "TGEN"},
  "Set_Tgenerator_Normalize_Trace": {"scpi": ":TGENerator:NORMalize:TRACe <value>", "description": "Reference Trace", "subsystem": "TGEN"},

  // TRAC
  "Set_Trace_Format": {"scpi": ":TRACe:FORMat <value>", "description": "Trace format", "subsystem": "TRAC"},

  // TRIG
  "Set_Trigger_Sequence_Delaytime": {"scpi": ":TRIGger:SEQuence:DELaytime <value>", "description": "Trigger Delay Time", "subsystem": "TRIG"},
  "Set_Trigger_Sequence_External_Slope": {"scpi": ":TRIGger:SEQuence:EXTernal1:SLOPe <value>", "description": "External Trigger Slope", "subsystem": "TRIG"},
  "Set_Trigger_Sequence_Source": {"scpi": ":TRIGger:SEQuence:SOURce <value>", "description": "Initiate a Single Sweep", "subsystem": "TRIG"},
  "Set_Trigger_Sequence_Video_Level": {"scpi": ":TRIGger:SEQuence:VIDeo:LEVel <value>", "description": "Command Example", "subsystem": "TRIG"},

  // UNIT
  "Set_Unit_Power": {"scpi": "UNIT:POW <value>", "description": "Using C with Marker Peak Search and Peak Excursion", "subsystem": "UNIT"},
  "Set_Unit_Power_Emf": {"scpi": ":UNIT:POWer:EMF <value>", "description": "EMF Mode", "subsystem": "UNIT"},
}
```

### DO — 42

```json
"do": {
  // CAL
  "Do_Calibration_Source_State": {"scpi": "CAL:SOUR:STAT", "description": "Using C with Marker Peak Search and Peak Excursion", "subsystem": "CAL"},

  // CALC
  "Do_Calculate_Lline": {"scpi": ":CALCulate:LLINe<n>", "description": "Limit Line Y-axis Value", "subsystem": "CALC"},
  "Do_Calculate_Lline_Buzzer_Statoff": {"scpi": ":CALCulate:LLINe1:BUZZer:STATe OFF", "description": "Turn on/off the Buzzer", "subsystem": "CALC"},
  "Do_Calculate_Marker": {"scpi": ":CALCulate:MARKer<n>", "subsystem": "CALC"},
  "Do_Calculate_Marker_Fcount": {"scpi": ":CALCulate:MARKer1:FCOunt", "description": "Frequency Counter Marker", "subsystem": "CALC"},
  "Do_Calculate_Marker_Mode": {"scpi": "CALC:MARK:MODE", "subsystem": "CALC"},
  "Do_Calculate_Marker_Peak_Exc": {"scpi": "CALC:MARK:PEAK:EXC", "subsystem": "CALC"},
  "Do_Calculate_Marker_Peak_Thr": {"scpi": "CALC:MARK:PEAK:THR", "subsystem": "CALC"},
  "Do_Calculate_Marker_Peak_Thr_State": {"scpi": "CALC:MARK:PEAK:THR:STAT", "subsystem": "CALC"},
  "Do_Calculate_Marker_Phn": {"scpi": "CALC:MARK1:PHN", "subsystem": "CALC"},
  "Do_Calculate_Phn_Offset": {"scpi": "CALC:PHN:OFFS", "subsystem": "CALC"},

  // Common
  "Do_Cls": {"scpi": "*CLS", "subsystem": "Common"},
  "Do_Opc": {"scpi": "*OPC", "subsystem": "Common"},
  "Do_Rst": {"scpi": "*RST", "subsystem": "Common"},
  "Do_Trg": {"scpi": "*TRG", "subsystem": "Common"},
  "Do_Wai": {"scpi": "*WAI", "subsystem": "Common"},

  // DISP
  "Do_Display_Window_Trace": {"scpi": ":DISPlay:WINDow:TRACe", "description": "Trace Y-Axis Scaling", "subsystem": "DISP"},

  // MEAS
  "Do_Measure_Semask_Bandwidth": {"scpi": ":MEASure:SEMask:BANDwidth", "description": "Set the Chan Integ BW", "subsystem": "MEAS"},
  "Do_Measure_Semask_Bandwidth_Integration": {"scpi": ":MEAS:SEM:BAND:INT", "subsystem": "MEAS"},
  "Do_Measure_Semask_Bwidth": {"scpi": "MEAS:SEM:BWID", "subsystem": "MEAS"},
  "Do_Measure_Semask_Bwidth_Integration": {"scpi": ":MEAS:SEM:BWID:INT", "subsystem": "MEAS"},
  "Do_Measure_Semask_Marker": {"scpi": "MEASure:SEMask:MARKer<n>", "description": "Turn On/Off the Marker", "subsystem": "MEAS"},
  "Do_Measure_Semask_Offset_List_Bandwidth": {"scpi": "MEASure:SEMask:OFFSet:LIST:BAND", "description": "Set the Channel Res BW", "subsystem": "MEAS"},
  "Do_Measure_Semask_Offset_List_Stop_Absolute": {"scpi": ":MEAS:SEM:OFFS:LIST:STOP:ABS", "description": "Set the Abs Stop", "subsystem": "MEAS"},
  "Do_Measure_Semask_Offset_List_Stop_Absolute_Cou": {"scpi": ":MEASure:SEMask:OFFSet:LIST:STOP:ABSolute:COU", "description": "Set the Abs Stop", "subsystem": "MEAS"},
  "Do_Measure_Semask_Offset_List_Stop_Rcarrier": {"scpi": ":MEAS:SEM:OFFS:LIST:STOP:RCAR", "subsystem": "MEAS"},
  "Do_Measure_Semask_Offset_List_Stop_Rcarrier_Cou": {"scpi": ":MEASure:SEMask:OFFSet:LIST:STOP:RCARrier:COU", "subsystem": "MEAS"},

  // SENS
  "Do_Sense_Average": {"scpi": ":SENSe:AVERage", "subsystem": "SENS"},
  "Do_Sense_Average_Trace": {"scpi": ":SENSe:AVERage:TRACe<n>", "description": "Set the Average Count", "subsystem": "SENS"},
  "Do_Sense_Bandwidth": {"scpi": ":SENSe:BANDwidth", "subsystem": "SENS"},
  "Do_Sense_Detector": {"scpi": ":SENSe:DETector", "subsystem": "SENS"},
  "Do_Sense_Detector_Funcneg": {"scpi": ":SENSe:DETector:FUNCtionNEGative", "description": "Type of Detection", "subsystem": "SENS"},
  "Do_Sense_Frequency": {"scpi": ":SENSe:FREQuency", "subsystem": "SENS"},
  "Do_Sense_Frequency_Span_Full": {"scpi": ":SENSe:FREQuency:SPAN:FULL", "description": "Full Frequency Span", "subsystem": "SENS"},
  "Do_Sense_Frequency_Span_Previous": {"scpi": ":SENSe:FREQuency:SPAN:PREVious", "description": "Last Frequency Span", "subsystem": "SENS"},
  "Do_Sense_Frequency_Span_Zero": {"scpi": ":SENSe:FREQuency:SPAN:ZERO", "description": "DEMOdulation Subsystem", "subsystem": "SENS"},
  "Do_Sense_Power": {"scpi": ":SENSe:POWer", "subsystem": "SENS"},
  "Do_Sense_Sweep": {"scpi": ":SENSe:SWEep", "subsystem": "SENS"},

  // SYST
  "Do_System_File_Save": {"scpi": ":SYSTem:FILE:SAVE", "description": "Screen save", "subsystem": "SYST"},
  "Do_System_Preset": {"scpi": ":SYSTem:PRESet", "subsystem": "SYST"},

  // TGEN
  "Do_Tgenerator_Amplitude_Offset": {"scpi": ":TGENerator:AMPLitude:OFFSet", "description": "Amplitude Offset", "subsystem": "TGEN"},
  "Do_Tgenerator_Normalize_Ref": {"scpi": ":TGENerator:NORMalize:REF", "description": "Storing as Reference", "subsystem": "TGEN"},
}
```

### NAB — 81

```json
"nab": {
  // BWID
  "Get_Bwidth_Integration": {"scpi": "BWIDth:INTegration?", "description": "Set the Chan Integ BW", "subsystem": "BWID"},
  "Get_Bwidth_Resolution": {"scpi": "BWIDth:RESolution?", "description": "Set the Channel Res BW", "subsystem": "BWID"},
  "Get_Bwidth_Video": {"scpi": "BWIDth:VIDeo?", "description": "Video Bandwidth", "subsystem": "BWID"},
  "Get_Bwidth_Video_Ratio": {"scpi": "BWIDth:VIDeo:RATio?", "description": "Video to Resolution Bandwidth Ratio", "subsystem": "BWID"},

  // CALC
  "Get_Calculate_Lline_Buzzer_State": {"scpi": ":CALCulate:LLINe1:BUZZer:STATe?", "description": "Turn on/off the Buzzer", "subsystem": "CALC"},
  "Get_Calculate_Lline_State": {"scpi": ":CALCulate:LLINe1:STATe?", "description": "Limit Line Testing", "subsystem": "CALC"},

  // Common
  "Get_Ese": {"scpi": "*ESE?", "subsystem": "Common"},
  "Get_Esr": {"scpi": "*ESR?", "subsystem": "Common"},
  "Get_Idn": {"scpi": "*IDN?", "subsystem": "Common"},
  "Get_Opc": {"scpi": "*OPC?", "subsystem": "Common"},
  "Get_Sre": {"scpi": "*SRE?", "subsystem": "Common"},
  "Get_Stb": {"scpi": "*STB?", "subsystem": "Common"},
  "Get_Tst": {"scpi": "*TST?", "subsystem": "Common"},

  // DEM
  "Get_Demod_Am_State": {"scpi": ":DEMod:AM:STATe?", "description": "AM Demodulation", "subsystem": "DEM"},
  "Get_Demod_Fm_State": {"scpi": ":DEMod:FM:STATe?", "description": "FM Demodulation", "subsystem": "DEM"},

  // DISP
  "Get_Display_Mode_Brightness": {"scpi": ":DISPlay:MODE:BRIGhtness?", "description": "Brightness", "subsystem": "DISP"},

  // FCO
  "Get_Fcount_State": {"scpi": "FCOunt:STATe?", "description": "Frequency Counter Marker", "subsystem": "FCO"},

  // INST
  "Get_Instrument_Measure": {"scpi": ":INSTrument:MEASure?", "description": "Power Measurement", "subsystem": "INST"},
  "Get_Instrument_Select": {"scpi": ":INSTrument:SELect?", "description": "Instrument Mode", "subsystem": "INST"},

  // MEAS
  "Get_Measure_Acpr_Adjacent": {"scpi": ":MEASure:ACPR:ADJacent?", "description": "Adjacent channel", "subsystem": "MEAS"},
  "Get_Measure_Acpr_Center": {"scpi": ":MEASure:ACPR:CENTer?", "description": "Center Freq", "subsystem": "MEAS"},
  "Get_Measure_Acpr_Lpower": {"scpi": ":MEASure:ACPR:LPOWer?", "description": "Low Adjacent Channel Power", "subsystem": "MEAS"},
  "Get_Measure_Acpr_Lratio": {"scpi": ":MEASure:ACPR:LRATio?", "description": "Low Adjacent Channel Power Ratio", "subsystem": "MEAS"},
  "Get_Measure_Acpr_Main": {"scpi": ":MEASure:ACPR:MAIN?", "description": "Main channel", "subsystem": "MEAS"},
  "Get_Measure_Acpr_Mpower": {"scpi": ":MEASure:ACPR:MPOWer?", "description": "Main Channel Power", "subsystem": "MEAS"},
  "Get_Measure_Acpr_Spacing": {"scpi": ":MEASure:ACPR:SPACe?", "description": "Channel space", "subsystem": "MEAS"},
  "Get_Measure_Acpr_Upower": {"scpi": ":MEASure:ACPR:UPOWer?", "description": "Upper Adjacent Channel Power", "subsystem": "MEAS"},
  "Get_Measure_Acpr_Uratio": {"scpi": ":MEASure:ACPR:URATio?", "description": "Upper Adjacent Channel Power Ratio", "subsystem": "MEAS"},
  "Get_Measure_Chpower": {"scpi": ":MEASure:CHPower?", "description": "Channel Power and Density", "subsystem": "MEAS"},
  "Get_Measure_Chpower_Center": {"scpi": ":MEASure:CHPower:CENTer?", "description": "Center Freq", "subsystem": "MEAS"},
  "Get_Measure_Chpower_Chpower": {"scpi": ":MEASure:CHPower:CHPower?", "description": "Channel Power and Density", "subsystem": "MEAS"},
  "Get_Measure_Chpower_Density": {"scpi": ":MEASure:CHPower:DENSity?", "description": "Channel Power and Density", "subsystem": "MEAS"},
  "Get_Measure_Chpower_Ibw": {"scpi": ":MEASure:CHPower:IBW?", "subsystem": "MEAS"},
  "Get_Measure_Chpower_Span": {"scpi": ":MEASure:CHPower:SPAN?", "description": "Channel Span", "subsystem": "MEAS"},
  "Get_Measure_Obw_Method": {"scpi": ":MEASure:OBW:METHod?", "description": "Select the measurement method of OBW", "subsystem": "MEAS"},
  "Get_Measure_Obw_Percent": {"scpi": ":MEASure:OBW:PERCent?", "description": "Set percentage (%) method of OBW", "subsystem": "MEAS"},
  "Get_Measure_Obw_Xdb": {"scpi": ":MEASure:OBW:XDB?", "description": "Set dBc method of OBW", "subsystem": "MEAS"},
  "Get_Measure_Semask_Average_Count": {"scpi": ":MEASure:SEMask:AVERage:COUNt?", "description": "Set the Average", "subsystem": "MEAS"},
  "Get_Measure_Semask_Average_State": {"scpi": ":MEASure:SEMask:AVERage:STATe?", "description": "Set the Average", "subsystem": "MEAS"},
  "Get_Measure_Semask_Carrier_Power": {"scpi": ":MEASure:SEMask:CARRier:POWer?", "description": "Set Total Power Reference", "subsystem": "MEAS"},
  "Get_Measure_Semask_Frequency_Center": {"scpi": "MEASure:SEMask:FREQuency:CENTer?", "description": "Set Center Frequency", "subsystem": "MEAS"},
  "Get_Measure_Semask_Frequency_Span": {"scpi": ":MEASure:SEMask:FREQuency:SPAN?", "description": "Set Chan Span", "subsystem": "MEAS"},
  "Get_Measure_Semask_Offset_List_Frequency_Start": {"scpi": ":MEASure:SEMask:OFFSet:LIST:FREQuency:STARt?", "description": "Set the Start Freq", "subsystem": "MEAS"},
  "Get_Measure_Semask_Offset_List_Frequency_Stop": {"scpi": ":MEASure:SEMask:OFFSet:LIST:FREQuency:STOP?", "description": "Set the Stop Freq", "subsystem": "MEAS"},
  "Get_Measure_Semask_Offset_List_Start_Absolute": {"scpi": ":MEASure:SEMask:OFFSet:LIST:STARt:ABSolute?", "description": "Set the Abs Start", "subsystem": "MEAS"},
  "Get_Measure_Semask_Offset_List_Start_Rcarrier": {"scpi": ":MEASure:SEMask:OFFSet:LIST:STARt:RCARrier?", "subsystem": "MEAS"},
  "Get_Measure_Semask_Offset_List_State": {"scpi": ":MEASure:SEMask:OFFSet:LIST:STATe?", "description": "Set the Start Freq", "subsystem": "MEAS"},
  "Get_Measure_Semask_Offset_List_Sweep": {"scpi": ":MEASure:SEMask:OFFSet:LIST:SWEeptime?", "description": "Set the Sweep Time", "subsystem": "MEAS"},
  "Get_Measure_Semask_Offset_List_Test": {"scpi": ":MEASure:SEMask:OFFSetn:LIST:TEST?", "description": "Set the Fail Mask", "subsystem": "MEAS"},
  "Get_Measure_Semask_Sweep": {"scpi": ":MEASure:SEMask:SWEeptime?", "description": "Set the Sweep Time", "subsystem": "MEAS"},

  // SCAL
  "Get_Scale_Pdivision": {"scpi": ":SCALe:PDIVision?", "description": "Trace Y-Axis Scaling", "subsystem": "SCAL"},
  "Get_Scale_Rlevel_Offset": {"scpi": ":SCALe:RLEVel:OFFSet?", "description": "Trace Y-Axis Reference Level", "subsystem": "SCAL"},
  "Get_Scale_Spacing": {"scpi": ":SCALe:SPACing?", "description": "Vertical Axis Scaling", "subsystem": "SCAL"},

  // SENS
  "Get_Sense_Detector_Function": {"scpi": ":SENSe:DETector:FUNCtion?", "description": "Type of Detection", "subsystem": "SENS"},
  "Get_Sense_Frequency_Center": {"scpi": ":SENSe:FREQuency:CENTer?", "description": "Center Frequency", "subsystem": "SENS"},
  "Get_Sense_Frequency_Center_Step_Increment": {"scpi": ":SENSe:FREQuency:CENTer:STEP:INCRement?", "description": "Center Frequency Step Size", "subsystem": "SENS"},
  "Get_Sense_Frequency_Span": {"scpi": ":SENSe:FREQuency:SPAN?", "description": "Frequency Span", "subsystem": "SENS"},
  "Get_Sense_Frequency_Start": {"scpi": ":SENSe:FREQuency:STARt?", "description": "Start Frequency", "subsystem": "SENS"},
  "Get_Sense_Frequency_Stop": {"scpi": ":SENSe:FREQuency:STOP?", "description": "Stop Frequency", "subsystem": "SENS"},
  "Get_Sense_Power_Rf_Attenuation": {"scpi": ":SENSe:POWer:RF:ATTenuation?", "description": "Input Attenuation", "subsystem": "SENS"},
  "Get_Sense_Power_Rf_Gain_State": {"scpi": ":SENSe:POWer:RF:GAIN:STATe?", "description": "Input Port Power Gain", "subsystem": "SENS"},
  "Get_Sense_Sweep_Tdmode": {"scpi": ":SENSe:SWEep:TDMode?", "subsystem": "SENS"},

  // SYST
  "Get_System_Channel": {"scpi": ":SYSTem:CHANnel?", "description": "Low Frequency Channel", "subsystem": "SYST"},
  "Get_System_Configure_Port": {"scpi": ":SYSTem:CONFigure:PORT?", "description": "Power on Type", "subsystem": "SYST"},
  "Get_System_Date": {"scpi": ":SYSTem:DATE?", "description": "Set Date", "subsystem": "SYST"},
  "Get_System_Error_Next": {"scpi": ":SYSTem:ERRor:NEXT?", "description": "Error Information Query", "subsystem": "SYST"},
  "Get_System_Time": {"scpi": ":SYSTem:TIME?", "description": "Set Time", "subsystem": "SYST"},

  // TGEN
  "Get_Tgenerator_Amplitude": {"scpi": ":TGENerator:AMPLitude?", "description": "Output Amplitdue", "subsystem": "TGEN"},
  "Get_Tgenerator_Amplitude_State": {"scpi": ":TGENerator:AMPLitude:STATe?", "description": "Amplitude On/Off", "subsystem": "TGEN"},
  "Get_Tgenerator_Amplitude_Step": {"scpi": ":TGENerator:AMPLitude:STEP?", "description": "Amplitude Step", "subsystem": "TGEN"},
  "Get_Tgenerator_Normalize_Level": {"scpi": ":TGENerator:NORMalize:LEVel?", "description": "Normalization Reference Level", "subsystem": "TGEN"},
  "Get_Tgenerator_Normalize_Posn": {"scpi": ":TGENerator:NORMalize:POSN?", "description": "Normalization Reference Position", "subsystem": "TGEN"},
  "Get_Tgenerator_Normalize_State": {"scpi": ":TGENerator:NORMalize:STATe?", "description": "Normalization", "subsystem": "TGEN"},
  "Get_Tgenerator_Normalize_Trace": {"scpi": ":TGENerator:NORMalize:TRACe?", "description": "Reference Trace", "subsystem": "TGEN"},

  // TRAC
  "Get_Trace_Format": {"scpi": ":TRACe:FORMat?", "description": "Trace format", "subsystem": "TRAC"},

  // TRIG
  "Get_Trigger_Sequence_Delaytime": {"scpi": ":TRIGger:SEQuence:DELaytime?", "description": "Trigger Delay Time", "subsystem": "TRIG"},
  "Get_Trigger_Sequence_External_Slope": {"scpi": ":TRIGger:SEQuence:EXTernal1:SLOPe?", "description": "External Trigger Slope", "subsystem": "TRIG"},
  "Get_Trigger_Sequence_Source": {"scpi": ":TRIGger:SEQuence:SOURce?", "description": "Trigger Source", "subsystem": "TRIG"},
  "Get_Trigger_Sequence_Video_Level": {"scpi": ":TRIGger:SEQuence:VIDeo:LEVel?", "description": "Video Trigger Level Amplitude", "subsystem": "TRIG"},

  // UNIT
  "Get_Unit_Power": {"scpi": ":UNIT:POWer?", "description": "Select Power Units of Measure", "subsystem": "UNIT"},
  "Get_Unit_Power_Emf": {"scpi": ":UNIT:POWer:EMF?", "description": "EMF Mode", "subsystem": "UNIT"},
}
```


---

# Addendum — the two PDFs, read directly

Added 2026-07-27, after the sweep above reported these two models as
unreachable. Both are now in the tables.

## `Distortion/Porta_one` — the .md was not lossy, it was shifted

The markdown conversion produced mojibake and I reported no SCPI as
recoverable. That was true of the markdown and wrong about the PDF: the PDF
**does** carry a text layer, and its font uses a custom encoding offset by a
constant **29**. Every code point shifted back by 29 recovers the document
exactly — `DQ\x03IRUP` is `any form`. No OCR was needed.

- **573 commands found, 286 of them queries.**
- **286 carry the manual's own summary sentence**, taken from the gloss
  printed under each command header.
- The table held 35 commands, all in the older AP-Mode notation; **573 were added**.

## `Load/6060B` — a 93-page scan, no text layer, no OCR available

`pdftotext` returns 93 characters for the whole document and there is one
image per page; `tesseract` is not installed. So this one was read visually,
and what is transcribed below is **Table 4-1, "Summary of Commands and
Parameters"** (printed page 4-67) — the manual's own complete, authoritative
list, rather than a regex sweep of prose.

The operator manual was right that the dictionary lives here: the sweep found
50 commands from scattered examples, the real language is HPSL with these
**66 command and query forms** absent from the table.

Three aliases the summary table documents, worth knowing before binding:

- `INST` is an alias for `CHAN`
- `OUTP` is an alias for `INP`
- `FUNC` is an alias for `MODE`

Every settable node also accepts `MIN` and `MAX` as query arguments
(`CURR:SLEW? MAX`), which is a per-model limit sheet the instrument will tell
you itself — a better source for `model.json` domains than the datasheet.

## Added to `6060B` — 66

### SET — 20

```json
"set": {
  "Set_Chan": {"scpi": "CHAN <value>", "description": "Select the electronic load channel this command stream addresses (INST is an alias)", "subsystem": "CHAN", "args": ["value"], "unverified": true},
  "Set_Curr_Lev_Trig": {"scpi": "CURR:LEV:TRIG <value>", "description": "Set the current level the load takes on when triggered", "subsystem": "CURR", "args": ["value"], "unverified": true},
  "Set_Curr_Prot_Del": {"scpi": "CURR:PROT:DEL <value>", "description": "Set how long an overcurrent may persist before the input is turned off", "subsystem": "CURR", "args": ["value"], "unverified": true},
  "Set_Curr_Prot_Lev": {"scpi": "CURR:PROT:LEV <value>", "description": "Set the overcurrent protection level", "subsystem": "CURR", "args": ["value"], "unverified": true},
  "Set_Curr_Prot_Stat": {"scpi": "CURR:PROT:STAT <value>", "description": "Enable or disable overcurrent protection", "subsystem": "CURR", "args": ["value"], "unverified": true},
  "Set_Inp_Shor_Stat": {"scpi": "INP:SHOR:STAT <value>", "description": "Close or open the input short across the load terminals", "subsystem": "INP", "args": ["value"], "unverified": true},
  "Set_Port0": {"scpi": "PORT0 <value>", "description": "Set the state of the rear-panel digital port 0 output", "subsystem": "PORT0", "args": ["value"], "unverified": true},
  "Set_Res_Lev_Trig": {"scpi": "RES:LEV:TRIG <value>", "description": "Set the resistance the load takes on when triggered", "subsystem": "RES", "args": ["value"], "unverified": true},
  "Set_Res_Rang": {"scpi": "RES:RANG <value>", "description": "Set the resistance range", "subsystem": "RES", "args": ["value"], "unverified": true},
  "Set_Res_Tlev": {"scpi": "RES:TLEV <value>", "description": "Set the transient resistance level", "subsystem": "RES", "args": ["value"], "unverified": true},
  "Set_Stat_Chan_Enab": {"scpi": "STAT:CHAN:ENAB <value>", "description": "Set which channel status bits are summarised into Channel Summary", "subsystem": "STAT", "args": ["value"], "unverified": true},
  "Set_Stat_Csum_Enab": {"scpi": "STAT:CSUM:ENAB <value>", "description": "Set which channels are summarised into the Status Byte CSUM bit", "subsystem": "STAT", "args": ["value"], "unverified": true},
  "Set_Stat_Oper_Enab": {"scpi": "STAT:OPER:ENAB <value>", "description": "Set the Operation Status enable mask", "subsystem": "STAT", "args": ["value"], "unverified": true},
  "Set_Stat_Oper_Ntr": {"scpi": "STAT:OPER:NTR <value>", "description": "Set the Operation Status negative-transition filter", "subsystem": "STAT", "args": ["value"], "unverified": true},
  "Set_Stat_Oper_Ptr": {"scpi": "STAT:OPER:PTR <value>", "description": "Set the Operation Status positive-transition filter", "subsystem": "STAT", "args": ["value"], "unverified": true},
  "Set_Stat_Ques_Enab": {"scpi": "STAT:QUES:ENAB <value>", "description": "Set the Questionable Status enable mask", "subsystem": "STAT", "args": ["value"], "unverified": true},
  "Set_Tran_Twid": {"scpi": "TRAN:TWID <value>", "description": "Set the transient pulse width", "subsystem": "TRAN", "args": ["value"], "unverified": true},
  "Set_Trig_Sour": {"scpi": "TRIG:SOUR <value>", "description": "Select the trigger source \u2014 BUS, EXT, HOLD, LINE or TIM", "subsystem": "TRIG", "args": ["value"], "unverified": true},
  "Set_Trig_Tim": {"scpi": "TRIG:TIM <value>", "description": "Set the internal trigger timer period", "subsystem": "TRIG", "args": ["value"], "unverified": true},
  "Set_Volt_Lev_Trig": {"scpi": "VOLT:LEV:TRIG <value>", "description": "Set the voltage level the load takes on when triggered", "subsystem": "VOLT", "args": ["value"], "unverified": true},
}
```

### DO — 2

```json
"do": {
  "Do_Abor": {"scpi": "ABOR", "description": "Abort the transient or trigger operation in progress", "subsystem": "ABOR", "unverified": true},
  "Do_Trig_Imm": {"scpi": "TRIG:IMM", "description": "Trigger immediately, whatever the selected trigger source", "subsystem": "TRIG", "unverified": true},
}
```

### NAB — 44

```json
"nab": {
  "Get_Chan": {"scpi": "CHAN?", "description": "Query the selected channel", "subsystem": "CHAN?", "unverified": true},
  "Get_Curr": {"scpi": "CURR?", "description": "Query the programmed main current level", "subsystem": "CURR?", "unverified": true},
  "Get_Curr_Lev_Trig": {"scpi": "CURR:LEV:TRIG?", "description": "Query the triggered current level", "subsystem": "CURR", "unverified": true},
  "Get_Curr_Prot_Del": {"scpi": "CURR:PROT:DEL?", "description": "Query the overcurrent protection delay", "subsystem": "CURR", "unverified": true},
  "Get_Curr_Prot_Lev": {"scpi": "CURR:PROT:LEV?", "description": "Query the overcurrent protection level", "subsystem": "CURR", "unverified": true},
  "Get_Curr_Prot_Stat": {"scpi": "CURR:PROT:STAT?", "description": "Query whether overcurrent protection is enabled", "subsystem": "CURR", "unverified": true},
  "Get_Curr_Rang": {"scpi": "CURR:RANG?", "description": "Query the current range", "subsystem": "CURR", "unverified": true},
  "Get_Curr_Slew": {"scpi": "CURR:SLEW?", "description": "Query the current slew rate", "subsystem": "CURR", "unverified": true},
  "Get_Curr_Tlev": {"scpi": "CURR:TLEV?", "description": "Query the transient current level", "subsystem": "CURR", "unverified": true},
  "Get_Inp_Shor_Stat": {"scpi": "INP:SHOR:STAT?", "description": "Query the input short state", "subsystem": "INP", "unverified": true},
  "Get_Inp_Stat": {"scpi": "INP:STAT?", "description": "Query whether the load input is on (OUTP is an alias for INP)", "subsystem": "INP", "unverified": true},
  "Get_Meas_Curr_Dc": {"scpi": "MEAS:CURR:DC?", "description": "Measure the DC current flowing into the load", "subsystem": "MEAS", "unverified": true},
  "Get_Meas_Pow_Dc": {"scpi": "MEAS:POW:DC?", "description": "Measure the DC power being dissipated", "subsystem": "MEAS", "unverified": true},
  "Get_Meas_Volt_Dc": {"scpi": "MEAS:VOLT:DC?", "description": "Measure the DC voltage across the load input", "subsystem": "MEAS", "unverified": true},
  "Get_Mode": {"scpi": "MODE?", "description": "Query the operating mode \u2014 CURR, RES or VOLT (FUNC is an alias)", "subsystem": "MODE?", "unverified": true},
  "Get_Rdt": {"scpi": "*RDT?", "description": "Return the device identification / topology string", "subsystem": "RDT?", "unverified": true},
  "Get_Res": {"scpi": "RES?", "description": "Query the programmed main resistance level", "subsystem": "RES?", "unverified": true},
  "Get_Res_Lev_Trig": {"scpi": "RES:LEV:TRIG?", "description": "Query the triggered resistance level", "subsystem": "RES", "unverified": true},
  "Get_Res_Rang": {"scpi": "RES:RANG?", "description": "Query the resistance range", "subsystem": "RES", "unverified": true},
  "Get_Res_Tlev": {"scpi": "RES:TLEV?", "description": "Query the transient resistance level", "subsystem": "RES", "unverified": true},
  "Get_Stat_Chan_Cond": {"scpi": "STAT:CHAN:COND?", "description": "Read the Channel Status condition register \u2014 the live fault state", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Chan_Enab": {"scpi": "STAT:CHAN:ENAB?", "description": "Query the Channel Status enable mask", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Chan_Even": {"scpi": "STAT:CHAN:EVEN?", "description": "Read and clear the Channel Status event register", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Csum_Enab": {"scpi": "STAT:CSUM:ENAB?", "description": "Query the Channel Summary enable mask", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Csum_Even": {"scpi": "STAT:CSUM:EVEN?", "description": "Read and clear the Channel Summary event register", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Oper_Cond": {"scpi": "STAT:OPER:COND?", "description": "Read the Operation Status condition register", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Oper_Enab": {"scpi": "STAT:OPER:ENAB?", "description": "Query the Operation Status enable mask", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Oper_Even": {"scpi": "STAT:OPER:EVEN?", "description": "Read and clear the Operation Status event register", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Oper_Ntr": {"scpi": "STAT:OPER:NTR?", "description": "Query the Operation Status negative-transition filter", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Oper_Ptr": {"scpi": "STAT:OPER:PTR?", "description": "Query the Operation Status positive-transition filter", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Ques_Cond": {"scpi": "STAT:QUES:COND?", "description": "Read the Questionable Status condition register", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Ques_Enab": {"scpi": "STAT:QUES:ENAB?", "description": "Query the Questionable Status enable mask", "subsystem": "STAT", "unverified": true},
  "Get_Stat_Ques_Even": {"scpi": "STAT:QUES:EVEN?", "description": "Read and clear the Questionable Status event register", "subsystem": "STAT", "unverified": true},
  "Get_Tran_Dcyc": {"scpi": "TRAN:DCYC?", "description": "Query the transient duty cycle", "subsystem": "TRAN", "unverified": true},
  "Get_Tran_Freq": {"scpi": "TRAN:FREQ?", "description": "Query the transient frequency", "subsystem": "TRAN", "unverified": true},
  "Get_Tran_Mode": {"scpi": "TRAN:MODE?", "description": "Query the transient mode \u2014 CONT, PULS or TOGG", "subsystem": "TRAN", "unverified": true},
  "Get_Tran_Stat": {"scpi": "TRAN:STAT?", "description": "Query whether transient operation is enabled", "subsystem": "TRAN", "unverified": true},
  "Get_Tran_Twid": {"scpi": "TRAN:TWID?", "description": "Query the transient pulse width", "subsystem": "TRAN", "unverified": true},
  "Get_Trig_Sour": {"scpi": "TRIG:SOUR?", "description": "Query the trigger source", "subsystem": "TRIG", "unverified": true},
  "Get_Trig_Tim": {"scpi": "TRIG:TIM?", "description": "Query the internal trigger timer period", "subsystem": "TRIG", "unverified": true},
  "Get_Volt": {"scpi": "VOLT?", "description": "Query the programmed main voltage level", "subsystem": "VOLT?", "unverified": true},
  "Get_Volt_Lev_Trig": {"scpi": "VOLT:LEV:TRIG?", "description": "Query the triggered voltage level", "subsystem": "VOLT", "unverified": true},
  "Get_Volt_Slew": {"scpi": "VOLT:SLEW?", "description": "Query the voltage slew rate", "subsystem": "VOLT", "unverified": true},
  "Get_Volt_Tlev": {"scpi": "VOLT:TLEV?", "description": "Query the transient voltage level", "subsystem": "VOLT", "unverified": true},
}
```

## Added to `Porta_one` — 573

### SET — 272

```json
"set": {
  "Set_Acm_Lun": {"scpi": ":ACM:LUN <value>", "description": "Selects the THD+N display units for the ACMAINS measurement function", "args": ["value"], "subsystem": "ACM", "unverified": true},
  "Set_Acm_Mmax": {"scpi": "ACMains:MMAX <value>", "description": "Selects the upper magnitude display range for the bargraph display in volts", "args": ["value"], "subsystem": "ACM", "unverified": true},
  "Set_Acm_Mmin": {"scpi": "ACMains:MMIN <value>", "description": "Selects the lower magnitude display range for the bargraph display in volts", "args": ["value"], "subsystem": "ACM", "unverified": true},
  "Set_Acm_Unit": {"scpi": "ACMains:UNIT <value>", "description": "Selects the default volts measurement units for the ACMAINS function", "args": ["value"], "subsystem": "ACM", "unverified": true},
  "Set_Ampl_Amax": {"scpi": ":AMPL:AMAX <value>", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Amin": {"scpi": ":AMPL:AMIN <value>", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Bpfr": {"scpi": "AMPLitude:BPFR <value>", "description": "Selects the center frequency for the tunable bandpass filter when the Selective filter is selected", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Ext": {"scpi": "AMPLitude:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Filt": {"scpi": "AMPLitude:FILTer <value>", "description": "Selects the filter for the Amplitude function, identical to the front- panel selection", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Fmax": {"scpi": "AMPLitude:FMAX <value>", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Fmin": {"scpi": "AMPLitude:FMIN <value>", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Hpas": {"scpi": "AMPLitude:HPASs <value>", "description": "Enables and disables the high pass filter", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Lpas": {"scpi": "AMPLitude:LPASs <value>", "description": "Selects the band pass filter when the unweighted filter is selected", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Mmax": {"scpi": "AMPLitude:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Mmin": {"scpi": "AMPLitude:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Spe": {"scpi": "AMPLitude:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Swpt": {"scpi": "AMPLitude:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Unit": {"scpi": "AMPLitude:UNIT <value>", "description": "Selects the measurement units for the Amplitude function", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Ampl_Wtd": {"scpi": "AMPLitude:WTD <value>", "description": "Selects the weighting filter for the Amplitude function when the WTD filter is selected", "args": ["value"], "subsystem": "AMPL", "unverified": true},
  "Set_Damp_Amax": {"scpi": ":DAMP:AMAX <value>", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Amin": {"scpi": "DAMPlitude:AMIN <value>", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Bpfr": {"scpi": "DAMPlitude:BPFR <value>", "description": "Selects the center frequency for the tunable bandpass filter when the Selective filter is selected", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Ext": {"scpi": "DAMPlitude:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Filt": {"scpi": "DAMPlitude:FILTer <value>", "description": "Selects the filter for the Amplitude function, identical to the front- panel selection", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Fmax": {"scpi": "DAMPlitude:FMAX <value>", "description": "Selects the upper frequency display range for the sweep display", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Fmin": {"scpi": "DAMPlitude:FMIN <value>", "description": "Selects the lower frequency display range for the sweep display", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Hpas": {"scpi": "DAMPlitude:HPASs <value>", "description": "Selects the high pass filter cut off frequency", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Lpas": {"scpi": "DAMPlitude:LPASs <value>", "description": "Selects the band pass filter cut off frequency and detector when the unweighted filter is selected", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Mmax": {"scpi": "DAMPlitude:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Mmin": {"scpi": "DAMPlitude:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep display", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Spe": {"scpi": "DAMPlitude:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Step": {"scpi": "DAMPlitude:STEP <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Swpt": {"scpi": "DAMPlitude:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Unit": {"scpi": "DAMPlitude:UNIT <value>", "description": "Selects the measurement units for the Digital Amplitude function", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Damp_Wtd": {"scpi": "DAMPlitude:WTD <value>", "description": "Selects the weighting filter for the Digital Amplitude function when the WTD filter is selected", "args": ["value"], "subsystem": "DAMP", "unverified": true},
  "Set_Dchk_Bits": {"scpi": ":DCHK:BITS <value>", "description": "This query returns two 32-bit decimal integers (only the low 24 bits are available, the top 8 bits are not used) indicating the state of the digital input signal on the A and B channels", "args": ["value"], "subsystem": "DCHK", "unverified": true},
  "Set_Dchk_Dbit": {"scpi": "DCHK:DBITs <value>", "description": "Selects the measurement mode for the digital interface data bits, either Active Bits mode (ACTV) or Actual Bits mode (ACTL)", "args": ["value"], "subsystem": "DCHK", "unverified": true},
  "Set_Dchk_Dun": {"scpi": "DCHK:DUNit <value>", "description": "Selects the data units for the data display, either decimal (DEC) or hexadecimal (HEX)", "args": ["value"], "subsystem": "DCHK", "unverified": true},
  "Set_Dchk_Mmax": {"scpi": "DCHK:MMAX <value>", "description": "Selects the upper magnitude display range and units for the bargraph display", "args": ["value"], "subsystem": "DCHK", "unverified": true},
  "Set_Dchk_Mmin": {"scpi": "DCHK:MMIN <value>", "description": "Selects the lower magnitude display range and unit for the bargraph display", "args": ["value"], "subsystem": "DCHK", "unverified": true},
  "Set_Dchk_Unit": {"scpi": "DCHK:UNIT <value>", "description": "Selects the measurement units for the data error measurements", "args": ["value"], "subsystem": "DCHK", "unverified": true},
  "Set_Dimd_Amax": {"scpi": ":DIMD:AMAX <value>", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator", "args": ["value"], "subsystem": "DIMD", "unverified": true},
  "Set_Dimd_Amin": {"scpi": "DIMD:AMIN <value>", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator", "args": ["value"], "subsystem": "DIMD", "unverified": true},
  "Set_Dimd_Lun": {"scpi": "DIMD:LUNit <value>", "description": "Selects the level display units for the Digital DIMD measurement function", "args": ["value"], "subsystem": "DIMD", "unverified": true},
  "Set_Dimd_Mmax": {"scpi": "DIMD:MMAX <value>", "description": "Selects the upper magnitude display range for the bargraph display in currently selected units", "args": ["value"], "subsystem": "DIMD", "unverified": true},
  "Set_Dimd_Mmin": {"scpi": "DIMD:MMIN <value>", "description": "Selects the lower magnitude display range for the bargraph display", "args": ["value"], "subsystem": "DIMD", "unverified": true},
  "Set_Dimd_Spe": {"scpi": "DIMD:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "DIMD", "unverified": true},
  "Set_Dimd_Step": {"scpi": "DIMD:STEPs <value>", "description": "Selects the the number of sweep steps", "args": ["value"], "subsystem": "DIMD", "unverified": true},
  "Set_Dimd_Unit": {"scpi": "DIMD:UNIT <value>", "description": "Selects the DIMD measurement units of percent and dB", "args": ["value"], "subsystem": "DIMD", "unverified": true},
  "Set_Dio_Ddref": {"scpi": ":DIO:DDREF <value>", "description": "Selects the reference source for the Digital Delay measurement function", "args": ["value"], "subsystem": "DIO", "unverified": true},
  "Set_Dio_Dir": {"scpi": "DIO:DIResolution <value>", "description": "Selects the number of data bits of resolution applied to both channels of the digital audio data on the digital inputs", "args": ["value"], "subsystem": "DIO", "unverified": true},
  "Set_Dio_Dref": {"scpi": "DIO:DREF <value>", "description": "Set dio dref", "args": ["value"], "subsystem": "DIO", "unverified": true},
  "Set_Dio_Dun": {"scpi": "DIO:DUNit <value>", "description": "Selects units for the Digital Delay measurement function", "args": ["value"], "subsystem": "DIO", "unverified": true},
  "Set_Dio_Frqr": {"scpi": "DIO:FRQRef <value>", "description": "Selects digital audio frequency reference source for digital audio frequency measurement functions", "args": ["value"], "subsystem": "DIO", "unverified": true},
  "Set_Dio_Mmax": {"scpi": "DIO:MMAX <value>", "description": "Selects the upper magnitude display range for the sample rate bargraph display", "args": ["value"], "subsystem": "DIO", "unverified": true},
  "Set_Dio_Mmin": {"scpi": "DIO:MMIN <value>", "description": "Selects the lower magnitude display range for the sample rate bargraph display", "args": ["value"], "subsystem": "DIO", "unverified": true},
  "Set_Dio_Unit": {"scpi": "DIO:UNIT <value>", "description": "Selects units for the Digital Sample Rate measurement function", "args": ["value"], "subsystem": "DIO", "unverified": true},
  "Set_Dist_Cod": {"scpi": ":DIST:COD <value>", "description": "Returns a value indicating a coding error in the data received at the digital interface input", "args": ["value"], "subsystem": "DIST", "unverified": true},
  "Set_Djit_Amax": {"scpi": ":DJIT:AMAX <value>", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Amin": {"scpi": "DJITter:AMIN <value>", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Bpfr": {"scpi": "DJITter:BPFR <value>", "description": "Selects the center frequency for the Digital Jitter analyzer tunable bandpass filter when the Selective filter is selected", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Det": {"scpi": "DJITter:DETector <value>", "description": "Set djit det", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Ext": {"scpi": "DJITter:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Filt": {"scpi": "DJITter:FILTer <value>", "description": "Selects the filter for the Digital Jitter analyzer function, identical to the front-panel selection", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Fmax": {"scpi": "DJITter:FMAX <value>", "description": "Selects the upper frequency display range for the sweep display", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Fmin": {"scpi": "DJITter:FMIN <value>", "description": "Selects the lower frequency display range for the sweep display", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Hpas": {"scpi": "DJITter:HPASs <value>", "description": "Selects the jitter measurement high pass filter cut off frequency", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Jdet": {"scpi": "DJITter:JDETector <value>", "description": "Selects Peak or RMS jitter detector", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Mmax": {"scpi": "DJITter:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Mmin": {"scpi": "DJITter:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep display", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Spe": {"scpi": "DJITter:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Step": {"scpi": "DJITter:STEP <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Swpt": {"scpi": "DJITter:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Djit_Unit": {"scpi": "DJITter:UNIT <value>", "description": "Selects either unit interval (UI) or seconds (SEC) units for the Digital Jitter measurement function", "args": ["value"], "subsystem": "DJIT", "unverified": true},
  "Set_Dlev_Amax": {"scpi": ":DLEV:AMAX <value>", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DLEV", "unverified": true},
  "Set_Dlev_Amin": {"scpi": "DLEVel:AMIN <value>", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DLEV", "unverified": true},
  "Set_Dlev_Ext": {"scpi": "DLEVel:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "DLEV", "unverified": true},
  "Set_Dlev_Lun": {"scpi": "DLEVel:LUNit <value>", "description": "Selects the measurement units for the second channel of the level function for the level meter :M2? query response", "args": ["value"], "subsystem": "DLEV", "unverified": true},
  "Set_Dlev_Mmax": {"scpi": "DLEVel:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "DLEV", "unverified": true},
  "Set_Dlev_Mmin": {"scpi": "DLEVel:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep display", "args": ["value"], "subsystem": "DLEV", "unverified": true},
  "Set_Dlev_Spe": {"scpi": "DLEVel:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "DLEV", "unverified": true},
  "Set_Dlev_Step": {"scpi": "DLEVel:STEP <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "DLEV", "unverified": true},
  "Set_Dlev_Swpt": {"scpi": "DLEVel:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "DLEV", "unverified": true},
  "Set_Dlev_Unit": {"scpi": "DLEVel:UNIT <value>", "description": "Selects the measurement units for the first channel of the level function for the function meter :M1? query response", "args": ["value"], "subsystem": "DLEV", "unverified": true},
  "Set_Dno_Amax": {"scpi": "DNOise:AMAX <value>", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Amin": {"scpi": "DNOise:AMIN <value>", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Bpfr": {"scpi": "DNOise:BPFR <value>", "description": "Selects the center frequency for the tunable bandpass filter when the Selective filter is selected", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Ext": {"scpi": "DNOise:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Filt": {"scpi": "DNOise:FILTer <value>", "description": "Selects the filter for the Digital Noise function, identical to the front- panel selection", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Fmax": {"scpi": "DNOise:FMAX <value>", "description": "Selects the upper frequency display range for the sweep display", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Fmin": {"scpi": "DNOise:FMIN <value>", "description": "Selects the lower frequency display range for the sweep display", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Hpas": {"scpi": "DNOise:HPASs <value>", "description": "Selects the high pass filter cut off frequency", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Lpas": {"scpi": "DNOise:LPASs <value>", "description": "Selects the band pass filter cut off frequency and detector when the unweighted filter is selected", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Mmax": {"scpi": "DNOise:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Mmin": {"scpi": "DNOise:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep display", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Spe": {"scpi": "DNOise:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Step": {"scpi": "DNOise:STEP <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Swpt": {"scpi": "DNOise:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Unit": {"scpi": "DNOise:UNIT <value>", "description": "Selects the measurement units for the Digital Noise function", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dno_Wtd": {"scpi": "DNOise:WTD <value>", "description": "Selects the weighting filter for the Digital Noise function when the WTD filter is selected", "args": ["value"], "subsystem": "DNO", "unverified": true},
  "Set_Dost_Cons": {"scpi": "DOSTatus:CONS <value>", "description": "Specifies the consumer standard status bit settings for the rate, emphasis, and copy bits", "args": ["value"], "subsystem": "DOST", "unverified": true},
  "Set_Dost_Prof": {"scpi": "DOSTatus:PROF <value>", "description": "Specifies the professional standard status bit settings for the rate, output pre-emphasis, origination, and destination status bits", "args": ["value"], "subsystem": "DOST", "unverified": true},
  "Set_Dost_Stdo": {"scpi": "DOSTatus:STDO <value>", "description": "Sets the standard for output status bits formatting, either professional standard (PROF) or consumer standard (CONS)", "args": ["value"], "subsystem": "DOST", "unverified": true},
  "Set_Dost_Val": {"scpi": "DOSTatus:VALidity <value>", "description": "Sets the VALIDITY bit for the digital interface output channel A B data streams to either VALID or INVALID", "args": ["value"], "subsystem": "DOST", "unverified": true},
  "Set_Dph_Amax": {"scpi": "DPHase:AMAX <value>", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Amin": {"scpi": "DPHase:AMIN <value>", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Ext": {"scpi": "DPHase:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Fmax": {"scpi": "DPHase:FMAX <value>", "description": "Selects the upper frequency display range for the sweep display", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Fmin": {"scpi": "DPHase:FMIN <value>", "description": "Selects the lower frequency display range for the sweep display", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Lun": {"scpi": "DPHase:LUNit <value>", "description": "Selects the Digital Level meter units for the center meter", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Mmax": {"scpi": "DPHase:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep display", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Mmin": {"scpi": "DPHase:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep display", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Rang": {"scpi": "DPHase:RANGe <value>", "description": "Selects the Digital Phase meter display range", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Spe": {"scpi": "DPHase:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Step": {"scpi": "DPHase:STEP <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Swpt": {"scpi": "DPHase:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Dph_Unit": {"scpi": "DPHase:UNIT <value>", "description": "Selects the default degree measurement units for the DPHASE function", "args": ["value"], "subsystem": "DPH", "unverified": true},
  "Set_Drat_Amax": {"scpi": ":DRAT:AMAX <value>", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Amin": {"scpi": "DRATio:AMIN <value>", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Ext": {"scpi": "DRATio:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Fmax": {"scpi": "DRATio:FMAX <value>", "description": "Selects the upper frequency display range for the sweep display", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Fmin": {"scpi": "DRATio:FMIN <value>", "description": "Selects the lower frequency display range for the sweep display", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Lun": {"scpi": "DRATio:LUNit <value>", "description": "Selects the Digital Ratio function Digital Level measurement units", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Mmax": {"scpi": "DRATio:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Mmin": {"scpi": "DRATio:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep display", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Spe": {"scpi": "DRATio:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Step": {"scpi": "DRATio:STEP <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Swpt": {"scpi": "DRATio:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Drat_Unit": {"scpi": "DRATio:UNIT <value>", "description": "Selects either X/Y or dB units for the Digital Ratio measurement function", "args": ["value"], "subsystem": "DRAT", "unverified": true},
  "Set_Dthd_Amax": {"scpi": ":DTHD:AMAX <value>", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Amin": {"scpi": "DTHD:AMIN <value>", "description": "Sets the minimum amplitude level for an amplitude sweep for the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Ext": {"scpi": "DTHD:EXTernal <value>", "description": "Selects glide or step in external sweep mode", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Filt": {"scpi": "DTHD:FILTer <value>", "description": "Selects the filter for the DTHD function, identical to the front-panel selection", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Fmax": {"scpi": "DTHD:FMAX <value>", "description": "Selects the upper frequency display range for the sweep display", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Fmin": {"scpi": "DTHD:FMIN <value>", "description": "Selects the lower frequency display range for the sweep display", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Hpas": {"scpi": "DTHD:HPASs <value>", "description": "Selects the high pass filter cut off frequency", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Lpas": {"scpi": "DTHD:LPASs <value>", "description": "Selects the band pass filter cut off frequency and detector when the unweighted filter or average filter is selected", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Lun": {"scpi": "DTHD:LUNit <value>", "description": "Selects the measurement units for the Digital Level measurement in the DTHD function", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Mmax": {"scpi": "DTHD:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Mmin": {"scpi": "DTHD:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep display", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Notc": {"scpi": "DTHD:NOTChfreq <value>", "description": "Selects the center frequency for the tunable notch filter when TUNE is set to FIXTune", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Spe": {"scpi": "DTHD:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Step": {"scpi": "DTHD:STEP <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Swpt": {"scpi": "DTHD:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Tun": {"scpi": "DTHD:TUNe <value>", "description": "Selects the notch filter tuning mode for the DTHD function", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Unit": {"scpi": "DTHD:UNIT <value>", "description": "Selects the measurement units for the DTHD function", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dthd_Wtd": {"scpi": "DTHD:WTD <value>", "description": "Selects the weighting filter for the DTHD+N function when the WTD filter is selected", "args": ["value"], "subsystem": "DTHD", "unverified": true},
  "Set_Dxt_Amax": {"scpi": "DXTalk:AMAX <value>", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Amin": {"scpi": "DXTalk:AMIN <value>", "description": "Sets the minimum amplitude level for an amplitude sweep for the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Ext": {"scpi": "DXTalk:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Fmax": {"scpi": "DXTalk:FMAX <value>", "description": "Selects the upper frequency display range for the sweep display", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Fmin": {"scpi": "DXTalk:FMIN <value>", "description": "Selects the lower frequency display range for the sweep display", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Lun": {"scpi": "DXTalk:LUNit <value>", "description": "Selects the level measurement units for the DXTALK function", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Mmax": {"scpi": "DXTalk:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Mmin": {"scpi": "DXTalk:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep display", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Spe": {"scpi": "DXTalk:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Step": {"scpi": "DXTalk:STEP <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Swpt": {"scpi": "DXTalk:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Dxt_Unit": {"scpi": "DXTalk:UNIT <value>", "description": "Selects the DXTALK measurement units", "args": ["value"], "subsystem": "DXT", "unverified": true},
  "Set_Genl_Fmax": {"scpi": ":GENL:FMAX <value>", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "GENL", "unverified": true},
  "Set_Genl_Fmin": {"scpi": "GENLoad:FMIN <value>", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "GENL", "unverified": true},
  "Set_Genl_Mmax": {"scpi": "GENLoad:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in OHMS units", "args": ["value"], "subsystem": "GENL", "unverified": true},
  "Set_Genl_Mmin": {"scpi": "GENLoad:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep and bargraph displays in OHMS units", "args": ["value"], "subsystem": "GENL", "unverified": true},
  "Set_Genl_Spe": {"scpi": "GENLoad:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "GENL", "unverified": true},
  "Set_Genl_Step": {"scpi": "GENLoad:STEPs <value>", "description": "Selects the sweep mode and the number of sweep steps", "args": ["value"], "subsystem": "GENL", "unverified": true},
  "Set_Genl_Unit": {"scpi": "GENLoad:UNIT <value>", "description": "Selects the default OHM measurement units for the GENLOAD function", "args": ["value"], "subsystem": "GENL", "unverified": true},
  "Set_Imd_Amax": {"scpi": ":IMD:AMAX <value>", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator", "args": ["value"], "subsystem": "IMD", "unverified": true},
  "Set_Imd_Amin": {"scpi": "IMD:AMIN <value>", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator", "args": ["value"], "subsystem": "IMD", "unverified": true},
  "Set_Imd_Lun": {"scpi": "IMD:LUNit <value>", "description": "Selects the level display units for the IMD measurement function", "args": ["value"], "subsystem": "IMD", "unverified": true},
  "Set_Imd_Mmax": {"scpi": "IMD:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "IMD", "unverified": true},
  "Set_Imd_Mmin": {"scpi": "IMD:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "IMD", "unverified": true},
  "Set_Imd_Spe": {"scpi": "IMD:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "IMD", "unverified": true},
  "Set_Imd_Unit": {"scpi": "IMD:UNIT <value>", "description": "Selects the IMD measurement units of percent or dB", "args": ["value"], "subsystem": "IMD", "unverified": true},
  "Set_Lev_Amax": {"scpi": ":LEV:AMAX <value>", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "LEV", "unverified": true},
  "Set_Lev_Amin": {"scpi": "LEVel:AMIN <value>", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "LEV", "unverified": true},
  "Set_Lev_Ext": {"scpi": "LEVel:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "LEV", "unverified": true},
  "Set_Lev_Lun": {"scpi": "LEVel:LUNit <value>", "description": "Selects the measurement units for the second channel of the level function for the level meter :M2? query response", "args": ["value"], "subsystem": "LEV", "unverified": true},
  "Set_Lev_Mmax": {"scpi": "LEVel:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "LEV", "unverified": true},
  "Set_Lev_Mmin": {"scpi": "LEVel:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "LEV", "unverified": true},
  "Set_Lev_Spe": {"scpi": "LEVel:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "LEV", "unverified": true},
  "Set_Lev_Step": {"scpi": "LEVel:STEPs <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "LEV", "unverified": true},
  "Set_Lev_Swpt": {"scpi": "LEVel:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "LEV", "unverified": true},
  "Set_Lev_Unit": {"scpi": "LEVel:UNIT <value>", "description": "Selects the measurement units for the first channel of the level function for the function meter :M1? query response", "args": ["value"], "subsystem": "LEV", "unverified": true},
  "Set_Nois_Amax": {"scpi": ":NOIS:AMAX <value>", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Amin": {"scpi": "NOISe:AMIN <value>", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Bpfr": {"scpi": "NOISe:BPFR <value>", "description": "Selects the center frequency for the tunable bandpass filter when the Selective filter is selected", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Ext": {"scpi": "NOISe:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Filt": {"scpi": "NOISe:FILTer <value>", "description": "Selects the filter for the Noise function, identical to the front-panel selection", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Fmax": {"scpi": "NOISe:FMAX <value>", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Fmin": {"scpi": "NOISe:FMIN <value>", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Hpas": {"scpi": "NOISe:HPASs <value>", "description": "Enables and disables the high pass filter", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Lpas": {"scpi": "NOISe:LPASs <value>", "description": "Selects the band pass filter when the unweighted filter is selected", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Mmax": {"scpi": "NOISe:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Mmin": {"scpi": "NOISe:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Spe": {"scpi": "NOISe:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Step": {"scpi": "NOISe:STEPs <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Swpt": {"scpi": "NOISe:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Unit": {"scpi": "NOISe:UNIT <value>", "description": "Selects the measurement units for the Noise function", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Nois_Wtd": {"scpi": "NOISe:WTD <value>", "description": "Selects the weighting filter for the Noise function when the WTD filter is selected", "args": ["value"], "subsystem": "NOIS", "unverified": true},
  "Set_Phas_Amax": {"scpi": ":PHAS:AMAX <value>", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Amin": {"scpi": "PHASe:AMIN <value>", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Ext": {"scpi": "PHASe:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Fmax": {"scpi": "PHASe:FMAX <value>", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Fmin": {"scpi": "PHASe:FMIN <value>", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Lun": {"scpi": "PHASe:LUNit <value>", "description": "Selects the Level meter units", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Mmax": {"scpi": "PHASe:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Mmin": {"scpi": "PHASe:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Rang": {"scpi": "PHASe:RANGe <value>", "description": "Selects the Phase meter display range", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Spe": {"scpi": "PHASe:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Step": {"scpi": "PHASe:STEPs <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Swpt": {"scpi": "PHASe:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Phas_Unit": {"scpi": "PHASe:UNIT <value>", "description": "Selects the default degree measurement units for the PHASE function", "args": ["value"], "subsystem": "PHAS", "unverified": true},
  "Set_Rat_Amax": {"scpi": ":RAT:AMAX <value>", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Amin": {"scpi": "RATio:AMIN <value>", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Ext": {"scpi": "RATio:EXTernal <value>", "description": "Selects glide or step settling in external sweep mode", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Fmax": {"scpi": "RATio:FMAX <value>", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Fmin": {"scpi": "RATio:FMIN <value>", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Lun": {"scpi": "RATio:LUNit <value>", "description": "Selects the Ratio function Level measurement units", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Mmax": {"scpi": "RATio:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Mmin": {"scpi": "RATio:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Mode": {"scpi": "RATio:MODE <value>", "description": "Selects the sensitivity mode for two channel level ratio measurements, either Mode 1 or Mode 2", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Spe": {"scpi": "RATio:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Step": {"scpi": "RATio:STEPs <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Swpt": {"scpi": "RATio:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Rat_Unit": {"scpi": "RATio:UNIT <value>", "description": "Selects either X/Y or dB units for the Ratio measurement function", "args": ["value"], "subsystem": "RAT", "unverified": true},
  "Set_Sin_Hpas": {"scpi": ":SIN:HPAS <value>", "description": "Enables and disables the SINAD high pass filter", "args": ["value"], "subsystem": "SIN", "unverified": true},
  "Set_Sin_Lpas": {"scpi": "SINad:LPASs <value>", "description": "Selects the SINAD band pass filter ", "args": ["value"], "subsystem": "SIN", "unverified": true},
  "Set_Sin_Lun": {"scpi": "SINad:LUNit <value>", "description": "Selects the measurement units for the Level measurement in the SINAD function", "args": ["value"], "subsystem": "SIN", "unverified": true},
  "Set_Sin_Mmax": {"scpi": "SINad:MMAX <value>", "description": "Selects the upper magnitude display range for the bargraph display", "args": ["value"], "subsystem": "SIN", "unverified": true},
  "Set_Sin_Mmin": {"scpi": "SINad:MMIN <value>", "description": "Selects the lower magnitude display range for the bargraph display", "args": ["value"], "subsystem": "SIN", "unverified": true},
  "Set_Sin_Notc": {"scpi": "SINad:NOTChfreq <value>", "description": "Selects the center frequency for the tunable notch filter when TUNE is set to FIXTUNE", "args": ["value"], "subsystem": "SIN", "unverified": true},
  "Set_Sin_Pres": {"scpi": "SINad:PRESet <value>", "description": "Selects the PRESET setting to set both the generator frequency and the SINAD notch filter frequency to either 400 Hz (F400) or 1000 Hz (F1000)", "args": ["value"], "subsystem": "SIN", "unverified": true},
  "Set_Sin_Tun": {"scpi": "SINad:TUNe <value>", "description": "Selects the notch filter tuning mode for the SINAD function", "args": ["value"], "subsystem": "SIN", "unverified": true},
  "Set_Sin_Unit": {"scpi": "SINad:UNIT <value>", "description": "Selects the default dB measurement units for the SINAD meter", "args": ["value"], "subsystem": "SIN", "unverified": true},
  "Set_Thd_Amax": {"scpi": ":THD:AMAX <value>", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Amin": {"scpi": "THD:AMIN <value>", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Ext": {"scpi": "THD:EXTernal <value>", "description": "Selects glide or step in external sweep mode", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Filt": {"scpi": "THD:FILTer <value>", "description": "Selects the filter for the THD function, identical to the front-panel selection", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Fmax": {"scpi": "THD:FMAX <value>", "description": "Selects the upper frequency display range for the sweep display", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Fmin": {"scpi": "THD:FMIN <value>", "description": "Selects the lower frequency display range for the sweep display", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Hpas": {"scpi": "THD:HPASs <value>", "description": "Enables and disables the high pass filter", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Lpas": {"scpi": "THD:LPASs <value>", "description": "Selects the band pass filter when the UNWTD filter is selected", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Lun": {"scpi": "THD:LUNit <value>", "description": "Selects the measurement units for the Level measurement in the THD function", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Mmax": {"scpi": "THD:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Mmin": {"scpi": "THD:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Notc": {"scpi": "THD:NOTChfreq <value>", "description": "Selects the center frequency for the tunable notch filter when TUNE is set to FIXTUNE", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Spe": {"scpi": "THD:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Step": {"scpi": "THD:STEPs <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Swpt": {"scpi": "THD:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Tun": {"scpi": "THD:TUNe <value>", "description": "Selects the notch filter tuning mode for the THD function", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Unit": {"scpi": "THD:UNIT <value>", "description": "Selects the measurement units for the THD function", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Thd_Wtd": {"scpi": "THD:WTD <value>", "description": "Selects the weighting filter for the THD+N function when the WTD filter is selected", "args": ["value"], "subsystem": "THD", "unverified": true},
  "Set_Wf_Det": {"scpi": ":WF:DET <value>", "description": "Selects the W+F detector", "args": ["value"], "subsystem": "WF", "unverified": true},
  "Set_Wf_Filt": {"scpi": "WF:FILTer <value>", "description": "Selects the W+F weighted or unweighted filters", "args": ["value"], "subsystem": "WF", "unverified": true},
  "Set_Wf_Lun": {"scpi": "WF:LUNit <value>", "description": "Selects the measurement units for the Level measurement in the W+F function", "args": ["value"], "subsystem": "WF", "unverified": true},
  "Set_Wf_Mmax": {"scpi": "WF:MMAX <value>", "description": "Selects the upper magnitude display range for the bargraph display", "args": ["value"], "subsystem": "WF", "unverified": true},
  "Set_Wf_Mmin": {"scpi": "WF:MMIN <value>", "description": "Selects the lower magnitude display range for the bargraph display", "args": ["value"], "subsystem": "WF", "unverified": true},
  "Set_Wf_Resp": {"scpi": "WF:RESPonse <value>", "description": "Selects the measurement response mode for W+F measurements", "args": ["value"], "subsystem": "WF", "unverified": true},
  "Set_Wf_Unit": {"scpi": "WF:UNIT <value>", "description": "Selects the default percent measurement units for the W+F meter", "args": ["value"], "subsystem": "WF", "unverified": true},
  "Set_Wf_Wfun": {"scpi": "WF:WFUNit <value>", "description": "Selects the W+F function frequency meter units and reference frequency for frequency deviation measurements", "args": ["value"], "subsystem": "WF", "unverified": true},
  "Set_Xtal_Amax": {"scpi": ":XTAL:AMAX <value>", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Amin": {"scpi": "XTALk:AMIN <value>", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Ext": {"scpi": "XTALk:EXTernal <value>", "description": "Returns the current external sweep settling mode", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Fmax": {"scpi": "XTALk:FMAX <value>", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Fmin": {"scpi": "XTALk:FMIN <value>", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Lun": {"scpi": "XTALk:LUNit <value>", "description": "Selects the level measurement units for the XTALK function", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Mmax": {"scpi": "XTALk:MMAX <value>", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Mmin": {"scpi": "XTALk:MMIN <value>", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Spe": {"scpi": "XTALk:SPEed <value>", "description": "Selects the sweep speed", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Step": {"scpi": "XTALk:STEPs <value>", "description": "Selects the sweep mode or the number of sweep steps", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Swpt": {"scpi": "XTALk:SWPType <value>", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "args": ["value"], "subsystem": "XTAL", "unverified": true},
  "Set_Xtal_Unit": {"scpi": "XTALk:UNIT <value>", "description": "Selects the XTALK measurement units", "args": ["value"], "subsystem": "XTAL", "unverified": true},
}
```

### DO — 15

```json
"do": {
  "Do_Ampl_Step": {"scpi": "AMPLitude:STEPs", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "AMPL", "unverified": true},
  "Do_At_Fmax": {"scpi": "ATio:FMAX", "description": "Do at fmax", "subsystem": "AT", "unverified": true},
  "Do_Dimd_Ext": {"scpi": "DIMD:EXTernal", "description": "Do dimd ext", "subsystem": "DIMD", "unverified": true},
  "Do_Dimd_Fmax": {"scpi": "DIMD:FMAX", "description": "Do dimd fmax", "subsystem": "DIMD", "unverified": true},
  "Do_Dimd_Fmin": {"scpi": "DIMD:FMIN", "description": "Do dimd fmin", "subsystem": "DIMD", "unverified": true},
  "Do_Dlev_Fm": {"scpi": "DLEVel:FMin", "description": "Do dlev fm", "subsystem": "DLEV", "unverified": true},
  "Do_Dthd_Medium": {"scpi": "DTHD:MEDIUM", "description": "Do dthd medium", "subsystem": "DTHD", "unverified": true},
  "Do_Gen_Dig": {"scpi": "GEN:DIG", "description": "Do gen dig", "subsystem": "GEN", "unverified": true},
  "Do_Gen_Jitt": {"scpi": "GEN:JITT", "description": "Do gen jitt", "subsystem": "GEN", "unverified": true},
  "Do_Imd_Ext": {"scpi": "IMD:EXTernal", "description": "Do imd ext", "subsystem": "IMD", "unverified": true},
  "Do_Imd_Step": {"scpi": "IMD:STEPs", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "IMD", "unverified": true},
  "Do_Lev_Fm": {"scpi": "LEVel:FMin", "description": "Do lev fm", "subsystem": "LEV", "unverified": true},
  "Do_Phas_Aver": {"scpi": "PHASe:AVERage", "description": "Selects the averaging function for the Phase meter", "subsystem": "PHAS", "unverified": true},
  "Do_Ref_Watt": {"scpi": "REF:WATT", "description": "Do ref watt", "subsystem": "REF", "unverified": true},
  "Do_Thd_Medium": {"scpi": "THD:MEDIUM", "description": "Do thd medium", "subsystem": "THD", "unverified": true},
}
```

### NAB — 286

```json
"nab": {
  "Get_Acm_Lun": {"scpi": "ACMains:LUNit?", "description": "Selects the THD+N display units for the ACMAINS measurement function", "subsystem": "ACM", "unverified": true},
  "Get_Acm_Mmax": {"scpi": "ACMains:MMAX?", "description": "Selects the upper magnitude display range for the bargraph display in volts", "subsystem": "ACM", "unverified": true},
  "Get_Acm_Mmin": {"scpi": "ACMains:MMIN?", "description": "Selects the lower magnitude display range for the bargraph display in volts", "subsystem": "ACM", "unverified": true},
  "Get_Acm_Unit": {"scpi": "ACMains:UNIT?", "description": "Selects the default volts measurement units for the ACMAINS function", "subsystem": "ACM", "unverified": true},
  "Get_Ampl_Amax": {"scpi": "AMPLitude:AMAX?", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Amin": {"scpi": "AMPLitude:AMIN?", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Bpfr": {"scpi": "AMPLitude:BPFR?", "description": "Selects the center frequency for the tunable bandpass filter when the Selective filter is selected", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Ext": {"scpi": "AMPLitude:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Filt": {"scpi": "AMPLitude:FILTer?", "description": "Selects the filter for the Amplitude function, identical to the front- panel selection", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Fmax": {"scpi": "AMPLitude:FMAX?", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Fmin": {"scpi": "AMPLitude:FMIN?", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Hpas": {"scpi": "AMPLitude:HPASs?", "description": "Enables and disables the high pass filter", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Lpas": {"scpi": "AMPLitude:LPASs?", "description": "Selects the band pass filter when the unweighted filter is selected", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Mmax": {"scpi": "AMPLitude:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Mmin": {"scpi": "AMPLitude:MMIN?", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Spe": {"scpi": "AMPLitude:SPEed?", "description": "Selects the sweep speed", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Steps": {"scpi": "AMPLitude:STEPS?", "description": "Returns the selected sweep mode or the number of sweep steps selected for the internal sweep mode", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Swpt": {"scpi": "AMPLitude:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Unit": {"scpi": "AMPLitude:UNIT?", "description": "Selects the measurement units for the Amplitude function", "subsystem": "AMPL", "unverified": true},
  "Get_Ampl_Wtd": {"scpi": "AMPLitude:WTD?", "description": "Selects the weighting filter for the Amplitude function when the WTD filter is selected", "subsystem": "AMPL", "unverified": true},
  "Get_Damp_Amax": {"scpi": "DAMPlitude:AMAX?", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Amin": {"scpi": "DAMPlitude:AMIN?", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Bpfr": {"scpi": "DAMPlitude:BPFR?", "description": "Selects the center frequency for the tunable bandpass filter when the Selective filter is selected", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Ext": {"scpi": "DAMPlitude:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Filt": {"scpi": "DAMPlitude:FILTer?", "description": "Selects the filter for the Amplitude function, identical to the front- panel selection", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Fmax": {"scpi": "DAMPlitude:FMAX?", "description": "Selects the upper frequency display range for the sweep display", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Fmin": {"scpi": "DAMPlitude:FMIN?", "description": "Selects the lower frequency display range for the sweep display", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Hpas": {"scpi": "DAMPlitude:HPASs?", "description": "Selects the high pass filter cut off frequency", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Lpas": {"scpi": "DAMPlitude:LPASs?", "description": "Selects the band pass filter cut off frequency and detector when the unweighted filter is selected", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Mmax": {"scpi": "DAMPlitude:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Mmin": {"scpi": "DAMPlitude:MMIN?", "description": "Selects the lower magnitude display range for the sweep display", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Spe": {"scpi": "DAMPlitude:SPEed?", "description": "Selects the sweep speed", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Step": {"scpi": "DAMPlitude:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Swpt": {"scpi": "DAMPlitude:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Unit": {"scpi": "DAMPlitude:UNIT?", "description": "Selects the measurement units for the Digital Amplitude function", "subsystem": "DAMP", "unverified": true},
  "Get_Damp_Wtd": {"scpi": "DAMPlitude:WTD?", "description": "Selects the weighting filter for the Digital Amplitude function when the WTD filter is selected", "subsystem": "DAMP", "unverified": true},
  "Get_Dchk_Bits": {"scpi": "DCHK:BITS?", "description": "This query returns two 32-bit decimal integers (only the low 24 bits are available, the top 8 bits are not used) indicating the state of the digital input signal on the A and B channels", "subsystem": "DCHK", "unverified": true},
  "Get_Dchk_Dbit": {"scpi": "DCHK:DBITs?", "description": "Selects the measurement mode for the digital interface data bits, either Active Bits mode (ACTV) or Actual Bits mode (ACTL)", "subsystem": "DCHK", "unverified": true},
  "Get_Dchk_Dun": {"scpi": "DCHK:DUNit?", "description": "Selects the data units for the data display, either decimal (DEC) or hexadecimal (HEX)", "subsystem": "DCHK", "unverified": true},
  "Get_Dchk_Mmax": {"scpi": "DCHK:MMAX?", "description": "Selects the upper magnitude display range and units for the bargraph display", "subsystem": "DCHK", "unverified": true},
  "Get_Dchk_Mmin": {"scpi": "DCHK:MMIN?", "description": "Selects the lower magnitude display range and unit for the bargraph display", "subsystem": "DCHK", "unverified": true},
  "Get_Dchk_Unit": {"scpi": "DCHK:UNIT?", "description": "Selects the measurement units for the data error measurements", "subsystem": "DCHK", "unverified": true},
  "Get_Dimd_Amax": {"scpi": "DIMD:AMAX?", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator", "subsystem": "DIMD", "unverified": true},
  "Get_Dimd_Amin": {"scpi": "DIMD:AMIN?", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator", "subsystem": "DIMD", "unverified": true},
  "Get_Dimd_Lun": {"scpi": "DIMD:LUNit?", "description": "Selects the level display units for the Digital DIMD measurement function", "subsystem": "DIMD", "unverified": true},
  "Get_Dimd_Mmax": {"scpi": "DIMD:MMAX?", "description": "Selects the upper magnitude display range for the bargraph display in currently selected units", "subsystem": "DIMD", "unverified": true},
  "Get_Dimd_Mmin": {"scpi": "DIMD:MMIN?", "description": "Selects the lower magnitude display range for the bargraph display", "subsystem": "DIMD", "unverified": true},
  "Get_Dimd_Spe": {"scpi": "DIMD:SPEed?", "description": "Selects the sweep speed", "subsystem": "DIMD", "unverified": true},
  "Get_Dimd_Step": {"scpi": "DIMD:STEPs?", "description": "Selects the the number of sweep steps", "subsystem": "DIMD", "unverified": true},
  "Get_Dimd_Unit": {"scpi": "DIMD:UNIT?", "description": "Selects the DIMD measurement units of percent and dB", "subsystem": "DIMD", "unverified": true},
  "Get_Dio_Ddref": {"scpi": "DIO:DDREF?", "description": "Selects the reference source for the Digital Delay measurement function", "subsystem": "DIO", "unverified": true},
  "Get_Dio_Dir": {"scpi": "DIO:DIResolution?", "description": "Selects the number of data bits of resolution applied to both channels of the digital audio data on the digital inputs", "subsystem": "DIO", "unverified": true},
  "Get_Dio_Dref": {"scpi": "DIO:DREF?", "description": "Get dio dref", "subsystem": "DIO", "unverified": true},
  "Get_Dio_Dun": {"scpi": "DIO:DUNit?", "description": "Selects units for the Digital Delay measurement function", "subsystem": "DIO", "unverified": true},
  "Get_Dio_Frqr": {"scpi": "DIO:FRQRef?", "description": "Selects digital audio frequency reference source for digital audio frequency measurement functions", "subsystem": "DIO", "unverified": true},
  "Get_Dio_Mmax": {"scpi": "DIO:MMAX?", "description": "Selects the upper magnitude display range for the sample rate bargraph display", "subsystem": "DIO", "unverified": true},
  "Get_Dio_Mmin": {"scpi": "DIO:MMIN?", "description": "Selects the lower magnitude display range for the sample rate bargraph display", "subsystem": "DIO", "unverified": true},
  "Get_Dio_Unit": {"scpi": "DIO:UNIT?", "description": "Selects units for the Digital Sample Rate measurement function", "subsystem": "DIO", "unverified": true},
  "Get_Dist_Cod": {"scpi": "DISTatus:CODing?", "description": "Returns a value indicating a coding error in the data received at the digital interface input", "subsystem": "DIST", "unverified": true},
  "Get_Dist_Con": {"scpi": "DISTatus:CONfidence?", "description": "Get dist con", "subsystem": "DIST", "unverified": true},
  "Get_Dist_Err": {"scpi": "DISTatus:ERRor?", "description": "Get dist err", "subsystem": "DIST", "unverified": true},
  "Get_Dist_Inv": {"scpi": "DISTatus:INValid?", "description": "Returns the state of digital interface input channel A validity bit", "subsystem": "DIST", "unverified": true},
  "Get_Dist_Lock": {"scpi": "DISTatus:LOCK?", "description": "Returns a value indicating loss of phase lock of the digital interface input to the incoming sample rate", "subsystem": "DIST", "unverified": true},
  "Get_Dist_Par": {"scpi": "DISTatus:PARity?", "description": "Returns a value indicating the received parity bit does not match the parity of the received sample", "subsystem": "DIST", "unverified": true},
  "Get_Dist_Stat": {"scpi": "DISTatus:STATus?", "description": "Analyzer Function-Setting Commands All function-setting commands have parameters specific to each measurement function", "subsystem": "DIST", "unverified": true},
  "Get_Dist_Std": {"scpi": ":DISTatus:STD?", "description": "Get dist std", "subsystem": "DIST", "unverified": true},
  "Get_Djit_Amax": {"scpi": "DJITter:AMAX?", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Amin": {"scpi": "DJITter:AMIN?", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Bpfr": {"scpi": "DJITter:BPFR?", "description": "Selects the center frequency for the Digital Jitter analyzer tunable bandpass filter when the Selective filter is selected", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Det": {"scpi": "DJITter:DETector?", "description": "Get djit det", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Ext": {"scpi": "DJITter:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Filt": {"scpi": "DJITter:FILTer?", "description": "Selects the filter for the Digital Jitter analyzer function, identical to the front-panel selection", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Fmax": {"scpi": "DJITter:FMAX?", "description": "Selects the upper frequency display range for the sweep display", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Fmin": {"scpi": "DJITter:FMIN?", "description": "Selects the lower frequency display range for the sweep display", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Hpas": {"scpi": "DJITter:HPASs?", "description": "Selects the jitter measurement high pass filter cut off frequency", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Jdet": {"scpi": "DJITter:JDETector?", "description": "Selects Peak or RMS jitter detector", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Mmax": {"scpi": "DJITter:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Mmin": {"scpi": "DJITter:MMIN?", "description": "Selects the lower magnitude display range for the sweep display", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Spe": {"scpi": "DJITter:SPEed?", "description": "Selects the sweep speed", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Step": {"scpi": "DJITter:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Swpt": {"scpi": "DJITter:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "DJIT", "unverified": true},
  "Get_Djit_Unit": {"scpi": "DJITter:UNIT?", "description": "Selects either unit interval (UI) or seconds (SEC) units for the Digital Jitter measurement function", "subsystem": "DJIT", "unverified": true},
  "Get_Dlev_Amax": {"scpi": "DLEVel:AMAX?", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Amin": {"scpi": "DLEVel:AMIN?", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Ext": {"scpi": "DLEVel:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Fmax": {"scpi": "DLEVel:FMAX?", "description": "Selects the upper frequency display range for the sweep display", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Fmin": {"scpi": "DLEVel:FMIN?", "description": "Selects the lower frequency display range for the sweep display", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Lun": {"scpi": "DLEVel:LUNit?", "description": "Selects the measurement units for the second channel of the level function for the level meter :M2? query response", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Mmax": {"scpi": "DLEVel:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Mmin": {"scpi": "DLEVel:MMIN?", "description": "Selects the lower magnitude display range for the sweep display", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Spe": {"scpi": "DLEVel:SPEed?", "description": "Selects the sweep speed", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Step": {"scpi": "DLEVel:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Swpt": {"scpi": "DLEVel:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "DLEV", "unverified": true},
  "Get_Dlev_Unit": {"scpi": "DLEVel:UNIT?", "description": "Selects the measurement units for the first channel of the level function for the function meter :M1? query response", "subsystem": "DLEV", "unverified": true},
  "Get_Dno_Amax": {"scpi": "DNOise:AMAX?", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Amin": {"scpi": "DNOise:AMIN?", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Bpfr": {"scpi": "DNOise:BPFR?", "description": "Selects the center frequency for the tunable bandpass filter when the Selective filter is selected", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Ext": {"scpi": "DNOise:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Filt": {"scpi": "DNOise:FILTer?", "description": "Selects the filter for the Digital Noise function, identical to the front- panel selection", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Fmax": {"scpi": "DNOise:FMAX?", "description": "Selects the upper frequency display range for the sweep display", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Fmin": {"scpi": "DNOise:FMIN?", "description": "Selects the lower frequency display range for the sweep display", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Hpas": {"scpi": "DNOise:HPASs?", "description": "Selects the high pass filter cut off frequency", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Lpas": {"scpi": "DNOise:LPASs?", "description": "Selects the band pass filter cut off frequency and detector when the unweighted filter is selected", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Mmax": {"scpi": "DNOise:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Mmin": {"scpi": "DNOise:MMIN?", "description": "Selects the lower magnitude display range for the sweep display", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Spe": {"scpi": "DNOise:SPEed?", "description": "Selects the sweep speed", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Step": {"scpi": "DNOise:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Swpt": {"scpi": "DNOise:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Unit": {"scpi": "DNOise:UNIT?", "description": "Selects the measurement units for the Digital Noise function", "subsystem": "DNO", "unverified": true},
  "Get_Dno_Wtd": {"scpi": "DNOise:WTD?", "description": "Selects the weighting filter for the Digital Noise function when the WTD filter is selected", "subsystem": "DNO", "unverified": true},
  "Get_Dost_Cons": {"scpi": ":DOSTatus:CONS?", "description": "Specifies the consumer standard status bit settings for the rate, emphasis, and copy bits", "subsystem": "DOST", "unverified": true},
  "Get_Dost_Prof": {"scpi": ":DOSTatus:PROF?", "description": "Specifies the professional standard status bit settings for the rate, output pre-emphasis, origination, and destination status bits", "subsystem": "DOST", "unverified": true},
  "Get_Dost_Stdo": {"scpi": ":DOSTatus:STDO?", "description": "Sets the standard for output status bits formatting, either professional standard (PROF) or consumer standard (CONS)", "subsystem": "DOST", "unverified": true},
  "Get_Dost_Val": {"scpi": "DOSTatus:VALidity?", "description": "Sets the VALIDITY bit for the digital interface output channel A B data streams to either VALID or INVALID", "subsystem": "DOST", "unverified": true},
  "Get_Dph_Amax": {"scpi": "DPHase:AMAX?", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Amin": {"scpi": "DPHase:AMIN?", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Ext": {"scpi": "DPHase:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Fmax": {"scpi": "DPHase:FMAX?", "description": "Selects the upper frequency display range for the sweep display", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Fmin": {"scpi": "DPHase:FMIN?", "description": "Selects the lower frequency display range for the sweep display", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Lun": {"scpi": "DPHase:LUNit?", "description": "Selects the Digital Level meter units for the center meter", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Mmax": {"scpi": "DPHase:MMAX?", "description": "Selects the upper magnitude display range for the sweep display", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Mmin": {"scpi": "DPHase:MMIN?", "description": "Selects the lower magnitude display range for the sweep display", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Rang": {"scpi": "DPHase:RANGe?", "description": "Selects the Digital Phase meter display range", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Spe": {"scpi": "DPHase:SPEed?", "description": "Selects the sweep speed", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Step": {"scpi": "DPHase:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Swpt": {"scpi": "DPHase:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "DPH", "unverified": true},
  "Get_Dph_Unit": {"scpi": "DPHase:UNIT?", "description": "Selects the default degree measurement units for the DPHASE function", "subsystem": "DPH", "unverified": true},
  "Get_Drat_Amax": {"scpi": "DRATio:AMAX?", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Amin": {"scpi": "DRATio:AMIN?", "description": "This command sets the minimum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Ext": {"scpi": "DRATio:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Fmax": {"scpi": "DRATio:FMAX?", "description": "Selects the upper frequency display range for the sweep display", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Fmin": {"scpi": "DRATio:FMIN?", "description": "Selects the lower frequency display range for the sweep display", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Lun": {"scpi": "DRATio:LUNit?", "description": "Selects the Digital Ratio function Digital Level measurement units", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Mmax": {"scpi": "DRATio:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Mmin": {"scpi": "DRATio:MMIN?", "description": "Selects the lower magnitude display range for the sweep display", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Spe": {"scpi": "DRATio:SPEed?", "description": "Selects the sweep speed", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Step": {"scpi": "DRATio:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Swpt": {"scpi": "DRATio:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "DRAT", "unverified": true},
  "Get_Drat_Unit": {"scpi": "DRATio:UNIT?", "description": "Selects either X/Y or dB units for the Digital Ratio measurement function", "subsystem": "DRAT", "unverified": true},
  "Get_Dthd_Amax": {"scpi": "DTHD:AMAX?", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Amin": {"scpi": "DTHD:AMIN?", "description": "Sets the minimum amplitude level for an amplitude sweep for the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Ext": {"scpi": "DTHD:EXTernal?", "description": "Selects glide or step in external sweep mode", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Filt": {"scpi": "DTHD:FILTer?", "description": "Selects the filter for the DTHD function, identical to the front-panel selection", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Fmax": {"scpi": "DTHD:FMAX?", "description": "Selects the upper frequency display range for the sweep display", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Fmin": {"scpi": "DTHD:FMIN?", "description": "Selects the lower frequency display range for the sweep display", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Hpas": {"scpi": "DTHD:HPASs?", "description": "Selects the high pass filter cut off frequency", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Lpas": {"scpi": "DTHD:LPASs?", "description": "Selects the band pass filter cut off frequency and detector when the unweighted filter or average filter is selected", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Lun": {"scpi": "DTHD:LUNit?", "description": "Selects the measurement units for the Digital Level measurement in the DTHD function", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Mmax": {"scpi": "DTHD:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Mmin": {"scpi": "DTHD:MMIN?", "description": "Selects the lower magnitude display range for the sweep display", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Notc": {"scpi": "DTHD:NOTChfreq?", "description": "Selects the center frequency for the tunable notch filter when TUNE is set to FIXTune", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Spe": {"scpi": "DTHD:SPEed?", "description": "Selects the sweep speed", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Step": {"scpi": "DTHD:STEP?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Swpt": {"scpi": "DTHD:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Tun": {"scpi": "DTHD:TUNe?", "description": "Selects the notch filter tuning mode for the DTHD function", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Unit": {"scpi": "DTHD:UNIT?", "description": "Selects the measurement units for the DTHD function", "subsystem": "DTHD", "unverified": true},
  "Get_Dthd_Wtd": {"scpi": "DTHD:WTD?", "description": "Selects the weighting filter for the DTHD+N function when the WTD filter is selected", "subsystem": "DTHD", "unverified": true},
  "Get_Dxt_Amax": {"scpi": "DXTalk:AMAX?", "description": "This command sets the maximum amplitude level for an amplitude sweep of the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Amin": {"scpi": "DXTalk:AMIN?", "description": "Sets the minimum amplitude level for an amplitude sweep for the analog generator, the digital generator, or the jitter generator when the SWPType command is set to AMPL", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Ext": {"scpi": "DXTalk:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Fmax": {"scpi": "DXTalk:FMAX?", "description": "Selects the upper frequency display range for the sweep display", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Fmin": {"scpi": "DXTalk:FMIN?", "description": "Selects the lower frequency display range for the sweep display", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Lun": {"scpi": "DXTalk:LUNit?", "description": "Selects the level measurement units for the DXTALK function", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Mmax": {"scpi": "DXTalk:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Mmin": {"scpi": "DXTalk:MMIN?", "description": "Selects the lower magnitude display range for the sweep display", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Spe": {"scpi": "DXTalk:SPEed?", "description": "Selects the sweep speed", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Step": {"scpi": "DXTalk:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Swpt": {"scpi": "DXTalk:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "DXT", "unverified": true},
  "Get_Dxt_Unit": {"scpi": "DXTalk:UNIT?", "description": "Selects the DXTALK measurement units", "subsystem": "DXT", "unverified": true},
  "Get_Genl_Fmax": {"scpi": "GENLoad:FMAX?", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "subsystem": "GENL", "unverified": true},
  "Get_Genl_Fmin": {"scpi": "GENLoad:FMIN?", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "subsystem": "GENL", "unverified": true},
  "Get_Genl_Mmax": {"scpi": "GENLoad:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in OHMS units", "subsystem": "GENL", "unverified": true},
  "Get_Genl_Mmin": {"scpi": "GENLoad:MMIN?", "description": "Selects the lower magnitude display range for the sweep and bargraph displays in OHMS units", "subsystem": "GENL", "unverified": true},
  "Get_Genl_Spe": {"scpi": "GENLoad:SPEed?", "description": "Selects the sweep speed", "subsystem": "GENL", "unverified": true},
  "Get_Genl_Step": {"scpi": "GENLoad:STEPs?", "description": "Selects the sweep mode and the number of sweep steps", "subsystem": "GENL", "unverified": true},
  "Get_Genl_Unit": {"scpi": "GENLoad:UNIT?", "description": "Selects the default OHM measurement units for the GENLOAD function", "subsystem": "GENL", "unverified": true},
  "Get_Imd_Amax": {"scpi": "IMD:AMAX?", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator", "subsystem": "IMD", "unverified": true},
  "Get_Imd_Amin": {"scpi": "IMD:AMIN?", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator", "subsystem": "IMD", "unverified": true},
  "Get_Imd_Lun": {"scpi": "IMD:LUNit?", "description": "Selects the level display units for the IMD measurement function", "subsystem": "IMD", "unverified": true},
  "Get_Imd_Mmax": {"scpi": "IMD:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "IMD", "unverified": true},
  "Get_Imd_Mmin": {"scpi": "IMD:MMIN?", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "subsystem": "IMD", "unverified": true},
  "Get_Imd_Spe": {"scpi": "IMD:SPEed?", "description": "Selects the sweep speed", "subsystem": "IMD", "unverified": true},
  "Get_Imd_Steps": {"scpi": "IMD:STEPS?", "description": "Returns the selected sweep mode or the number of sweep steps selected for the internal sweep mode", "subsystem": "IMD", "unverified": true},
  "Get_Imd_Unit": {"scpi": "IMD:UNIT?", "description": "Selects the IMD measurement units of percent or dB", "subsystem": "IMD", "unverified": true},
  "Get_Lev_Amax": {"scpi": "LEVel:AMAX?", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Amin": {"scpi": "LEVel:AMIN?", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Ext": {"scpi": "LEVel:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Fmax": {"scpi": "LEVel:FMAX?", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Fmin": {"scpi": "LEVel:FMIN?", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Lun": {"scpi": "LEVel:LUNit?", "description": "Selects the measurement units for the second channel of the level function for the level meter :M2? query response", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Mmax": {"scpi": "LEVel:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Mmin": {"scpi": "LEVel:MMIN?", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Spe": {"scpi": "LEVel:SPEed?", "description": "Selects the sweep speed", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Step": {"scpi": "LEVel:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Swpt": {"scpi": "LEVel:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "LEV", "unverified": true},
  "Get_Lev_Unit": {"scpi": "LEVel:UNIT?", "description": "Selects the measurement units for the first channel of the level function for the function meter :M1? query response", "subsystem": "LEV", "unverified": true},
  "Get_Nois_Amax": {"scpi": "NOISe:AMAX?", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Amin": {"scpi": "NOISe:AMIN?", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Bpfr": {"scpi": "NOISe:BPFR?", "description": "Selects the center frequency for the tunable bandpass filter when the Selective filter is selected", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Ext": {"scpi": "NOISe:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Filt": {"scpi": "NOISe:FILTer?", "description": "Selects the filter for the Noise function, identical to the front-panel selection", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Fmax": {"scpi": "NOISe:FMAX?", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Fmin": {"scpi": "NOISe:FMIN?", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Hpas": {"scpi": "NOISe:HPASs?", "description": "Enables and disables the high pass filter", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Lpas": {"scpi": "NOISe:LPASs?", "description": "Selects the band pass filter when the unweighted filter is selected", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Mmax": {"scpi": "NOISe:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Mmin": {"scpi": "NOISe:MMIN?", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Spe": {"scpi": "NOISe:SPEed?", "description": "Selects the sweep speed", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Step": {"scpi": "NOISe:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Swpt": {"scpi": "NOISe:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Unit": {"scpi": "NOISe:UNIT?", "description": "Selects the measurement units for the Noise function", "subsystem": "NOIS", "unverified": true},
  "Get_Nois_Wtd": {"scpi": "NOISe:WTD?", "description": "Selects the weighting filter for the Noise function when the WTD filter is selected", "subsystem": "NOIS", "unverified": true},
  "Get_Phas_Amax": {"scpi": "PHASe:AMAX?", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Amin": {"scpi": "PHASe:AMIN?", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Ave": {"scpi": "PHASe:AVErage?", "description": "Get phas ave", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Ext": {"scpi": "PHASe:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Fmax": {"scpi": "PHASe:FMAX?", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Fmin": {"scpi": "PHASe:FMIN?", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Lun": {"scpi": "PHASe:LUNit?", "description": "Selects the Level meter units", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Mmax": {"scpi": "PHASe:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Mmin": {"scpi": "PHASe:MMIN?", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Rang": {"scpi": "PHASe:RANGe?", "description": "Selects the Phase meter display range", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Spe": {"scpi": "PHASe:SPEed?", "description": "Selects the sweep speed", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Step": {"scpi": "PHASe:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Swpt": {"scpi": "PHASe:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "PHAS", "unverified": true},
  "Get_Phas_Unit": {"scpi": "PHASe:UNIT?", "description": "Selects the default degree measurement units for the PHASE function", "subsystem": "PHAS", "unverified": true},
  "Get_Rat_Amax": {"scpi": "RATio:AMAX?", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Amin": {"scpi": "RATio:AMIN?", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Ext": {"scpi": "RATio:EXTernal?", "description": "Selects glide or step settling in external sweep mode", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Fmax": {"scpi": "RATio:FMAX?", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Fmin": {"scpi": "RATio:FMIN?", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Lun": {"scpi": "RATio:LUNit?", "description": "Selects the Ratio function Level measurement units", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Mmax": {"scpi": "RATio:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Mmin": {"scpi": "RATio:MMIN?", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Mode": {"scpi": "RATio:MODE?", "description": "Selects the sensitivity mode for two channel level ratio measurements, either Mode 1 or Mode 2", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Spe": {"scpi": "RATio:SPEed?", "description": "Selects the sweep speed", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Step": {"scpi": "RATio:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Swpt": {"scpi": "RATio:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "RAT", "unverified": true},
  "Get_Rat_Unit": {"scpi": "RATio:UNIT?", "description": "Selects either X/Y or dB units for the Ratio measurement function", "subsystem": "RAT", "unverified": true},
  "Get_Sin_Hpas": {"scpi": "SINad:HPASs?", "description": "Enables and disables the SINAD high pass filter", "subsystem": "SIN", "unverified": true},
  "Get_Sin_Lpas": {"scpi": "SINad:LPASs?", "description": "Selects the SINAD band pass filter ", "subsystem": "SIN", "unverified": true},
  "Get_Sin_Lun": {"scpi": "SINad:LUNit?", "description": "Selects the measurement units for the Level measurement in the SINAD function", "subsystem": "SIN", "unverified": true},
  "Get_Sin_Mmax": {"scpi": "SINad:MMAX?", "description": "Selects the upper magnitude display range for the bargraph display", "subsystem": "SIN", "unverified": true},
  "Get_Sin_Mmin": {"scpi": "SINad:MMIN?", "description": "Selects the lower magnitude display range for the bargraph display", "subsystem": "SIN", "unverified": true},
  "Get_Sin_Notc": {"scpi": "SINad:NOTChfreq?", "description": "Selects the center frequency for the tunable notch filter when TUNE is set to FIXTUNE", "subsystem": "SIN", "unverified": true},
  "Get_Sin_Pres": {"scpi": "SINad:PRESet?", "description": "Selects the PRESET setting to set both the generator frequency and the SINAD notch filter frequency to either 400 Hz (F400) or 1000 Hz (F1000)", "subsystem": "SIN", "unverified": true},
  "Get_Sin_Tun": {"scpi": "SINad:TUNe?", "description": "Selects the notch filter tuning mode for the SINAD function", "subsystem": "SIN", "unverified": true},
  "Get_Sin_Unit": {"scpi": "SINad:UNIT?", "description": "Selects the default dB measurement units for the SINAD meter", "subsystem": "SIN", "unverified": true},
  "Get_Thd_Amax": {"scpi": "THD:AMAX?", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "THD", "unverified": true},
  "Get_Thd_Amin": {"scpi": "THD:AMIN?", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "THD", "unverified": true},
  "Get_Thd_Ext": {"scpi": "THD:EXTernal?", "description": "Selects glide or step in external sweep mode", "subsystem": "THD", "unverified": true},
  "Get_Thd_Filt": {"scpi": "THD:FILTer?", "description": "Selects the filter for the THD function, identical to the front-panel selection", "subsystem": "THD", "unverified": true},
  "Get_Thd_Fmax": {"scpi": "THD:FMAX?", "description": "Selects the upper frequency display range for the sweep display", "subsystem": "THD", "unverified": true},
  "Get_Thd_Fmin": {"scpi": "THD:FMIN?", "description": "Selects the lower frequency display range for the sweep display", "subsystem": "THD", "unverified": true},
  "Get_Thd_Hpas": {"scpi": "THD:HPASs?", "description": "Enables and disables the high pass filter", "subsystem": "THD", "unverified": true},
  "Get_Thd_Lpas": {"scpi": "THD:LPASs?", "description": "Selects the band pass filter when the UNWTD filter is selected", "subsystem": "THD", "unverified": true},
  "Get_Thd_Lun": {"scpi": "THD:LUNit?", "description": "Selects the measurement units for the Level measurement in the THD function", "subsystem": "THD", "unverified": true},
  "Get_Thd_Mmax": {"scpi": "THD:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "THD", "unverified": true},
  "Get_Thd_Mmin": {"scpi": "THD:MMIN?", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "subsystem": "THD", "unverified": true},
  "Get_Thd_Notc": {"scpi": "THD:NOTChfreq?", "description": "Selects the center frequency for the tunable notch filter when TUNE is set to FIXTUNE", "subsystem": "THD", "unverified": true},
  "Get_Thd_Spe": {"scpi": "THD:SPEed?", "description": "Selects the sweep speed", "subsystem": "THD", "unverified": true},
  "Get_Thd_Step": {"scpi": "THD:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "THD", "unverified": true},
  "Get_Thd_Swpt": {"scpi": "THD:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "THD", "unverified": true},
  "Get_Thd_Tun": {"scpi": "THD:TUNe?", "description": "Selects the notch filter tuning mode for the THD function", "subsystem": "THD", "unverified": true},
  "Get_Thd_Unit": {"scpi": "THD:UNIT?", "description": "Selects the measurement units for the THD function", "subsystem": "THD", "unverified": true},
  "Get_Thd_Wtd": {"scpi": "THD:WTD?", "description": "Selects the weighting filter for the THD+N function when the WTD filter is selected", "subsystem": "THD", "unverified": true},
  "Get_Wf_Det": {"scpi": "WF:DETector?", "description": "Selects the W+F detector", "subsystem": "WF", "unverified": true},
  "Get_Wf_Filt": {"scpi": "WF:FILTer?", "description": "Selects the W+F weighted or unweighted filters", "subsystem": "WF", "unverified": true},
  "Get_Wf_Lun": {"scpi": "WF:LUNit?", "description": "Selects the measurement units for the Level measurement in the W+F function", "subsystem": "WF", "unverified": true},
  "Get_Wf_Mmax": {"scpi": "WF:MMAX?", "description": "Selects the upper magnitude display range for the bargraph display", "subsystem": "WF", "unverified": true},
  "Get_Wf_Mmin": {"scpi": "WF:MMIN?", "description": "Selects the lower magnitude display range for the bargraph display", "subsystem": "WF", "unverified": true},
  "Get_Wf_Resp": {"scpi": "WF:RESPonse?", "description": "Selects the measurement response mode for W+F measurements", "subsystem": "WF", "unverified": true},
  "Get_Wf_Unit": {"scpi": "WF:UNIT?", "description": "Selects the default percent measurement units for the W+F meter", "subsystem": "WF", "unverified": true},
  "Get_Wf_Wfun": {"scpi": "WF:WFUNit?", "description": "Selects the W+F function frequency meter units and reference frequency for frequency deviation measurements", "subsystem": "WF", "unverified": true},
  "Get_Xtal_Amax": {"scpi": "XTALk:AMAX?", "description": "For the Access instrument, this command sets the maximum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Amin": {"scpi": "XTALk:AMIN?", "description": "For the Access instrument, this command sets the minimum amplitude level for an amplitude sweep of the analog generator when the SWPType command is set to AMPL", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Ext": {"scpi": "XTALk:EXTernal?", "description": "Returns the current external sweep settling mode", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Fmax": {"scpi": "XTALk:FMAX?", "description": "Selects the upper frequency display range for the sweep and bargraph displays", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Fmin": {"scpi": "XTALk:FMIN?", "description": "Selects the lower frequency display range for the sweep and bargraph displays", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Lun": {"scpi": "XTALk:LUNit?", "description": "Selects the level measurement units for the XTALK function", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Mmax": {"scpi": "XTALk:MMAX?", "description": "Selects the upper magnitude display range for the sweep and bargraph displays in currently selected units", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Mmin": {"scpi": "XTALk:MMIN?", "description": "Selects the lower magnitude display range for the sweep and bargraph displays", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Spe": {"scpi": "XTALk:SPEed?", "description": "Selects the sweep speed", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Step": {"scpi": "XTALk:STEPs?", "description": "Selects the sweep mode or the number of sweep steps", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Swpt": {"scpi": "XTALk:SWPType?", "description": "Specifies that either a frequency sweep or amplitude sweep is to be performed when the SWEEP START command is received", "subsystem": "XTAL", "unverified": true},
  "Get_Xtal_Unit": {"scpi": "XTALk:UNIT?", "description": "Selects the XTALK measurement units", "subsystem": "XTAL", "unverified": true},
}
```

