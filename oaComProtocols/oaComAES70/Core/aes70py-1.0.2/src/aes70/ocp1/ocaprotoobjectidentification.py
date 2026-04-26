"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocaprotoobjectidentification import OcaProtoObjectIdentification as type
from .ocaclassidentification import OcaClassIdentification
from .ocauint32 import OcaUint32
from .struct import Struct

OcaProtoObjectIdentification = Struct(
  {
    "POno": OcaUint32,
    "ClassIdentification": OcaClassIdentification,
  },
  type
)
