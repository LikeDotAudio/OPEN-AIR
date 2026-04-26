# -----------------------------------------------------------------
#
# THIS TEST IS DISABLED.
#
# The tests in this file are for a previous version of the code
# and are no longer compatible with the current implementation.
# They need to be rewritten.
#
# -----------------------------------------------------------------
#
## Create a dummy class that uses the mixin for testing
#        tk.Frame.__init__(self, parent)
#        # The mixin might expect certain instance attributes
#        self.canvas = tk.Canvas(self)
#        self.canvas.pack()
#        self.event_bus = MagicMock()
#
#
#        self.root = tk.Tk()
#        self.root.withdraw()
#        self.host = DummyHost(self.root)
#
#        self.root.destroy()
#
#        """Test the drawing of a grid overlay on the canvas."""
#        # The mixin adds methods to the host class
#        self.host.draw_grid_overlay(10, 10, 20, 20)
#
#        # Check that lines were drawn on the canvas
#        # The number of items will depend on the implementation
#        self.assertGreater(len(self.host.canvas.find_all()), 0)
#        # A more specific test would check for 'line' items
#        line_items = self.host.canvas.find_withtag("grid_line")
#        self.assertGreater(len(line_items), 0)
#
#        """Test drawing a selection rectangle."""
#        self.host.draw_selection_rectangle(5, 5, 25, 25)
#
#        rect_items = self.host.canvas.find_withtag("selection_rectangle")
#        self.assertEqual(len(rect_items), 1)
#
#        # Check coordinates
#        coords = self.host.canvas.coords(rect_items[0])
#        self.assertEqual(coords, [5.0, 5.0, 25.0, 25.0])
#
#        """Test that overlays can be cleared from the canvas."""
#        self.host.draw_grid_overlay(10, 10, 20, 20)
#        self.host.draw_selection_rectangle(5, 5, 25, 25)
#
#        # Clear a specific tag
#        self.host.clear_overlay("grid_line")
#        self.assertEqual(len(self.host.canvas.find_withtag("grid_line")), 0)
#        self.assertGreater(len(self.host.canvas.find_withtag("selection_rectangle")), 0)
#
#        # Clear another tag
#        self.host.clear_overlay("selection_rectangle")
#        self.assertEqual(len(self.host.canvas.find_all()), 0)
#
#
#    unittest.main()
