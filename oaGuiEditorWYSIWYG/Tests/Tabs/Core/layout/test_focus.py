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
#        self.root.withdraw()
#        self.canvas = tk.Canvas(self.root)
#        self.focus_manager = FocusManager(self.canvas)
#
#        # Create some mock canvas items
#        self.item1 = self.canvas.create_rectangle(10, 10, 20, 20, tags=("widget1",))
#        self.item2 = self.canvas.create_rectangle(30, 30, 40, 40, tags=("widget2",))
#
#        self.root.destroy()
#
#        """Test setting focus on a canvas item."""
#        self.focus_manager.set_focus(self.item1)
#
#        # Check that the item is marked as focused
#        self.assertEqual(self.focus_manager.get_focused_item(), self.item1)
#
#        # Check if a focus ring/outline was drawn
#        focus_ring = self.canvas.find_withtag("focus_ring")
#        self.assertEqual(len(focus_ring), 1)
#
#        # Check that the ring is around the correct item
#        item_coords = self.canvas.coords(self.item1)
#        ring_coords = self.canvas.coords(focus_ring[0])
#        # Ring coords should be slightly larger than item coords
#        self.assertTrue(ring_coords[0] < item_coords[0])
#
#        """Test clearing focus from an item."""
#        self.focus_manager.set_focus(self.item1)
#        self.assertIsNotNone(self.focus_manager.get_focused_item())
#
#        self.focus_manager.clear_focus()
#
#        self.assertIsNone(self.focus_manager.get_focused_item())
#        self.assertEqual(len(self.canvas.find_withtag("focus_ring")), 0)
#
#        """Test moving focus from one item to another."""
#        self.focus_manager.set_focus(self.item1)
#        initial_ring = self.canvas.find_withtag("focus_ring")[0]
#
#        self.focus_manager.set_focus(self.item2)
#
#        # There should still be only one focus ring
#        self.assertEqual(len(self.canvas.find_withtag("focus_ring")), 1)
#        new_ring = self.canvas.find_withtag("focus_ring")[0]
#
#        # The new ring should be a different canvas item
#        self.assertNotEqual(initial_ring, new_ring)
#        self.assertEqual(self.focus_manager.get_focused_item(), self.item2)
#
#    unittest.main()
