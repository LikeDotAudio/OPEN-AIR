# Report_Builder/DiscoverTests.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import glob

def identify_test_directories(project_root):
    """
    Scans the project for test_*.py files and returns a sorted list 
    of unique directories containing them.
    Also identifies top-level "Tests" directories for visibility.
    """
    test_pattern = os.path.join(project_root, "**", "test_*.py")
    test_files = glob.glob(test_pattern, recursive=True)
    
    # 1. Leaf directories (those that actually contain test_*.py)
    leaf_dirs = set([os.path.dirname(f) for f in test_files])
    
    # 2. Top-level "Tests" directories for better visibility
    # For each leaf dir, find its highest ancestor that is still within project_root
    # and is named "Tests" (or just the leaf itself if no "Tests" parent)
    test_roots = set()
    for d in leaf_dirs:
        curr = d
        root_for_this_leaf = d
        while curr and curr != project_root:
            if os.path.basename(curr).lower() == "tests":
                root_for_this_leaf = curr
            curr = os.path.dirname(curr)
        test_roots.add(root_for_this_leaf)
        
    return sorted(list(test_roots))

def print_discovery_summary(project_root, found_dirs):
    """
    Prints a formatted summary of discovered test directories.
    """
    print(f"📂 Discovery identified {len(found_dirs)} test-containing root folders.")
    for d in found_dirs:
        rel = os.path.relpath(d, project_root)
        print(f"   - {rel}")
