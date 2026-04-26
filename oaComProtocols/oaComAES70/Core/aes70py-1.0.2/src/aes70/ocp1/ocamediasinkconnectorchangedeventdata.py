"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocamediasinkconnectorchangedeventdata import OcaMediaSinkConnectorChangedEventData as type
from .ocamediaconnectorelement import OcaMediaConnectorElement
from .ocamediasinkconnector import OcaMediaSinkConnector
from .ocapropertychangetype import OcaPropertyChangeType
from .struct import Struct

OcaMediaSinkConnectorChangedEventData = Struct(
  {
    "SinkConnector": OcaMediaSinkConnector,
    "ChangeType": OcaPropertyChangeType,
    "ChangedElement": OcaMediaConnectorElement,
  },
  type
)
