# oaComProtocols.oaComVisa/Tests/test_cli_visa_find.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the main function in cli_visa_find.py.

import unittest
from unittest.mock import MagicMock, patch
import os

from oaComProtocols.oaComVisa.Workers.cli_visa_find import main

class TestCliVisaFind(unittest.TestCase):

    @patch('oaComProtocols.oaComVisa.Workers.cli_visa_find.DiscoveryOrchestrator')
    @patch('os.path.dirname')
    @patch('os.path.abspath')
    def test_main(self, mock_abspath, mock_dirname, MockOrchestrator):
        """
        BUILD: Mock DiscoveryOrchestrator and filesystem tools.
        OPERATE: Call main().
        CHECK: Assert the orchestrator is run, report is printed, and inventory is saved.
        """
        mock_orch = MockOrchestrator.return_value
        mock_abspath.return_value = "/fake/path/cli_visa_find.py"
        mock_dirname.return_value = "/fake/path"
        mock_orch.save_inventory.return_value = "/fake/path/fleet_inventory.json"
        
        # We also need to mock print because it's used heavily in main() and we want to avoid cluttering test output
        with patch('builtins.print'):
            main()
            
            MockOrchestrator.assert_called_once()
            mock_orch.run_discovery.assert_called_once()
            mock_orch.print_report.assert_called_once()
            mock_orch.save_inventory.assert_called_once_with(dir_path="/fake/path")

if __name__ == '__main__':
    unittest.main()
