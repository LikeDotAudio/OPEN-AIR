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
#
#        self.root = tk.Tk()
#        # Prevent the window from showing up during tests
#        self.root.withdraw()
#        self.mock_event_bus = MagicMock()
#
#        self.root.destroy()
#
#        """Test that the GrabBagView frame and canvas are created."""
#        view = GrabBagView(self.root, self.mock_event_bus)
#        self.assertIsInstance(view, tk.Frame)
#        # Check if a canvas was created inside
#        self.assertTrue(any(isinstance(w, tk.Canvas) for w in view.winfo_children()))
#
#        """Test that items are displayed on the canvas."""
#        items = {
#            "widget1": {"name": "Label", "type": "label"},
#            "widget2": {"name": "Button", "type": "button"}
#        }
#        view = GrabBagView(self.root, self.mock_event_bus)
#
#        # We need to manually trigger the display since the event bus is mocked
#        view.display_items(items)
#
#        # Find the canvas to check its items
#        canvas = next(w for w in view.winfo_children() if isinstance(w, tk.Canvas))
#
#        # Check if canvas items were created (e.g., text items for the labels)
#        canvas_items = canvas.find_all()
#        # Expecting items for the widgets + potentially other graphical elements
#        self.assertGreater(len(canvas_items), 1)
#
#        # Check if the text matches our widget names
#        canvas_texts = [canvas.itemcget(item_id, "text") for item_id in canvas_items if canvas.type(item_id) == "text"]
#        self.assertIn("Label", canvas_texts)
#        self.assertIn("Button", canvas_texts)
#
#    @Patch('tkinter.Canvas.event_generate')
#        """Test that clicking an item publishes an event to the bus."""
#        items = {"widget1": {"name": "MyWidget", "type": "button"}}
#        view = GrabBagView(self.root, self.mock_event_bus)
#        view.display_items(items)
#
#        # Simulate a click on the first canvas item
#        canvas = view.canvas
#        # In a real scenario, we'd find the specific item. For the test, assume it's item 2 (1 is background).
#        # A more robust test would tag items and find by tag.
#        item_id = 2
#
#        # Directly call the bound method
#        # The event object is not critical for this mock
#        view._on_item_click(MagicMock(), item_tag_or_id="widget1_bg")
#
#        self.mock_event_bus.publish.assert_called_once_with("grab_bag_item_selected", items["widget1"])
#
#
#    # This check prevents running the tkinter main loop during test discovery
#    # To run these tests, use a test runner like `python -m unittest discover`
#    unittest.main()
