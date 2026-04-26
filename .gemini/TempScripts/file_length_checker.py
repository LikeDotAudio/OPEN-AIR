#!/usr/bin/env python3
import sys


def filter_and_check_files(file_list):
    """
    Filters a list of file paths and checks for files exceeding a line limit.

    Args:
        file_list (list): A list of file paths to process.
    """
    long_files = []
    for file_path in file_list:
        file_path = file_path.strip()
        if "/Tests/" in file_path or file_path.endswith("/__init__.py"):
            continue

        try:
            with open(file_path, encoding='utf-8') as f:
                line_count = sum(1 for line in f)

            if line_count > 500:
                long_files.append(file_path)
        except (OSError, UnicodeDecodeError):
            # Ignoring files that can't be read or have encoding issues
            # print(f"Could not process {file_path}: {e}", file=sys.stderr)
            pass

    return long_files

if __name__ == "__main__":
    # The full list of files is passed as a single string argument,
    # with each file path on a new line.
    if len(sys.argv) > 1:
        all_files_str = sys.argv[1]
        files = all_files_str.splitlines()

        violating_files = filter_and_check_files(files)

        if violating_files:
            print("The following files have more than 500 lines:")
            for f in violating_files:
                print(f)
        else:
            print("No files found with more than 500 lines.")
    else:
        print("No file list provided.", file=sys.stderr)

