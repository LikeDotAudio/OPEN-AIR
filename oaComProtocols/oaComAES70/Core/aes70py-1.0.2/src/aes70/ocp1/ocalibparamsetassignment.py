"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocalibparamsetassignment import OcaLibParamSetAssignment as type
from .ocalibvolidentifier import OcaLibVolIdentifier
from .ocauint32 import OcaUint32
from .struct import Struct

OcaLibParamSetAssignment = Struct(
  {
    "ParamSetIdentifier": OcaLibVolIdentifier,
    "TargetBlockONo": OcaUint32,
  },
  type
)
