"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocamediaclockrate import OcaMediaClockRate as type
from .ocafloat32 import OcaFloat32
from .struct import Struct

OcaMediaClockRate = Struct(
  {
    "NominalRate": OcaFloat32,
    "PullRange": OcaFloat32,
    "Accuracy": OcaFloat32,
    "JitterMax": OcaFloat32,
  },
  type
)
