# oaTests/Core/Report_Builder/DiscoverTests.py
import os
import glob

def identify_test_directories(project_root):
    """
    Scans the project for test_*.py files and returns a sorted list 
    of unique directories containing them.
    """
    test_pattern = os.path.join(project_root, "**", "test_*.py")
    test_files = glob.glob(test_pattern, recursive=True)
    
    # DEBUG
    # print(f"--- DEBUG: found {len(test_files)} test files total ---")
    
    # Extract unique directories
    found_dirs = sorted(list(set([os.path.dirname(f) for f in test_files])))
    
    return found_dirs

def print_discovery_summary(project_root, found_dirs):
    """
    Prints a formatted summary of discovered test directories.
    """
    print(f"📂 Discovery identified {len(found_dirs)} sub-folders containing test files.")
    for d in found_dirs:
        rel = os.path.relpath(d, project_root)
        print(f"   - {rel}")
