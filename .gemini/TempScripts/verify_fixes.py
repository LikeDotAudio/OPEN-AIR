# .gemini/TempScripts/verify_fixes.py
import sys
import os

# Add project root to sys.path
project_root = "/home/anthony/Documents/OPEN-AIR"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Test 1: Import BlueprintLoader
try:
    from oaGuiManager.FileReaders.blueprint_loader import BlueprintLoader
    print("✅ [FIX 1] BlueprintLoader imported successfully.")
except Exception as e:
    print(f"❌ [FIX 1] BlueprintLoader import FAILED: {e}")

# Test 2: Check Rust oatranslatorcore_rs
try:
    import oatranslatorcore_rs
    print("✅ [FIX 2] oatranslatorcore_rs is available.")
except ImportError:
    print("❌ [FIX 2] oatranslatorcore_rs is MISSING.")

# Test 3: Check Rust oablueprintparser_rs
try:
    import oablueprintparser_rs
    print("✅ [FIX 2] oablueprintparser_rs is available.")
except ImportError:
    print("❌ [FIX 2] oablueprintparser_rs is MISSING.")
