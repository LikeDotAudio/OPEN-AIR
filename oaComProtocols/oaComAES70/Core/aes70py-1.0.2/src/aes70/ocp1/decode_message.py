
from aes70.ocp1.command import Command
from aes70.ocp1.commandrrq import CommandRrq
from aes70.ocp1.keepalive import KeepAlive
from aes70.ocp1.notification import Notification
from aes70.ocp1.response import Response

PDU_TYPES = [Command, CommandRrq, Notification, Response, KeepAlive]


def decode_message(data: bytearray, byte_position: int, result_list: list) -> int:
    #print(data)
    #print(len(data))
    #print(data.find(b'\x3b'))
    #print(len(data) < (data.find(b'\x3b') + 10))
    if len(data) < (data.find(b'\x3b', byte_position) + 10):
        #print('not enough data for header')
        return -1
    #print('parsing')
    byte_position = byte_position | 0
    if data[byte_position] != 0x3b:
        raise ValueError('Bad sync value.')
    start_position = byte_position
    byte_position += 1
    # skipping protocol version?
    byte_position += 2
    message_size = int.from_bytes(data[byte_position:byte_position+4], byteorder='big')
    byte_position += 4
    message_type = data[byte_position]
    byte_position += 1
    message_count = int.from_bytes(data[byte_position:byte_position+2], byteorder='big')
    byte_position += 2

    # todo this seems more complicated logically than necessary.
    #print('marker: ' + str(start_position))
    # message size doesn't include the sync byte, so header is 9 bytes long
    message_offset = start_position - 9 + message_size
    #print('message size ' + str(message_size))

    #print('offset ' + str(message_offset))
    #print('pos ' + str(byte_position))
    #print('len ' + str(len(data)))

    # The message length must be at least message_size + 10 bytes long,
    # which includes the sync byte
    if message_offset > (len(data) - start_position - 10):
        #print('not enough data to parse message length')
        return -1

    result_list.clear()
    result_list.extend([None] * message_count)

    message_pdu_type = PDU_TYPES[message_type]

    if message_pdu_type is None:
        raise ValueError('Bad Message Type')

    if message_pdu_type is KeepAlive and message_count != 1:
        raise ValueError('Bad KeepAlive message count.')

    for message_index in range(message_count):
        result_list[message_index] = message_pdu_type()
        byte_position = result_list[message_index].decode_from(data, byte_position, message_offset)

    if byte_position != (start_position + 10 + message_offset):
        raise ValueError(f'Decode error: {byte_position} vs {message_offset}')

    return byte_position


