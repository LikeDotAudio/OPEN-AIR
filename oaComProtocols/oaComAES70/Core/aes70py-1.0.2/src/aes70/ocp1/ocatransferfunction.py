"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocatransferfunction import OcaTransferFunction as type
from .ocafloat32 import OcaFloat32
from .ocalist import OcaList
from .struct import Struct

OcaTransferFunction = Struct(
  {
    "Frequency": OcaList(OcaFloat32),
    "Amplitude": OcaList(OcaFloat32),
    "Phase": OcaList(OcaFloat32),
  },
  type
)
