"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocadbr import OcaDBr as type
from .ocafloat32 import OcaFloat32
from .struct import Struct

OcaDBr = Struct(
  {
    "Value": OcaFloat32,
    "Ref": OcaFloat32,
  },
  type
)
