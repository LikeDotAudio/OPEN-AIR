"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocamodeldescription import OcaModelDescription as type
from .ocastring import OcaString
from .struct import Struct

OcaModelDescription = Struct(
  {
    "Manufacturer": OcaString,
    "Name": OcaString,
    "Version": OcaString,
  },
  type
)
