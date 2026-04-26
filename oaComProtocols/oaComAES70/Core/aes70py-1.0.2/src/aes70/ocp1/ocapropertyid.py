"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocapropertyid import OcaPropertyID as type
from .ocauint16 import OcaUint16
from .struct import Struct

OcaPropertyID = Struct(
  {
    "DefLevel": OcaUint16,
    "PropertyIndex": OcaUint16,
  },
  type
)
