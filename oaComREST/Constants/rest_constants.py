# oaComREST/Constants/rest_constants.py
# Author: Anthony Peter Kuzub
# Version: 20260326.1200.1
#
# Description: Shared constants and defaults for the REST module.

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

# --- Debugging ---
LOCAL_DEBUG = getattr(app_constants, "REST_DEBUG_ENABLE", False)

# --- FastAPI Settings ---
REST_HOST = getattr(app_constants, "REST_HOST", "0.0.0.0")
REST_PORT = getattr(app_constants, "REST_PORT", 8000)
REST_CORS_ORIGINS = getattr(app_constants, "REST_CORS_ORIGINS", "*").split(",")
