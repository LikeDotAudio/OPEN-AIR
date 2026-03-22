# Core/publish_splinks.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import time
import orjson
from ..Constants.constants import app_constants

def publish_splinks(self):
    from oaComBroker.Managers.protocol_router import ProtocolRouter
    router = ProtocolRouter.get_instance()
    
    # ⚡ INGEST: Pass the status update to the router for broadcast
    # This ensures it's wrapped with GUID and Partition correctly.
    router.ingest("SPLINKER", "OPEN-AIR/System/Status/Splinker/List", self.splinks)
