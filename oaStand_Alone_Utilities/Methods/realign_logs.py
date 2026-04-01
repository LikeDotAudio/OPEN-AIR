# oaStand_Alone_Utilities/Methods/realign_logs.py
# Author: Anthony Peter Kuzub
# Version: 20260331.1100.1
#
# Description: A utility to ingest dozens of log files, sort them by microsecond timestamps, and merge them.

import os
import re
import argparse
from pathlib import Path

# The standardized OPEN-AIR log pattern
LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d+\.\d+)\s+\|\s+(?P<level>\w+)\s+\|\s+(?P<partition>\w+)\s+\|\s+(?P<process>\w+)\s+\|\s+(?P<function>[\w\.]+)\s+\|\s+(?P<message>.*)$"
)

def realign_logs(input_dir, output_file):
    """
    Ingests all .log files in the input_dir, sorts them by timestamp, and merges them.
    """
    all_log_lines = []
    
    input_path = Path(input_dir)
    if not input_path.is_dir():
        print(f"Error: {input_dir} is not a directory.")
        return False

    for log_file in input_path.glob("*.log"):
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                match = LOG_PATTERN.match(line)
                if match:
                    # Store as (timestamp_float, original_line)
                    try:
                        ts = float(match.group('timestamp'))
                        all_log_lines.append((ts, line))
                    except ValueError:
                        continue
                else:
                    # If it doesn't match, we might want to skip it or keep it with the previous line?
                    # For a simple realigner, we'll skip non-matching lines for now.
                    pass

    # Sort by timestamp
    all_log_lines.sort(key=lambda x: x[0])

    # Write to output
    with open(output_file, 'w', encoding='utf-8') as f:
        for _, line in all_log_lines:
            f.write(line + '\n')
            
    return True

def main():
    parser = argparse.ArgumentParser(description="Realign OPEN-AIR log files by timestamp.")
    parser.add_argument("--dir", required=True, help="Directory containing .log files.")
    parser.add_argument("--output", default="realigned_logs.log", help="Output file name.")
    args = parser.parse_args()

    success = realign_logs(args.dir, args.output)
    if success:
        print(f"Successfully realigned logs into {args.output}")
    else:
        exit(1)

if __name__ == '__main__':
    main()
