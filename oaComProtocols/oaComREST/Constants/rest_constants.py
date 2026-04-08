# oaComProtocols.oaComREST/Constants/rest_constants.py
# Author: Anthony Peter Kuzub
# Version: 20260326.1200.1
#
# Description: Shared constants and defaults for the REST module.

from oaConfigurationManager.FileReaders.config_reader import Config
from oaOchestration.Methods.network_utils import get_local_ip

app_constants = Config.get_instance()

# --- Debugging ---
LOCAL_DEBUG = getattr(app_constants, "REST_DEBUG_ENABLE", False)

# --- FastAPI Settings ---
# Use 0.0.0.0 for robust binding on all interfaces, but report the detected local IP for URLs.
detected_ip = get_local_ip()
REST_BIND_HOST = getattr(app_constants, "REST_HOST", "0.0.0.0")
# If configured as 0.0.0.0, we use it for binding but use detected_ip for reporting.
REST_REPORT_HOST = detected_ip if REST_BIND_HOST == "0.0.0.0" else REST_BIND_HOST

REST_PORT = getattr(app_constants, "REST_PORT", 44845)
REST_CORS_ORIGINS = getattr(app_constants, "REST_CORS_ORIGINS", "*").split(",")
