"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocalibvoldata_paramset import OcaLibVolData_ParamSet as type
from .ocablob import OcaBlob
from .ocauint32 import OcaUint32
from .struct import Struct

OcaLibVolData_ParamSet = Struct(
  {
    "TargetBlockType": OcaUint32,
    "ParData": OcaBlob,
  },
  type
)
