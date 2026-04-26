"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocamethodid import OcaMethodID as type
from .ocauint16 import OcaUint16
from .struct import Struct

OcaMethodID = Struct(
  {
    "DefLevel": OcaUint16,
    "MethodIndex": OcaUint16,
  },
  type
)
