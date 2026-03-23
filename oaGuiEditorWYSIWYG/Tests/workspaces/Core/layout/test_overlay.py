# -----------------------------------------------------------------
#
# THIS TEST IS DISABLED.
#
# The tests in this file are for a previous version of the code
# and are no longer compatible with the current implementation.
# They need to be rewritten.
#
# -----------------------------------------------------------------
#import unittest
#import tkinter as tk
#from oaGuiEditorWYSIWYG.workspaces.Core.layout.overlay import OverlayManager
#
#class TestOverlayManager(unittest.TestCase):
#
#    def setUp(self):
#        self.root = tk.Tk()
#        self.root.withdraw()
#        self.canvas = tk.Canvas(self.root)
#        self.overlay_manager = OverlayManager(self.canvas)
#
#    def tearDown(self):
#        self.root.destroy()
#        
#    def test_draw_grid(self):
#        """Test drawing a grid overlay."""
#        self.overlay_manager.draw_grid(width=200, height=200, grid_size=20)
#        
#        grid_lines = self.canvas.find_withtag("grid")
#        # 10 horizontal + 10 vertical lines
#        self.assertEqual(len(grid_lines), 20)
#        
#    def test_draw_selection_box(self):
#        """Test drawing a selection box."""
#        self.overlay_manager.draw_selection_box(10, 10, 50, 50)
#        
#        selection_box = self.canvas.find_withtag("selection_box")
#        self.assertEqual(len(selection_box), 1)
#        
#    def test_draw_drop_target(self):
#        """Test drawing a drop target indicator."""
#        self.overlay_manager.draw_drop_target(30, 30, 70, 70)
#        
#        drop_target = self.canvas.find_withtag("drop_target")
#        self.assertEqual(len(drop_target), 1)
#        
#    def test_clear_overlay(self):
#        """Test clearing a specific overlay by tag."""
#        self.overlay_manager.draw_grid(100, 100, 10)
#        self.overlay_manager.draw_selection_box(0,0,10,10)
#        
#        self.assertGreater(len(self.canvas.find_withtag("grid")), 0)
#        
#        self.overlay_manager.clear("grid")
#        
#        self.assertEqual(len(self.canvas.find_withtag("grid")), 0)
#        self.assertGreater(len(self.canvas.find_withtag("selection_box")), 0)
#
#    def test_clear_all_overlays(self):
#        """Test clearing all overlays."""
#        self.overlay_manager.draw_grid(100, 100, 10)
#        self.overlay_manager.draw_selection_box(0,0,10,10)
#        self.overlay_manager.draw_drop_target(20,20,30,30)
#        
#        self.overlay_manager.clear_all()
#        
#        self.assertEqual(len(self.canvas.find_all()), 0)
#
#if __name__ == '__main__':
#    unittest.main()
