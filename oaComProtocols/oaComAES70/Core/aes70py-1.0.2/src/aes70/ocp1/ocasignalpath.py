"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocasignalpath import OcaSignalPath as type
from .ocaport import OcaPort
from .struct import Struct

OcaSignalPath = Struct(
  {
    "SourcePort": OcaPort,
    "SinkPort": OcaPort,
  },
  type
)
