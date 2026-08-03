<!-- BEGIN GENERATED — openair-yak build-trees -->

# Spectrum/N9342CN — command tree

Generated from `commands.json` by `openair-yak build-trees`. Edit the table, not this file.

**28 commands** — SET 9 · RIG 3 · NAB 8 · DO 8 · 0 unverified (0%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Compound commands

Several statements in one message, so they hang off no single branch. Every statement after the first carries a leading colon — without it the parser reads it relative to the previous header's path and the instrument answers `-113`.

- **NAB** `Frequency_settings` · → start, stop, center, span<br>Primary Frequency Monitoring
  - `:FREQuency:STARt?;:FREQuency:STOP?;:FREQuency:CENTer?;:FREQuency:SPAN?`
- **RIG** `RBW_VBW_Hz` · args: `rbw_hz_value`, `vbw_hz_value`<br>Set Resolution and Video BW
  - `:SENSe:BANDwidth:RESolution <rbw_hz_value>;:SENSe:BANDwidth:VIDeo <vbw_hz_value>`
- **RIG** `Ref_Level_dBm` · args: `Ref_Level_dBm`, `Attenuation_dB`, `Preamp_On` · numeric (V)<br>Set Power Levels
  - `:DISPlay:WINDow:TRACe:Y:RLEVel <Ref_Level_dBm>;:POWer:RF:ATTenuation <Attenuation_dB>;:POWer:GAIN <Preamp_On>`
- **NAB** `all_marker_settings` · → y_1, y_2, y_3, y_4, y_5, y_6, x_1, x_2, x_3, x_4, x_5, x_6<br>Marker Amplitude and Frequency Readbacks
  - `:CALCulate:MARKer1:Y?;:CALCulate:MARKer2:Y?;:CALCulate:MARKer3:Y?;:CALCulate:MARKer4:Y?;:CALCulate:MARKer5:Y?;:CALCulate:MARKer6:Y?;:CALCulate:MARKer1:X?;:CALCulate:MARKer2:X?;:CALCulate:MARKer3:X?;:CALCulate:MARKer4:X?;:CALCulate:MARKer5:X?;:CALCulate:MARKer6:X?`
- **NAB** `amplitude_settings` · → rlevel, attenuation, gain<br>Power and Attenuation Readbacks
  - `:DISPlay:WINDow:TRACe:Y:RLEVel?;:POWer:ATTenuation?;:POWer:GAIN?`
- **NAB** `bandwidth_settings` · → resolution, video, auto, continuous, time<br>Bandwidth and Sweep Monitoring
  - `:SENSe:BANDwidth:RESolution?;:SENSe:BANDwidth:VIDeo?;:SENSe:BANDwidth:VIDeo:AUTO?;:INITiate:CONTinuous?;:SENSe:SWEep:TIME?`
- **RIG** `freq_start_stop` · args: `start_freq`, `stop_freq` · numeric<br>Frequency Range Commands
  - `:FREQuency:STARt <start_freq>;:FREQuency:STOP <stop_freq>`

## Tree

- **`CALCulate`**
  - **`MARKer<marker_number>`**
    - `X` — **SET** `Marker_X_position` · `<x_value>` · args: `x_value` · numeric · per-instance: `marker_number`<br>Set Marker Frequency
    - `STATe` — **DO** `Marker_State_OFF` · `OFF` · per-instance: `marker_number`<br>Disable Marker
    - `STATe` — **DO** `Marker_State_ON` · `ON` · per-instance: `marker_number`<br>Enable Marker
- **`DISPlay`**
  - **`WINDow`**
    - **`TRACe`**
      - **`Y`**
        - `RLEVel` — **SET** `Set_Reference_Level` · `<Ref_Level_dBm>` · args: `Ref_Level_dBm` · numeric (V)
        - `RLEVel?` — **NAB** `Get_Reference_Level` · → NR3 V
- **`FREQuency`**
  - `SPAN` — **SET** `Span_Frequency` · `<hz_value>` · args: `hz_value` · numeric
  - `STARt` — **SET** `Start_Freq_MHz` · `<hz_value>` · args: `hz_value` · numeric
  - `STOP` — **SET** `Stop_Freq_MHz` · `<hz_value>` · args: `hz_value` · numeric
- **`POWer`**
  - `ATTenuation` — **SET** `Power_Attenuation` · `<Power_Attenuation>` · args: `Power_Attenuation` · numeric (dB)
  - `GAIN` — **DO** `Set_Power_Gain_OFF` · `OFF`
  - `GAIN` — **DO** `Set_Power_Gain_ON` · `ON`
  - **`ATTenuation`**
    - `AUTO` — **DO** `Set_Input_Auto_Attenuation_OFF` · `OFF`
    - `AUTO` — **DO** `Set_Input_Auto_Attenuation_ON` · `ON`
  - **`RF`**
    - `ATTenuation?` — **NAB** `Attenuation` · → NR3 dB
- **`SENSE`**
  - **`POWer`**
    - **`RF`**
      - **`GAIN`**
        - `STATe?` — **NAB** `Preamp_State` · → BOOL dB
- **`SENSe`**
  - **`BANDwidth`**
    - `RESolution` — **SET** `Resolution_Bandwidth` · `<hz_value>` · args: `hz_value`
    - `VIDeo` — **SET** `Video_Bandwidth` · `<hz_value>` · args: `hz_value`
  - **`SWEep`**
    - `TIME` — **SET** `Sweep_Time` · `<sweep_time_s>` · args: `sweep_time_s` · numeric (s)
- **`SYSTem`**
  - `ERRor?` — **NAB** `Get_error_information` · → NR2<br>System Error Check
  - **`DISPlay`**
    - `UPDate` — **DO** `Do_Update_Display`
  - **`POWer`**
    - `RESet` — **DO** `Do_Power_Cycle`

<!-- END GENERATED -->
