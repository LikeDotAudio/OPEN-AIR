"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocanetworkstatistics import OcaNetworkStatistics as type
from .ocauint32 import OcaUint32
from .struct import Struct

OcaNetworkStatistics = Struct(
  {
    "rxPacketErrors": OcaUint32,
    "txPacketErrors": OcaUint32,
  },
  type
)
