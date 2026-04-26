"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocastreamconnectoridentification import OcaStreamConnectorIdentification as type
from .ocablob import OcaBlob
from .struct import Struct

OcaStreamConnectorIdentification = Struct(
  {
    "HostID": OcaBlob,
    "NetworkAddress": OcaBlob,
    "NodeID": OcaBlob,
    "StreamConnectorID": OcaBlob,
  },
  type
)
