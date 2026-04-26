# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/4_Splinker/__init__.py
# This __init__.py file acts as a pointer to the actual implementation of Splinker
# located in the oaSplinker module's Interface directory.

try:
    # Import the actual implementation from the new location
    # Assuming the main logic for Splinker is in __init__.py within its Interface folder
    from oaSplinker.Interface import __init__ as SplinkerInterface

    # For a simple __init__.py, it might just be about namespace availability.
    # If the original structure had a top-level function or class here,
    # you would need to explicitly import and re-export it.
    # For now, we'll assume this is sufficient to maintain the import path.

    # Placeholder to show the module is recognized.
    print("Splinker interface module loaded via pointer.")

except ImportError as e:
    print(f"Error importing Splinker from oaSplinker.Interface: {e}")
    print("Ensure oaSplinker module and its Interface directory are correctly set up.")

    # Fallback or error handling if import fails
    class Splinker:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("Splinker interface module could not be loaded. Please check module paths.")
