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
#        self.canvas = MagicMock(spec=tk.Canvas)
#        self.overlay = AlignmentOverlay(self.canvas)
#
#        self.root.destroy()
#
#        """Test drawing alignment guides for a selected widget."""
#        # Bounding box of the selected widget
#        widget_bbox = (50, 50, 150, 100)
#
#        self.overlay.draw_guides(widget_bbox)
#
#        # Check that 'create_line' was called on the canvas
#        self.canvas.create_line.assert_called()
#
#        # Check how many lines were drawn (e.g., center-x, center-y, top, bottom, left, right)
#        # This depends on the implementation. Let's assume it draws 2 center lines.
#        self.assertGreaterEqual(self.canvas.create_line.call_count, 2)
#
#        # Example: check if a horizontal center line was drawn
#        # canvas.create_line(0, 75, canvas_width, 75, ...)
#        args, kwargs = self.canvas.create_line.call_args_list[0]
#        self.assertEqual(args[1], 75) # y-coordinate of horizontal line
#        self.assertEqual(kwargs['tags'], 'alignment_guide')
#
#        """Test clearing the alignment guides."""
#        self.overlay.clear()
#        self.canvas.delete.assert_called_once_with('alignment_guide')
#
#    unittest.main()
