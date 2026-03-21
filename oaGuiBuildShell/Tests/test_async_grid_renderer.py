import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiBuildShell.Workers.async_grid_renderer import AsyncGridRenderer

class TestAsyncGridRenderer(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        self.parent = tk.Frame(self.root)
        
        # Mock the builder and its factory
        self.builder = MagicMock()
        self.builder.widget_factory = MagicMock()
        
        self.renderer = AsyncGridRenderer(builder_instance=self.builder)

    def test_render_initialization(self):
        """Goal: Verify that AsyncGridRenderer initializes with a builder and batch engine."""
        self.assertEqual(self.renderer.builder, self.builder)
        self.assertIsNotNone(self.renderer.batch_engine)

    def test_render_functional_widget_trigger(self):
        """Goal: Verify that functional widgets are passed to the batch engine."""
        data = {
            "test_btn": {
                "type": "Actuator",
                "geometry": {"row": 0, "col": 0}
            }
        }
        
        # Patch the batch processing engine's process method
        with patch.object(self.renderer.batch_engine, "process") as mock_process:
            self.renderer.render(self.parent, data)
            # Verify process was called
            self.assertTrue(mock_process.called)

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
