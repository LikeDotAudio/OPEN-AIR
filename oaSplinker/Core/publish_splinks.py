# Core/publish_splinks.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose


def publish_splinks(self):
    from oaComBroker.Core.protocol_router.manager import ProtocolRouter
    router = ProtocolRouter.get_instance()

    # ⚡ INGEST: Pass the status update to the router for broadcast
    # This ensures it's wrapped with GUID and Partition correctly.
    router.ingest("SPLINKER", "OpenAir/System/Status/Splinker/List", self.registry.all_splinks())
