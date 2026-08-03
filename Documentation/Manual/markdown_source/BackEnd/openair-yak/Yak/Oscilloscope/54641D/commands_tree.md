<!-- BEGIN GENERATED — openair-yak build-trees -->

# Oscilloscope/54641D — command tree

Generated from `commands.json` by `openair-yak build-trees`. Edit the table, not this file.

**438 commands** — SET 169 · RIG 1 · NAB 163 · DO 105 · 325 unverified (74%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Compound commands

Several statements in one message, so they hang off no single branch. Every statement after the first carries a leading colon — without it the parser reads it relative to the previous header's path and the instrument answers `-113`.

- **NAB** `Get_Math_Statistics` · → vpp, vmax, vmin, vaverage
  - `:MEASure:SOURce FUNCtion;:MEASure:VPP?;:MEASure:VMAX?;:MEASure:VMIN?;:MEASure:VAVerage?`
- **NAB** `Get_Time_Stats_CH1` · args: `source` · → frequency, period, dutycycle, risetime
  - `:MEASure:SOURce <source>;:MEASure:FREQuency?;:MEASure:PERiod?;:MEASure:DUTYcycle?;:MEASure:RISetime?`
- **NAB** `Get_Time_Stats_CH2` · args: `source` · → frequency, period, dutycycle, risetime
  - `:MEASure:SOURce <source>;:MEASure:FREQuency?;:MEASure:PERiod?;:MEASure:DUTYcycle?;:MEASure:RISetime?`
- **NAB** `Get_Voltage_Stats_CH1` · args: `source` · → vpp, vrms, vmax, vmin
  - `:MEASure:SOURce <source>;:MEASure:VPP?;:MEASure:VRMS?;:MEASure:VMAX?;:MEASure:VMIN?`
- **NAB** `Get_Voltage_Stats_CH2` · args: `source` · → vpp, vrms, vmax, vmin
  - `:MEASure:SOURce <source>;:MEASure:VPP?;:MEASure:VRMS?;:MEASure:VMAX?;:MEASure:VMIN?`
- **RIG** `Setup_Trigger_Edge` · args: `source`, `slope`, `level` · enum · †<br>Set edge trigger source, slope and level together
  - `:TRIGger:EDGE:SOURce <source>;:TRIGger:EDGE:SLOPe <slope>;:TRIGger:EDGE:LEVel <level>`

## Tree

- `AUToscale` — **DO** `Autoscale`
- `DIGitize` — **DO** `Digitize_Channel` · `<chan>` · per-instance: `chan`
- `AUToscale` — **DO** `Do_Autoscale`
- `RUN` — **DO** `Do_Run`
- `SINGle` — **DO** `Do_Single`
- `STOP` — **DO** `Do_Stop`
- `RUN` — **DO** `Run`
- `SINGle` — **DO** `Single`
- `STOP` — **DO** `Stop`
- **`ACQuire`**
  - `COMPlete` — **SET** `Set_Acquire_Complete` · `<value>` · args: `value` · †
  - `MODE` — **SET** `Set_Acquire_Mode` · `<value>` · args: `value` · enum · †
  - `TYPE` — **SET** `Set_Acquire_Mode_AVERage` · `<type>` · args: `type` · enum
  - `TYPE` — **SET** `Set_Acquire_Mode_HRESolution` · `<type>` · args: `type` · enum
  - `TYPE` — **SET** `Set_Acquire_Mode_NORMal` · `<type>` · args: `type` · enum
  - `TYPE` — **SET** `Set_Acquire_Mode_PEAK` · `<type>` · args: `type` · enum
  - `TYPE` — **SET** `Set_Acquire_Type` · `<type>` · args: `type` · enum
  - `COUNt` — **SET** `Set_Average_Count` · `<count>` · args: `count` · integer
  - `COUNt` — **SET** `Set_Averaging_Count` · `<count>` · args: `count` · integer
  - `POINts` — **SET** `Set_Points` · `<points>` · args: `points` · integer
  - `COMPlete?` — **NAB** `Get_Acquire_Complete` · → 1 value · †
  - `COUNT?` — **NAB** `Get_Acquire_Count` · → NR1 · †
  - `MODE?` — **NAB** `Get_Acquire_Mode` · → CRD · †
  - `POINts?` — **NAB** `Get_Acquire_Points` · → NR1 · †
  - `SRATe?` — **NAB** `Get_Sample_Rate` · → 1 value
- **`CALibrate`**
  - `LABel` — **SET** `Set_Calibrate_Label` · `<value>` · args: `value` · †
  - `DATE?` — **NAB** `Get_Calibrate_Date` · → 1 value · †
  - `LABel?` — **NAB** `Get_Calibrate_Label` · → 1 value · †
  - `SWITch?` — **NAB** `Get_Calibrate_Switch` · → 1 value · †
  - `TIME?` — **NAB** `Get_Calibrate_Time` · → NR3 s · †
- **`CHANNEL1`**
  - `COUPLING` — **SET** `Set_Channel_Coupling` · `<value>` · args: `value` · enum · †<br>Receiving Information from the Instrument
  - `COUPLING?` — **NAB** `Get_Channel_Coupling` · → CRD · †<br>Receiving Information from the Instrument
  - `RANGE?` — **NAB** `Get_Channel_Range` · → NR3 · †<br>Address Varies According to Configuration
  - `BWLIMIT` — **DO** `Do_Channel_Bwlimit` · †
  - `OFFSET` — **DO** `Do_Channel_Offset` · †
  - `PROBE` — **DO** `Do_Channel_Probe` · †<br>Setting Up the Instrument
- **`CHANnel`**
  - `ACTivity` — **DO** `Do_Channel_Activity` · †
  - `MATH` — **DO** `Do_Channel_Math` · †
  - `THReshold` — **DO** `Do_Channel_Threshold` · †
- **`CHANnel1`**
  - `BWLimit` — **SET** `CH1_BWLimit` · `<state>` · args: `state` · bool: `OFF` | `ON`
  - `COUPling` — **SET** `CH1_Coupling` · `<coupling>` · args: `coupling` · enum
  - `INVert` — **SET** `CH1_Invert` · `<state>` · args: `state` · bool: `OFF` | `ON`
  - `LABel` — **SET** `CH1_Label` · `<string>` · args: `string`
  - `OFFSet` — **SET** `CH1_Offset` · `<offset>` · args: `offset` · numeric
  - `PROBe` — **SET** `CH1_Probe` · `<attenuation>` · args: `attenuation` · numeric
  - `SCALe` — **SET** `CH1_Scale` · `<scale>` · args: `scale` · numeric
  - `OFFSet` — **SET** `Set_Channel_Offset` · `<offset>` · args: `offset` · numeric
  - `RANGe` — **SET** `Set_Channel_Range` · `<range>` · args: `range` · numeric
  - `SCALe` — **SET** `Set_Channel_Scale` · `<scale>` · args: `scale` · numeric
  - `DISPlay` — **DO** `Do_CH1_OFF` · `OFF`
  - `DISPlay` — **DO** `Do_CH1_ON` · `ON`
- **`CHANnel2`**
  - `BWLimit` — **SET** `CH2_BWLimit` · `<state>` · args: `state` · bool: `OFF` | `ON`
  - `COUPling` — **SET** `CH2_Coupling` · `<coupling>` · args: `coupling` · enum
  - `INVert` — **SET** `CH2_Invert` · `<state>` · args: `state` · bool: `OFF` | `ON`
  - `LABel` — **SET** `CH2_Label` · `<string>` · args: `string`
  - `OFFSet` — **SET** `CH2_Offset` · `<offset>` · args: `offset` · numeric
  - `PROBe` — **SET** `CH2_Probe` · `<attenuation>` · args: `attenuation` · numeric
  - `SCALe` — **SET** `CH2_Scale` · `<scale>` · args: `scale` · numeric
  - `DISPlay` — **DO** `Do_CH2_OFF` · `OFF`
  - `DISPlay` — **DO** `Do_CH2_ON` · `ON`
  - `SKEW` — **DO** `Do_Channel_Skew` · †
- **`CHANnel<n>`**
  - `BWLimit` — **SET** `Set_Bandwidth_Limit` · `<state>` · args: `state` · bool: `OFF` | `ON` · per-instance: `n`
  - `COUPling` — **SET** `Set_Coupling` · `<coupling>` · args: `coupling` · enum · per-instance: `n`
  - `DISPlay` — **SET** `Set_Display` · `<state>` · args: `state` · bool: `OFF` | `ON` · per-instance: `n`
  - `IMPedance` — **SET** `Set_Impedance` · `<imp>` · args: `imp` · enum · per-instance: `n`
  - `INVert` — **SET** `Set_Invert` · `<state>` · args: `state` · bool: `OFF` | `ON` · per-instance: `n`
  - `PROBe` — **SET** `Set_Probe` · `<atten>` · args: `atten` · numeric · per-instance: `n`
- **`DIGital<n>`**
  - `DISPlay` — **SET** `Set_Digital_Display` · `<state>` · args: `state` · bool: `OFF` | `ON` · per-instance: `n`
  - `LABel` — **SET** `Set_Digital_Label` · `<label>` · args: `label` · per-instance: `n`
  - `POSition` — **SET** `Set_Digital_Position` · `<pos>` · args: `pos` · numeric · per-instance: `n`
- **`DISPLay`**
  - `LINE` — **DO** `Do_Display_Line` · †
- **`DISPlay`**
  - `DATA` — **SET** `Set_Display_Data` · `<value>` · args: `value` · block · †
  - `LABel` — **SET** `Set_Display_Label` · `<value>` · args: `value` · †
  - `PERSistence` — **SET** `Set_Display_Persistence` · `<value>` · args: `value` · numeric (s) · †
  - `SOURce` — **SET** `Set_Display_Source` · `<value>` · args: `value` · enum · †
  - `VECTors` — **SET** `Set_Display_Vectors` · `<value>` · args: `value` · †
  - `DATA?` — **NAB** `Get_Display_Data` · → BLOCK · †
  - `LABel?` — **NAB** `Get_Display_Label` · → 1 value · †
  - `PERSistence?` — **NAB** `Get_Display_Persistence` · → NR3 s · †
  - `SOURce?` — **NAB** `Get_Display_Source` · → CRD · †
  - `VECTors?` — **NAB** `Get_Display_Vectors` · → 1 value · †
  - `CLEar` — **DO** `Do_Clear_Display`
  - `COLumn` — **DO** `Do_Display_Column` · †
  - `CONNect` — **DO** `Do_Display_Connect` · †
  - `GRID` — **DO** `Do_Display_Grid` · †
  - `INVerse` — **DO** `Do_Display_Invert` · †
  - `ORDer` — **DO** `Do_Display_Order` · †
  - `PIXel` — **DO** `Do_Display_Pixel` · †
  - `POSition` — **DO** `Do_Display_Position` · †
  - `ROW` — **DO** `Do_Display_Row` · †
  - `TEXT` — **DO** `Do_Display_Text` · †
- **`EXTernal`**
  - `BWLimit` — **SET** `Set_External_Bwlimit` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
  - `IMPedance` — **SET** `Set_External_Impedance` · `<value>` · args: `value` · enum · †
  - `PROBe` — **SET** `Set_External_Probe` · `<value>` · args: `value` · numeric · †
  - `RANGe` — **SET** `Set_External_Range` · `<value>` · args: `value` · numeric · †
  - `UNITs` — **SET** `Set_External_Units` · `<value>` · args: `value` · enum · †
  - `BWLimit?` — **NAB** `Get_External_Bwlimit` · → BOOL · †
  - `IMPedance?` — **NAB** `Get_External_Impedance` · → CRD · †
  - `PROBe?` — **NAB** `Get_External_Probe` · → NR3 · †
  - `PROTection?` — **NAB** `Get_External_Protection` · → 1 value · †
  - `RANGe?` — **NAB** `Get_External_Range` · → NR3 · †
  - `UNITs?` — **NAB** `Get_External_Units` · → CRD · †
  - `INPut` — **DO** `Do_External_Input` · †
  - `PMODe` — **DO** `Do_External_Pmode` · †
  - **`PROTection`**
    - `CLEAR` — **DO** `Do_External_Protection_Clear` · †
- **`FUNCtion`**
  - `CENTer` — **SET** `Set_Center_Frequency` · `<frequency>` · args: `frequency` · numeric
  - `SCALe` — **SET** `Set_FFT_Scale` · `<scale>` · args: `scale` · numeric
  - `OPERation` — **SET** `Set_Function_Operation` · `<op>` · args: `op` · enum
  - `REFerence` — **SET** `Set_Function_Reference` · `<value>` · args: `value` · enum · †
  - `OFFSet` — **SET** `Set_Math_Offset` · `<offset>` · args: `offset` · numeric
  - `RANGe` — **SET** `Set_Math_Range` · `<range>` · args: `range` · numeric
  - `OPERation` — **SET** `Set_Operation` · `<operation>` · args: `operation` · enum
  - `SOURce1` — **SET** `Set_Source1` · `<src>` · args: `src` · enum
  - `SOURce2` — **SET** `Set_Source2` · `<src>` · args: `src` · enum
  - `SPAN` — **SET** `Set_Span` · `<span>` · args: `span` · numeric
  - `WINDow` — **SET** `Set_Window_FLATtop` · `<window>` · args: `window` · enum
  - `WINDow` — **SET** `Set_Window_HANNing` · `<window>` · args: `window` · enum
  - `WINDow` — **SET** `Set_Window_RECTangular` · `<window>` · args: `window` · enum
  - `CENTer?` — **NAB** `Get_Function_Center` · → NR3 · †
  - `DISPlay?` — **NAB** `Get_Function_Display` · → BOOL · †<br>Obsolete and Discontinued Commands
  - `OFFSet?` — **NAB** `Get_Function_Offset` · → NR3 · †
  - `OPERation?` — **NAB** `Get_Function_Operation` · → CRD · †
  - `RANGe?` — **NAB** `Get_Function_Range` · → NR3 · †
  - `REFerence?` — **NAB** `Get_Function_Reference` · → CRD · †
  - `SOURce?` — **NAB** `Get_Function_Source` · → CRD · †
  - `SPAN?` — **NAB** `Get_Function_Span` · → NR3 · †
  - `WINDow?` — **NAB** `Get_Function_Window` · → CRD · †
  - `MOVE` — **DO** `Do_Function_Move` · †
  - `PEAKs` — **DO** `Do_Function_Peaks` · †
  - `VIEW` — **DO** `Do_Function_View` · †<br>Obsolete and Discontinued Commands
  - `DISPlay` — **DO** `Do_Math_OFF` · `OFF`
  - `DISPlay` — **DO** `Do_Math_ON` · `ON`
  - `SOURce` — **DO** `Set_Source_CH1` · `CHANnel1`
  - `SOURce` — **DO** `Set_Source_CH2` · `CHANnel2`
- **`HARDcopy`**
  - `FACTors` — **SET** `Set_Hardcopy_Factors` · `<value>` · args: `value` · †
  - `FFEed` — **SET** `Set_Hardcopy_Ffeed` · `<value>` · args: `value` · †
  - `FORMat` — **SET** `Set_Hardcopy_Format` · `<value>` · args: `value` · enum · †<br>Obsolete and Discontinued Commands
  - `GRAYscale` — **SET** `Set_Hardcopy_Grayscale` · `<value>` · args: `value` · †
  - `FACTors?` — **NAB** `Get_Hardcopy_Factors` · → 1 value · †
  - `FFEed?` — **NAB** `Get_Hardcopy_Ffeed` · → 1 value · †
  - `FORMat?` — **NAB** `Get_Hardcopy_Format` · → CRD · †<br>Obsolete and Discontinued Commands
  - `GRAYscale?` — **NAB** `Get_Hardcopy_Grayscale` · → 1 value · †
  - `ADDRess` — **DO** `Do_Hardcopy_Address` · †
  - `DESTination` — **DO** `Do_Hardcopy_Destination` · †
  - `DEVice` — **DO** `Do_Hardcopy_Device` · †<br>Obsolete and Discontinued Commands
- **`MARKer`**
  - `MODE` — **SET** `Set_Marker_Mode` · `<mode>` · args: `mode` · enum
  - `X1Position` — **SET** `Set_X1` · `<pos>` · args: `pos` · numeric
  - `X2Position` — **SET** `Set_X2` · `<pos>` · args: `pos` · numeric
  - `Y1Position` — **SET** `Set_Y1` · `<lev>` · args: `lev` · numeric
  - `Y2Position` — **SET** `Set_Y2` · `<lev>` · args: `lev` · numeric
  - `MODE?` — **NAB** `Get_Marker_Mode` · → CRD · †
  - `XDELta?` — **NAB** `Get_X_Delta` · → NR3 s
  - `YDELta?` — **NAB** `Get_Y_Delta` · → NR3 s
  - `TDELta` — **DO** `Do_Marker_Tdelta` · †<br>Obsolete and Discontinued Commands
  - `VDELta` — **DO** `Do_Marker_Vdelta` · †
- **`MARker`**
  - `XDELta?` — **NAB** `Get_Marker_Xdelta` · → NR3 s · †
- **`MEASURE`**
  - `RISETIME?` — **NAB** `Get_Measure_Risetime` · → NR3 s · †<br>Query Command
- **`MEASure`**
  - `COUNter` — **SET** `Set_Measure_Count` · `<value>` · args: `value` · integer · †
  - `DELay` — **SET** `Set_Measure_Delay` · `<value>` · args: `value` · numeric (s) · †
  - `FALLtime` — **SET** `Set_Measure_Falltime` · `<value>` · args: `value` · numeric (s) · †
  - `NWIDth` — **SET** `Set_Measure_Nwidth` · `<value>` · args: `value` · †
  - `OVERshoot` — **SET** `Set_Measure_Overshoot` · `<value>` · args: `value` · †
  - `PHASe` — **SET** `Set_Measure_Phase` · `<value>` · args: `value` · †
  - `PREShoot` — **SET** `Set_Measure_Preshoot` · `<value>` · args: `value` · block · †
  - `PWIDth` — **SET** `Set_Measure_Pwidth` · `<value>` · args: `value` · †
  - `SHOW` — **SET** `Set_Measure_Show` · `<value>` · args: `value` · †
  - `SOURce` — **SET** `Set_Measure_Source` · `<source>` · args: `source` · enum
  - `TEDGe` — **SET** `Set_Measure_Tedge` · `<value>` · args: `value` · †
  - `TVALue` — **SET** `Set_Measure_Tvalue` · `<value>` · args: `value` · †
  - `VAMPlitude` — **SET** `Set_Measure_Vamplitude` · `<value>` · args: `value` · †
  - `VBASe` — **SET** `Set_Measure_Vbase` · `<value>` · args: `value` · †
  - `VTOP` — **SET** `Set_Measure_Vtop` · `<value>` · args: `value` · †
  - `XMAX` — **SET** `Set_Measure_Xmax` · `<value>` · args: `value` · numeric · †<br>Obsolete and Discontinued Commands
  - `XMIN` — **SET** `Set_Measure_Xmin` · `<value>` · args: `value` · numeric · †<br>Obsolete and Discontinued Commands
  - `COUNter?` — **NAB** `Get_Measure_Count` · → NR1 · †
  - `DELay?` — **NAB** `Get_Measure_Delay` · → NR3 s · †
  - `FALLtime?` — **NAB** `Get_Measure_Falltime` · → NR3 s · †
  - `NWIDth?` — **NAB** `Get_Measure_Nwidth` · → 1 value · †
  - `OVERshoot?` — **NAB** `Get_Measure_Overshoot` · → 1 value · †
  - `PHASe?` — **NAB** `Get_Measure_Phase` · → 1 value · †
  - `PREShoot?` — **NAB** `Get_Measure_Preshoot` · → BLOCK · †
  - `PWIDth?` — **NAB** `Get_Measure_Pwidth` · → 1 value · †
  - `SHOW?` — **NAB** `Get_Measure_Show` · → 1 value · †
  - `SOURce?` — **NAB** `Get_Measure_Source` · → CRD · †
  - `TEDGe?` — **NAB** `Get_Measure_Tedge` · → 1 value · †
  - `TVALue?` — **NAB** `Get_Measure_Tvalue` · → 1 value · †
  - `VAMPlitude?` — **NAB** `Get_Measure_Vamplitude` · → 1 value · †
  - `VBASe?` — **NAB** `Get_Measure_Vbase` · → 1 value · †
  - `VTIMe?` — **NAB** `Get_Measure_Vtime` · → NR3 s · †
  - `VTOP?` — **NAB** `Get_Measure_Vtop` · → 1 value · †
  - `XMAX?` — **NAB** `Get_Measure_Xmax` · → NR3 · †<br>Obsolete and Discontinued Commands
  - `XMIN?` — **NAB** `Get_Measure_Xmin` · → NR3 · †<br>Obsolete and Discontinued Commands
  - `CLEar` — **DO** `Do_Measure_Clear` · †<br>Obsolete and Discontinued Commands
  - `LOWer` — **DO** `Do_Measure_Lower` · †<br>Obsolete and Discontinued Commands
  - `RISEtime` — **DO** `Do_Measure_Risetime` · †
  - `SCRatch` — **DO** `Do_Measure_Scratch` · †<br>Obsolete and Discontinued Commands
  - `TDELta` — **DO** `Do_Measure_Tdelta` · †<br>Obsolete and Discontinued Commands
  - `THResholds` — **DO** `Do_Measure_Threshold` · †<br>Obsolete and Discontinued Commands
  - `TMAX` — **DO** `Do_Measure_Tmax` · †<br>Obsolete and Discontinued Commands
  - `TMIN` — **DO** `Do_Measure_Tmin` · †<br>Obsolete and Discontinued Commands
  - `TSTArt` — **DO** `Do_Measure_Tstart` · †<br>Obsolete and Discontinued Commands
  - `TSTOp` — **DO** `Do_Measure_Tstop` · †<br>Obsolete and Discontinued Commands
  - `TVOLt` — **DO** `Do_Measure_Tvolt` · †
  - `UPPer` — **DO** `Do_Measure_Upper` · †
  - `VDELta` — **DO** `Do_Measure_Vdelta` · †
  - `VSTArt` — **DO** `Do_Measure_Vstart` · †
  - `VSTOp` — **DO** `Do_Measure_Vstop` · †
  - **`DEFine`**
    - `THResholds` — **SET** `Set_Measure_Thresholds` · `<mode>` · args: `mode` · numeric
- **`POD<n>`**
  - `THReshold` — **SET** `Set_Pod_Threshold` · `<thresh>` · args: `thresh` · numeric · per-instance: `n`
- **`PROBe`**
  - `SKEW` — **SET** `Set_Probe_Skew` · `<value>` · args: `value` · numeric · †
  - `SKEW?` — **NAB** `Get_Probe_Skew` · → NR3 · †
- **`PROTection`**
  - `CLEAR` — **DO** `Do_Protection_Clear` · †
- **`SYSTEM`**
  - `DSP?` — **NAB** `Get_System_Dsp` · → 1 value · †<br>Message Queue
- **`SYSTem`**
  - `LOCK` — **SET** `Lock_Front_Panel` · `<state>` · args: `state`
  - `DATE` — **SET** `Set_System_Date` · `<value>` · args: `value` · †
  - `TIME` — **SET** `Set_System_Time` · `<value>` · args: `value` · numeric (s) · †
  - `ERRor?` — **NAB** `Get_Error` · → NR2
  - `SETup?` — **NAB** `Get_Setup` · → BLOCK
  - `DATE?` — **NAB** `Get_System_Date` · → 1 value · †
  - `LOCK?` — **NAB** `Get_System_Lock` · → 1 value · †
  - `TIME?` — **NAB** `Get_System_Time` · → NR3 s · †
  - `ERRor?` — **NAB** `Read_Error` · → NR2
  - `DSP` — **DO** `Do_System_Dsp` · †<br>Message Queue
  - `KEY` — **DO** `Do_System_Key` · †
- **`TIM`**
  - `DEL` — **DO** `Do_Timebase_Delay` · †<br>Program Header Options
- **`TIMebase`**
  - `MODE` — **SET** `Set_Mode` · `<mode>` · args: `mode` · enum
  - `POSition` — **SET** `Set_Position` · `<pos>` · args: `pos` · numeric (s)
  - `REFerence` — **SET** `Set_Reference` · `<ref>` · args: `ref` · enum
  - `POSition` — **SET** `Set_Timebase_Position` · `<position>` · args: `position` · numeric (s)
  - `RANGe` — **SET** `Set_Timebase_Range` · `<value>` · args: `value` · numeric (s) · †
  - `SCALe` — **SET** `Set_Timebase_Scale` · `<scale>` · args: `scale` · numeric (s)
  - `MODE?` — **NAB** `Get_Timebase_Mode` · → CRD s · †
  - `POSition?` — **NAB** `Get_Timebase_Position` · → NR3 s · †
  - `RANGe?` — **NAB** `Get_Timebase_Range` · → NR3 s · †
  - `REFerence?` — **NAB** `Get_Timebase_Reference` · → CRD s · †
  - `SCALe?` — **NAB** `Get_Timebase_Scale` · → NR3 s · †
  - `WINDow` — **DO** `Do_Timebase_Window` · †<br>Command Set Organization
  - **`WINDow`**
    - `RANGe` — **SET** `Set_Timebase_Window_Range` · `<value>` · args: `value` · numeric (s) · †
    - `POSition` — **SET** `Set_Window_Position` · `<pos>` · args: `pos` · numeric (s)
    - `SCALe` — **SET** `Set_Window_Scale` · `<scale>` · args: `scale` · numeric (s)
    - `POSition?` — **NAB** `Get_Timebase_Window_Position` · → NR3 s · †
    - `RANGe?` — **NAB** `Get_Timebase_Window_Range` · → NR3 s · †
    - `SCALe?` — **NAB** `Get_Timebase_Window_Scale` · → NR3 s · †
- **`TRIGGER`**
  - `LEVEL` — **DO** `Do_Trigger_Level` · †
  - `SLOPE` — **DO** `Do_Trigger_Slope` · †
  - **`DURation`**
    - `GREaterthan` — **DO** `Do_Trigger_Duration_Greaterthan` · †
    - `LESSthan` — **DO** `Do_Trigger_Duration_Lessthan` · †
  - **`GLITch`**
    - `GREaterthan` — **DO** `Do_Trigger_Glitch_Greaterthan` · †
    - `LESSthan` — **DO** `Do_Trigger_Glitch_Lessthan` · †
  - **`SEQuence`**
    - `FIND` — **SET** `Set_Trigger_Sequence_Find` · `<value>` · args: `value` · †
    - `RESet` — **SET** `Set_Trigger_Sequence_Reset` · `<value>` · args: `value` · †
    - `TIMer` — **SET** `Set_Trigger_Sequence_Timebase` · `<value>` · args: `value` · numeric (s) · †
    - `TRIGger` — **SET** `Set_Trigger_Sequence_Trigger` · `<value>` · args: `value` · †
    - `FIND?` — **NAB** `Get_Trigger_Sequence_Find` · → 1 value · †
    - `RESet?` — **NAB** `Get_Trigger_Sequence_Reset` · → 1 value · †
    - `TIMer?` — **NAB** `Get_Trigger_Sequence_Timebase` · → NR3 s · †
    - `TRIGger?` — **NAB** `Get_Trigger_Sequence_Trigger` · → 1 value · †
- **`TRIGger`**
  - `HOLDoff` — **SET** `Set_Holdoff` · `<time>` · args: `time` · numeric
  - `HFReject` — **SET** `Set_Trigger_Hfreject` · `<value>` · args: `value` · †
  - `MODE` — **SET** `Set_Trigger_Mode` · `<mode>` · args: `mode` · enum
  - `NREJect` — **SET** `Set_Trigger_Nreject` · `<value>` · args: `value` · †
  - `PATTern` — **SET** `Set_Trigger_Pattern` · `<value>` · args: `value` · †
  - `SWEep` — **SET** `Set_Trigger_Sweep` · `<sweep>` · args: `sweep` · enum
  - `COUPling?` — **NAB** `Get_Trigger_Coupling` · → CRD · †
  - `HFReject?` — **NAB** `Get_Trigger_Hfreject` · → 1 value · †
  - `HOLDoff?` — **NAB** `Get_Trigger_Holdoff` · → NR3 · †
  - `MODE?` — **NAB** `Get_Trigger_Mode` · → CRD · †
  - `NREJect?` — **NAB** `Get_Trigger_Nreject` · → 1 value · †
  - `PATTern?` — **NAB** `Get_Trigger_Pattern` · → 1 value · †
  - `REJect?` — **NAB** `Get_Trigger_Reject` · → 1 value · †
  - `SWEep?` — **NAB** `Get_Trigger_Sweep` · → CRD · †
  - `ADVanced` — **DO** `Do_Trigger_Advanced` · †
  - `CAN` — **DO** `Do_Trigger_Can` · †<br>Table 5-1
  - `DURation` — **DO** `Do_Trigger_Duration` · †<br>Table 5-1
  - `EDGE` — **DO** `Do_Trigger_Edge` · †<br>Table 5-1
  - `GLITch` — **DO** `Do_Trigger_Glitch` · †<br>Table 5-1
  - `IIC` — **DO** `Do_Trigger_Iic` · †<br>Command Set Organization
  - `LIN` — **DO** `Do_Trigger_Lin` · †<br>Command Set Organization
  - `SEQuence` — **DO** `Do_Trigger_Sequence` · †<br>Table 5-1
  - `SPI` — **DO** `Do_Trigger_Spi` · †<br>Table 5-1
  - `THReshold` — **DO** `Do_Trigger_Threshold` · †
  - `TV` — **DO** `Do_Trigger_Tv` · †<br>Table 5-1
  - `USB` — **DO** `Do_Trigger_Usb` · †<br>Command Set Organization
  - **`CAN`**
    - `ACKNowledge` — **SET** `Set_Trigger_Can_Acknowledge` · `<value>` · args: `value` · †
    - `SAMPlepoint` — **SET** `Set_Trigger_Can_Samplepoint` · `<value>` · args: `value` · †
    - `SOURce` — **SET** `Set_Trigger_Can_Source` · `<value>` · args: `value` · enum · †
    - `TRIGger` — **SET** `Set_Trigger_Can_Trigger` · `<value>` · args: `value` · †
    - `ACKNowledge?` — **NAB** `Get_Trigger_Can_Acknowledge` · → 1 value · †
    - `SAMPlepoint?` — **NAB** `Get_Trigger_Can_Samplepoint` · → 1 value · †
    - `SOURce?` — **NAB** `Get_Trigger_Can_Source` · → CRD · †
    - `TRIGer?` — **NAB** `Get_Trigger_Can_Trigger` · → 1 value · †
    - `PATTern` — **DO** `Do_Trigger_Can_Pattern` · †<br>Table 5-1
    - `SIGNal` — **DO** `Do_Trigger_Can_Signal` · †<br>Table 5-1
    - **`PATTern`**
      - `DATA` — **SET** `Set_Trigger_Can_Pattern_Data` · `<value>` · args: `value` · block · †<br>Table 5-1
      - `ID` — **SET** `Set_Trigger_Can_Pattern_Id` · `<value>` · args: `value` · †<br>Table 5-1
      - `DATA?` — **NAB** `Get_Trigger_Can_Pattern_Data` · → BLOCK · †<br>Table 5-1
      - `ID?` — **NAB** `Get_Trigger_Can_Pattern_Id` · → 1 value · †<br>Table 5-1
      - **`ID`**
        - `MODE` — **SET** `Set_Trigger_Can_Pattern_Id_Mode` · `<value>` · args: `value` · enum · †
        - `MODE?` — **NAB** `Get_Trigger_Can_Pattern_Id_Mode` · → CRD · †
    - **`SIGNal`**
      - `BAUDrate` — **SET** `Set_Trigger_Can_Signal_Baudrate` · `<value>` · args: `value` · †
      - `BAUDrate?` — **NAB** `Get_Trigger_Can_Signal_Baudrate` · → 1 value · †
  - **`DURation`**
    - `PATTern` — **SET** `Set_Trigger_Duration_Pattern` · `<value>` · args: `value` · †
    - `QUALifier` — **SET** `Set_Trigger_Duration_Qualifier` · `<value>` · args: `value` · †
    - `RANGe` — **SET** `Set_Trigger_Duration_Range` · `<value>` · args: `value` · numeric · †
    - `GREaterthan?` — **NAB** `Get_Trigger_Duration_Greaterthan` · → 1 value · †
    - `LESSthan?` — **NAB** `Get_Trigger_Duration_Lessthan` · → 1 value · †
    - `PATTern?` — **NAB** `Get_Trigger_Duration_Pattern` · → 1 value · †
    - `QUALifier?` — **NAB** `Get_Trigger_Duration_Qualifier` · → 1 value · †
    - `RANGe?` — **NAB** `Get_Trigger_Duration_Range` · → NR3 · †
  - **`EDGE`**
    - `SLOPe` — **SET** `Set_Edge_Slope` · `<slope>` · args: `slope` · enum
    - `SOURce` — **SET** `Set_Edge_Source` · `<source>` · args: `source` · enum
    - `SOURce` — **SET** `Set_Edge_Source_CH1` · `<source>` · args: `source` · enum
    - `SOURce` — **SET** `Set_Edge_Source_CH2` · `<source>` · args: `source` · enum
    - `SOURce` — **SET** `Set_Edge_Source_EXT` · `<source>` · args: `source` · enum
    - `LEVel` — **SET** `Set_Trigger_Level` · `<level>` · args: `level` · numeric
    - `LEVel?` — **NAB** `Get_Trigger_Edge_Level` · → NR3 · †
    - `SLOPe?` — **NAB** `Get_Trigger_Edge_Slope` · → CRD · †
    - `SOURce?` — **NAB** `Get_Trigger_Edge_Source` · → CRD · †
  - **`GLITch`**
    - `QUALifier` — **SET** `Set_Glitch_Condition` · `<qual>` · args: `qual`
    - `SOURce` — **SET** `Set_Glitch_Source` · `<source>` · args: `source` · enum
    - `LESSthan` — **SET** `Set_Glitch_Width` · `<time>` · args: `time`
    - `LEVel` — **SET** `Set_Trigger_Glitch_Level` · `<value>` · args: `value` · numeric · †
    - `POLarity` — **SET** `Set_Trigger_Glitch_Polarity` · `<value>` · args: `value` · enum · †
    - `RANGe` — **SET** `Set_Trigger_Glitch_Range` · `<value>` · args: `value` · numeric · †
    - `GREaterthan?` — **NAB** `Get_Trigger_Glitch_Greaterthan` · → 1 value · †
    - `LESSthan?` — **NAB** `Get_Trigger_Glitch_Lessthan` · → 1 value · †
    - `LEVel?` — **NAB** `Get_Trigger_Glitch_Level` · → NR3 · †
    - `POLarity?` — **NAB** `Get_Trigger_Glitch_Polarity` · → CRD · †
    - `QUALifier?` — **NAB** `Get_Trigger_Glitch_Qualifier` · → 1 value · †
    - `RANGe?` — **NAB** `Get_Trigger_Glitch_Range` · → NR3 · †
    - `SOURce?` — **NAB** `Get_Trigger_Glitch_Source` · → CRD · †
  - **`IIC`**
    - `PATTern` — **DO** `Do_Trigger_Iic_Pattern` · †<br>Table 5-1
    - `SOURce` — **DO** `Do_Trigger_Iic_Source` · †<br>Table 5-1
    - `TRIGger` — **DO** `Do_Trigger_Iic_Trigger` · †<br>Command Set Organization
    - **`PATTern`**
      - `ADDRess` — **SET** `Set_Trigger_Iic_Pattern_Address` · `<value>` · args: `value` · integer · †
      - `DATA` — **SET** `Set_Trigger_Iic_Pattern_Data` · `<value>` · args: `value` · block · †
      - `ADDRess?` — **NAB** `Get_Trigger_Iic_Pattern_Address` · → NR1 · †
      - `DATA?` — **NAB** `Get_Trigger_Iic_Pattern_Data` · → BLOCK · †
    - **`TRIGger`**
      - `QUALifier` — **SET** `Set_Trigger_Iic_Trigger_Qualifier` · `<value>` · args: `value` · †
      - `QUALifer?` — **NAB** `Get_Trigger_Iic_Trigger_Qualifier` · → 1 value · †
  - **`LIN`**
    - `SOURce` — **SET** `Set_Trigger_Lin_Source` · `<value>` · args: `value` · enum · †
    - `TRIGger` — **SET** `Set_Trigger_Lin_Trigger` · `<value>` · args: `value` · †
    - `SOURce?` — **NAB** `Get_Trigger_Lin_Source` · → CRD · †
    - `TRIGger?` — **NAB** `Get_Trigger_Lin_Trigger` · → 1 value · †
    - `SIGNal` — **DO** `Do_Trigger_Lin_Signal` · †<br>Table 5-1
    - **`SIGNal`**
      - `BAUDrate` — **SET** `Set_Trigger_Lin_Signal_Baudrate` · `<value>` · args: `value` · †
      - `BAUDrate?` — **NAB** `Get_Trigger_Lin_Signal_Baudrate` · → 1 value · †
  - **`SEQuence`**
    - `COUNt` — **SET** `Set_Trigger_Sequence_Count` · `<value>` · args: `value` · integer · †
    - `COUNt?` — **NAB** `Get_Trigger_Sequence_Count` · → NR1 · †
    - `EDGE` — **DO** `Do_Trigger_Sequence_Edge` · †
    - `PATTern` — **DO** `Do_Trigger_Sequence_Pattern` · †
  - **`SPI`**
    - `FRAMing` — **SET** `Set_Trigger_Spi_Frame` · `<value>` · args: `value` · †
    - `FRAMing?` — **NAB** `Get_Trigger_Spi_Frame` · → 1 value · †
    - `CLOCk` — **DO** `Do_Trigger_Spi_Clock` · †<br>Command Set Organization
    - `PATTERN` — **DO** `Do_Trigger_Spi_Pattern` · †<br>Table 5-1
    - `SOURce` — **DO** `Do_Trigger_Spi_Source` · †<br>Table 5-1
    - **`CLOCk`**
      - `SLOPe` — **SET** `Set_Trigger_Spi_Clock_Slope` · `<value>` · args: `value` · enum · †
      - `TIMeout` — **SET** `Set_Trigger_Spi_Clock_Timebase` · `<value>` · args: `value` · numeric (s) · †
      - `SLOPe?` — **NAB** `Get_Trigger_Spi_Clock_Slope` · → CRD · †
      - `TIMeout?` — **NAB** `Get_Trigger_Spi_Clock_Timebase` · → NR3 s · †
    - **`PATTern`**
      - `DATA` — **SET** `Set_Trigger_Spi_Pattern_Data` · `<value>` · args: `value` · block · †
      - `WIDth` — **SET** `Set_Trigger_Spi_Pattern_Width` · `<value>` · args: `value` · numeric · †
      - `DATA?` — **NAB** `Get_Trigger_Spi_Pattern_Data` · → BLOCK · †
      - `WIDth?` — **NAB** `Get_Trigger_Spi_Pattern_Width` · → NR3 · †
    - **`SOURce`**
      - `CLOCk` — **SET** `Set_Trigger_Spi_Source_Clock` · `<value>` · args: `value` · †
      - `DATA` — **SET** `Set_Trigger_Spi_Source_Data` · `<value>` · args: `value` · block · †
      - `FRAMe` — **SET** `Set_Trigger_Spi_Source_Frame` · `<value>` · args: `value` · †
      - `CLOCk?` — **NAB** `Get_Trigger_Spi_Source_Clock` · → 1 value · †
      - `DATA?` — **NAB** `Get_Trigger_Spi_Source_Data` · → BLOCK · †
      - `FRAMe?` — **NAB** `Get_Trigger_Spi_Source_Frame` · → 1 value · †
  - **`TV`**
    - `LINE` — **SET** `Set_Trigger_Tv_Line` · `<value>` · args: `value` · †
    - `MODE` — **SET** `Set_Trigger_Tv_Mode` · `<value>` · args: `value` · enum · †
    - `POLarity` — **SET** `Set_Trigger_Tv_Polarity` · `<value>` · args: `value` · enum · †
    - `SOURce` — **SET** `Set_Trigger_Tv_Source` · `<value>` · args: `value` · enum · †
    - `STANdard` — **SET** `Set_Trigger_Tv_Standard` · `<value>` · args: `value` · †
    - `LINE?` — **NAB** `Get_Trigger_Tv_Line` · → 1 value · †
    - `MODE?` — **NAB** `Get_Trigger_Tv_Mode` · → CRD · †
    - `POLarity?` — **NAB** `Get_Trigger_Tv_Polarity` · → CRD · †
    - `SOURce?` — **NAB** `Get_Trigger_Tv_Source` · → CRD · †
    - `STANdard?` — **NAB** `Get_Trigger_Tv_Standard` · → 1 value · †
    - `TVMODE?` — **NAB** `Get_Trigger_Tv_Tvmode` · → 1 value · †
    - `FIELd` — **DO** `Do_Trigger_Tv_Field` · †
    - `TVHFrej` — **DO** `Do_Trigger_Tv_Tvhfrej` · †
    - `TVMode` — **DO** `Do_Trigger_Tv_Tvmode` · †
    - `VIR` — **DO** `Do_Trigger_Tv_Vir` · †
  - **`USB`**
    - `SPEed` — **SET** `Set_Trigger_Usb_Speed` · `<value>` · args: `value` · numeric · †
    - `TRIGer` — **SET** `Set_Trigger_Usb_Trigger` · `<value>` · args: `value` · †
    - `SPEed?` — **NAB** `Get_Trigger_Usb_Speed` · → NR3 · †
    - `TRIGger?` — **NAB** `Get_Trigger_Usb_Trigger` · → 1 value · †
    - `SOURce` — **DO** `Do_Trigger_Usb_Source` · †<br>Table 5-1
    - **`SOURce`**
      - `DMINus` — **SET** `Set_Trigger_Usb_Source_Dminus` · `<value>` · args: `value` · †
      - `DPLus` — **SET** `Set_Trigger_Usb_Source_Dplus` · `<value>` · args: `value` · †
      - `DMINus?` — **NAB** `Get_Trigger_Usb_Source_Dminus` · → 1 value · †
      - `DPLus?` — **NAB** `Get_Trigger_Usb_Source_Dplus` · → 1 value · †
- **`WAVeform`**
  - `BYTeorder` — **SET** `Set_Byte_Order` · `<order>` · args: `order`
  - `UNSigned` — **SET** `Set_Unsigned` · `<state>` · args: `state`
  - `FORMat` — **SET** `Set_Waveform_Format` · `<format>` · args: `format` · enum
  - `POINts` — **SET** `Set_Waveform_Points` · `<points>` · args: `points` · integer
  - `SOURce` — **SET** `Set_Waveform_Source` · `<source>` · args: `source` · enum
  - `VIEW` — **SET** `Set_Waveform_View` · `<value>` · args: `value` · †
  - `PREamble?` — **NAB** `Get_Preamble` · → BLOCK
  - `BYTeorder?` — **NAB** `Get_Waveform_Byteorder` · → 1 value · †
  - `COUNt?` — **NAB** `Get_Waveform_Count` · → NR1 · †
  - `DATA?` — **NAB** `Get_Waveform_Data` · → BLOCK
  - `FORMat?` — **NAB** `Get_Waveform_Format` · → CRD · †
  - `POINts?` — **NAB** `Get_Waveform_Points` · → NR1 · †
  - `SOURce?` — **NAB** `Get_Waveform_Source` · → CRD · †
  - `UNSigned?` — **NAB** `Get_Waveform_Unsigned` · → 1 value · †
  - `VIEW?` — **NAB** `Get_Waveform_View` · → 1 value · †
  - `XINCrement?` — **NAB** `Get_Waveform_Xincrement` · → NR3 · †
  - `XORigin?` — **NAB** `Get_Waveform_Xorigin` · → NR3 · †
  - `XREFerence?` — **NAB** `Get_Waveform_Xreference` · → NR3 · †
  - `YINCrement?` — **NAB** `Get_Waveform_Yincrement` · → NR3 · †
  - `YORigin?` — **NAB** `Get_Waveform_Yorigin` · → NR3 · †
  - `YREFerence?` — **NAB** `Get_Waveform_Yreference` · → NR3 · †

## Common commands (IEEE 488.2)

- `*CLS` — **DO** `Do_Clear_Status`
- `*OPC` — **DO** `Do_Opc` · †
- `*TRG` — **DO** `Do_Trg` · †
- `*WAI` — **DO** `Do_Wai` · †
- `*ESE?` — **NAB** `Get_Ese` · → NR1 · †
- `*ESR?` — **NAB** `Get_Esr` · → NR1 · †
- `*LRN?` — **NAB** `Get_Lrn` · → AARD · †
- `*OPC?` — **NAB** `Get_Opc` · → NR1 · †
- `*OPT?` — **NAB** `Get_Opt` · → AARD · †
- `*SRE?` — **NAB** `Get_Sre` · → NR1 · †
- `*STB?` — **NAB** `Get_Stb` · → NR1 · †
- `*TST?` — **NAB** `Get_Tst` · → NR1 · †
- `*IDN?` — **NAB** `Read_IDN` · → AARD
- `*RST` — **DO** `Reset_Device`<br>Do Reset
- `*ESE <value>` — **SET** `Set_Ese` · `<value>` · args: `value` · integer · †
- `*RCL <value>` — **SET** `Set_Rcl` · `<value>` · args: `value` · †
- `*SAV <value>` — **SET** `Set_Sav` · `<value>` · args: `value` · †
- `*SRE <value>` — **SET** `Set_Sre` · `<value>` · args: `value` · integer · †

<!-- END GENERATED -->

---

## Notes carried over

The **Keysight/Agilent 54641D** is a **Mixed Signal Oscilloscope (MSO)**, and that
is what makes its command tree bigger than a meter's. It deals with time, triggers
and two kinds of data: **analog** (voltage vs time) and **digital** (logic level vs
time). The tree splits the vertical controls to match — `CHANnel` for the 2 analog
BNC inputs, `DIGital`/`POD` for the 16 logic inputs.

It is part of the "54640-series", which has 50 Ω input impedance and deeper memory
than the 54620-series. Where a command below is 54640-only, it says so.

Sources: the Agilent 54621A/22A/24A/41A/42A and 54621D/22D/41D/42D Programmer's
Guide.

---

### 1. Root actions and `ACQuire`

The flow controls sit at the top of the tree — running versus stopped.

* **`RUN`** — start the scope (green light).
* **`STOP`** — stop it (red light).
* **`SINGle`** — one acquisition, then stop.
* **`AUToscale`** — the "Auto Set" button; tries to find the signal for you.
* **`DIGitize`** `<channel>` — block the computer until data is ready. This is the
  one you use from a script.

Configure **how** data is captured before you `DIGitize` it:

* **`ACQuire`**
  * `:TYPE` `NORMal|AVERage|PEAK` — `AVERage` to reduce noise, `PEAK` to catch
    glitches.
  * `:COUNt` `<number>` — number of averages (8, 64, …).
  * `:POINts` `100|250|500|1000|2000|MAXimum` — memory depth. `MAXimum` uses the
    deep memory, up to 2 MB on some models.
  * `:SRATe?` — current sample rate.

---

### 2. `CHANnel<n>` — analog vertical

The two BNC inputs on the front. `<n>` is 1 or 2.

* **`CHANnel<n>`**
  * `:BWLimit` `ON|OFF` — 20 MHz low-pass filter.
  * `:COUPling` `AC|DC|GND` — input coupling.
  * `:OFFSet` `<volts>` — moves the trace up or down (zero point).
  * `:RANGe` `<volts>` — full-scale vertical range, e.g. 40 V.
  * `:SCALe` `<volts/div>` — volts per division, e.g. 5 V.
  * `:DISPlay` `ON|OFF` — show or hide the trace.
  * `:IMPedance` `ONEMeg|FIFTy` — **54640-specific.** 50 Ω for high-speed active
    RF probes, 1 MΩ for standard passive probes.
  * `:PROBe` `<attenuation>` — probe ratio (1, 10, 100), so the scope's math is
    right.
  * `:PROBe:SKEW` `<seconds>` — deskew the analog channels to match digital timing.
  * `:INVert` `ON|OFF` — invert signal polarity.
  * `:UNITs` `VOLTs|AMPeres` — amps when a current probe is attached.

---

### 3. `DIGital<n>` and `POD<n>` — digital vertical

**This is the MSO part.** 16 digital lines, D0–D15.

* **Channels** are individual: `DIG0` … `DIG15`.
* **Pods** are groups of 8: `POD1` = D0–D7, `POD2` = D8–D15.

* **`DIGital<n>`** (n is 0–15)
  * `:DISPlay` `ON|OFF` — turn one logic bit on or off.
  * `:POSition` `<number>` — move the line up or down on screen. The range depends
    on display size: 0–7 large, 0–15 medium, 0–31 small.
  * `:LABel` `<string>` — rename "D0" to something like "CLK".

* **`POD<n>`** (n is 1 or 2)
  * `:THReshold` `TTL|CMOS|ECL|<voltage>` — logic level for the *entire* group of
    8 pins. Send a number instead of a standard name for a custom threshold, e.g.
    1.5 V.
  * **Note:** you cannot set D0 and D1 separately — they share the Pod 1 threshold.

---

### 4. `TIMebase` — horizontal

The X axis, and it applies to **all** channels at once, analog and digital.

* **`TIMebase`**
  * `:SCALe` `<seconds>` — time per division, e.g. `500e-6` for 500 µs.
  * `:POSition` `<seconds>` — delay from trigger to centre of screen.
  * `:REFerence` `LEFT|CENTer|RIGHt` — where the trigger point stays as you zoom.
  * `:MODE` `MAIN|WINDow|XY|ROLL`
    * `MAIN` — normal Y-T view.
    * `WINDow` — split-screen zoom.
    * `XY` — Lissajous, voltage vs voltage.
    * `ROLL` — strip chart, for slow signals.
  * **`:WINDow`** (delayed sweep / zoom)
    * `:POSition` `<seconds>` — scroll the zoom window.
    * `:SCALe` `<seconds>` — zoom factor, i.e. the window's width.

---

### 5. `TRIGger` — the brains

Advanced triggering, because of the digital lines.

* **`TRIGger`**
  * `:MODE` `EDGE|GLITch|PATTern|TV|IIC|SPI|USB|CAN…` — trigger type.
  * `:HOLDoff` `<seconds>` — holdoff before re-triggering. Crucial for complex
    bursts.
  * **`:EDGE`** (standard)
    * `:SOURce` `CHAN1|CHAN2|DIG0…DIG15|EXT` — analog channel 1, or digital bit 5.
    * `:SLOPe` `POSitive|NEGative`
  * **`:PATTern`** (logic)
    * `:LOGic` `<string>` — a binary code, e.g. `"10XX01"`.
  * **`:GLITch`** (pulse width)
    * `:SOURce` `<channel>`
    * `:POLarity` `POSitive|NEGative` — trigger on a high or a low pulse.
    * `:QUALifier` `LESSthan|GREaterthan|RANGe` — pulses narrower or wider than X.
    * `:LESSthan` / `:GREaterthan` `<seconds>` — the time limits.
  * **`:TV`**
    * `:STANdard` `NTSC|PAL|SECAM`
    * `:MODE` `LINE|FIEld1|FIEld2`
  * **`:IIC`** (I²C)
    * `:SOURce:CLOCk` `<channel>` · `:SOURce:DATA` `<channel>`
    * `:TRIGger:TYPE` `STARt|STOP|READ7|WRITe7|NACK…`
  * **`:SPI`**
    * `:SOURce:CLOCk` `<channel>` · `:SOURce:DATA` `<channel>`
    * `:SOURce:FRAMe` `<channel>` — chip select.

---

### 6. `WAVeform` — getting data out

A meter gives you one number; a scope gives you an array of 2000+ points. Set the
format before asking for data.

* **`WAVeform`**
  * `:SOURce` `CHAN1|DIGital0…` — which signal to download.
  * `:FORMat` `ASCii|WORD|BYTE`
    * `ASCii` — slow, human readable: `1.23, 1.24, 1.25…`
    * `BYTE` — fast, raw binary 0–255.
  * `:POINts` `100|250|500|1000|2000|MAXimum` — **critical.** Leave it unset and
    you may get 500 screen points instead of the full memory dump.
  * `:BYTeorder` `LSBFirst|MSBFirst` — binary endianness; the default is usually
    right for a PC.
  * `:UNSigned` `ON|OFF` — ON returns 0..255, OFF returns -128..127.
  * `:DATA?` — **the query.** The actual array of points.
  * `:PREamble?` — the scale factors that convert `BYTE` data back to volts and
    seconds.
  * `:TYPE?` — whether the data is normal, average or peak detect.

---

### 7. `MEASure` — automated math

* **`MEASure`**
  * `:SOURce` `<channel>` — which channel to measure.
  * **Voltage:** `:VPP?`, `:VMAX?`, `:VRMS?`, `:VAVerage?` (mean), `:VBASE?`,
    `:VTOP?`, `:OVERshoot?`, `:PREShoot?`
  * **Time:** `:FREQuency?`, `:PERiod?`, `:RISetime?`, `:FALLtime?`,
    `:DUTYcycle?`, `:PWIDth?` (positive width), `:NWIDth?` (negative width)
  * **Mixed:** `:DELay?` (time between Ch1 and Ch2 edges), `:PHASE?`
  * **`:DEFine`**
    * `:THResholds` `PERCent|ABSolute` — whether rise time means 10%/90% or
      specific voltages.

---

### 8. `MARKer` — cursors

Manual measurement is cursor work; these are the X and Y markers.

* **`MARKer`**
  * `:MODE` `MANual|MEASure|OFF`
  * `:X1Position` / `:X2Position` `<seconds>` — time cursors.
  * `:Y1Position` / `:Y2Position` `<volts>` — voltage cursors.
  * `:XDELta?` — time difference between them.
  * `:YDELta?` — voltage difference between them.

---

### 9. `FUNCtion` — math trace

The "Math" trace, the pink line.

* **`FUNCtion`**
  * `:OPERation` `ADD|SUBTract|MULTiply|FFT|INTegrate`
  * `:SOURce1` `<channel>` · `:SOURce2` `<channel>`

---

### 10. `SYSTem` — utilities

* **`SYSTem`**
  * `:ERRor?` — read the error queue; returns a code and a string.
  * `:SETup?` — the complete instrument setup as a binary block, to save and
    restore state.
  * `:LOCK` `ON|OFF` — lock the front-panel keys.

---

### Worked examples

**Setting up the digital channels.** Viewing an SPI bus with D0 as clock and D1 as
data, at TTL levels:

```text
POD1:THR TTL               (set D0-D7 to trigger at 1.4V)
DIG0:DISP ON               (turn on D0)
DIG1:DISP ON               (turn on D1)
DIG0:LAB "SPI_CLK"         (label D0)
TRIG:MODE EDGE             (set trigger mode)
TRIG:EDGE:SOUR DIG0        (trigger on the clock line)
```

**Asking for a measurement.** The frequency of that clock:

```text
MEAS:SOUR DIG0             (focus the measurement system on D0)
MEAS:FREQ?                 (scope answers: +1.00000E+06)
```
