# .gemini/TempScripts/verify_oaproceduralart.py
import sys
import os

# Add the project root to sys.path if needed
sys.path.append("/home/anthony/Documents/OPEN-AIR")

try:
    print("Attempting to from oaRustCore import oa_procedural_art_rs as oaproceduralart_rs...")
    from oaRustCore import oa_procedural_art_rs as oaproceduralart_rs
    print(f"Success! Imported oaproceduralart_rs from {oaproceduralart_rs.__file__}")
    
    from oaRustCore.oa_procedural_art_rs import ProceduralArtEngine
    engine = ProceduralArtEngine()
    print("Successfully instantiated ProceduralArtEngine")
    
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
