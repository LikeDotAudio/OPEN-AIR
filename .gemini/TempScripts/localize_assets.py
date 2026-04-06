import os
import json
import glob
import re

# Load pre-translated chunk 1
try:
    with open('/home/anthony/Documents/OPEN-AIR/.gemini/TempScripts/translations_chunk_1.json', 'r', encoding='utf-8') as f:
        TRANSLATION_MAP = json.load(f)
except FileNotFoundError:
    TRANSLATION_MAP = {}

# Common audio terms and patterns
TERMS = {
    'Subs': {'Fr': 'Subs', 'De': 'Subgruppen', 'Es': 'Subgrupos'},
    'Aux': {'Fr': 'Aux', 'De': 'Aux', 'Es': 'Aux'},
    'Needle': {'Fr': 'Aiguille', 'De': 'Nadel', 'Es': 'Aguja'},
    'Wink': {'Fr': 'Volet', 'De': 'Shutter', 'Es': 'Obturador'},
    'Channel': {'Fr': 'Canal', 'De': 'Kanal', 'Es': 'Canal'},
    'CH': {'Fr': 'CH', 'De': 'CH', 'Es': 'CH'},
    'Input': {'Fr': 'Entrée', 'De': 'Eingang', 'Es': 'Entrada'},
    'Output': {'Fr': 'Sortie', 'De': 'Ausgang', 'Es': 'Salida'},
    'Level': {'Fr': 'Niveau', 'De': 'Pegel', 'Es': 'Nivel'},
    'Gain': {'Fr': 'Gain', 'De': 'Verstärkung', 'Es': 'Ganancia'},
    'Volume': {'Fr': 'Volume', 'De': 'Lautstärke', 'Es': 'Volumen'},
    'Pan': {'Fr': 'Pan', 'De': 'Pan', 'Es': 'Pan'},
    'Solo': {'Fr': 'Solo', 'De': 'Solo', 'Es': 'Solo'},
    'Mute': {'Fr': 'Mute', 'De': 'Mute', 'Es': 'Mute'},
    'On': {'Fr': 'On', 'De': 'An', 'Es': 'On'},
    'Off': {'Fr': 'Off', 'De': 'Aus', 'Es': 'Off'},
    'Status': {'Fr': 'État', 'De': 'Status', 'Es': 'Estado'},
    'Settings': {'Fr': 'Paramètres', 'De': 'Einstellungen', 'Es': 'Ajustes'},
    'Frequency': {'Fr': 'Fréquence', 'De': 'Frequenz', 'Es': 'Frecuencia'},
    'Amplitude': {'Fr': 'Amplitude', 'De': 'Amplitude', 'Es': 'Amplitud'},
    'Bandwidth': {'Fr': 'Bande passante', 'De': 'Bandbreite', 'Es': 'Ancho de banda'},
    'Resolution': {'Fr': 'Résolution', 'De': 'Auflösung', 'Es': 'Resolución'},
    'Time': {'Fr': 'Temps', 'De': 'Zeit', 'Es': 'Tiempo'},
    'Trigger': {'Fr': 'Déclencheur', 'De': 'Trigger', 'Es': 'Disparo'},
    'Marker': {'Fr': 'Marqueur', 'De': 'Marker', 'Es': 'Marcador'},
    'Trace': {'Fr': 'Trace', 'De': 'Trace', 'Es': 'Traza'},
    'Display': {'Fr': 'Affichage', 'De': 'Anzeige', 'Es': 'Pantalla'},
    'Menu': {'Fr': 'Menu', 'De': 'Menü', 'Es': 'Menú'},
    'Select': {'Fr': 'Sélect.', 'De': 'Auswahl', 'Es': 'Selec.'},
    'Next': {'Fr': 'Suivant', 'De': 'Weiter', 'Es': 'Siguiente'},
    'Back': {'Fr': 'Retour', 'De': 'Zurück', 'Es': 'Atrás'},
    'Cancel': {'Fr': 'Annuler', 'De': 'Abbrechen', 'Es': 'Cancelar'},
    'Ok': {'Fr': 'Ok', 'De': 'Ok', 'Es': 'Ok'},
    'Yes': {'Fr': 'Oui', 'De': 'Ja', 'Es': 'Sí'},
    'No': {'Fr': 'Non', 'De': 'Nein', 'Es': 'No'},
    'Error': {'Fr': 'Erreur', 'De': 'Fehler', 'Es': 'Error'},
    'Warning': {'Fr': 'Avertissement', 'De': 'Warnung', 'Es': 'Advertencia'},
    'Info': {'Fr': 'Info', 'De': 'Info', 'Es': 'Info'},
    'Help': {'Fr': 'Aide', 'De': 'Hilfe', 'Es': 'Ayuda'},
}

# Extend TRANSLATION_MAP with some more common patterns
def naive_translate(s, lang):
    if not s: return s
    if re.fullmatch(r'\{\{.*?\}\}', s): return s
    if s in TRANSLATION_MAP:
        return TRANSLATION_MAP[s].get(lang, s)
    
    # Check for simple terms
    if s in TERMS:
        return TERMS[s].get(lang, s)
    
    # Check for CH X or Channel X
    m = re.match(r'(CH|Channel|Canal)\s*(\d+)', s, re.I)
    if m:
        prefix = TERMS.get(m.group(1).title(), {}).get(lang, m.group(1))
        return f'{prefix} {m.group(2)}'
    
    # Check for number + units
    m = re.match(r'(-?\d+\.?\d*)\s*(dB|Hz|kHz|MHz|GHz|V|A|Ohms|ms|s)', s, re.I)
    if m:
        return s # Units are usually the same
    
    # If it is a known term with a number
    for term, trans in TERMS.items():
        if s.startswith(term + ' '):
            rest = s[len(term):]
            return trans.get(lang, term) + rest
            
    return s # Fallback to English

def localize_obj(obj):
    if isinstance(obj, dict):
        if 'En' in obj and isinstance(obj['En'], str):
            en_val = obj['En']
            for lang in ['Fr', 'De', 'Es']:
                if lang not in obj or not obj[lang]:
                    obj[lang] = naive_translate(en_val, lang)
        for k, v in obj.items():
            localize_obj(v)
    elif isinstance(obj, list):
        for item in obj:
            localize_obj(item)

assets_dir = '/home/anthony/Documents/OPEN-AIR/oaGuiDefinitions/Assets'
files = glob.glob(os.path.join(assets_dir, '**', '*.json'), recursive=True)

for fpath in files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        localize_obj(data)
        
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f'Error processing {fpath}: {e}')

print(f'Processed {len(files)} files.')
