"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocadelayvalue import OcaDelayValue as type
from .ocadelayunit import OcaDelayUnit
from .ocafloat32 import OcaFloat32
from .struct import Struct

OcaDelayValue = Struct(
  {
    "DelayValue": OcaFloat32,
    "DelayUnit": OcaDelayUnit,
  },
  type
)
