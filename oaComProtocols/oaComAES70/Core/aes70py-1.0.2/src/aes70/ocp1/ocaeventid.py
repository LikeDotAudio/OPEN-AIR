"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocaeventid import OcaEventID as type
from .ocauint16 import OcaUint16
from .struct import Struct

OcaEventID = Struct(
  {
    "DefLevel": OcaUint16,
    "EventIndex": OcaUint16,
  },
  type
)
