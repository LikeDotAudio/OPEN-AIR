# oaComProtocols/oaComNmos/Constants/nmos_constants.py
# Author: Anthony Peter Kuzub
# Version: 20260505.1215.1
#
# Description: NMOS-specific configuration constants.

# Default port for IS-07 WebSocket transport
NMOS_IS07_DEFAULT_PORT = 8085
NMOS_IS07_DEFAULT_URI = f"ws://localhost:{NMOS_IS07_DEFAULT_PORT}/is07"

# Timing
NMOS_IS07_RECONNECT_INTERVAL = 5.0
NMOS_IS07_CONNECTION_WAIT = 2.0
