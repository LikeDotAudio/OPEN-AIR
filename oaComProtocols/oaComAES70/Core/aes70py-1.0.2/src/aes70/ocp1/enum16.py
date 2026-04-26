from .createtype import Type
from .enum import Enum
from .ocauint16 import OcaUint16


def Enum16(datatype: Type):
    return Enum(datatype, OcaUint16)
