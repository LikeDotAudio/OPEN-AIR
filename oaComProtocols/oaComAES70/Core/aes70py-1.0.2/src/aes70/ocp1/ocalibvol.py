"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocalibvol import OcaLibVol as type
from .ocablob import OcaBlob
from .ocalibvolmetadata import OcaLibVolMetadata
from .struct import Struct

OcaLibVol = Struct(
  {
    "Metadata": OcaLibVolMetadata,
    "Data": OcaBlob,
  },
  type
)
