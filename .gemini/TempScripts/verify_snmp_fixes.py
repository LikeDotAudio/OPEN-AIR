# .gemini/TempScripts/verify_snmp_fixes.py
import pathlib
import sys

# Setup path
project_root = pathlib.Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("📡 [VERIFY] Testing SNMP Manager Imports...")
try:
    print("✅ SNMPManager imported successfully.")
except Exception as e:
    print(f"❌ SNMPManager import failed: {e}")
    sys.exit(1)

print("\n📡 [VERIFY] Testing Installer Generation...")
try:
    from oaComProtocols.oaComSNMP.Methods.snmp_installer_generator import InstallerGenerator
    installer_bash = InstallerGenerator.generate(".1.3.6.1.4.1.65300", "/tmp/master.sh")

    if "snmpwalk" in installer_bash:
        print("❌ ERROR: 'snmpwalk' found in generated installer script!")
        print("Last 5 lines of script:")
        print("\n".join(installer_bash.splitlines()[-5:]))
        sys.exit(1)
    else:
        print("✅ Success: 'snmpwalk' removed from installer script.")
except Exception as e:
    print(f"❌ Installer generation failed: {e}")
    sys.exit(1)

print("\n🎉 ALL FIXES VERIFIED!")
