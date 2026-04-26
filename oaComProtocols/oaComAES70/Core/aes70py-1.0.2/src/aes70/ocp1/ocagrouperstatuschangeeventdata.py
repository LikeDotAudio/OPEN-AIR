"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocagrouperstatuschangeeventdata import OcaGrouperStatusChangeEventData as type
from .ocagrouperstatuschangetype import OcaGrouperStatusChangeType
from .ocauint16 import OcaUint16
from .struct import Struct

OcaGrouperStatusChangeEventData = Struct(
  {
    "groupIndex": OcaUint16,
    "citizenIndex": OcaUint16,
    "changeType": OcaGrouperStatusChangeType,
  },
  type
)
