import tkinter as tk

root = tk.Tk()
canvas = tk.Canvas(root, width=200, height=200)
canvas.pack()

test_cases = [
    ("empty_list", []),
    ("empty_tuple", ()),
    ("list_of_empty_tuples", [(), (), ()]),
    ("list_of_tuples", [(1, 2), (3, 4), (5, 6)]),
    ("flat_list", [1, 2, 3, 4, 5, 6]),
    ("less_than_3_points", [1, 2, 3, 4])
]

for name, points in test_cases:
    try:
        canvas.create_polygon(points, outline="red", fill="")
        print(f"{name}: SUCCESS")
    except Exception as e:
        print(f"{name}: FAILED with {type(e).__name__}: {e}")

root.destroy()
