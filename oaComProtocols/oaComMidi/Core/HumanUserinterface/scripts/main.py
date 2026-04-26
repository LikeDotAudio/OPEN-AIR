# scripts/main.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import configparser
import time
from threading import Event, Thread

import csvReader
import csvWriter
import midiParser
import mido
from Cell import Cell
from midiParser import Direction

UPDATE_PERIOD = 0.5  # Seconds
POLL_PERIOD = 0.01  # Seconds
stop_flag = Event()

UPDATE_LCD_CONSTANT = 0x66
LCD_POSITION_INDEX = 5
LCDS_PER_ROW = 8
SEGMENTS_PER_LCD = 7   # number of segments in each lcd section

def handle_midi_input(input_port_name: str, output_port_name: str, table: list[list[int]], direction: Direction) -> None:
    """Handles input from the device and updates the shared table accordingly
    :parameter input_port_name: The name of the midi input port to read from
    :parameter output_port_name: The name of the midi output port to write to
    :parameter table: The table to update
    :parameter direction: The direction of the midi message (incoming from or outgoing to rtp)
    """

    try:
        output_port = mido.open_output(output_port_name)
        input_port = mido.open_input(input_port_name)
    except Exception as e:
        print("Could not open output port " + output_port_name + ":")
        print(e)
        return

    try:
        listen_to_midi(input_port, output_port, table, direction)
    except Exception as e:
        print(e)

    print("Closing port" + input_port_name)
    input_port.close()
    print("Closing port" + output_port_name)
    output_port.close()


def listen_to_midi(input_port, output_port, table, direction: Direction) -> None:
    while True:

        if stop_flag.is_set():
            print("Stopping thread")
            break

        for message in input_port.iter_pending():
            if message.type == 'sysex' and direction == Direction.INCOMING:
                print(message)
                print(message.hex())
            update_table(table, message, direction)
            output_port.send(message)

        time.sleep(POLL_PERIOD)


def update_table(table: list[list[int]], message, direction: Direction) -> None:
    """Updates the table based on the midi message
    :parameter table: The table to update
    :parameter message: The midi message to parse
    :parameter direction: The direction of the midi message (incoming from or outgoing to rtp)
    """

    if message.type == 'sysex':
        update_table_lcd(table, message, direction)
        return


    cell = midiParser.parse_message(message, direction, table)
    if cell is None:
        return

    table[cell.row][cell.column] = midiParser.get_message_value(message)

    # csvWriter.write_table('hui_data.csv', table)


def update_table_lcd(table: list[list[int]], message, direction: Direction) -> None:
    """Updates the lcd portion of the table based on the midi message
    :parameter table: The table to update
    :parameter message: The midi message to parse
    :parameter direction: The direction of the midi message (incoming from or outgoing to rtp)
    """

    length = (len(message.data) - 1) - LCD_POSITION_INDEX
    starting_position = message.data[LCD_POSITION_INDEX] # This is the "id" of the starting lcd segment

    position = starting_position

    # Parses through the message.data and upates each affected character in the table induvidually
    for char_index in range(LCD_POSITION_INDEX + 1, LCD_POSITION_INDEX + length + 1): # for each ascii character in the message

        cell = lcd_seg_to_cell(table, position)

        new_char = chr(message.data[char_index])

        seg = position % SEGMENTS_PER_LCD

        # replace the character at the position seg in the string
        str_val = table[cell.row][cell.column]
        str_val = str_val[:seg] + new_char + str_val[seg + 1:]
        table[cell.row][cell.column] = str_val

        position += 1


def lcd_seg_to_cell(table: list[list[int]], position: int) -> Cell:
    """Returns the cell corresponding to the lcd segment
    :parameter table: The table containing the lcd text data
    :parameter position: The position of the lcd segment
    :return: The cell corresponding to the lcd segment
    """

    lcd_section = position // SEGMENTS_PER_LCD # the lcd section (1-8 is first row, 9-16 is second row)

    lcd_row_index = midiParser.get_row_num('lcd_line_' + str(lcd_section // LCDS_PER_ROW), table)
    lcd_column_index = lcd_section % LCDS_PER_ROW

    if lcd_row_index is None:
        print("lcd_line_" + str(lcd_section // LCDS_PER_ROW) + " not found")
        return None

    return Cell(lcd_row_index, lcd_column_index)



def init_device_from_table(table: list[list[int]], output_port_name: str) -> None:
    """Sets all the faders to the values in the table
    :parameter table: The table to read from
    :parameter output_port_name: The name of the output port to write to
    """

    try:
        output_port = mido.open_output(output_port_name)
    except Exception as e:
        print("Could not open output port " + output_port_name + ":")
        print(e)
        return

    # i know theres alot of magic numbers here but i think eventually i might redo this function
    # so i wont worry about it for now

    # faders
    fader_row = table[midiParser.get_row_num('pitchwheel_0', table)]
    for column in range(midiParser.ROW_SIZE):
        value = int(fader_row[column])
        message = mido.Message('pitchwheel')
        message.channel = column
        message.pitch = value
        output_port.send(message)

    # buttons leds
    for led in range(4):
        led_row = table[midiParser.get_row_num('note_led_on_' + str(led), table)]
        for column in range(midiParser.ROW_SIZE):
            value = int(led_row[column])
            message = mido.Message('note_on')
            message.note = column + led * midiParser.ROW_SIZE
            message.velocity = value
            output_port.send(message)

    # knob leds
    knob_led_row = table[midiParser.get_row_num('control_change_6', table)]
    for column in range(midiParser.ROW_SIZE):
        value = int(knob_led_row[column])
        message = mido.Message('control_change')
        message.control = column + 6 * midiParser.ROW_SIZE
        message.value = value
        output_port.send(message)

    output_port.close()


#         print(row)


def update_csv(csv_path: str, table: list[list[int]], period: int) -> None:
    """Updates the csv file periodically
    :parameter csv_path: The path to the csv file
    :parameter table: The table to write to the csv file
    """

    while not stop_flag.is_set():
        csvWriter.write_table(csv_path, table)
        time.sleep(period)


if __name__ == "__main__":

    # Read the config file
    config = configparser.ConfigParser()
    config.read('config.ini')

    device_count = int(config.get('MIDI', 'DEVICE_COUNT'))

    threads = []

    for device_num in range (device_count):

        csv_path = config.get('Paths', 'PATH_TO_CSV_FILE_' + str(device_num))
        table = csvReader.read_table(csv_path)
        midi_read = config.get('MIDI', 'MIDI_DEVICE_INPUT_PORT_' + str(device_num))

        rtp_midi_read = config.get('MIDI', 'RTPMIDI_INPUT_PORT_' + str(device_num))
        rtp_midi_write = config.get('MIDI', 'RTPMIDI_OUTPUT_PORT_' + str(device_num))

        init_device_from_table(table, midi_write)

        hui_input_thread = Thread(target=handle_midi_input,
                                  args=(midi_read, rtp_midi_write, table, Direction.OUTGOING))

        rtp_input_thread = Thread(target=handle_midi_input,
                                  args=(rtp_midi_read, midi_write, table, Direction.INCOMING))

        csv_writer = Thread(target=update_csv, args=(csv_path, table, UPDATE_PERIOD))

        hui_input_thread.start()
        rtp_input_thread.start()
        csv_writer.start()

        # Creates threads to handle input, output, and updating the csv periodically

        threads.append(hui_input_thread)
        threads.append(rtp_input_thread)
        threads.append(csv_writer)









    # Wait for a keyboard interrupt
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        stop_flag.set()  # Set the stop flag to stop the threads

    finally:
        # Wait for the threads to finish
        for thread in threads:
            thread.join()
