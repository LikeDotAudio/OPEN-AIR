"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocaopath import OcaOPath as type
from .ocablob import OcaBlob
from .ocauint32 import OcaUint32
from .struct import Struct

OcaOPath = Struct(
  {
    "HostID": OcaBlob,
    "ONo": OcaUint32,
  },
  type
)
