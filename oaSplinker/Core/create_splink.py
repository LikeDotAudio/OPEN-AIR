# Core/create_splink.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import time

def create_splink(self):
    new_id = f"SPLINK_{int(time.time() * 1000)}"
    splink = {
        "id": new_id, "source": None, "dest": None, "mode": "BOTH",
        "active": True, "label": f"New Splink ({new_id})", "handlers": []
    }
    self.splinks.append(splink)
    self._save_splink(splink)
    
    # ⚡ FIREHOSE: Ingest creation event for visibility
    from oaComBroker.Core.protocol_router.manager import ProtocolRouter
    ProtocolRouter.get_instance().ingest("SPLINKER", f"OPEN-AIR/System/Status/Splinker/{new_id}", "CREATED", {"id": new_id, "type": "Empty"})
    
    self.set_learn_mode(new_id)
