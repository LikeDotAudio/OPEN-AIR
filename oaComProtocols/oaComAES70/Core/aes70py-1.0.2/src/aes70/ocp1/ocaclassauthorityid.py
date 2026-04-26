"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocaclassauthorityid import OcaClassAuthorityID as type
from .ocablobfixedlen import OcaBlobFixedLen
from .ocauint8 import OcaUint8
from .ocauint16 import OcaUint16
from .struct import Struct

OcaClassAuthorityID = Struct(
  {
    "Sentinel": OcaUint16,
    "Reserved": OcaUint8,
    "OrganizationID": OcaBlobFixedLen(3),
  },
  type
)
