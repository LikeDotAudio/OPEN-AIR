"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocaprotosignalpath import OcaProtoSignalPath as type
from .ocaprotoport import OcaProtoPort
from .struct import Struct

OcaProtoSignalPath = Struct(
  {
    "SourceProtoPort": OcaProtoPort,
    "SinkProtoPort": OcaProtoPort,
  },
  type
)
