import tkinter as tk
import array

root = tk.Tk()
canvas = tk.Canvas(root, width=200, height=200)
canvas.pack()

test_cases = [
    ("array_float", array.array('d', [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])),
    ("tuple_of_floats", (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)),
    ("list_of_lists", [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]),
    ("dict", {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6})
]

try:
    import numpy as np
    test_cases.append(("numpy_array", np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])))
except ImportError:
    print("Numpy not installed, skipping numpy test")

for name, points in test_cases:
    if points and len(points) >= 6:
        try:
            canvas.create_polygon(points, outline="red", fill="")
            print(f"{name}: SUCCESS")
        except Exception as e:
            print(f"{name}: FAILED with {type(e).__name__}: {e}")
    else:
        print(f"{name}: skipped len check")

root.destroy()
