"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocaclassidentification import OcaClassIdentification as type
from .ocauint16 import OcaUint16
from .string16 import String16
from .struct import Struct

OcaClassIdentification = Struct(
  {
    "ClassID": String16,
    "ClassVersion": OcaUint16,
  },
  type
)
