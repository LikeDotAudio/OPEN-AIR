"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocamediaconnectorstatuschangedeventdata import OcaMediaConnectorStatusChangedEventData as type
from .ocamediaconnectorstatus import OcaMediaConnectorStatus
from .struct import Struct

OcaMediaConnectorStatusChangedEventData = Struct(
  {
    "ConnectorStatus": OcaMediaConnectorStatus,
  },
  type
)
