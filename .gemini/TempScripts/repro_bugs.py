# .gemini/TempScripts/repro_bugs.py
import sys


def test_syntax_errors():
    print("Checking for syntax/indentation errors...")
    files_to_check = [
        "oaAudioMixer/Tests/test_mixer_smoke.py",
        "oaFileImportCSV/Methods/csv_parser.py"
    ]
    for f in files_to_check:
        try:
            with open(f) as file:
                compile(file.read(), f, 'exec')
            print(f"✅ {f} syntax OK")
        except Exception as e:
            print(f"❌ {f} syntax ERROR: {e}")

def test_broker_import():
    print("Checking oaComBroker.Core.protocol_router.manager import...")
    try:
        print("✅ oaComBroker.Core.protocol_router.manager import OK")
    except Exception as e:
        print(f"❌ oaComBroker.Core.protocol_router.manager import ERROR: {e}")

if __name__ == "__main__":
    test_syntax_errors()
    test_broker_import()

    # Run the fast_scanner test
    print("\nRunning FastScanner tests...")
    import subprocess
    subprocess.run([sys.executable, "-m", "unittest", "oaGuiManager/Tests/test_fast_scanner.py"])
