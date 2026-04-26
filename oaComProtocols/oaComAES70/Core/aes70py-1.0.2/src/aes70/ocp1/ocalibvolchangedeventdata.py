"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocalibvolchangedeventdata import OcaLibVolChangedEventData as type
from .ocapropertychangetype import OcaPropertyChangeType
from .ocauint32 import OcaUint32
from .struct import Struct

OcaLibVolChangedEventData = Struct(
  {
    "VolumeID": OcaUint32,
    "ChangeType": OcaPropertyChangeType,
  },
  type
)
