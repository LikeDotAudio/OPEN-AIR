# .gemini/TempScripts/fix_all_exports.py
import re
import sys


def fix_entry_py(file_path):
    print(f"Auditing: {file_path}")
    with open(file_path) as f:
        lines = f.readlines()

    orphaned_list_start = -1
    orphaned_list_end = -1

    # Identify orphaned list
    for i in range(len(lines)):
        line = lines[i]
        # Look for the orphaned list pattern:
        # current line starts with 4 spaces and a quote
        if re.match(r'^    ["\'][^"\']+["\'],?$', line):
            if orphaned_list_start == -1:
                # Check previous line: if it's NOT __all__ = [ AND NOT another string
                if i > 0 and "__all__ = [" not in lines[i-1] and not re.match(r'^    ["\'][^"\']+["\'],?$', lines[i-1]):
                    orphaned_list_start = i

        # Find the end of the list: first ] after start
        if orphaned_list_start != -1 and orphaned_list_end == -1:
            if re.match(r'^]$', line.strip()):
                orphaned_list_end = i

    # If orphaned list found
    if orphaned_list_start != -1 and orphaned_list_end != -1:
        print(f"  Found orphaned list at lines {orphaned_list_start+1}-{orphaned_list_end+1}")
        # Insert __all__ = [
        lines.insert(orphaned_list_start, "__all__ = [\n")
    else:
        print("  No orphaned list found.")

    # Consolidate __all__
    # Re-read definitions
    all_definitions = [i for i, line in enumerate(lines) if "__all__ =" in line]

    if len(all_definitions) > 1:
        print(f"  Found {len(all_definitions)} __all__ definitions. Consolidating into the first one...")
        # We'll keep the first one and remove others.
        # But wait, if the second one has more stuff, we might lose it.
        # However, the orphaned list we just fixed is likely the "real" one.
        for idx in sorted(all_definitions[1:], reverse=True):
            print(f"  Removing redundant __all__ at line {idx+1}")
            del lines[idx]

    # Now find the primary __all__ list and ensure it has start, stop, status, run_tests
    primary_all_start = -1
    primary_all_end = -1
    for i, line in enumerate(lines):
        if "__all__ = [" in line:
            primary_all_start = i
            for j in range(i, len(lines)):
                if "]" in lines[j]:
                    primary_all_end = j
                    break
            break

    if primary_all_start != -1 and primary_all_end != -1:
        # Check for start, stop, status, run_tests definitions
        file_content = "".join(lines)
        has_start = re.search(r'^def start\(', file_content, re.MULTILINE) is not None
        has_stop = re.search(r'^def stop\(', file_content, re.MULTILINE) is not None
        has_status = re.search(r'^def status\(', file_content, re.MULTILINE) is not None
        has_run_tests = re.search(r'^def run_tests\(', file_content, re.MULTILINE) is not None

        # Extract existing symbols
        existing_symbols = set()
        for i in range(primary_all_start + 1, primary_all_end):
            matches = re.findall(r'["\']([^"\']+)["\']', lines[i])
            for m in matches:
                existing_symbols.add(m)

        # Symbols to add
        to_add = []
        if has_start and "start" not in existing_symbols: to_add.append("start")
        if has_stop and "stop" not in existing_symbols: to_add.append("stop")
        if has_status and "status" not in existing_symbols: to_add.append("status")
        if has_run_tests and "run_tests" not in existing_symbols: to_add.append("run_tests")

        if to_add:
            print(f"  Adding missing symbols to __all__: {to_add}")
            # Insert before the closing ]
            for symbol in to_add:
                lines.insert(primary_all_end, f'    "{symbol}",\n')
                primary_all_end += 1

    # Write back
    with open(file_path, 'w') as f:
        f.writelines(lines)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            fix_entry_py(f)
    else:
        import glob
        files = glob.glob("**/Entry.py", recursive=True)
        for f in files:
            fix_entry_py(f)
