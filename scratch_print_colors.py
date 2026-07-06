import json

def find_caps(d):
    results = []
    if isinstance(d, dict):
        if 'LTP_Freq_Gain' in d:
            kc = d['LTP_Freq_Gain'].get('knob_config', {})
            results.append(kc.get('cap_color', 'MISSING'))
        for v in d.values():
            results.extend(find_caps(v))
    elif isinstance(d, list):
        for item in d:
            results.extend(find_caps(item))
    return results

data = json.load(open('FrontEnd/api/tree.json'))
print(find_caps(data))
