import configparser
import sys
import subprocess
from loguru import logger
from oaConfiguration.config import create_default_config_ini

class ConfigLoader:
    """Orchestrates the loading, parsing, and auto-generation of the config.ini file."""

    @staticmethod
    def load(config_path, setup_path, local_debug=True):
        config = configparser.ConfigParser()
        
        if not config_path.exists():
            if local_debug: logger.debug(f"📜 config.ini not found at {config_path}. Recreating...")
            try:
                create_default_config_ini(config_path)
                if setup_path.exists():
                    if local_debug: logger.info("🚀 Launching Setup.py...")
                    subprocess.run([sys.executable, str(setup_path)], check=True)
            except Exception as e:
                logger.error(f"❌ Failed to initialize config or setup: {e}")
                return None

        try:
            config.read(config_path)
            return config
        except Exception as e:
            logger.error(f"❌ Failed to read config.ini: {e}")
            return None
