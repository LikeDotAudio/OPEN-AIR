import json
with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f)

demo = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']

# 1. Update EQ_Graph topics to include LoCut and HiCut
demo['fields']['EQ_Graph']['topics'] = {
    'LoCut': 'OpenAir/Gui/EQ_Params/LoCut',
    'Low': 'OpenAir/Gui/EQ_Params/Low',
    'LowMid': 'OpenAir/Gui/EQ_Params/LowMid',
    'Mid': 'OpenAir/Gui/EQ_Params/Mid',
    'HighMid': 'OpenAir/Gui/EQ_Params/HighMid',
    'High': 'OpenAir/Gui/EQ_Params/High',
    'HiCut': 'OpenAir/Gui/EQ_Params/HiCut'
}

# 2. Update Band_Controls columns
band_controls = demo['fields']['Band_Controls']
band_controls['layout_columns'] = 7
band_controls['column_sizing'] = [{'weight': 1} for _ in range(7)]

import copy
band_0 = band_controls['fields']['Band_0']

# Create LoCut
locut = copy.deepcopy(band_0)
locut['description']['En'] = 'LoCut'
locut['fields']['LTP_Freq_Gain']['fader_config']['value']['default_value'] = 20.0
locut['fields']['LTP_Freq_Gain']['topic'] = 'OpenAir/Gui/EQ_Params/LoCut'
locut['fields']['LTP_Freq_Gain']['fader_config']['cosmetics']['colors']['highlight'] = '#BDBDBD'
locut['fields']['LTP_Freq_Gain']['knob_config']['cap_outline_color'] = '#BDBDBD'
locut['fields']['LTP_Freq_Gain']['knob_config']['rotation_min'] = -32.0
locut['fields']['LTP_Freq_Gain']['knob_config']['rotation_max'] = 32.0
locut['fields']['LTP_Freq_Gain']['knob_config']['rotation_default'] = 0.0

locut['fields']['Q_Knob']['topic'] = 'OpenAir/Gui/EQ_Params/LoCut/Q'

# Create HiCut
hicut = copy.deepcopy(band_0)
hicut['description']['En'] = 'HiCut'
hicut['fields']['LTP_Freq_Gain']['fader_config']['value']['default_value'] = 20000.0
hicut['fields']['LTP_Freq_Gain']['topic'] = 'OpenAir/Gui/EQ_Params/HiCut'
hicut['fields']['LTP_Freq_Gain']['fader_config']['cosmetics']['colors']['highlight'] = '#795548'
hicut['fields']['LTP_Freq_Gain']['knob_config']['cap_outline_color'] = '#795548'
hicut['fields']['LTP_Freq_Gain']['knob_config']['rotation_min'] = -32.0
hicut['fields']['LTP_Freq_Gain']['knob_config']['rotation_max'] = 32.0
hicut['fields']['LTP_Freq_Gain']['knob_config']['rotation_default'] = 0.0

hicut['fields']['Q_Knob']['topic'] = 'OpenAir/Gui/EQ_Params/HiCut/Q'

# Reconstruct fields to order them: LoCut -> 0..4 -> HiCut
old_fields = band_controls['fields']
new_fields = {'LoCut_Band': locut}
for k, v in old_fields.items():
    new_fields[k] = v
new_fields['HiCut_Band'] = hicut

band_controls['fields'] = new_fields

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)
