"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocaportid import OcaPortID as type
from .ocaportmode import OcaPortMode
from .ocauint16 import OcaUint16
from .struct import Struct

OcaPortID = Struct(
  {
    "Mode": OcaPortMode,
    "Index": OcaUint16,
  },
  type
)
