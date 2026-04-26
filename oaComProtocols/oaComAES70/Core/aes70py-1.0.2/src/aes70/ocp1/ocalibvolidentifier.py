"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocalibvolidentifier import OcaLibVolIdentifier as type
from .ocauint32 import OcaUint32
from .struct import Struct

OcaLibVolIdentifier = Struct(
  {
    "Library": OcaUint32,
    "ID": OcaUint32,
  },
  type
)
