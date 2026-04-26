"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocapositiondescriptor import OcaPositionDescriptor as type
from .fixedlengtharray import FixedLengthArray
from .ocafloat32 import OcaFloat32
from .ocapositioncoordinatesystem import OcaPositionCoordinateSystem
from .ocapositiondescriptorfieldflags import OcaPositionDescriptorFieldFlags
from .struct import Struct

OcaPositionDescriptor = Struct(
  {
    "CoordinateSystem": OcaPositionCoordinateSystem,
    "FieldFlags": OcaPositionDescriptorFieldFlags,
    "Values": FixedLengthArray(OcaFloat32, 6),
  },
  type
)
