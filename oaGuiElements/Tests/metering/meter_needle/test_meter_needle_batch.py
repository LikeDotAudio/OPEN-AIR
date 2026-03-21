import unittest
import json
import os
import tkinter as tk
from unittest.mock import MagicMock, patch
from oaGuiElements.Core.metering.meter_needle.meter_needle import BuilderMeterNeedleCreator

class TestMeterNeedleBatch(unittest.TestCase):
    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.root.cget.return_value = '#2b2b2b'
            
            # Patch variables and widgets
            self.patchers.append(patch('tkinter.DoubleVar', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Canvas', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Frame', return_value=MagicMock()))
            
            for p in self.patchers:
                p.start()

        # Load the composite test JSON
        json_path = os.path.join(os.path.dirname(__file__), 'composite_needle_test_20.json')
        with open(json_path, 'r') as f:
            self.full_data = json.load(f)
        
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.builder_instance = MagicMock()

    def test_batch_creation(self):
        """Goal: Verify all 20 meter variations in the composite JSON can be built."""
        creator = BuilderMeterNeedleCreator()
        
        # Traverse the OcaBin structure to get the fields
        blocks = self.full_data.get("Composite_Needle_Test_20", {}).get("blocks", {})
        test_block = blocks.get("Test_Block", {})
        fields = test_block.get("fields", {})
        
        self.assertEqual(len(fields), 20, f"Expected 20 fields, found {len(fields)}")
        
        for key, config_data in fields.items():
            try:
                # Add a path if missing
                if 'path' not in config_data:
                    config_data['path'] = f"test/needle/{key}"
                
                meter_frame = creator.make_meter_needle(
                    parent_widget=self.root, 
                    config_data=config_data, 
                    context=self.context
                )
                
                self.assertIsNotNone(meter_frame, f"Failed to create meter for {key}")
                # logger.success(f"Successfully built meter: {key}")
            except Exception as e:
                self.fail(f"Meter creation failed for '{key}' with error: {str(e)}")

    def tearDown(self):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self.root, 'destroy') and not isinstance(self.root, MagicMock):
            self.root.destroy()

if __name__ == '__main__':
    unittest.main()
