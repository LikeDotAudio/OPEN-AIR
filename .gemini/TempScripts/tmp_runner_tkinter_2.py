import tkinter as tk

root = tk.Tk()
canvas = tk.Canvas(root, width=200, height=200)
canvas.pack()

test_cases = [
    ("list_of_empty_tuples", [(), (), (), (), (), ()]),
    ("list_of_empty_lists", [[], [], [], [], [], []]),
    ("tuple_of_empty_tuples", ((), (), (), (), (), ())),
    ("none_elements", [None, None, None, None, None, None])
]

for name, points in test_cases:
    if points and len(points) >= 6:
        try:
            canvas.create_polygon(points, outline="red", fill="")
            print(f"{name}: SUCCESS")
        except Exception as e:
            print(f"{name}: FAILED with {type(e).__name__}: {e}")

root.destroy()
