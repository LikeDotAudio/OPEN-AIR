# .gemini/TempScripts/repro_rest_bug.py
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

print("Checking oaComREST.Methods.rest_server import...")
try:
    from oaComProtocols.oaComREST.Methods.rest_server import RestServer
    print("✅ oaComREST.Methods.rest_server import OK")
    s = RestServer()
    print("✅ RestServer instantiation OK")
except ModuleNotFoundError as e:
    print(f"❌ ModuleNotFoundError: {e}")
except ImportError as e:
    print(f"❌ ImportError: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
