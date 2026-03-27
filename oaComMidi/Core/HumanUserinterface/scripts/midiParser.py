# scripts/midiParser.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from Cell import Cell
from enum import Enum

ROW_SIZE = 8  # Temporary

class Direction(Enum):
    INCOMING = 1
    OUTGOING = 0



def parse_message(message, direction, table) -> Cell:
    """Parses the midi message and returns the corresponding cell in the table
    :param message: The midi message to parse
    :param table: The table to search
    :return: The cell corresponding to the midi message
    """

    row_name = get_row_name(message, direction)
    if row_name is None:
        return None

    row = get_row_num(row_name, table)
    if row is None:
        return None
    
    column = get_column(message)
    if column is None:
        return None

    return Cell(row, column)


def get_row_num(row_name: str, table) -> int:
    """Returns the row number of the row with the given name
    :param row_name: The name of the row to find
    :param table: The table to search
    :return: The row number of the row with the given name
    """

    row_num = 0
    for row in table:
        if row[ROW_SIZE] == row_name:
            return row_num
        row_num += 1

    print("Row " + row_name + " not found")

    return None


def get_message_value(message) -> int:
    """Returns the value of the midi message
    :param message: The midi message to parse
    :return: The value associated with the midi message
    """

    match message.type:
        case "pitchwheel":
            return message.pitch
        case "control_change":
            return message.value
        case "note_on":
            return message.velocity
        case "sysex":
            return message_data_to_int(message.data)

    return 0

def message_data_to_int(data: tuple) -> int:
    """Converts a tuple of bytes to an int
    :param data: The tuple of bytes to convert
    :return: The int value of the tuple of bytes
    """

    value = 0
    for byte in data:
        value = (value << 8) + byte # << shifts the bits left by 8, effectively multiplying by 256. So Cool!!!!!!!!!!

    return value


def get_column(message) -> int:
    """Returns the table column number of the midi message
    :param message: The midi message to parse
    :return: The column number of the midi message
    """

    match message.type:
        case "pitchwheel":
            return message.channel % ROW_SIZE
        case "control_change":
            return message.control % ROW_SIZE
        case "note_on":
            return message.note % ROW_SIZE

    return 0


def get_row_name(message, direction: Direction) -> str:
    """Returns the corresponding row identifier of the midi message
    :param message: The midi message to parse
    :return: The row identifier of the midi message
    """

    match message.type:
        case "pitchwheel":
            return "pitchwheel_" + str(message.channel // ROW_SIZE)
        case "control_change":
            return "control_change_" + str(message.control // ROW_SIZE)
        case "note_on":
            if direction == Direction.OUTGOING:
                return "note_on_" + str(message.note // ROW_SIZE)
            else:
                return "note_led_on_" + str(message.note // ROW_SIZE)
        # case "sysex":
                

    return None


def parse_table(table, cell: Cell) -> tuple[str, int]:
    """Returns the midi message corresponding to the cell in the table. Basically the inverse of parse_message
    :param table: The table to search
    :param cell: The cell to find
    :return: The midi message corresponding to the cell
    """

    return (table[cell.row][ROW_SIZE + 1], table[cell.row][cell.column])
