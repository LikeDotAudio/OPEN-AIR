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
#        self.canvas = MagicMock(spec=tk.Canvas)
#        self.overlay = SelectionOverlay(self.canvas)
#
#        """Test drawing a highlight around a selected widget."""
#        selected_widget_info = {
#            "id": "w1",
#            "bbox": (10, 20, 110, 70)
#        }
#
#        self.overlay.draw(selected_widget_info)
#
#        self.canvas.create_rectangle.assert_called_once_with(
#            10, 20, 110, 70,
#            tags='selection_highlight',
#            outline='red',
#            width=2
#        )
#
#        self.overlay.clear()
#        self.canvas.delete.assert_called_once_with('selection_highlight')
#
#    unittest.main()
