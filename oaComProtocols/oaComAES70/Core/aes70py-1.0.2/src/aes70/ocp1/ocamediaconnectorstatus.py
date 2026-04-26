"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocamediaconnectorstatus import OcaMediaConnectorStatus as type
from .ocamediaconnectorstate import OcaMediaConnectorState
from .ocauint16 import OcaUint16
from .struct import Struct

OcaMediaConnectorStatus = Struct(
  {
    "ConnectorID": OcaUint16,
    "State": OcaMediaConnectorState,
    "ErrorCode": OcaUint16,
  },
  type
)
