# scripts/csvReader.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import csv
from Cell import Cell

def read(file_path: str, cell: Cell) -> int:
    """Reads the csv file and returns the value at the cell
    :param file_path: The path to the csv file
    :param cell: The cell to read from
    """
    
    with open(file_path, 'r') as file:
        csv_reader = list(csv.reader(file))
    
    try:
        value = int(csv_reader[cell.column][cell.row])
    except IndexError:
        print("Index out of bounds")
    
    return value

def read_table(file_path: str) -> list:
    """Reads the csv file and returns the table
    :param file_path: The path to the csv file
    :return: The table read from the csv file
    """

    with open(file_path, 'r') as file:
        table = list(csv.reader(file))
    
    return table
