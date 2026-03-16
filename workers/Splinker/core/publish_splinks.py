import time
import orjson
from ..constants import app_constants

def _publish_splinks(self):
    from workers.Command_Router.protocol_router import ProtocolRouter
    router = ProtocolRouter.get_instance()
    
    # ⚡ INGEST: Pass the status update to the router for broadcast
    # This ensures it's wrapped with GUID and Partition correctly.
    router.ingest("SPLINKER", "OPEN-AIR/System/Status/Splinker/List", self.splinks)
