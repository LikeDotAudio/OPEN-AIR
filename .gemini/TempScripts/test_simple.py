import unittest
from unittest.mock import MagicMock
from oaTranslator.Core.state_mirror_engine import StateMirrorEngine

class TestSimple(unittest.TestCase):
    def setUp(self):
        self.root = MagicMock()
        self.engine = StateMirrorEngine("BASE", None, self.root, None)
        
    def test_calculate_topic(self):
        self.assertEqual(self.engine.calculate_topic("v", "T"), "BASE/T/v")

if __name__ == "__main__":
    unittest.main()
