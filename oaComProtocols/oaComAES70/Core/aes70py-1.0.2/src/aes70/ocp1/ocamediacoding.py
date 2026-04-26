"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocamediacoding import OcaMediaCoding as type
from .ocastring import OcaString
from .ocauint16 import OcaUint16
from .ocauint32 import OcaUint32
from .struct import Struct

OcaMediaCoding = Struct(
  {
    "CodingSchemeID": OcaUint16,
    "CodecParameters": OcaString,
    "ClockONo": OcaUint32,
  },
  type
)
