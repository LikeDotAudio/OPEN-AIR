# oaComMidi/Core/Hui/scripts/csvWriter.py
# Author: Anthony Peter Kuzub
# Version: 20260322.1000.1
#
# Description: Provides utility for writing tables to CSV files.

import csv

def write_table(file_path, table):
    """
    Writes a 2D table to a CSV file.
    """
    with open(file_path, 'w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(table)
