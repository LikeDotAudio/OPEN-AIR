import time
import orjson
from ..constants import app_constants

def publish_splinks(self):
    from oaComsBroker.protocol_router import ProtocolRouter
    router = ProtocolRouter.get_instance()
    
    # ⚡ INGEST: Pass the status update to the router for broadcast
    # This ensures it's wrapped with GUID and Partition correctly.
    router.ingest("SPLINKER", "OPEN-AIR/System/Status/Splinker/List", self.splinks)
