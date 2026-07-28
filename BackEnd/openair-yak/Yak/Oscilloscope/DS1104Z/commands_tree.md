<!-- BEGIN GENERATED — Deployment/build_yak_command_trees.py -->

# Oscilloscope/DS1104Z — command tree

Generated from `commands.json` by `Deployment/build_yak_command_trees.py`. Edit the table, not this file.

**760 commands** — SET 339 · RIG 0 · NAB 358 · DO 63 · 687 unverified (90%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Compound commands

Several statements in one message, so they hang off no single branch. Every statement after the first carries a leading colon — without it the parser reads it relative to the previous header's path and the instrument answers `-113`.

- **NAB** `Get_Stats_CH1` · → vpp_1, vrms_1, frequency_1, pduty_1
  - `:MEASure:VPP? CHANnel1;:MEASure:VRMS? CHANnel1;:MEASure:FREQuency? CHANnel1;:MEASure:PDUTy? CHANnel1`
- **NAB** `Get_Stats_CH2` · → vpp_2, vrms_2, frequency_2, pduty_2
  - `:MEASure:VPP? CHANnel2;:MEASure:VRMS? CHANnel2;:MEASure:FREQuency? CHANnel2;:MEASure:PDUTy? CHANnel2`
- **NAB** `Get_Stats_CH3` · → vpp_3, vrms_3, frequency_3, pduty_3
  - `:MEASure:VPP? CHANnel3;:MEASure:VRMS? CHANnel3;:MEASure:FREQuency? CHANnel3;:MEASure:PDUTy? CHANnel3`
- **NAB** `Get_Stats_CH4` · → vpp_4, vrms_4, frequency_4, pduty_4
  - `:MEASure:VPP? CHANnel4;:MEASure:VRMS? CHANnel4;:MEASure:FREQuency? CHANnel4;:MEASure:PDUTy? CHANnel4`

## Tree

- `AUTO` — **DO** `Auto`
- `AUToscale` — **DO** `Auto_Scale`
- `CLEar` — **DO** `Clear`
- `TFORce` — **DO** `Force_Trigger`
- `RUN` — **DO** `Run`
- `SINGle` — **DO** `Single`
- `STOP` — **DO** `Stop`
- **`ACQuire`**
  - `AVERages` — **SET** `Set_Acquire_Averages` · `<value>` · args: `value` · integer · †<br>Set or query the number of averages under the average acquisition mode
  - `MDEPth` — **SET** `Set_Acquire_Mdepth` · `<value>` · args: `value` · †<br>Set or query the memory depth of the oscilloscope (namely the number of waveform points that can be stored in a single trigger sample)
  - `AVERages?` — **NAB** `Get_Acquire_Averages` · → NR1 · †<br>Set or query the number of averages under the average acquisition mode
  - `MDEPth?` — **NAB** `Get_Acquire_Mdepth` · → 1 value · †<br>Set or query the memory depth of the oscilloscope (namely the number of waveform points that can be stored in a single trigger sample)
  - `SRATe?` — **NAB** `Get_Acquire_Srate` · → 1 value · †<br>Query the current sample rate
- **`APPLy`**
  - `NOISe` — **DO** `Do_Apply_Noise` · †<br>Configure the specified source channel to output a signal with the specified waveform and parameters
  - `PULSe` — **DO** `Do_Apply_Pulse` · †<br>Configure the specified source channel to output a signal with the specified waveform and parameters
  - `RAMP` — **DO** `Do_Apply_Ramp` · †<br>Configure the specified source channel to output a signal with the specified waveform and parameters
  - `SINusoid` — **DO** `Do_Apply_Sinusoid` · †<br>Configure the specified source channel to output a signal with the specified waveform and parameters
  - `SQUare` — **DO** `Do_Apply_Square` · †<br>Configure the specified source channel to output a signal with the specified waveform and parameters
  - `USER` — **DO** `Do_Apply_User` · †<br>Configure the specified source channel to output a signal with the specified waveform and parameters
- **`CALibrate`**
  - `QUIT` — **DO** `Do_Calibrate_Quit` · †<br>Exit the self-calibration at any time
  - `STARt` — **DO** `Do_Calibrate_Start` · †<br>The oscilloscope starts to execute self-calibration
- **`CHAN1`**
  - `DISP?` — **NAB** `Get_Channel_Display` · → BOOL · †
- **`CHANnel1`**
  - `BWLimit` — **SET** `CH1_BWLimit` · `<limit>` · args: `limit` · enum: `20M` | `OFF`
  - `COUPling` — **SET** `CH1_Coupling` · `<coupling>` · args: `coupling` · enum: `AC` | `DC` | `GND`
  - `OFFSet` — **SET** `CH1_Offset` · `<offset>` · args: `offset` · numeric
  - `PROBe` — **SET** `CH1_Probe` · `<atten>` · args: `atten` · enum: `1` | `2` | `5` | `10` | `20` | `50` | `100` | `200` | `500` | `1000`
  - `SCALe` — **SET** `CH1_Scale` · `<scale>` · args: `scale` · numeric (V)
  - `INVert` — **SET** `Set_Channel_Invert` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
  - `RANGe` — **SET** `Set_Channel_Range` · `<value>` · args: `value` · numeric (V) · †
  - `TCAL` — **SET** `Set_Channel_Tcalibrate` · `<value>` · args: `value` · numeric (s) · †
  - `VERNier` — **SET** `Set_Channel_Vernier` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
  - `BWLimit?` — **NAB** `Get_Channel_Bwlimit` · → BOOL · †
  - `COUPling?` — **NAB** `Get_Channel_Coupling` · → CRD · †
  - `INVert?` — **NAB** `Get_Channel_Invert` · → BOOL · †
  - `OFFSet?` — **NAB** `Get_Channel_Offset` · → NR3 · †
  - `PROBe?` — **NAB** `Get_Channel_Probe` · → NR3 · †
  - `RANGe?` — **NAB** `Get_Channel_Range` · → NR3 · †
  - `SCALe?` — **NAB** `Get_Channel_Scale` · → NR3 · †
  - `TCAL?` — **NAB** `Get_Channel_Tcalibrate` · → 1 value · †
  - `UNITs?` — **NAB** `Get_Channel_Units` · → CRD · †
  - `VERNier?` — **NAB** `Get_Channel_Vernier` · → BOOL · †
  - `DISPlay` — **DO** `CH1_OFF` · `OFF`
  - `DISPlay` — **DO** `CH1_ON` · `ON`
- **`CHANnel2`**
  - `BWLimit` — **SET** `CH2_BWLimit` · `<limit>` · args: `limit` · enum: `20M` | `OFF`
  - `COUPling` — **SET** `CH2_Coupling` · `<coupling>` · args: `coupling` · enum: `AC` | `DC` | `GND`
  - `OFFSet` — **SET** `CH2_Offset` · `<offset>` · args: `offset` · numeric
  - `PROBe` — **SET** `CH2_Probe` · `<atten>` · args: `atten` · enum: `1` | `2` | `5` | `10` | `20` | `50` | `100` | `200` | `500` | `1000`
  - `SCALe` — **SET** `CH2_Scale` · `<scale>` · args: `scale` · numeric (V)
  - `DISPlay` — **DO** `CH2_OFF` · `OFF`
  - `DISPlay` — **DO** `CH2_ON` · `ON`
- **`CHANnel3`**
  - `BWLimit` — **SET** `CH3_BWLimit` · `<limit>` · args: `limit` · enum: `20M` | `OFF`
  - `COUPling` — **SET** `CH3_Coupling` · `<coupling>` · args: `coupling` · enum: `AC` | `DC` | `GND`
  - `OFFSet` — **SET** `CH3_Offset` · `<offset>` · args: `offset` · numeric
  - `PROBe` — **SET** `CH3_Probe` · `<atten>` · args: `atten` · enum: `1` | `2` | `5` | `10` | `20` | `50` | `100` | `200` | `500` | `1000`
  - `SCALe` — **SET** `CH3_Scale` · `<scale>` · args: `scale` · numeric (V)
  - `DISPlay` — **DO** `CH3_OFF` · `OFF`
  - `DISPlay` — **DO** `CH3_ON` · `ON`
- **`CHANnel4`**
  - `BWLimit` — **SET** `CH4_BWLimit` · `<limit>` · args: `limit` · enum: `20M` | `OFF`
  - `COUPling` — **SET** `CH4_Coupling` · `<coupling>` · args: `coupling` · enum: `AC` | `DC` | `GND`
  - `OFFSet` — **SET** `CH4_Offset` · `<offset>` · args: `offset` · numeric
  - `PROBe` — **SET** `CH4_Probe` · `<atten>` · args: `atten` · enum: `1` | `2` | `5` | `10` | `20` | `50` | `100` | `200` | `500` | `1000`
  - `SCALe` — **SET** `CH4_Scale` · `<scale>` · args: `scale` · numeric (V)
  - `DISPlay` — **DO** `CH4_OFF` · `OFF`
  - `DISPlay` — **DO** `CH4_ON` · `ON`
- **`CHANnel<n>`**
  - `BWLimit` — **SET** `Set_Bandwidth_Limit` · `<limit>` · args: `limit` · enum: `20M` | `OFF` · per-instance: `n`
  - `OFFSet` — **SET** `Set_Channel_Offset` · `<offset>` · args: `offset` · numeric · per-instance: `n`
  - `SCALe` — **SET** `Set_Channel_Scale` · `<scale>` · args: `scale` · numeric (V) · per-instance: `n`
  - `COUPling` — **SET** `Set_Coupling` · `<coupling>` · args: `coupling` · enum: `AC` | `DC` | `GND` · per-instance: `n`
  - `DISPlay` — **SET** `Set_Display` · `<state>` · args: `state` · bool: `OFF` | `ON` · per-instance: `n`
  - `PROBe` — **SET** `Set_Probe` · `<atten>` · args: `atten` · enum: `1` | `2` | `5` | `10` | `20` | `50` | `100` | `200` | `500` | `1000` · per-instance: `n`
  - `UNITs` — **SET** `Set_Units` · `<unit>` · args: `unit` · enum: `VOLT` | `WATT` | `AMP` | `UNKN` · per-instance: `n`
- **`CONFig`**
  - `ENDian` — **SET** `Set_Config_Endian` · `<value>` · args: `value` · †<br>Turn on or off the endian display function in serial bus decoding, or query the status of the endian display function in serial bus decoding
  - `FORMat` — **SET** `Set_Config_Format` · `<value>` · args: `value` · enum · †<br>Turn on or off the format display function, or query the status of the format display function
  - `LABel` — **SET** `Set_Config_Label` · `<value>` · args: `value` · †<br>Turn on or off the label display function, or query the status of the label display function
  - `LINE` — **SET** `Set_Config_Line` · `<value>` · args: `value` · †
  - `WIDth` — **SET** `Set_Config_Width` · `<value>` · args: `value` · numeric · †<br>Turn on or off the width display function, or query the status of the width display function
  - `ENDian?` — **NAB** `Get_Config_Endian` · → 1 value · †<br>Turn on or off the endian display function in serial bus decoding, or query the status of the endian display function in serial bus decoding
  - `FORMat?` — **NAB** `Get_Config_Format` · → CRD · †<br>Turn on or off the format display function, or query the status of the format display function
  - `LABel?` — **NAB** `Get_Config_Label` · → 1 value · †<br>Turn on or off the label display function, or query the status of the label display function
  - `LINE?` — **NAB** `Get_Config_Line` · → 1 value · †
  - `SRATe?` — **NAB** `Get_Config_Srate` · → 1 value · †<br>Query the current digital sample rate
  - `WIDth?` — **NAB** `Get_Config_Width` · → NR3 · †<br>Turn on or off the width display function, or query the status of the width display function
- **`CURSor`**
  - `MODE` — **SET** `Set_Cursor_Mode` · `<value>` · args: `value` · enum: `OFF` | `MAN` | `TRAC` | `AUTO` | `XY` · †<br>Set or query the cursor measurement mode
  - `MODE?` — **NAB** `Get_Cursor_Mode` · → CRD · †<br>Set or query the cursor measurement mode
  - `MANual` — **DO** `Do_Cursor_Manual` · †<br>Set or query the cursor type in manual cursor measurement mode
  - `TRACk` — **DO** `Do_Cursor_Track` · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
  - `XY` — **DO** `Do_Cursor_Xy` · †<br>Set or query the horizontal position of cursor A in the XY cursor measurement mode
  - **`MANual`**
    - `AX` — **SET** `Set_Cursor_Manual_Ax` · `<value>` · args: `value` · integer · †<br>Set or query the cursor type in manual cursor measurement mode
    - `AY` — **SET** `Set_Cursor_Manual_Ay` · `<value>` · args: `value` · integer · †<br>Set or query the cursor type in manual cursor measurement mode
    - `BX` — **SET** `Set_Cursor_Manual_Bx` · `<value>` · args: `value` · integer · †<br>Set or query the cursor type in manual cursor measurement mode
    - `BY` — **SET** `Set_Cursor_Manual_By` · `<value>` · args: `value` · integer · †<br>Set or query the cursor type in manual cursor measurement mode
    - `SOURce` — **SET** `Set_Cursor_Manual_Source` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `MATH` | `LA` · †<br>Set or query the cursor type in manual cursor measurement mode
    - `TUNit` — **SET** `Set_Cursor_Manual_Tunit` · `<value>` · args: `value` · enum: `S` | `HZ` | `DEGR` | `PERC` · †<br>Set or query the cursor type in manual cursor measurement mode
    - `VUNit` — **SET** `Set_Cursor_Manual_Vunit` · `<value>` · args: `value` · enum: `PERC` | `SOUR` · †<br>Set or query the cursor type in manual cursor measurement mode
    - `AX?` — **NAB** `Get_Cursor_Manual_Ax` · → 1 value · †<br>Set or query the cursor type in manual cursor measurement mode
    - `AY?` — **NAB** `Get_Cursor_Manual_Ay` · → 1 value · †<br>Set or query the cursor type in manual cursor measurement mode
    - `BX?` — **NAB** `Get_Cursor_Manual_Bx` · → 1 value · †<br>Set or query the cursor type in manual cursor measurement mode
    - `BY?` — **NAB** `Get_Cursor_Manual_By` · → 1 value · †<br>Set or query the cursor type in manual cursor measurement mode
    - `IXDELta?` — **NAB** `Get_Cursor_Manual_Ixdelta` · → NR3 s · †<br>Set or query the cursor type in manual cursor measurement mode
    - `SOURce?` — **NAB** `Get_Cursor_Manual_Source` · → CRD · †<br>Set or query the cursor type in manual cursor measurement mode
    - `TUNit?` — **NAB** `Get_Cursor_Manual_Tunit` · → 1 value · †<br>Set or query the cursor type in manual cursor measurement mode
    - `VUNit?` — **NAB** `Get_Cursor_Manual_Vunit` · → 1 value · †<br>Set or query the cursor type in manual cursor measurement mode
    - `XDELta?` — **NAB** `Get_Cursor_Manual_Xdelta` · → NR3 s · †<br>Set or query the cursor type in manual cursor measurement mode
    - `YDELta?` — **NAB** `Get_Cursor_Manual_Ydelta` · → NR3 s · †<br>Set or query the cursor type in manual cursor measurement mode
  - **`TRACk`**
    - `AX` — **SET** `Set_Cursor_Track_Ax` · `<value>` · args: `value` · integer · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
    - `BX` — **SET** `Set_Cursor_Track_Bx` · `<value>` · args: `value` · integer · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
    - `SOURce<chan>` — **SET** `Set_Cursor_Track_Source` · `<value>` · args: `value` · enum: `OFF` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `MATH` · per-instance: `chan` · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
    - `AX?` — **NAB** `Get_Cursor_Track_Ax` · → 1 value · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
    - `AY?` — **NAB** `Get_Cursor_Track_Ay` · → 1 value · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
    - `BX?` — **NAB** `Get_Cursor_Track_Bx` · → 1 value · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
    - `BY?` — **NAB** `Get_Cursor_Track_By` · → 1 value · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
    - `IXDELTA?` — **NAB** `Get_Cursor_Track_Ixdelta` · → NR3 s · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
    - `SOURce<chan>?` — **NAB** `Get_Cursor_Track_Source` · per-instance: `chan` · → CRD · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
    - `XDELta?` — **NAB** `Get_Cursor_Track_Xdelta` · → NR3 s · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
    - `YDELta?` — **NAB** `Get_Cursor_Track_Ydelta` · → NR3 s · †<br>Set or query the channel source of cursor A in the track cursor measurement mode
  - **`XY`**
    - `AX` — **SET** `Set_Cursor_Xy_Ax` · `<value>` · args: `value` · integer · †<br>Set or query the horizontal position of cursor A in the XY cursor measurement mode
    - `AY` — **SET** `Set_Cursor_Xy_Ay` · `<value>` · args: `value` · integer · †<br>Set or query the horizontal position of cursor A in the XY cursor measurement mode
    - `BX` — **SET** `Set_Cursor_Xy_Bx` · `<value>` · args: `value` · integer · †<br>Set or query the horizontal position of cursor A in the XY cursor measurement mode
    - `BY` — **SET** `Set_Cursor_Xy_By` · `<value>` · args: `value` · integer · †<br>Set or query the horizontal position of cursor A in the XY cursor measurement mode
    - `AX?` — **NAB** `Get_Cursor_Xy_Ax` · → 1 value · †<br>Set or query the horizontal position of cursor A in the XY cursor measurement mode
    - `AY?` — **NAB** `Get_Cursor_Xy_Ay` · → 1 value · †<br>Set or query the horizontal position of cursor A in the XY cursor measurement mode
    - `BX?` — **NAB** `Get_Cursor_Xy_Bx` · → 1 value · †<br>Set or query the horizontal position of cursor A in the XY cursor measurement mode
    - `BY?` — **NAB** `Get_Cursor_Xy_By` · → 1 value · †<br>Set or query the horizontal position of cursor A in the XY cursor measurement mode
- **`DATA`**
  - `POINts` — **SET** `Set_Data_Points` · `<value>` · args: `value` · integer · †<br>Set or query the initial number of points of the arbitrary waveform of the specified signal source channel
  - `VALue` — **SET** `Set_Data_Value` · `<value>` · args: `value` · numeric · †<br>Modify or query the decimal value of the specified point in the volatile memory of the specified signal source
  - `LOAD?` — **NAB** `Get_Data_Load` · → 1 value · †<br>Read the specified data packet in the volatile memory of the specified signal source
  - `POINts?` — **NAB** `Get_Data_Points` · → NR1 · †<br>Set or query the initial number of points of the arbitrary waveform of the specified signal source channel
  - `VALue?` — **NAB** `Get_Data_Value` · → NR3 · †<br>Modify or query the decimal value of the specified point in the volatile memory of the specified signal source
  - `DAC<chan>` — **DO** `Do_Data_Dac` · per-instance: `chan` · †<br>Download binary data block to the volatile memory of the specified signal source
  - **`POINts`**
    - `INTerpolate` — **SET** `Set_Data_Points_Internal` · `<value>` · args: `value` · †<br>Set or query the interpolation mode of the editable points of the arbitrary waveform of the specified signal source channel
    - `INTerpolate?` — **NAB** `Get_Data_Points_Internal` · → 1 value · †<br>Set or query the interpolation mode of the editable points of the arbitrary waveform of the specified signal source channel
- **`DECoder1`**
  - `DISPlay` — **SET** `Set_Decoder_Display` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
  - `FORMat` — **SET** `Set_Decoder_Format` · `<value>` · args: `value` · enum: `HEX` | `ASC` | `DEC` | `BIN` | `LINE` · †
  - `MODE` — **SET** `Set_Decoder_Mode` · `<value>` · args: `value` · enum: `PAR` | `UART` | `SPI` | `IIC` · †
  - `POSition` — **SET** `Set_Decoder_Positive` · `<value>` · args: `value` · integer · †
  - `DISPlay?` — **NAB** `Get_Decoder_Display` · → BOOL · †
  - `FORMat?` — **NAB** `Get_Decoder_Format` · → CRD · †
  - `MODE?` — **NAB** `Get_Decoder_Mode` · → CRD · †
  - `POSition?` — **NAB** `Get_Decoder_Positive` · → NR3 · †
  - **`CONFig`**
    - `ENDian` — **SET** `Set_Decoder_Config_Endian` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
    - `FORMat` — **SET** `Set_Decoder_Config_Format` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
    - `LABel` — **SET** `Set_Decoder_Config_Label` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
    - `LINE` — **SET** `Set_Decoder_Config_Line` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
    - `WIDth` — **SET** `Set_Decoder_Config_Width` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
    - `ENDian?` — **NAB** `Get_Decoder_Config_Endian` · → 1 value · †
    - `FORMat?` — **NAB** `Get_Decoder_Config_Format` · → CRD · †
    - `LABel?` — **NAB** `Get_Decoder_Config_Label` · → 1 value · †
    - `LINE?` — **NAB** `Get_Decoder_Config_Line` · → 1 value · †
    - `SRATe?` — **NAB** `Get_Decoder_Config_Srate` · → 1 value · †
    - `WIDth?` — **NAB** `Get_Decoder_Config_Width` · → NR3 · †
  - **`IIC`**
    - `ADDRess` — **SET** `Set_Decoder_Iic_Address` · `<value>` · args: `value` · enum: `NORM` | `RW` · †
    - `CLK` — **SET** `Set_Decoder_Iic_Clk` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †
    - `DATA` — **SET** `Set_Decoder_Iic_Data` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †
    - `ADDRess?` — **NAB** `Get_Decoder_Iic_Address` · → NR1 · †
    - `CLK?` — **NAB** `Get_Decoder_Iic_Clk` · → 1 value · †
    - `DATA?` — **NAB** `Get_Decoder_Iic_Data` · → BLOCK · †
  - **`PARallel`**
    - `BITX` — **SET** `Set_Decoder_Parallel_Bitx` · `<value>` · args: `value` · integer · †
    - `CCOMpensation` — **SET** `Set_Decoder_Parallel_Ccompensation` · `<value>` · args: `value` · numeric (s) · †
    - `CLK` — **SET** `Set_Decoder_Parallel_Clk` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `OFF` · †
    - `EDGE` — **SET** `Set_Decoder_Parallel_Edge` · `<value>` · args: `value` · enum: `RISE` | `FALL` | `BOTH` · †
    - `NREJect` — **SET** `Set_Decoder_Parallel_Nreject` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
    - `NRTime` — **SET** `Set_Decoder_Parallel_Nrtime` · `<value>` · args: `value` · numeric (s) · †
    - `PLOT` — **SET** `Set_Decoder_Parallel_Plot` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
    - `POLarity` — **SET** `Set_Decoder_Parallel_Polarity` · `<value>` · args: `value` · enum: `NEG` | `POS` · †
    - `SOURce` — **SET** `Set_Decoder_Parallel_Source` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †
    - `WIDTh` — **SET** `Set_Decoder_Parallel_Width` · `<value>` · args: `value` · integer · †
    - `BITX?` — **NAB** `Get_Decoder_Parallel_Bitx` · → 1 value · †
    - `CCOMpensation?` — **NAB** `Get_Decoder_Parallel_Ccompensation` · → 1 value · †
    - `CLK?` — **NAB** `Get_Decoder_Parallel_Clk` · → 1 value · †
    - `EDGE?` — **NAB** `Get_Decoder_Parallel_Edge` · → 1 value · †
    - `NREJect?` — **NAB** `Get_Decoder_Parallel_Nreject` · → 1 value · †
    - `NRTime?` — **NAB** `Get_Decoder_Parallel_Nrtime` · → NR3 s · †
    - `PLOT?` — **NAB** `Get_Decoder_Parallel_Plot` · → 1 value · †
    - `POLarity?` — **NAB** `Get_Decoder_Parallel_Polarity` · → CRD · †
    - `SOURce?` — **NAB** `Get_Decoder_Parallel_Source` · → CRD · †
    - `WIDTh?` — **NAB** `Get_Decoder_Parallel_Width` · → NR3 · †
  - **`SPI`**
    - `CLK` — **SET** `Set_Decoder_Spi_Clk` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †
    - `CS` — **SET** `Set_Decoder_Spi_Csrc` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †
    - `EDGE` — **SET** `Set_Decoder_Spi_Edge` · `<value>` · args: `value` · enum: `RISE` | `FALL` · †
    - `ENDian` — **SET** `Set_Decoder_Spi_Endian` · `<value>` · args: `value` · enum: `LSB` | `MSB` · †
    - `MISO` — **SET** `Set_Decoder_Spi_Miso` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `OFF` · †
    - `MODE` — **SET** `Set_Decoder_Spi_Mode` · `<value>` · args: `value` · enum: `CS` | `TIM` · †
    - `MOSI` — **SET** `Set_Decoder_Spi_Mosi` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `OFF` · †
    - `POLarity` — **SET** `Set_Decoder_Spi_Polarity` · `<value>` · args: `value` · enum: `NEG` | `POS` · †
    - `SELect` — **SET** `Set_Decoder_Spi_Select` · `<value>` · args: `value` · enum: `NCS` | `CS` · †
    - `TIMeout` — **SET** `Set_Decoder_Spi_Timebase` · `<value>` · args: `value` · numeric · †
    - `WIDTh` — **SET** `Set_Decoder_Spi_Width` · `<value>` · args: `value` · integer · †
    - `CLK?` — **NAB** `Get_Decoder_Spi_Clk` · → 1 value · †
    - `CS?` — **NAB** `Get_Decoder_Spi_Csrc` · → 1 value · †
    - `EDGE?` — **NAB** `Get_Decoder_Spi_Edge` · → 1 value · †
    - `ENDian?` — **NAB** `Get_Decoder_Spi_Endian` · → 1 value · †
    - `MISO?` — **NAB** `Get_Decoder_Spi_Miso` · → 1 value · †
    - `MODE?` — **NAB** `Get_Decoder_Spi_Mode` · → CRD · †
    - `MOSI?` — **NAB** `Get_Decoder_Spi_Mosi` · → 1 value · †
    - `POLarity?` — **NAB** `Get_Decoder_Spi_Polarity` · → CRD · †
    - `SELect?` — **NAB** `Get_Decoder_Spi_Select` · → CRD · †
    - `TIMeout?` — **NAB** `Get_Decoder_Spi_Timebase` · → NR3 s · †
    - `WIDTh?` — **NAB** `Get_Decoder_Spi_Width` · → NR3 · †
  - **`THREshold`**
    - `CHANnel<chan>` — **SET** `Set_Decoder_Threshold_Channel` · `<value>` · args: `value` · numeric · per-instance: `chan` · †
    - `CHANnel<chan>?` — **NAB** `Get_Decoder_Threshold_Channel` · per-instance: `chan` · → CRD · †
  - **`UART`**
    - `BAUD` — **SET** `Set_Decoder_Uart_Baud` · `<value>` · args: `value` · integer · †
    - `ENDian` — **SET** `Set_Decoder_Uart_Endian` · `<value>` · args: `value` · enum: `LSB` | `MSB` · †
    - `PARity` — **SET** `Set_Decoder_Uart_Parallel` · `<value>` · args: `value` · enum: `NONE` | `EVEN` | `ODD` · †
    - `POLarity` — **SET** `Set_Decoder_Uart_Polarity` · `<value>` · args: `value` · enum: `NEG` | `POS` · †
    - `RX` — **SET** `Set_Decoder_Uart_Rx` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `OFF` · †
    - `STOP` — **SET** `Set_Decoder_Uart_Stop` · `<value>` · args: `value` · enum: `1` | `2` · †
    - `TX` — **SET** `Set_Decoder_Uart_Tx` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `OFF` · †
    - `WIDTh` — **SET** `Set_Decoder_Uart_Width` · `<value>` · args: `value` · integer · †
    - `BAUD?` — **NAB** `Get_Decoder_Uart_Baud` · → 1 value · †
    - `ENDian?` — **NAB** `Get_Decoder_Uart_Endian` · → 1 value · †
    - `PARity?` — **NAB** `Get_Decoder_Uart_Parallel` · → 1 value · †
    - `POLarity?` — **NAB** `Get_Decoder_Uart_Polarity` · → CRD · †
    - `RX?` — **NAB** `Get_Decoder_Uart_Rx` · → 1 value · †
    - `STOP?` — **NAB** `Get_Decoder_Uart_Stop` · → NR3 · †
    - `TX?` — **NAB** `Get_Decoder_Uart_Tx` · → 1 value · †
    - `WIDTh?` — **NAB** `Get_Decoder_Uart_Width` · → NR3 · †
- **`DISPlay`**
  - `GBRightness` — **SET** `Set_Display_Gbrightness` · `<value>` · args: `value` · integer · †<br>Set or query the brightness of the screen grid
  - `GRID` — **SET** `Set_Display_Grid` · `<value>` · args: `value` · enum: `FULL` | `HALF` | `NONE` · †
  - `WBRightness` — **SET** `Set_Display_Wbrightness` · `<value>` · args: `value` · integer · †<br>Set or query the waveform brightness
  - `DATA?` — **NAB** `Get_Display_Data` · → BLOCK · †<br>Read the data stream of the image currently displayed on the screen and set the color, invert display, and format of the image acquired
  - `GBRightness?` — **NAB** `Get_Display_Gbrightness` · → 1 value · †<br>Set or query the brightness of the screen grid
  - `GRID?` — **NAB** `Get_Display_Grid` · → 1 value · †
  - `WBRightness?` — **NAB** `Get_Display_Wbrightness` · → 1 value · †<br>Set or query the waveform brightness
  - `CLEar` — **DO** `Do_Display_Clear` · †<br>Clear all the waveforms on the screen
  - **`GRADing`**
    - `TIME` — **SET** `Set_Display_Grading_Time` · `<value>` · args: `value` · enum: `MIN` | `1` | `5` | `10` | `INF` · †<br>Set or query the persistence time
    - `TIME?` — **NAB** `Get_Display_Grading_Time` · → NR3 s · †<br>Set or query the persistence time
- **`ETABle1`**
  - `COLumn` — **SET** `Set_Etable_Color` · `<value>` · args: `value` · enum: `DATA` | `TX` | `RX` | `MISO` | `MOSI` · †
  - `DISP` — **SET** `Set_Etable_Display` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
  - `FORMat` — **SET** `Set_Etable_Format` · `<value>` · args: `value` · enum: `HEX` | `ASC` | `DEC` · †
  - `ROW` — **SET** `Set_Etable_Row` · `<value>` · args: `value` · integer · †
  - `SORT` — **SET** `Set_Etable_Sort` · `<value>` · args: `value` · enum: `ASC` | `DESC` · †
  - `VIEW` — **SET** `Set_Etable_View` · `<value>` · args: `value` · enum: `PACK` | `DET` | `PAYL` · †
  - `COLumn?` — **NAB** `Get_Etable_Color` · → CRD · †
  - `DATA?` — **NAB** `Get_Etable_Data` · → BLOCK · †
  - `DISP?` — **NAB** `Get_Etable_Display` · → BOOL · †
  - `FORMat?` — **NAB** `Get_Etable_Format` · → CRD · †
  - `ROW?` — **NAB** `Get_Etable_Row` · → 1 value · †
  - `SORT?` — **NAB** `Get_Etable_Sort` · → 1 value · †
  - `VIEW?` — **NAB** `Get_Etable_View` · → 1 value · †
- **`FREQuency`**
  - `FIXed` — **SET** `Set_Frequency_Fixed` · `<value>` · args: `value` · †<br>Set or query the output frequency of the specified source channel if the modulation is not enabled or the carrier frequency if the modulation is enabled
  - `FIXed?` — **NAB** `Get_Frequency_Fixed` · → 1 value · †<br>Set or query the output frequency of the specified source channel if the modulation is not enabled or the carrier frequency if the modulation is enabled
- **`FUNCtion`**
  - `SHAPe` — **SET** `Set_Function_Shape` · `<value>` · args: `value` · enum: `SIN` | `SQU` | `RAMP` | `PULS` | `NOIS` | `DC` | `INTE` | `EXT` · †<br>Select or query the output waveform when the modulation of the specified source channel is not enabled
  - `SHAPe?` — **NAB** `Get_Function_Shape` · → CRD · †<br>Select or query the output waveform when the modulation of the specified source channel is not enabled
  - **`RAMP`**
    - `SYMMetry` — **SET** `Set_Function_Ramp_Symmetry` · `<value>` · args: `value` · †<br>Set or query the ramp symmetry (the percentage that the rising period takes up in the whole period) of the specified source channel
    - `SYMMetry?` — **NAB** `Get_Function_Ramp_Symmetry` · → 1 value · †<br>Set or query the ramp symmetry (the percentage that the rising period takes up in the whole period) of the specified source channel
  - **`WRECord`**
    - `ENABle` — **SET** `Set_Function_Wrecord_Enable` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Turn on or off the waveform recording function, or query the status of the waveform recording function
    - `FEND` — **SET** `Set_Function_Wrecord_Fend` · `<value>` · args: `value` · integer · †<br>Set or query the end frame of waveform recording
    - `FINTerval` — **SET** `Set_Function_Wrecord_Finterval` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the time interval between frames in waveform recording
    - `OPERate` — **SET** `Set_Function_Wrecord_Operator` · `<value>` · args: `value` · enum: `RUN` | `STOP` · †<br>Start or stop the waveform recording, or query the status of the waveform recording
    - `PROMpt` — **SET** `Set_Function_Wrecord_Prompt` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Turn on or off the sound prompt when the recording finishes, or query the status of the sound prompt when the recording finishes
    - `ENABle?` — **NAB** `Get_Function_Wrecord_Enable` · → NR1 · †<br>Turn on or off the waveform recording function, or query the status of the waveform recording function
    - `FEND?` — **NAB** `Get_Function_Wrecord_Fend` · → 1 value · †<br>Set or query the end frame of waveform recording
    - `FINTerval?` — **NAB** `Get_Function_Wrecord_Finterval` · → 1 value · †<br>Set or query the time interval between frames in waveform recording
    - `FMAX?` — **NAB** `Get_Function_Wrecord_Fmax` · → NR3 Hz · †<br>Query the maximum number of frames can be recorded currently
    - `OPERate?` — **NAB** `Get_Function_Wrecord_Operator` · → CRD · †<br>Start or stop the waveform recording, or query the status of the waveform recording
    - `PROMpt?` — **NAB** `Get_Function_Wrecord_Prompt` · → 1 value · †<br>Turn on or off the sound prompt when the recording finishes, or query the status of the sound prompt when the recording finishes
  - **`WREPlay`**
    - `DIRection` — **SET** `Set_Function_Wreplay_Direction` · `<value>` · args: `value` · enum: `FORW` | `BACK` · †<br>Set or query the waveform playback direction
    - `FCURrent` — **SET** `Set_Function_Wreplay_Fcurrent` · `<value>` · args: `value` · integer · †<br>Set or query the current frame in waveform playback
    - `FEND` — **SET** `Set_Function_Wreplay_Fend` · `<value>` · args: `value` · integer · †<br>Set or query the end frame of waveform playback
    - `FINTerval` — **SET** `Set_Function_Wreplay_Finterval` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the time interval between frames in waveform playback
    - `FSTart` — **SET** `Set_Function_Wreplay_Fstart` · `<value>` · args: `value` · integer · †<br>Set or query the start frame of waveform playback
    - `MODE` — **SET** `Set_Function_Wreplay_Mode` · `<value>` · args: `value` · enum: `REP` | `SING` · †<br>Set or query the waveform playback mode
    - `OPERate` — **SET** `Set_Function_Wreplay_Operator` · `<value>` · args: `value` · enum: `PLAY` | `PAUS` | `STOP` · †<br>Start, pause, or stop the waveform playback, or query the status of the waveform playback
    - `DIRection?` — **NAB** `Get_Function_Wreplay_Direction` · → 1 value · †<br>Set or query the waveform playback direction
    - `FCURrent?` — **NAB** `Get_Function_Wreplay_Fcurrent` · → 1 value · †<br>Set or query the current frame in waveform playback
    - `FEND?` — **NAB** `Get_Function_Wreplay_Fend` · → 1 value · †<br>Set or query the end frame of waveform playback
    - `FINTerval?` — **NAB** `Get_Function_Wreplay_Finterval` · → 1 value · †<br>Set or query the time interval between frames in waveform playback
    - `FMAX?` — **NAB** `Get_Function_Wreplay_Fmax` · → NR3 Hz · †<br>Query theb maximum number of frames can be played, namely the maximum number of frames recorded
    - `FSTart?` — **NAB** `Get_Function_Wreplay_Fstart` · → 1 value · †<br>Set or query the start frame of waveform playback
    - `MODE?` — **NAB** `Get_Function_Wreplay_Mode` · → CRD · †<br>Set or query the waveform playback mode
    - `OPERate?` — **NAB** `Get_Function_Wreplay_Operator` · → CRD · †<br>Start, pause, or stop the waveform playback, or query the status of the waveform playback
- **`IIC`**
  - `ADDRess` — **SET** `Set_Iic_Address` · `<value>` · args: `value` · integer · †<br>Set or query the signal source of the clock channel in I2C decoding
  - `CLK` — **SET** `Set_Iic_Clk` · `<value>` · args: `value` · †<br>Set or query the signal source of the clock channel in I2C decoding
  - `DATA` — **SET** `Set_Iic_Data` · `<value>` · args: `value` · block · †<br>Set or query the signal source of the clock channel in I2C decoding
  - `ADDRess?` — **NAB** `Get_Iic_Address` · → NR1 · †<br>Set or query the signal source of the clock channel in I2C decoding
  - `CLK?` — **NAB** `Get_Iic_Clk` · → 1 value · †<br>Set or query the signal source of the clock channel in I2C decoding
  - `DATA?` — **NAB** `Get_Iic_Data` · → BLOCK · †<br>Set or query the signal source of the clock channel in I2C decoding
- **`IMMediate`**
  - `OFFSet` — **SET** `Set_Immediate_Offset` · `<value>` · args: `value` · numeric · †
  - `OFFSet?` — **NAB** `Get_Immediate_Offset` · → NR3 · †
- **`LA`**
  - `ACTive` — **SET** `Set_La_Active` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` · †<br>Set or query the current active channel or channel group
  - `DISPlay` — **SET** `Set_La_Display` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Turn on or off the specified digital channel, user-defined channel group or default channel group, or query the status of the specified digital channel, user-defined channel group or default channel group
  - `SIZE` — **SET** `Set_La_Size` · `<value>` · args: `value` · enum: `SMAL` | `LARG` · †<br>Set or query the display size of the waveforms of the channels turned on on the screen
  - `STATe` — **SET** `Set_La_Statistic` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Turn on or off the LA function, or query the status of the LA function
  - `TCALibrate` — **SET** `Set_La_Tcalibrate` · `<value>` · args: `value` · numeric (s) · †
  - `ACTive?` — **NAB** `Get_La_Active` · → BOOL · †<br>Set or query the current active channel or channel group
  - `DISPlay?` — **NAB** `Get_La_Display` · → BOOL · †<br>Turn on or off the specified digital channel, user-defined channel group or default channel group, or query the status of the specified digital channel, user-defined channel group or default channel group
  - `SIZE?` — **NAB** `Get_La_Size` · → NR3 · †<br>Set or query the display size of the waveforms of the channels turned on on the screen
  - `STATe?` — **NAB** `Get_La_Statistic` · → BOOL · †<br>Turn on or off the LA function, or query the status of the LA function
  - `TCALibrate?` — **NAB** `Get_La_Tcalibrate` · → 1 value · †
  - `AUTosort` — **DO** `Do_La_Autoscale` · †<br>Set the auto ordering mode of the waveforms of the channels turned on on the screen
  - `DIGital` — **DO** `Do_La_Digital` · †<br>Turn on or off the specified digital channel, or query the status of the specified digital channel
  - `POD` — **DO** `Do_La_Pod` · †<br>Turn on or off the specified default channel group, or query the status of the specified |Type|Range| |---|---| |Integer|1 to 2| |Bool|{{1|ON}|{0|OFF}}|
  - **`DIGital1`**
    - `POSition` — **SET** `Set_La_Digital_Positive` · `<value>` · args: `value` · integer · †
    - `POSition?` — **NAB** `Get_La_Digital_Positive` · → NR3 · †
  - **`DIGital3`**
    - `DISPlay` — **SET** `Set_La_Digital_Display` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
    - `DISPlay?` — **NAB** `Get_La_Digital_Display` · → BOOL · †
  - **`POD1`**
    - `DISPlay` — **SET** `Set_La_Pod_Display` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
    - `THReshold` — **SET** `Set_La_Pod_Threshold` · `<value>` · args: `value` · numeric · †
    - `DISPlay?` — **NAB** `Get_La_Pod_Display` · → BOOL · †
    - `THReshold?` — **NAB** `Get_La_Pod_Threshold` · → NR3 · †
- **`MASK`**
  - `ENABle` — **SET** `Set_Mask_Enable` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the pass/fail test or query the status of the past/fail test
  - `MDISplay` — **SET** `Set_Mask_Mdisplay` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the statistic information when the pass/fail test is enabled, or query the status of the statistic information
  - `OPERate` — **SET** `Set_Mask_Operator` · `<value>` · args: `value` · enum: `RUN` | `STOP` · †<br>Run or stop the pass/fail test, or query the status of the pass/fail test
  - `OUTPut` — **SET** `Set_Mask_Output` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the sound prompt when failed waveforms are detected, or query the status of the sound prompt
  - `SOOutput` — **SET** `Set_Mask_Sooutput` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Turn the "Stop on Fail" function on or off, or query the status of the "Stop on Fail" function
  - `SOURce` — **SET** `Set_Mask_Source` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †
  - `ENABle?` — **NAB** `Get_Mask_Enable` · → NR1 · †<br>Enable or disable the pass/fail test or query the status of the past/fail test
  - `FAILed?` — **NAB** `Get_Mask_Failed` · → 1 value · †<br>Query the number of failed frames in the pass/fail test
  - `MDISplay?` — **NAB** `Get_Mask_Mdisplay` · → 1 value · †<br>Enable or disable the statistic information when the pass/fail test is enabled, or query the status of the statistic information
  - `OPERate?` — **NAB** `Get_Mask_Operator` · → CRD · †<br>Run or stop the pass/fail test, or query the status of the pass/fail test
  - `OUTPut?` — **NAB** `Get_Mask_Output` · → 1 value · †<br>Enable or disable the sound prompt when failed waveforms are detected, or query the status of the sound prompt
  - `PASSed?` — **NAB** `Get_Mask_Passed` · → 1 value · †<br>Query the number of passed frames in the pass/fail test
  - `SOOutput?` — **NAB** `Get_Mask_Sooutput` · → 1 value · †<br>Turn the "Stop on Fail" function on or off, or query the status of the "Stop on Fail" function
  - `SOURce?` — **NAB** `Get_Mask_Source` · → CRD · †
  - `TOTal?` — **NAB** `Get_Mask_Total` · → 1 value · †<br>Query the total number of frames in the pass/fail test
  - `CREate` — **DO** `Do_Mask_Create` · †<br>Create the pass/fail test mask using the current horizontal adjustment parameter and vertical adjustment parameter
  - `RESet` — **DO** `Do_Mask_Reset` · †<br>Reset the numbers of passed frames and failed frames as well as the total number of frames in the pass/fail test to 0
- **`MATH`**
  - `DISPlay` — **SET** `Set_Math_Display` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the math operation function or query the math operation status
  - `INVert` — **SET** `Set_Math_Invert` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the inverted display mode of the operation result, or query the inverted display mode status of the operation result
  - `LSOUrce<chan>` — **SET** `Set_Math_Lsou` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · per-instance: `chan` · †<br>Set or query source A of logic operation
  - `OFFSet` — **SET** `Set_Math_Offset` · `<value>` · args: `value` · numeric · †<br>Set or query the vertical offset of the operation result
  - `OPERator` — **SET** `Set_Math_Operator` · `<value>` · args: `value` · enum: `ADD` | `SUBT` | `MULT` | `DIV` | `AND` | `OR` | `XOR` | `NOT` | `FFT` | `INTG` | `DIFF` | `SQRT` | `LOG` | `LN` | `EXP` | `ABS` | `FILT` · †<br>Set or query the operator of the math operation
  - `SCALe` — **SET** `Set_Math_Scale` · `<value>` · args: `value` · numeric · †<br>Set or query the vertical scale of the operation result
  - `SOURce<chan>` — **SET** `Set_Math_Source` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `FX` · per-instance: `chan` · †<br>Set or query the source or source A of algebraic operation/functional operation/the outer layer operation of compound operation
  - `DISPlay?` — **NAB** `Get_Math_Display` · → BOOL · †<br>Enable or disable the math operation function or query the math operation status
  - `INVert?` — **NAB** `Get_Math_Invert` · → BOOL · †<br>Enable or disable the inverted display mode of the operation result, or query the inverted display mode status of the operation result
  - `LSOUrce<chan>?` — **NAB** `Get_Math_Lsou` · per-instance: `chan` · → 1 value · †<br>Set or query source A of logic operation
  - `OFFSet?` — **NAB** `Get_Math_Offset` · → NR3 · †<br>Set or query the vertical offset of the operation result
  - `OPERator?` — **NAB** `Get_Math_Operator` · → CRD · †<br>Set or query the operator of the math operation
  - `SCALe?` — **NAB** `Get_Math_Scale` · → NR3 · †<br>Set or query the vertical scale of the operation result
  - `SOURce<chan>?` — **NAB** `Get_Math_Source` · per-instance: `chan` · → CRD · †<br>Set or query the source or source A of algebraic operation/functional operation/the outer layer operation of compound operation
  - `FILTer` — **DO** `Do_Math_Filter` · †<br>Set or query the cutoff frequency ( ωc1 ) of the low pass/high pass filter or cutoff frequency 1 ( ωc1 ) of the band pass/band stop filter
  - `RESet` — **DO** `Do_Math_Reset` · †<br>Sending this command, the instrument adjusts the vertical scale of the operation result to the most proper value according to the current operator and the horizontal timebase of the source
  - **`FFT`**
    - `HCENter` — **SET** `Set_Math_Fft_Hcenter` · `<value>` · args: `value` · numeric · †<br>Set or query the center frequency of the FFT operation result, namely the frequency relative to the horizontal center of the screen
    - `HSCale` — **SET** `Set_Math_Fft_Hscale` · `<value>` · args: `value` · numeric · †<br>Set or query the horizontal scale of the FFT operation result
    - `MODE` — **SET** `Set_Math_Fft_Mode` · `<value>` · args: `value` · enum: `TRAC` | `MEM` · †<br>Set or query the FFT mode
    - `SOURce` — **SET** `Set_Math_Fft_Source` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the source of FFT operation/filter
    - `SPLit` — **SET** `Set_Math_Fft_Split` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the half-screen display mode of the FFT operation, or query the status of the half display mode of the FFT operation
    - `UNIT` — **SET** `Set_Math_Fft_Units` · `<value>` · args: `value` · enum: `VRMS` | `DB` · †<br>Set or query the vertical unit of the FFT operation result
    - `WINDow` — **SET** `Set_Math_Fft_Windows` · `<value>` · args: `value` · enum: `RECT` | `BLAC` | `HANN` | `HAMM` | `FLAT` | `TRI` · †<br>Set or query the window function of the FFT operation
    - `HCENter?` — **NAB** `Get_Math_Fft_Hcenter` · → 1 value · †<br>Set or query the center frequency of the FFT operation result, namely the frequency relative to the horizontal center of the screen
    - `HSCale?` — **NAB** `Get_Math_Fft_Hscale` · → 1 value · †<br>Set or query the horizontal scale of the FFT operation result
    - `MODE?` — **NAB** `Get_Math_Fft_Mode` · → CRD · †<br>Set or query the FFT mode
    - `SOURce?` — **NAB** `Get_Math_Fft_Source` · → CRD · †<br>Set or query the source of FFT operation/filter
    - `SPLit?` — **NAB** `Get_Math_Fft_Split` · → 1 value · †<br>Enable or disable the half-screen display mode of the FFT operation, or query the status of the half display mode of the FFT operation
    - `UNIT?` — **NAB** `Get_Math_Fft_Units` · → CRD · †<br>Set or query the vertical unit of the FFT operation result
    - `WINDow?` — **NAB** `Get_Math_Fft_Windows` · → CRD · †<br>Set or query the window function of the FFT operation
  - **`OPTion`**
    - `ASCale` — **SET** `Set_Math_Option_Ascale` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the auto scale setting of the operation result or query the status of the auto scale setting
    - `DIStance` — **SET** `Set_Math_Option_Distance` · `<value>` · args: `value` · integer · †<br>Set or query the smoothing window width of differential operation (diff)
    - `END` — **SET** `Set_Math_Option_Endian` · `<value>` · args: `value` · †
    - `INVert` — **SET** `Set_Math_Option_Invert` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the inverted display mode of the operation result, or query the inverted display mode status of the operation result
    - `SENSitivity` — **SET** `Set_Math_Option_Sensitivity` · `<value>` · args: `value` · numeric · †<br>Set or query the sensitivity of the logic operation
    - `STARt` — **SET** `Set_Math_Option_Start` · `<value>` · args: `value` · integer · †<br>Set or query the start point of the waveform math operation
    - `THReshold<chan>` — **SET** `Set_Math_Option_Threshold` · `<value>` · args: `value` · numeric · per-instance: `chan` · †<br>Set or query the threshold level of source A in logic operations
    - `ASCale?` — **NAB** `Get_Math_Option_Ascale` · → 1 value · †<br>Enable or disable the auto scale setting of the operation result or query the status of the auto scale setting
    - `DIStance?` — **NAB** `Get_Math_Option_Distance` · → 1 value · †<br>Set or query the smoothing window width of differential operation (diff)
    - `END?` — **NAB** `Get_Math_Option_Endian` · → 1 value · †
    - `INVert?` — **NAB** `Get_Math_Option_Invert` · → BOOL · †<br>Enable or disable the inverted display mode of the operation result, or query the inverted display mode status of the operation result
    - `SENSitivity?` — **NAB** `Get_Math_Option_Sensitivity` · → 1 value · †<br>Set or query the sensitivity of the logic operation
    - `STARt?` — **NAB** `Get_Math_Option_Start` · → NR3 · †<br>Set or query the start point of the waveform math operation
    - `THReshold<chan>?` — **NAB** `Get_Math_Option_Threshold` · per-instance: `chan` · → NR3 · †<br>Set or query the threshold level of source A in logic operations
    - **`FX`**
      - `OPERator` — **SET** `Set_Math_Option_Fx_Operator` · `<value>` · args: `value` · enum: `ADD` | `SUBT` | `MULT` | `DIV` · †<br>Set or query the operator of the inner layer operation of compound operation
      - `SOURce<chan>` — **SET** `Set_Math_Option_Fx_Source` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · per-instance: `chan` · †<br>Set or query source A of the inner layer operation of compound operation
      - `OPERator?` — **NAB** `Get_Math_Option_Fx_Operator` · → CRD · †<br>Set or query the operator of the inner layer operation of compound operation
      - `SOURce<chan>?` — **NAB** `Get_Math_Option_Fx_Source` · per-instance: `chan` · → CRD · †<br>Set or query source A of the inner layer operation of compound operation
- **`MEASure`**
  - `ADISplay` — **SET** `Set_Measure_Adisplay` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the all measurement function, or query the status of the all measurement function
  - `AMSource` — **SET** `Set_Measure_Amsource` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `MATH` · †<br>Set or query the source(s) of the all measurement function
  - `SOURce` — **SET** `Set_Measure_Source` · `<source>` · args: `source` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `MATH`
  - `ADISplay?` — **NAB** `Get_Measure_Adisplay` · → 1 value · †<br>Enable or disable the all measurement function, or query the status of the all measurement function
  - `AMSource?` — **NAB** `Get_Measure_Amsource` · → 1 value · †<br>Set or query the source(s) of the all measurement function
  - `SOURce?` — **NAB** `Get_Measure_Source` · → CRD · †<br>Set or query the source of the current measurement parameter
  - `ITEM?` — **NAB** `Measure_Frequency` · `FREQ,<chan>` · per-instance: `chan` · → 1 value
  - `ITEM?` — **NAB** `Measure_Vpp` · `VPP,<chan>` · per-instance: `chan` · → 1 value
  - `RECover` — **DO** `Do_Measure_Recover` · †<br>Recover the measurement item which has been cleared
  - `CLEar` — **DO** `Execute Command`<br>Execute Command
  - **`COUNter`**
    - `SOURce` — **SET** `Set_Measure_Counter_Source` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `OFF` · †<br>Set or query the source of the frequency counter, or disable the frequency counter
    - `SOURce?` — **NAB** `Get_Measure_Counter_Source` · → CRD · †<br>Set or query the source of the frequency counter, or disable the frequency counter
    - `VALue?` — **NAB** `Get_Measure_Counter_Value` · → NR3 · †<br>Query the measurement result of the frequency counter
  - **`STATistic`**
    - `ITEM` — **SET** `Set_Measure_Statistic_Item` · `<value>` · args: `value` · enum: `VMAX` | `VMIN` | `VPP` | `VTOP` | `VBAS` | `VAMP` | `VAVG` | `VRMS` | `OVER` | `PRES` | `MAR` | `MPAR` | `PER` | `FREQ` | `RTIM` | `FTIM` | `PWID` | `NWID` | `PDUT` | `NDUT` | `RDEL` | `FDEL` | `RPH` | `FPH` | `TVMAX` | `TVMIN` | `PSLEW` | `NSLEW` | `VUP` | `VMID` | `VLOW` | `VARI` | `PVRMS` | `PPUL` | `NPUL` | `PEDG` | `NEDG` · †<br>Enable the statistic function of any waveform parameter of the specified source, or query the statistic result of any waveform parameter of the specified source
    - `MODE` — **SET** `Set_Measure_Statistic_Mode` · `<value>` · args: `value` · enum: `DIFF` | `EXTR` · †<br>Set or query the statistic mode
    - `DISPlay` — **SET** `Show_Statistics` · `<state>` · args: `state` · bool: `OFF` | `ON`
    - `DISPlay?` — **NAB** `Get_Measure_Statistic_Display` · → BOOL · †<br>Enable or disable the statistic function, or query the status of the statistic function
    - `ITEM?` — **NAB** `Get_Measure_Statistic_Item` · → 1 value · †<br>Enable the statistic function of any waveform parameter of the specified source, or query the statistic result of any waveform parameter of the specified source
    - `MODE?` — **NAB** `Get_Measure_Statistic_Mode` · → CRD · †<br>Set or query the statistic mode
    - `RESet` — **DO** `Do_Measure_Statistic_Reset` · †<br>Clear the history data and make statistic again
- **`MOD`**
  - `AM` — **SET** `Set_Mod_Am` · `<value>` · args: `value` · †
  - `FM` — **SET** `Set_Mod_Fm` · `<value>` · args: `value` · †
  - `STATe` — **SET** `Set_Mod_Statistic` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the modulation of the specified source channel, or query the status of the modulation of the specified source channel
  - `TYPe` — **SET** `Set_Mod_Type` · `<value>` · args: `value` · enum · †<br>Set or query the modulation type of the specified source channel
  - `AM?` — **NAB** `Get_Mod_Am` · → 1 value · †
  - `FM?` — **NAB** `Get_Mod_Fm` · → 1 value · †
  - `STATe?` — **NAB** `Get_Mod_Statistic` · → BOOL · †<br>Enable or disable the modulation of the specified source channel, or query the status of the modulation of the specified source channel
  - `TYPe?` — **NAB** `Get_Mod_Type` · → CRD · †<br>Set or query the modulation type of the specified source channel
  - **`AM`**
    - `DEPTh` — **SET** `Set_Mod_Am_Depth` · `<value>` · args: `value` · †<br>Set or query the AM modulation depth (indicates the amplitude variation degree and is expressed as a percentage) of the specified source channel
    - `DEPTh?` — **NAB** `Get_Mod_Am_Depth` · → 1 value · †<br>Set or query the AM modulation depth (indicates the amplitude variation degree and is expressed as a percentage) of the specified source channel
    - **`INTernal`**
      - `FREQuency` — **SET** `Set_Mod_Am_Internal_Frequency` · `<value>` · args: `value` · †<br>Set or query the modulating waveform frequency of AM or FM of the specified source channel
      - `FUNCtion` — **SET** `Set_Mod_Am_Internal_Function` · `<value>` · args: `value` · enum: `SIN` | `SQU` | `RAMP` | `NOIS` · †<br>Set or query the modulating waveform of AM or FM of the specified source channel
      - `FREQuency?` — **NAB** `Get_Mod_Am_Internal_Frequency` · → 1 value · †<br>Set or query the modulating waveform frequency of AM or FM of the specified source channel
      - `FUNCtion?` — **NAB** `Get_Mod_Am_Internal_Function` · → CRD · †<br>Set or query the modulating waveform of AM or FM of the specified source channel
  - **`FM`**
    - `DEVIation` — **SET** `Set_Mod_Fm_Deviation` · `<value>` · args: `value` · †<br>Set or query the FM frequency deviation of the specified source channel
    - `DEVIation?` — **NAB** `Get_Mod_Fm_Deviation` · → 1 value · †<br>Set or query the FM frequency deviation of the specified source channel
    - **`INTernal`**
      - `FREQuency` — **SET** `Set_Mod_Fm_Internal_Frequency` · `<value>` · args: `value` · †<br>Set or query the modulating waveform frequency of AM or FM of the specified source channel
      - `FUNCtion` — **SET** `Set_Mod_Fm_Internal_Function` · `<value>` · args: `value` · enum: `SIN` | `SQU` | `RAMP` | `NOIS` · †<br>Set or query the modulating waveform of AM or FM of the specified source channel
      - `FREQuency?` — **NAB** `Get_Mod_Fm_Internal_Frequency` · → 1 value · †<br>Set or query the modulating waveform frequency of AM or FM of the specified source channel
      - `FUNCtion?` — **NAB** `Get_Mod_Fm_Internal_Function` · → CRD · †<br>Set or query the modulating waveform of AM or FM of the specified source channel
- **`OUTPut`**
  - `IMPedance` — **SET** `Set_Output_Impedance` · `<value>` · args: `value` · enum · †
  - `IMPedance?` — **NAB** `Get_Output_Impedance` · → CRD · †
- **`PARallel`**
  - `BITX` — **SET** `Set_Parallel_Bitx` · `<value>` · args: `value` · †<br>Set or query the CLK channel source of parallel decoding
  - `CCOMpensation` — **SET** `Set_Parallel_Ccompensation` · `<value>` · args: `value` · †<br>Set or query the CLK channel source of parallel decoding
  - `CLK` — **SET** `Set_Parallel_Clk` · `<value>` · args: `value` · †<br>Set or query the CLK channel source of parallel decoding
  - `EDGE` — **SET** `Set_Parallel_Edge` · `<value>` · args: `value` · †<br>Set or query the CLK channel source of parallel decoding
  - `NREJect` — **SET** `Set_Parallel_Nreject` · `<value>` · args: `value` · †<br>Set or query the CLK channel source of parallel decoding
  - `NRTime` — **SET** `Set_Parallel_Nrtime` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the CLK channel source of parallel decoding
  - `PLOT` — **SET** `Set_Parallel_Plot` · `<value>` · args: `value` · †<br>Set or query the CLK channel source of parallel decoding
  - `POLarity` — **SET** `Set_Parallel_Polarity` · `<value>` · args: `value` · enum · †<br>Set or query the CLK channel source of parallel decoding
  - `SOURce` — **SET** `Set_Parallel_Source` · `<value>` · args: `value` · enum · †<br>Set or query the CLK channel source of parallel decoding
  - `WIDTh` — **SET** `Set_Parallel_Width` · `<value>` · args: `value` · numeric · †<br>Set or query the CLK channel source of parallel decoding
  - `BITX?` — **NAB** `Get_Parallel_Bitx` · → 1 value · †<br>Set or query the CLK channel source of parallel decoding
  - `CCOMpensation?` — **NAB** `Get_Parallel_Ccompensation` · → 1 value · †<br>Set or query the CLK channel source of parallel decoding
  - `CLK?` — **NAB** `Get_Parallel_Clk` · → 1 value · †<br>Set or query the CLK channel source of parallel decoding
  - `EDGE?` — **NAB** `Get_Parallel_Edge` · → 1 value · †<br>Set or query the CLK channel source of parallel decoding
  - `NREJect?` — **NAB** `Get_Parallel_Nreject` · → 1 value · †<br>Set or query the CLK channel source of parallel decoding
  - `NRTime?` — **NAB** `Get_Parallel_Nrtime` · → NR3 s · †<br>Set or query the CLK channel source of parallel decoding
  - `PLOT?` — **NAB** `Get_Parallel_Plot` · → 1 value · †<br>Set or query the CLK channel source of parallel decoding
  - `POLarity?` — **NAB** `Get_Parallel_Polarity` · → CRD · †<br>Set or query the CLK channel source of parallel decoding
  - `SOURce?` — **NAB** `Get_Parallel_Source` · → CRD · †<br>Set or query the CLK channel source of parallel decoding
  - `WIDTh?` — **NAB** `Get_Parallel_Width` · → NR3 · †<br>Set or query the CLK channel source of parallel decoding
- **`PHASe`**
  - `ADJust` — **SET** `Set_Phase_Adjust` · `<value>` · args: `value` · †<br>Set or query the start phase of the specified source channel
  - `ADJust?` — **NAB** `Get_Phase_Adjust` · → 1 value · †<br>Set or query the start phase of the specified source channel
  - `INITiate` — **DO** `Do_Phase_Initiate` · †<br>Execute the align phase operation
- **`PULSe`**
  - `DCYCle` — **SET** `Set_Pulse_Dcycle` · `<value>` · args: `value` · numeric (%) · †<br>Set or query the pulse duty cycle (the percentage that the high level takes up in the whole period) of the specified source channel
  - `DCYCle?` — **NAB** `Get_Pulse_Dcycle` · → NR3 % · †<br>Set or query the pulse duty cycle (the percentage that the high level takes up in the whole period) of the specified source channel
- **`REFerence`**
  - `DISPlay` — **SET** `Set_Reference_Display` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the REF function, or query the status of the REF function
  - `DISPlay?` — **NAB** `Get_Reference_Display` · → BOOL · †<br>Enable or disable the REF function, or query the status of the REF function
- **`REFerence1`**
  - `COLor` — **SET** `Set_Reference_Color` · `<value>` · args: `value` · enum: `GRAY` | `GREE` | `LBL` | `MAG` | `ORAN` · †
  - `ENABle` — **SET** `Set_Reference_Enable` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
  - `SOURce` — **SET** `Set_Reference_Source` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `MATH` · †
  - `VOFFset` — **SET** `Set_Reference_Voffset` · `<value>` · args: `value` · numeric · †<br>Commands
  - `VSCale` — **SET** `Set_Reference_Vscale` · `<value>` · args: `value` · numeric (V) · †
  - `COLor?` — **NAB** `Get_Reference_Color` · → CRD · †
  - `ENABle?` — **NAB** `Get_Reference_Enable` · → NR1 · †
  - `SOURce?` — **NAB** `Get_Reference_Source` · → CRD · †
  - `VOFFset?` — **NAB** `Get_Reference_Voffset` · → 1 value · †<br>Commands
  - `VSCale?` — **NAB** `Get_Reference_Vscale` · → 1 value · †
- **`SPI`**
  - `CLK` — **SET** `Set_Spi_Clk` · `<value>` · args: `value` · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `CS` — **SET** `Set_Spi_Csrc` · `<value>` · args: `value` · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `EDGE` — **SET** `Set_Spi_Edge` · `<value>` · args: `value` · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `ENDian` — **SET** `Set_Spi_Endian` · `<value>` · args: `value` · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `MISO` — **SET** `Set_Spi_Miso` · `<value>` · args: `value` · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `MODE` — **SET** `Set_Spi_Mode` · `<value>` · args: `value` · enum · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `MOSI` — **SET** `Set_Spi_Mosi` · `<value>` · args: `value` · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `POLarity` — **SET** `Set_Spi_Polarity` · `<value>` · args: `value` · enum · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `SELect` — **SET** `Set_Spi_Select` · `<value>` · args: `value` · enum · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `TIMeout` — **SET** `Set_Spi_Timebase` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `WIDTh` — **SET** `Set_Spi_Width` · `<value>` · args: `value` · numeric · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `CLK?` — **NAB** `Get_Spi_Clk` · → 1 value · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `CS?` — **NAB** `Get_Spi_Csrc` · → 1 value · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `EDGE?` — **NAB** `Get_Spi_Edge` · → 1 value · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `ENDian?` — **NAB** `Get_Spi_Endian` · → 1 value · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `MISO?` — **NAB** `Get_Spi_Miso` · → 1 value · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `MODE?` — **NAB** `Get_Spi_Mode` · → CRD · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `MOSI?` — **NAB** `Get_Spi_Mosi` · → 1 value · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `POLarity?` — **NAB** `Get_Spi_Polarity` · → CRD · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `SELect?` — **NAB** `Get_Spi_Select` · → CRD · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `TIMeout?` — **NAB** `Get_Spi_Timebase` · → NR3 s · †<br>Set or query the signal source of the clock channel in SPI decoding
  - `WIDTh?` — **NAB** `Get_Spi_Width` · → NR3 · †<br>Set or query the signal source of the clock channel in SPI decoding
- **`STORage`**
  - **`IMAGe`**
    - `COLor` — **SET** `Set_Storage_Image_Color` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Set the image color when storing images to color (ON) or intensity graded color (OFF)
    - `INVERT` — **SET** `Set_Storage_Image_Invert` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Turn on or off the invert function when storing images
    - `COLor?` — **NAB** `Get_Storage_Image_Color` · → CRD · †<br>Set the image color when storing images to color (ON) or intensity graded color (OFF)
    - `INVERT?` — **NAB** `Get_Storage_Image_Invert` · → BOOL · †<br>Turn on or off the invert function when storing images
- **`SYSTem`**
  - `AUToscale` — **SET** `Set_System_Autoscale` · `<value>` · args: `value` · bool: `OFF` | `ON` · †
  - `BEEPer` — **SET** `Set_System_Beeper` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the beeper, or query the status of the beeper
  - `LANGuage` — **SET** `Set_System_Language` · `<value>` · args: `value` · enum: `SCH` | `TCH` | `ENGL` | `PORT` | `GERM` | `POL` | `KOR` | `JAPA` | `FREN` | `RUSS` · †<br>Set or query the system language
  - `LOCKed` — **SET** `Set_System_Locked` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the keyboard lock function, or query the status of the keyboard lock function
  - `PON` — **SET** `Set_System_Pon` · `<value>` · args: `value` · enum: `LAT` | `DEF` · †<br>Set or query the system configuration to be recalled when the oscilloscope is powered on again after power-off
  - `AUToscale?` — **NAB** `Get_System_Autoscale` · → BOOL · †
  - `BEEPer?` — **NAB** `Get_System_Beeper` · → 1 value · †<br>Enable or disable the beeper, or query the status of the beeper
  - `GAM?` — **NAB** `Get_System_Gam` · → 1 value · †<br>Query the number of grids in the horizontal direction of the instrument screen
  - `LANGuage?` — **NAB** `Get_System_Language` · → 1 value · †<br>Set or query the system language
  - `LOCKed?` — **NAB** `Get_System_Locked` · → 1 value · †<br>Enable or disable the keyboard lock function, or query the status of the keyboard lock function
  - `PON?` — **NAB** `Get_System_Pon` · → 1 value · †<br>Set or query the system configuration to be recalled when the oscilloscope is powered on again after power-off
  - `RAM?` — **NAB** `Get_System_Ram` · → 1 value · †<br>Query the number of analog channels of the instrument
  - **`ERRor`**
    - `NEXT?` — **NAB** `Get_System_Error_Next` · → ERROR · †<br>Query and delete the last system error message
  - **`OPTion`**
    - `INSTall` — **DO** `Do_System_Option_Install` · †<br>Install a option. |Name|Type|Range|Default| |---|---|---|---| |<license>|ASCII String|Refer to
    - `UNINSTall` — **DO** `Do_System_Option_Uninstall` · †<br>Uninstall the options installed
- **`THREshold`**
  - `CHANnel<chan>` — **SET** `Set_Threshold_Channel` · `<value>` · args: `value` · enum · per-instance: `chan` · †<br>Set or query the threshold level of the specified analog channel
  - `CHANnel<chan>?` — **NAB** `Get_Threshold_Channel` · per-instance: `chan` · → CRD · †<br>Set or query the threshold level of the specified analog channel
- **`TIMebase`**
  - `MODE` — **SET** `Set_Timebase_Mode` · `<mode>` · args: `mode` · enum: `MAIN` | `XY` | `ROLL`
  - `OFFSet` — **SET** `Set_Timebase_Offset` · `<offset>` · args: `offset` · numeric (s)
  - `SCALe` — **SET** `Set_Timebase_Scale` · `<scale>` · args: `scale` · numeric (s)
  - `MODE?` — **NAB** `Get_Timebase_Mode` · → CRD s · †<br>Set or query the mode of the horizontal timebase
  - **`DELay`**
    - `ENABle` — **SET** `Set_Timebase_Delay_Enable` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable the delayed sweep, or query the status of the delayed sweep
    - `OFFSet` — **SET** `Set_Timebase_Delay_Offset` · `<value>` · args: `value` · numeric · †<br>Set or query the delayed timebase offset
    - `SCALe` — **SET** `Set_Timebase_Delay_Scale` · `<value>` · args: `value` · numeric · †<br>Set or query the delayed timebase scale
    - `ENABle?` — **NAB** `Get_Timebase_Delay_Enable` · → NR1 s · †<br>Enable or disable the delayed sweep, or query the status of the delayed sweep
    - `OFFSet?` — **NAB** `Get_Timebase_Delay_Offset` · → NR3 s · †<br>Set or query the delayed timebase offset
    - `SCALe?` — **NAB** `Get_Timebase_Delay_Scale` · → NR3 s · †<br>Set or query the delayed timebase scale
  - **`MAIN`**
    - `OFFSet` — **SET** `Time_Offset` · `<offset>` · args: `offset` · numeric
    - `SCALe` — **SET** `Time_Scale` · `<scale>` · args: `scale` · numeric (s/div)
    - `OFFSet?` — **NAB** `Get_Timebase_Main_Offset` · → NR3 s · †<br>Set or query the main timebase offset
    - `SCALe?` — **NAB** `Get_Timebase_Main_Scale` · → NR3 s · †<br>Commands
- **`TRIGger`**
  - `SWEep` — **SET** `Set_Sweep` · `<sweep>` · args: `sweep` · enum: `AUTO` | `NORM` | `SING`
  - `COUPling` — **SET** `Set_Trigger_Coupling` · `<value>` · args: `value` · enum: `AC` | `DC` | `LFR` | `HFR` · †<br>Select or query the trigger coupling type
  - `HOLDoff` — **SET** `Set_Trigger_Holdoff` · `<value>` · args: `value` · numeric (s) · †
  - `MODE` — **SET** `Set_Trigger_Mode` · `<mode>` · args: `mode` · enum: `EDGE` | `PULS` | `RUNT` | `WIND` | `NEDG` | `SLOP` | `VID` | `PATT` | `DEL` | `TIM` | `DUR` | `SHOL` | `RS232` | `IIC` | `SPI`
  - `NREJect` — **SET** `Set_Trigger_Nreject` · `<value>` · args: `value` · bool: `OFF` | `ON` · †<br>Enable or disable noise rejection, or query the status of noise rejection
  - `SWEep` — **SET** `Trigger_Sweep` · `<sweep>` · args: `sweep` · enum: `AUTO` | `NORM` | `SING`
  - `STATus?` — **NAB** `Get_Status` · → BOOL
  - `COUPling?` — **NAB** `Get_Trigger_Coupling` · → CRD · †<br>Select or query the trigger coupling type
  - `HOLDoff?` — **NAB** `Get_Trigger_Holdoff` · → NR3 · †
  - `MODE?` — **NAB** `Get_Trigger_Mode` · → CRD · †<br>Select or query the trigger type
  - `NREJect?` — **NAB** `Get_Trigger_Nreject` · → 1 value · †<br>Enable or disable noise rejection, or query the status of noise rejection
  - `POSition?` — **NAB** `Get_Trigger_Positive` · → NR3 · †<br>Query the position in the internal memory that corresponds to the waveform trigger position
  - `SWEep?` — **NAB** `Get_Trigger_Sweep` · → CRD · †<br>Set or query the trigger mode
  - `DELay` — **DO** `Do_Trigger_Delay` · †<br>Set or query the trigger source A in delay trigger
  - `DURATion` — **DO** `Do_Trigger_Duration` · †<br>Set or query the pattern of each channel in duration trigger
  - `EDGe` — **DO** `Do_Trigger_Edge` · †<br>Set or query the trigger source in edge trigger
  - `IIC` — **DO** `Do_Trigger_Iic` · †<br>Set or query the channel source of SCL in I2C trigger
  - `NEDGe` — **DO** `Do_Trigger_Nedge` · †<br>Set or query the trigger source in Nth edge trigger
  - `PATTern` — **DO** `Do_Trigger_Pattern` · †<br>Set or query the pattern of each channel in pattern trigger
  - `PULSe` — **DO** `Do_Trigger_Pulse` · †<br>Set or query the trigger source in pulse width trigger
  - `RS<chan>` — **DO** `Do_Trigger_Rs` · per-instance: `chan` · †<br>Set or query the trigger source in RS232 trigger
  - `RUNT` — **DO** `Do_Trigger_Runt` · †<br>Set or query the trigger source in runt trigger
  - `SHOLd` — **DO** `Do_Trigger_Shold` · †<br>Set or query the data source in setup/hold trigger
  - `SLOPe` — **DO** `Do_Trigger_Slope` · †<br>Set or query the time value in slope trigger
  - `SPI` — **DO** `Do_Trigger_Spi` · †<br>Set or query the channel source of SCL in SPI trigger
  - `TIMeout` — **DO** `Do_Trigger_Timebase` · †<br>Set or query the trigger source in timeout trigger
  - `VIDeo` — **DO** `Do_Trigger_Video` · †<br>Select or query the trigger source in video trigger
  - `WINDows` — **DO** `Do_Trigger_Windows` · †<br>Set or query the trigger source in windows trigger
  - **`DELay`**
    - `SA` — **SET** `Set_Trigger_Delay_Sa` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the trigger source A in delay trigger
    - `SB` — **SET** `Set_Trigger_Delay_Sb` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the trigger source A in delay trigger
    - `SLOPA` — **SET** `Set_Trigger_Delay_Slopa` · `<value>` · args: `value` · enum: `POS` | `NEG` · †<br>Set or query the trigger source A in delay trigger
    - `SLOPB` — **SET** `Set_Trigger_Delay_Slopb` · `<value>` · args: `value` · enum: `POS` | `NEG` · †<br>Set or query the trigger source A in delay trigger
    - `TLOWer` — **SET** `Set_Trigger_Delay_Tlower` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the trigger source A in delay trigger
    - `TUPPer` — **SET** `Set_Trigger_Delay_Tupper` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the trigger source A in delay trigger
    - `TYPe` — **SET** `Set_Trigger_Delay_Type` · `<value>` · args: `value` · enum · †<br>Set or query the trigger source A in delay trigger
    - `SA?` — **NAB** `Get_Trigger_Delay_Sa` · → NR3 s · †<br>Set or query the trigger source A in delay trigger
    - `SB?` — **NAB** `Get_Trigger_Delay_Sb` · → NR3 s · †<br>Set or query the trigger source A in delay trigger
    - `SLOPA?` — **NAB** `Get_Trigger_Delay_Slopa` · → CRD s · †<br>Set or query the trigger source A in delay trigger
    - `SLOPB?` — **NAB** `Get_Trigger_Delay_Slopb` · → CRD s · †<br>Set or query the trigger source A in delay trigger
    - `TLOWer?` — **NAB** `Get_Trigger_Delay_Tlower` · → NR3 s · †<br>Set or query the trigger source A in delay trigger
    - `TUPPer?` — **NAB** `Get_Trigger_Delay_Tupper` · → NR3 s · †<br>Set or query the trigger source A in delay trigger
    - `TYPe?` — **NAB** `Get_Trigger_Delay_Type` · → CRD s · †<br>Set or query the trigger source A in delay trigger
  - **`DURATion`**
    - `SOURce` — **SET** `Set_Trigger_Duration_Source` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the pattern of each channel in duration trigger
    - `TLOWer` — **SET** `Set_Trigger_Duration_Tlower` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the pattern of each channel in duration trigger
    - `TUPPer` — **SET** `Set_Trigger_Duration_Tupper` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the pattern of each channel in duration trigger
    - `TYPe` — **SET** `Set_Trigger_Duration_Type` · `<value>` · args: `value` · enum: `H` | `L` | `X` · †<br>Set or query the pattern of each channel in duration trigger
    - `WHEN` — **SET** `Set_Trigger_Duration_When` · `<value>` · args: `value` · enum: `GRE` | `LESS` | `GLES` · †<br>Set or query the pattern of each channel in duration trigger
    - `SOURce?` — **NAB** `Get_Trigger_Duration_Source` · → CRD · †<br>Set or query the pattern of each channel in duration trigger
    - `TLOWer?` — **NAB** `Get_Trigger_Duration_Tlower` · → 1 value · †<br>Set or query the pattern of each channel in duration trigger
    - `TUPPer?` — **NAB** `Get_Trigger_Duration_Tupper` · → 1 value · †<br>Set or query the pattern of each channel in duration trigger
    - `TYPe?` — **NAB** `Get_Trigger_Duration_Type` · → CRD · †<br>Set or query the pattern of each channel in duration trigger
    - `WHEN?` — **NAB** `Get_Trigger_Duration_When` · → 1 value · †<br>Set or query the pattern of each channel in duration trigger
  - **`EDGe`**
    - `LEVel` — **SET** `Set_Edge_Level` · `<level>` · args: `level` · numeric
    - `SLOPe` — **SET** `Set_Edge_Slope` · `<slope>` · args: `slope` · enum: `POS` | `NEG` | `RFAL`
    - `SOURce` — **SET** `Set_Edge_Source` · `<source>` · args: `source` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `AC`
    - `LEVel` — **SET** `Trigger_Level` · `<level>` · args: `level` · numeric
    - `SOURce` — **SET** `Trigger_Source` · `<source>` · args: `source` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `AC`
    - `LEVel?` — **NAB** `Get_Trigger_Edge_Level` · → NR3 · †<br>Set or query the trigger source in edge trigger
    - `SLOPe?` — **NAB** `Get_Trigger_Edge_Slope` · → CRD · †<br>Set or query the trigger source in edge trigger
    - `SOURce?` — **NAB** `Get_Trigger_Edge_Source` · → CRD · †<br>Set or query the trigger source in edge trigger
  - **`IIC`**
    - `ADDRess` — **SET** `Set_Trigger_Iic_Address` · `<value>` · args: `value` · integer · †<br>Set or query the channel source of SCL in I2C trigger
    - `AWIDth` — **SET** `Set_Trigger_Iic_Awidth` · `<value>` · args: `value` · enum: `7` | `8` | `10` · †<br>Set or query the channel source of SCL in I2C trigger
    - `CLEVel` — **SET** `Set_Trigger_Iic_Clevel` · `<value>` · args: `value` · numeric · †<br>Set or query the channel source of SCL in I2C trigger
    - `DATA` — **SET** `Set_Trigger_Iic_Data` · `<value>` · args: `value` · integer · †<br>Set or query the channel source of SCL in I2C trigger
    - `DIRection` — **SET** `Set_Trigger_Iic_Direction` · `<value>` · args: `value` · enum: `READ` | `WRIT` | `RWR` · †<br>Set or query the channel source of SCL in I2C trigger
    - `DLEVel` — **SET** `Set_Trigger_Iic_Dlevel` · `<value>` · args: `value` · numeric · †<br>Set or query the channel source of SCL in I2C trigger
    - `SCL` — **SET** `Set_Trigger_Iic_Scl` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the channel source of SCL in I2C trigger
    - `SDA` — **SET** `Set_Trigger_Iic_Sda` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the channel source of SCL in I2C trigger
    - `WHEN` — **SET** `Set_Trigger_Iic_When` · `<value>` · args: `value` · enum: `STAR` | `REST` | `STOP` | `NACK` | `ADDR` | `DATA` | `ADAT` · †<br>Set or query the channel source of SCL in I2C trigger
    - `ADDRess?` — **NAB** `Get_Trigger_Iic_Address` · → NR1 · †<br>Set or query the channel source of SCL in I2C trigger
    - `AWIDth?` — **NAB** `Get_Trigger_Iic_Awidth` · → 1 value · †<br>Set or query the channel source of SCL in I2C trigger
    - `CLEVel?` — **NAB** `Get_Trigger_Iic_Clevel` · → 1 value · †<br>Set or query the channel source of SCL in I2C trigger
    - `DATA?` — **NAB** `Get_Trigger_Iic_Data` · → BLOCK · †<br>Set or query the channel source of SCL in I2C trigger
    - `DIRection?` — **NAB** `Get_Trigger_Iic_Direction` · → 1 value · †<br>Set or query the channel source of SCL in I2C trigger
    - `DLEVel?` — **NAB** `Get_Trigger_Iic_Dlevel` · → 1 value · †<br>Set or query the channel source of SCL in I2C trigger
    - `SCL?` — **NAB** `Get_Trigger_Iic_Scl` · → 1 value · †<br>Set or query the channel source of SCL in I2C trigger
    - `SDA?` — **NAB** `Get_Trigger_Iic_Sda` · → 1 value · †<br>Set or query the channel source of SCL in I2C trigger
    - `WHEN?` — **NAB** `Get_Trigger_Iic_When` · → 1 value · †<br>Set or query the channel source of SCL in I2C trigger
  - **`NEDGe`**
    - `EDGE` — **SET** `Set_Trigger_Nedge_Edge` · `<value>` · args: `value` · integer · †<br>Set or query the trigger source in Nth edge trigger
    - `IDLE` — **SET** `Set_Trigger_Nedge_Idle` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the trigger source in Nth edge trigger
    - `LEVel` — **SET** `Set_Trigger_Nedge_Level` · `<value>` · args: `value` · numeric · †<br>Set or query the trigger source in Nth edge trigger
    - `SLOPe` — **SET** `Set_Trigger_Nedge_Slope` · `<value>` · args: `value` · enum: `POS` | `NEG` · †<br>Set or query the trigger source in Nth edge trigger
    - `SOURce` — **SET** `Set_Trigger_Nedge_Source` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the trigger source in Nth edge trigger
    - `EDGE?` — **NAB** `Get_Trigger_Nedge_Edge` · → 1 value · †<br>Set or query the trigger source in Nth edge trigger
    - `IDLE?` — **NAB** `Get_Trigger_Nedge_Idle` · → 1 value · †<br>Set or query the trigger source in Nth edge trigger
    - `LEVel?` — **NAB** `Get_Trigger_Nedge_Level` · → NR3 · †<br>Set or query the trigger source in Nth edge trigger
    - `SLOPe?` — **NAB** `Get_Trigger_Nedge_Slope` · → CRD · †<br>Set or query the trigger source in Nth edge trigger
    - `SOURce?` — **NAB** `Get_Trigger_Nedge_Source` · → CRD · †<br>Set or query the trigger source in Nth edge trigger
  - **`PATTern`**
    - `LEVel` — **SET** `Set_Trigger_Pattern_Level` · `<value>` · args: `value` · numeric · †<br>Set or query the pattern of each channel in pattern trigger
    - `PATTern` — **SET** `Set_Trigger_Pattern_Pattern` · `<value>` · args: `value` · enum: `H` | `L` | `X` | `R` | `F` · †<br>Set or query the pattern of each channel in pattern trigger
    - `LEVel?` — **NAB** `Get_Trigger_Pattern_Level` · → NR3 · †<br>Set or query the pattern of each channel in pattern trigger
    - `PATTern?` — **NAB** `Get_Trigger_Pattern_Pattern` · → 1 value · †<br>Set or query the pattern of each channel in pattern trigger
  - **`PULSe`**
    - `LEVel` — **SET** `Set_Trigger_Pulse_Level` · `<value>` · args: `value` · numeric · †<br>Set or query the trigger source in pulse width trigger
    - `LWIDth` — **SET** `Set_Trigger_Pulse_Lwidth` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the trigger source in pulse width trigger
    - `SOURce` — **SET** `Set_Trigger_Pulse_Source` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the trigger source in pulse width trigger
    - `UWIDth` — **SET** `Set_Trigger_Pulse_Uwidth` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the trigger source in pulse width trigger
    - `WHEN` — **SET** `Set_Trigger_Pulse_When` · `<value>` · args: `value` · enum: `PGR` | `PLES` | `NGR` | `NLES` | `PGL` | `NGL` · †<br>Set or query the trigger source in pulse width trigger
    - `WIDTh` — **SET** `Set_Trigger_Pulse_Width` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the trigger source in pulse width trigger
    - `LEVel?` — **NAB** `Get_Trigger_Pulse_Level` · → NR3 · †<br>Set or query the trigger source in pulse width trigger
    - `LWIDth?` — **NAB** `Get_Trigger_Pulse_Lwidth` · → 1 value · †<br>Set or query the trigger source in pulse width trigger
    - `SOURce?` — **NAB** `Get_Trigger_Pulse_Source` · → CRD · †<br>Set or query the trigger source in pulse width trigger
    - `UWIDth?` — **NAB** `Get_Trigger_Pulse_Uwidth` · → 1 value · †<br>Set or query the trigger source in pulse width trigger
    - `WHEN?` — **NAB** `Get_Trigger_Pulse_When` · → 1 value · †<br>Set or query the trigger source in pulse width trigger
    - `WIDTh?` — **NAB** `Get_Trigger_Pulse_Width` · → NR3 · †<br>Set or query the trigger source in pulse width trigger
  - **`RUNT`**
    - `ALEVel` — **SET** `Set_Trigger_Runt_Alevel` · `<value>` · args: `value` · numeric · †<br>Set or query the trigger source in runt trigger
    - `BLEVel` — **SET** `Set_Trigger_Runt_Blevel` · `<value>` · args: `value` · numeric · †<br>Set or query the trigger source in runt trigger
    - `POLarity` — **SET** `Set_Trigger_Runt_Polarity` · `<value>` · args: `value` · enum: `POS` | `NEG` · †<br>Set or query the trigger source in runt trigger
    - `SOURce` — **SET** `Set_Trigger_Runt_Source` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the trigger source in runt trigger
    - `WHEN` — **SET** `Set_Trigger_Runt_When` · `<value>` · args: `value` · enum: `NONE` | `GRE` | `LESS` | `GLES` · †<br>Set or query the trigger source in runt trigger
    - `WLOWer` — **SET** `Set_Trigger_Runt_Wlower` · `<value>` · args: `value` · numeric · †<br>Set or query the trigger source in runt trigger
    - `WUPPer` — **SET** `Set_Trigger_Runt_Wupper` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the trigger source in runt trigger
    - `ALEVel?` — **NAB** `Get_Trigger_Runt_Alevel` · → 1 value · †<br>Set or query the trigger source in runt trigger
    - `BLEVel?` — **NAB** `Get_Trigger_Runt_Blevel` · → 1 value · †<br>Set or query the trigger source in runt trigger
    - `POLarity?` — **NAB** `Get_Trigger_Runt_Polarity` · → CRD · †<br>Set or query the trigger source in runt trigger
    - `SOURce?` — **NAB** `Get_Trigger_Runt_Source` · → CRD · †<br>Set or query the trigger source in runt trigger
    - `WHEN?` — **NAB** `Get_Trigger_Runt_When` · → 1 value · †<br>Set or query the trigger source in runt trigger
    - `WLOWer?` — **NAB** `Get_Trigger_Runt_Wlower` · → 1 value · †<br>Set or query the trigger source in runt trigger
    - `WUPPer?` — **NAB** `Get_Trigger_Runt_Wupper` · → 1 value · †<br>Set or query the trigger source in runt trigger
  - **`SHOLd`**
    - `CSrc` — **SET** `Set_Trigger_Shold_Csrc` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the data source in setup/hold trigger
    - `DSrc` — **SET** `Set_Trigger_Shold_Dsrc` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the data source in setup/hold trigger
    - `HTIMe` — **SET** `Set_Trigger_Shold_Htime` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the data source in setup/hold trigger
    - `PATTern` — **SET** `Set_Trigger_Shold_Pattern` · `<value>` · args: `value` · †<br>Set or query the data source in setup/hold trigger
    - `SLOPe` — **SET** `Set_Trigger_Shold_Slope` · `<value>` · args: `value` · enum: `POS` | `NEG` · †<br>Set or query the data source in setup/hold trigger
    - `STIMe` — **SET** `Set_Trigger_Shold_Stime` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the data source in setup/hold trigger
    - `TYPe` — **SET** `Set_Trigger_Shold_Type` · `<value>` · args: `value` · enum: `SET` | `HOL` | `SETHOL` · †<br>Set or query the data source in setup/hold trigger
    - `CSrc?` — **NAB** `Get_Trigger_Shold_Csrc` · → 1 value · †<br>Set or query the data source in setup/hold trigger
    - `DSrc?` — **NAB** `Get_Trigger_Shold_Dsrc` · → 1 value · †<br>Set or query the data source in setup/hold trigger
    - `HTIMe?` — **NAB** `Get_Trigger_Shold_Htime` · → NR3 s · †<br>Set or query the data source in setup/hold trigger
    - `PATTern?` — **NAB** `Get_Trigger_Shold_Pattern` · → 1 value · †<br>Set or query the data source in setup/hold trigger
    - `SLOPe?` — **NAB** `Get_Trigger_Shold_Slope` · → CRD · †<br>Set or query the data source in setup/hold trigger
    - `STIMe?` — **NAB** `Get_Trigger_Shold_Stime` · → NR3 s · †<br>Set or query the data source in setup/hold trigger
    - `TYPe?` — **NAB** `Get_Trigger_Shold_Type` · → CRD · †<br>Set or query the data source in setup/hold trigger
  - **`SLOPe`**
    - `ALEVel` — **SET** `Set_Trigger_Slope_Alevel` · `<value>` · args: `value` · numeric · †<br>Set or query the time value in slope trigger
    - `BLEVel` — **SET** `Set_Trigger_Slope_Blevel` · `<value>` · args: `value` · numeric · †<br>Set or query the time value in slope trigger
    - `SOURce` — **SET** `Set_Trigger_Slope_Source` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the time value in slope trigger
    - `TIME` — **SET** `Set_Trigger_Slope_Time` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the time value in slope trigger
    - `TLOWer` — **SET** `Set_Trigger_Slope_Tlower` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the time value in slope trigger
    - `TUPPer` — **SET** `Set_Trigger_Slope_Tupper` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the time value in slope trigger
    - `WHEN` — **SET** `Set_Trigger_Slope_When` · `<value>` · args: `value` · enum: `PGR` | `PLES` | `NGR` | `NLES` | `PGL` | `NGL` · †<br>Set or query the time value in slope trigger
    - `WINDow` — **SET** `Set_Trigger_Slope_Windows` · `<value>` · args: `value` · enum: `TA` | `TB` | `TAB` · †<br>Set or query the time value in slope trigger
    - `ALEVel?` — **NAB** `Get_Trigger_Slope_Alevel` · → 1 value · †<br>Set or query the time value in slope trigger
    - `BLEVel?` — **NAB** `Get_Trigger_Slope_Blevel` · → 1 value · †<br>Set or query the time value in slope trigger
    - `SOURce?` — **NAB** `Get_Trigger_Slope_Source` · → CRD · †<br>Set or query the time value in slope trigger
    - `TIME?` — **NAB** `Get_Trigger_Slope_Time` · → NR3 s · †<br>Set or query the time value in slope trigger
    - `TLOWer?` — **NAB** `Get_Trigger_Slope_Tlower` · → 1 value · †<br>Set or query the time value in slope trigger
    - `TUPPer?` — **NAB** `Get_Trigger_Slope_Tupper` · → 1 value · †<br>Set or query the time value in slope trigger
    - `WHEN?` — **NAB** `Get_Trigger_Slope_When` · → 1 value · †<br>Set or query the time value in slope trigger
    - `WINDow?` — **NAB** `Get_Trigger_Slope_Windows` · → CRD · †<br>Set or query the time value in slope trigger
  - **`SPI`**
    - `CLEVel` — **SET** `Set_Trigger_Spi_Clevel` · `<value>` · args: `value` · numeric · †<br>Set or query the channel source of SCL in SPI trigger
    - `CS` — **SET** `Set_Trigger_Spi_Csrc` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the channel source of SCL in SPI trigger
    - `DATA` — **SET** `Set_Trigger_Spi_Data` · `<value>` · args: `value` · integer · †<br>Set or query the channel source of SCL in SPI trigger
    - `DLEVel` — **SET** `Set_Trigger_Spi_Dlevel` · `<value>` · args: `value` · numeric · †<br>Set or query the channel source of SCL in SPI trigger
    - `MODE` — **SET** `Set_Trigger_Spi_Mode` · `<value>` · args: `value` · enum: `HIGH` | `LOW` · †<br>Set or query the channel source of SCL in SPI trigger
    - `SCL` — **SET** `Set_Trigger_Spi_Scl` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the channel source of SCL in SPI trigger
    - `SDA` — **SET** `Set_Trigger_Spi_Sda` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the channel source of SCL in SPI trigger
    - `SLEVel` — **SET** `Set_Trigger_Spi_Slevel` · `<value>` · args: `value` · numeric · †<br>Set or query the channel source of SCL in SPI trigger
    - `SLOPe` — **SET** `Set_Trigger_Spi_Slope` · `<value>` · args: `value` · enum: `POS` | `NEG` · †<br>Set or query the channel source of SCL in SPI trigger
    - `TIMeout` — **SET** `Set_Trigger_Spi_Timebase` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the channel source of SCL in SPI trigger
    - `WHEN` — **SET** `Set_Trigger_Spi_When` · `<value>` · args: `value` · enum: `CS` | `TIM` · †<br>Set or query the channel source of SCL in SPI trigger
    - `WIDTh` — **SET** `Set_Trigger_Spi_Width` · `<value>` · args: `value` · integer · †<br>Set or query the channel source of SCL in SPI trigger
    - `CLEVel?` — **NAB** `Get_Trigger_Spi_Clevel` · → 1 value · †<br>Set or query the channel source of SCL in SPI trigger
    - `CS?` — **NAB** `Get_Trigger_Spi_Csrc` · → 1 value · †<br>Set or query the channel source of SCL in SPI trigger
    - `DATA?` — **NAB** `Get_Trigger_Spi_Data` · → BLOCK · †<br>Set or query the channel source of SCL in SPI trigger
    - `DLEVel?` — **NAB** `Get_Trigger_Spi_Dlevel` · → 1 value · †<br>Set or query the channel source of SCL in SPI trigger
    - `MODE?` — **NAB** `Get_Trigger_Spi_Mode` · → CRD · †<br>Set or query the channel source of SCL in SPI trigger
    - `SCL?` — **NAB** `Get_Trigger_Spi_Scl` · → 1 value · †<br>Set or query the channel source of SCL in SPI trigger
    - `SDA?` — **NAB** `Get_Trigger_Spi_Sda` · → 1 value · †<br>Set or query the channel source of SCL in SPI trigger
    - `SLEVel?` — **NAB** `Get_Trigger_Spi_Slevel` · → 1 value · †<br>Set or query the channel source of SCL in SPI trigger
    - `SLOPe?` — **NAB** `Get_Trigger_Spi_Slope` · → CRD · †<br>Set or query the channel source of SCL in SPI trigger
    - `TIMeout?` — **NAB** `Get_Trigger_Spi_Timebase` · → NR3 s · †<br>Set or query the channel source of SCL in SPI trigger
    - `WHEN?` — **NAB** `Get_Trigger_Spi_When` · → 1 value · †<br>Set or query the channel source of SCL in SPI trigger
    - `WIDTh?` — **NAB** `Get_Trigger_Spi_Width` · → NR3 · †<br>Set or query the channel source of SCL in SPI trigger
  - **`TIMeout`**
    - `SLOPe` — **SET** `Set_Trigger_Timebase_Slope` · `<value>` · args: `value` · enum: `POS` | `NEG` | `RFAL` · †<br>Set or query the trigger source in timeout trigger
    - `SOURce` — **SET** `Set_Trigger_Timebase_Source` · `<value>` · args: `value` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the trigger source in timeout trigger
    - `TIMe` — **SET** `Set_Trigger_Timebase_Timebase` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the trigger source in timeout trigger
    - `SLOPe?` — **NAB** `Get_Trigger_Timebase_Slope` · → CRD s · †<br>Set or query the trigger source in timeout trigger
    - `SOURce?` — **NAB** `Get_Trigger_Timebase_Source` · → CRD s · †<br>Set or query the trigger source in timeout trigger
    - `TIMe?` — **NAB** `Get_Trigger_Timebase_Timebase` · → NR3 s · †<br>Set or query the trigger source in timeout trigger
  - **`VIDeo`**
    - `LEVel` — **SET** `Set_Trigger_Video_Level` · `<value>` · args: `value` · numeric · †<br>Select or query the trigger source in video trigger
    - `LINE` — **SET** `Set_Trigger_Video_Line` · `<value>` · args: `value` · integer · †<br>Select or query the trigger source in video trigger
    - `MODE` — **SET** `Set_Trigger_Video_Mode` · `<value>` · args: `value` · enum: `ODDF` | `EVEN` | `LINE` | `ALIN` · †<br>Select or query the trigger source in video trigger
    - `POLarity` — **SET** `Set_Trigger_Video_Polarity` · `<value>` · args: `value` · enum: `POS` | `NEG` · †<br>Select or query the trigger source in video trigger
    - `SOURce` — **SET** `Set_Trigger_Video_Source` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Select or query the trigger source in video trigger
    - `STANdard` — **SET** `Set_Trigger_Video_Standard` · `<value>` · args: `value` · enum: `PALS` | `NTSC` | `480P` | `576P` · †<br>Select or query the trigger source in video trigger
    - `LEVel?` — **NAB** `Get_Trigger_Video_Level` · → NR3 · †<br>Select or query the trigger source in video trigger
    - `LINE?` — **NAB** `Get_Trigger_Video_Line` · → 1 value · †<br>Select or query the trigger source in video trigger
    - `MODE?` — **NAB** `Get_Trigger_Video_Mode` · → CRD · †<br>Select or query the trigger source in video trigger
    - `POLarity?` — **NAB** `Get_Trigger_Video_Polarity` · → CRD · †<br>Select or query the trigger source in video trigger
    - `SOURce?` — **NAB** `Get_Trigger_Video_Source` · → CRD · †<br>Select or query the trigger source in video trigger
    - `STANdard?` — **NAB** `Get_Trigger_Video_Standard` · → 1 value · †<br>Select or query the trigger source in video trigger
  - **`WINDows`**
    - `ALEVel` — **SET** `Set_Trigger_Windows_Alevel` · `<value>` · args: `value` · numeric · †<br>Set or query the trigger source in windows trigger
    - `BLEVel` — **SET** `Set_Trigger_Windows_Blevel` · `<value>` · args: `value` · numeric · †<br>Set or query the trigger source in windows trigger
    - `POSition` — **SET** `Set_Trigger_Windows_Positive` · `<value>` · args: `value` · enum: `EXIT` | `ENTER` | `TIM` · †<br>Set or query the trigger source in windows trigger
    - `SLOPe` — **SET** `Set_Trigger_Windows_Slope` · `<value>` · args: `value` · enum: `POS` | `NEG` | `RFAL` · †<br>Set or query the trigger source in windows trigger
    - `SOURce` — **SET** `Set_Trigger_Windows_Source` · `<value>` · args: `value` · enum: `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` · †<br>Set or query the trigger source in windows trigger
    - `TIMe` — **SET** `Set_Trigger_Windows_Timebase` · `<value>` · args: `value` · numeric (s) · †<br>Set or query the trigger source in windows trigger
    - `ALEVel?` — **NAB** `Get_Trigger_Windows_Alevel` · → 1 value · †<br>Set or query the trigger source in windows trigger
    - `BLEVel?` — **NAB** `Get_Trigger_Windows_Blevel` · → 1 value · †<br>Set or query the trigger source in windows trigger
    - `POSition?` — **NAB** `Get_Trigger_Windows_Positive` · → NR3 · †<br>Set or query the trigger source in windows trigger
    - `SLOPe?` — **NAB** `Get_Trigger_Windows_Slope` · → CRD · †<br>Set or query the trigger source in windows trigger
    - `SOURce?` — **NAB** `Get_Trigger_Windows_Source` · → CRD · †<br>Set or query the trigger source in windows trigger
    - `TIMe?` — **NAB** `Get_Trigger_Windows_Timebase` · → NR3 s · †<br>Set or query the trigger source in windows trigger
- **`UART`**
  - `BAUD` — **SET** `Set_Uart_Baud` · `<value>` · args: `value` · †<br>Set or query the TX channel source of RS232 decoding
  - `ENDian` — **SET** `Set_Uart_Endian` · `<value>` · args: `value` · †<br>Set or query the TX channel source of RS232 decoding
  - `PARity` — **SET** `Set_Uart_Parallel` · `<value>` · args: `value` · †<br>Set or query the TX channel source of RS232 decoding
  - `POLarity` — **SET** `Set_Uart_Polarity` · `<value>` · args: `value` · enum · †<br>Set or query the TX channel source of RS232 decoding
  - `RX` — **SET** `Set_Uart_Rx` · `<value>` · args: `value` · †<br>Set or query the TX channel source of RS232 decoding
  - `STOP` — **SET** `Set_Uart_Stop` · `<value>` · args: `value` · numeric · †<br>Set or query the TX channel source of RS232 decoding
  - `TX` — **SET** `Set_Uart_Tx` · `<value>` · args: `value` · †<br>Set or query the TX channel source of RS232 decoding
  - `WIDTh` — **SET** `Set_Uart_Width` · `<value>` · args: `value` · numeric · †<br>Set or query the TX channel source of RS232 decoding
  - `BAUD?` — **NAB** `Get_Uart_Baud` · → 1 value · †<br>Set or query the TX channel source of RS232 decoding
  - `ENDian?` — **NAB** `Get_Uart_Endian` · → 1 value · †<br>Set or query the TX channel source of RS232 decoding
  - `PARity?` — **NAB** `Get_Uart_Parallel` · → 1 value · †<br>Set or query the TX channel source of RS232 decoding
  - `POLarity?` — **NAB** `Get_Uart_Polarity` · → CRD · †<br>Set or query the TX channel source of RS232 decoding
  - `RX?` — **NAB** `Get_Uart_Rx` · → 1 value · †<br>Set or query the TX channel source of RS232 decoding
  - `STOP?` — **NAB** `Get_Uart_Stop` · → NR3 · †<br>Set or query the TX channel source of RS232 decoding
  - `TX?` — **NAB** `Get_Uart_Tx` · → 1 value · †<br>Set or query the TX channel source of RS232 decoding
  - `WIDTh?` — **NAB** `Get_Uart_Width` · → NR3 · †<br>Set or query the TX channel source of RS232 decoding
- **`VOLTage`**
  - `OFFSet` — **SET** `Set_Voltage_Offset` · `<value>` · args: `value` · numeric (V) · †
  - `OFFSet?` — **NAB** `Get_Voltage_Offset` · → NR3 V · †
  - `LEVel` — **DO** `Do_Voltage_Level` · †
  - **`LEVel`**
    - **`IMMediate`**
      - `AMPLitude` — **SET** `Set_Voltage_Level_Immediate_Amplitude` · `<value>` · args: `value` · numeric (V) · †<br>Set or query the output amplitude of the specified source channel
      - `AMPLitude?` — **NAB** `Get_Voltage_Level_Immediate_Amplitude` · → NR3 V · †<br>Set or query the output amplitude of the specified source channel
      - `OFFSet` — **DO** `Do_Voltage_Level_Immediate_Offset` · †
- **`WAV`**
  - `SOR` — **DO** `Do_Waveform_Sor` · †<br>LabVIEW Programming Demo
- **`WAVeform`**
  - `FORMat` — **SET** `Set_Waveform_Format` · `<format>` · args: `format` · enum: `WORD` | `BYTE` | `ASC`
  - `MODE` — **SET** `Set_Waveform_Mode` · `<mode>` · args: `mode` · enum: `NORM` | `MAX` | `RAW`
  - `SOURce` — **SET** `Set_Waveform_Source` · `<source>` · args: `source` · enum: `D0` | `D1` | `D2` | `D3` | `D4` | `D5` | `D6` | `D7` | `D8` | `D9` | `D10` | `D11` | `D12` | `D13` | `D14` | `D15` | `CHAN1` | `CHAN2` | `CHAN3` | `CHAN4` | `MATH`
  - `STARt` — **SET** `Set_Waveform_Start` · `<value>` · args: `value` · integer · †<br>Set or query the start point of waveform data reading
  - `STOP` — **SET** `Set_Waveform_Stop` · `<value>` · args: `value` · integer · †<br>Set or query the stop point of waveform data reading
  - `DATA?` — **NAB** `Get_Waveform_Data` · → BLOCK
  - `FORMat?` — **NAB** `Get_Waveform_Format` · → CRD · †<br>Set or query the return format of the waveform data
  - `MODE?` — **NAB** `Get_Waveform_Mode` · → CRD · †<br>Set or query the reading mode used by :WAVeform:DATA?
  - `PREamble?` — **NAB** `Get_Waveform_Preamble` · → BLOCK · †<br>Query and return all the waveform parameters
  - `SOURce?` — **NAB** `Get_Waveform_Source` · → CRD · †<br>Set or query the channel of which the waveform data will be read
  - `STARt?` — **NAB** `Get_Waveform_Start` · → NR3 · †<br>Set or query the start point of waveform data reading
  - `STOP?` — **NAB** `Get_Waveform_Stop` · → NR3 · †<br>Set or query the stop point of waveform data reading
  - `XORigin?` — **NAB** `Get_Waveform_Xorigin` · → NR3 · †<br>Query the start time of the waveform data of the channel source currently selected in the X direction
  - `XREFerence?` — **NAB** `Get_Waveform_Xreference` · → NR3 · †<br>Query the reference time of the specified channel source in the X direction
  - `XINC?` — **NAB** `Get_XInc` · → NR3
  - `YINC?` — **NAB** `Get_YInc` · → NR3
  - `YORigin?` — **NAB** `Get_YOrigin` · → NR3
  - `YREFerence?` — **NAB** `Get_YRef` · → NR3

## Common commands (IEEE 488.2)

- `*CLS` — **DO** `Do_Cls` · †
- `*OPC` — **DO** `Do_Opc` · †
- `*RST` — **DO** `Do_Rst` · †
- `*WAI` — **DO** `Do_Wai` · †
- `*ESE?` — **NAB** `Get_Ese` · → NR1 · †
- `*ESR?` — **NAB** `Get_Esr` · → NR1 · †
- `*IDN?` — **NAB** `Get_Idn` · → AARD · †
- `*OPC?` — **NAB** `Get_Opc` · → NR1 · †
- `*SRE?` — **NAB** `Get_Sre` · → NR1 · †
- `*STB?` — **NAB** `Get_Stb` · → NR1 · †
- `*TST?` — **NAB** `Get_Tst` · → NR1 · †
- `*ESE <value>` — **SET** `Set_Ese` · `<value>` · args: `value` · integer · †
- `*SRE <value>` — **SET** `Set_Sre` · `<value>` · args: `value` · integer · †

<!-- END GENERATED -->

---

## Notes carried over

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
