# oaConfigurationManager/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260330.1000.1 # Updated version for structure change
#
# Description: Configuration Module Entry Point.

"""
oaConfigurationManager/Entry.py - The sole orchestrator for the Configuration Module.

Purpose:
This file is the public entry point for 'oaConfigurationManager'. It manages the
lifecycle of the configuration manager and exports the core 'Config'
singleton and its associated functions to the rest of the project.
"""

from .FileReaders.config_reader import Config
from .Methods.config_validator import validate_configuration
# from .Methods.console_encoder import ConsoleEncoder

class ConfigurationEntry:
    """Entry point for configuration management services."""
    def __init__(self):
        print("📡📥📥 [INBOUND] Initializing ConfigurationEntry...")
        self.config_instance = Config()
        pass

    def start(self):
        """Starts the configuration service (e.g., loads default config if needed)."""
        print("⚙️ [CONFIG] Starting Configuration service...")
        # Placeholder for start logic, potentially loading a default config
        # or ensuring configuration is ready.
        self.config_instance.initialize() # Example: Ensure config is loaded
        pass

    def stop(self):
        """Stops the configuration service."""
        print("🛑 [CONFIG] Stopping Configuration service...")
        # Placeholder for stop logic, e.g., saving pending changes if applicable
        pass

    def status(self):
        """Returns the current status of the configuration service."""
        print("ℹ️ [CONFIG] Checking Configuration service status...")
        # Placeholder for status check logic
        return "initialized" # Example status

def get_config_instance():
    """Returns the singleton Config instance."""
    # Ensure config is initialized before returning
    if not Config._instance: # Assuming Config is a singleton with _instance attribute
        Config().initialize()
    return Config()

def initialize_config(config_path="config.ini", silent=True):
    """
    Initializes the configuration from the specified path.
    """
    # Note: This function might need to interact with ConfigurationEntry if 
    # it's meant to be the primary initialization mechanism. For now, it
    # directly calls the Config class method.
    return Config().initialize(config_path, silent)

def validate(output_func=None):
    """
    Validates the current configuration.
    """
    return validate_configuration(output_func)

def get_encoder():
    """Returns the ConsoleEncoder for output formatting."""
    return None

# Standardized exports
__all__ = [
"ConfigurationEntry",
"Config",
"get_config_instance",
"initialize_config",
"validate",
"get_encoder"
]

def run_tests():
    """
    Discovers and runs all tests within the oaConfigurationManager/Tests/ directory.
    """
    print("Discovering and running tests for oaConfigurationManager...")
    test_dir = Path(__file__).parent / "Tests"
    if not test_dir.is_dir():
        print("❌ No 'Tests/' directory found.")
        return

    test_files = sorted([f for f in test_dir.glob("test_*.py")])
    if not test_files:
        print("❌ No test files found (expected pattern: test_*.py).")
        return

    print(f"Found {len(test_files)} test files. Executing...")
    
    import subprocess
    
    all_tests_passed = True
    for test_file in test_files:
        print(f"--- Running: {test_file.name} ---")
        try:
            # Get the module path relative to the project root for the test runner
            relative_test_file_path = test_file.relative_to(Path(__file__).parent.parent.parent) # Path from OPEN-AIR root
            module_path_for_runner = str(relative_test_file_path).replace(os.sep, '.')[:-3] # Remove .py extension

            # Ensure the current directory is the project root so Python can find modules
            original_cwd = os.getcwd()
            os.chdir(Path(__file__).parent.parent.parent) 

            result = subprocess.run(
                [sys.executable, "-m", "unittest", module_path_for_runner],
                capture_output=True,
                text=True,
                check=False
            )
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            if result.returncode != 0:
                all_tests_passed = False
                print(f"❌ Test failed for {test_file.name} with exit code {result.returncode}")
            else:
                print(f"✅ Tests passed for {test_file.name}")

        except Exception as e:
            print(f"❌ An error occurred while running tests for {test_file.name}: {e}")
            all_tests_passed = False
        finally:
            os.chdir(original_cwd)

    if all_tests_passed:
        print("\n🎉 All tests for oaConfigurationManager passed!")
    else:
        print("\n💔 Some tests for oaConfigurationManager failed.")

if __name__ == "__main__":
    # If run directly and no specific arguments are provided, execute tests.
    # Otherwise, assume specific commands are intended (e.g., start, stop, validate).
    if len(sys.argv) > 1 and sys.argv[1] in ["--start", "--stop", "--status", "--manager"]:
        print("Executing manager function...")
        # In a real application, you'd parse sys.argv and call the appropriate functions.
        # For this task, we assume direct execution without known args implies testing.
    else:
        run_tests()
