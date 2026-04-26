"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocanetworksysteminterfaceid import OcaNetworkSystemInterfaceID as type
from .ocablob import OcaBlob
from .struct import Struct

OcaNetworkSystemInterfaceID = Struct(
  {
    "SystemInterfaceHandle": OcaBlob,
    "MyNetworkAddress": OcaBlob,
  },
  type
)
