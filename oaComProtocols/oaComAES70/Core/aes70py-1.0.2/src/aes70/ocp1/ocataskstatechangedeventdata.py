"""
This file is part of aes70py.
This file has been generated.
"""
from ..types.ocataskstatechangedeventdata import OcaTaskStateChangedEventData as type
from .ocalibvolidentifier import OcaLibVolIdentifier
from .ocataskstatus import OcaTaskStatus
from .ocauint32 import OcaUint32
from .struct import Struct

OcaTaskStateChangedEventData = Struct(
  {
    "TaskID": OcaUint32,
    "ProgramID": OcaLibVolIdentifier,
    "Status": OcaTaskStatus,
  },
  type
)
