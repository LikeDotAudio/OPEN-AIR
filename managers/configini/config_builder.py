# managers/configini/config_builder.py

import configparser
import pathlib


def create_default_config_ini(config_path: pathlib.Path, silent: bool = False):
    """
    Creates a default config.ini file with predefined settings.
    """
    config = configparser.ConfigParser()

    config["Version"] = {"CURRENT_VERSION": "20251225"}

    config["Mode"] = {"SKIP_DEP_CHECK": "False", "CLEAN_INSTALL_MODE": "True"}

    config["Debug"] = {"ENABLE_DEBUG_MODE": "True", "ENABLE_DEBUG_SCREEN": "True"}

    config["UI"] = {
        "LAYOUT_SPLIT_EQUAL": "50",
        "LAYOUT_FULL_WEIGHT": "100",
        "RELOAD_CONFIG_DISPLAYED": "False",
    }

    config["MQTT"] = {
        "BROKER_ADDRESS": "localhost",
        "BROKER_PORT": "1883",
        "MQTT_USERNAME": "guest",
        "MQTT_PASSWORD": "guest",
        "MQTT_RETAIN_BEHAVIOR": "True",
    }

    with open(config_path, "w") as configfile:
        config.write(configfile)
