from .createtype import Type
from .enum import Enum
from .ocauint8 import OcaUint8


def Enum8(datatype: Type):
    return Enum(datatype, OcaUint8)
