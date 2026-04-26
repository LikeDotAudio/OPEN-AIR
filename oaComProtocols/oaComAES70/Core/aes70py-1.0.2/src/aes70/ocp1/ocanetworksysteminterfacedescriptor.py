"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocanetworksysteminterfacedescriptor import OcaNetworkSystemInterfaceDescriptor as type
from .ocablob import OcaBlob
from .struct import Struct

OcaNetworkSystemInterfaceDescriptor = Struct(
  {
    "SystemInterfaceParameters": OcaBlob,
    "MyNetworkAddress": OcaBlob,
  },
  type
)
