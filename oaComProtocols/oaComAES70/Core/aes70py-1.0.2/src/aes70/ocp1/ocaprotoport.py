"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocaprotoport import OcaProtoPort as type
from .ocaprotoportid import OcaProtoPortID
from .ocastring import OcaString
from .ocauint32 import OcaUint32
from .struct import Struct

OcaProtoPort = Struct(
  {
    "Owner": OcaUint32,
    "ProtoID": OcaProtoPortID,
    "Name": OcaString,
  },
  type
)
