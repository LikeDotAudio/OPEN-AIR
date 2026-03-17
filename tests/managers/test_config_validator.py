import unittest
from managers.configini.config_validator import validate_configuration

class TestConfigValidator(unittest.TestCase):
    def test_validate_configuration(self):
        """Test that validation returns True with a dummy printer."""
        def dummy_printer(msg):
            pass
            
        result = validate_configuration(dummy_printer)
        self.assertTrue(result, "Validation failed unexpectedly")

if __name__ == "__main__":
    unittest.main()
