# oaGuiManager/Tests/test_schema_defaults.py
# Author: Gemini CLI
# Version: 20260404.1.0
#
# Description: Unit tests for schema_defaults.py

import unittest

from oaGuiManager.Constants.schema_defaults import (
    ANCHOR_MAP,
    DEFAULT_COLORS,
    LEXICON,
    PILLARS,
    STRUCT_TYPES,
)


class TestSchemaDefaults(unittest.TestCase):
    """Verifies that foundational UI schema constants are correctly defined."""

    def test_lexicon_mapping(self):
        """CHECK: Verify that short-hand keys map to correct internal property names."""
        self.assertEqual(LEXICON["lbl"], "label")
        self.assertEqual(LEXICON["bg"], "bg_color")
        self.assertEqual(LEXICON["fg"], "text_color")

    def test_structural_types(self):
        """CHECK: Verify that transparency-defaulting types are listed."""
        self.assertIn("OcaBlock", STRUCT_TYPES)
        self.assertIn("Array", STRUCT_TYPES)

    def test_anchor_map(self):
        """CHECK: Verify that semantic anchors map to Tkinter compass points."""
        self.assertEqual(ANCHOR_MAP["top"], "n")
        self.assertEqual(ANCHOR_MAP["bottom"], "s")

    def test_default_colors(self):
        """CHECK: Verify that industry standard colors are present."""
        self.assertEqual(DEFAULT_COLORS["active_accent"], "#FF9900")
        self.assertEqual(DEFAULT_COLORS["panel_bg"], "#2b2b2b")

    def test_pillars(self):
        """CHECK: Verify the 5 pillars of the Universal Rhyme schema."""
        self.assertEqual(len(PILLARS), 5)
        self.assertIn("identity", PILLARS)
        self.assertIn("cosmetics", PILLARS)

if __name__ == '__main__':
    unittest.main()
