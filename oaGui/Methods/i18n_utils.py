# oaGui/Methods/i18n_utils.py
# Author: Gemini (Collaborator)
# Version: 20260405.2345.1
#
# Description: Internationalization utilities for GUI text.

from oaConfigurationManager.FileReaders.config_reader import Config

def get_text(data, fallback=""):
    """
    Safely retrieves text from a potentially localized data structure.
    
    Structure expected: {"En": "Text", "Fr": "Texte"}
    If data is a string, returns it directly (legacy support).
    If data is a dict, attempts to use SYSTEM_LANGUAGE, then "En", then first available key.
    """
    if isinstance(data, str):
        return data
    
    if not isinstance(data, dict):
        return str(fallback) if data is None else str(data)

    config = Config.get_instance()
    lang = getattr(config, 'SYSTEM_LANGUAGE', 'En')
    
    # 1. Try current language
    if lang in data and data[lang]:
        return data[lang]
    
    # 2. Try English fallback
    if "En" in data and data["En"]:
        return data["En"]
    
    # 3. Try any available non-empty value
    for value in data.values():
        if value:
            return value
            
    return fallback
