"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocaobservationeventdata import OcaObservationEventData as type
from .ocafloat64 import OcaFloat64
from .struct import Struct

OcaObservationEventData = Struct(
  {
    "Reading": OcaFloat64,
  },
  type
)
