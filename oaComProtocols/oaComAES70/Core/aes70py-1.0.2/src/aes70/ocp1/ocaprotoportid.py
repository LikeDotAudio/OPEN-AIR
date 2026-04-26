"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocaprotoportid import OcaProtoPortID as type
from .ocaportmode import OcaPortMode
from .ocauint16 import OcaUint16
from .struct import Struct

OcaProtoPortID = Struct(
  {
    "Mode": OcaPortMode,
    "Index": OcaUint16,
  },
  type
)
