import unittest
from unittest.mock import patch, MagicMock
from oaThreadManager.Workers.launcher import launch_core_managers

# To prevent the logger from trying to write files during tests
@patch('loguru.logger.add')
class TestLauncher(unittest.TestCase):

    # Patch all the external dependencies imported by the launcher
    @patch('oaThreadManager.Workers.launcher.MqttConnectionManager')
    @patch('oaThreadManager.Workers.launcher.MqttSubscriberRouter')
    @patch('oaThreadManager.Workers.launcher.MqttManager')
    @patch('oaThreadManager.Workers.launcher.ProtocolRouter')
    @patch('oaThreadManager.Workers.launcher.Config')
    @patch('oaThreadManager.Workers.launcher.initialize_filter_engine')
    @patch('oaThreadManager.Workers.launcher.importlib')
    def test_launch_core_managers_structure(self, mock_importlib, mock_init_filter,
                                          mock_config, mock_proto_router, mock_mqtt_manager,
                                          mock_sub_router, mock_conn_manager, mock_logger_add):
        """
        Test the overall structure and return value of launch_core_managers.
        """
        # --- BUILD ---
        # Configure mocks to return other mocks
        mock_conn_manager_inst = MagicMock()
        mock_sub_router_inst = MagicMock()
        
        # Mock the dynamic imports for protocol managers
        mock_midi_module = MagicMock()
        mock_importlib.import_module.return_value = mock_midi_module
        mock_importlib.util.find_spec.return_value = True

        # Mock the app constants that control dynamic loading
        mock_config.get_instance.return_value.SCAN_SNMP = False

        # --- OPERATE ---
        managers = launch_core_managers(mock_conn_manager_inst, mock_sub_router_inst)

        # --- CHECK ---
        # 1. Check if it returns a dictionary
        self.assertIsInstance(managers, dict)
        
        # 2. Check for the presence of key manager instances
        self.assertIn("mqtt_connection_manager", managers)
        self.assertIn("subscriber_router", managers)
        self.assertIn("protocol_router", managers)
        self.assertIn("mqtt_manager", managers)
        
        # 3. Check that core components were initialized
        mock_sub_router.assert_called_once()
        mock_proto_router.get_instance.assert_called_once()
        
        # 4. Check if linking phase happened
        mock_proto_router.get_instance.return_value.set_mqtt_manager.assert_called_once()
        
        # 5. Check if start phase was attempted
        mock_proto_router.get_instance.return_value.start.assert_called_once()

    @patch('oaThreadManager.Workers.launcher.MqttConnectionManager')
    @patch('oaThreadManager.Workers.launcher.MqttSubscriberRouter')
    @patch('oaThreadManager.Workers.launcher.MqttManager')
    @patch('oaThreadManager.Workers.launcher.ProtocolRouter')
    @patch('oaThreadManager.Workers.launcher.initialize_filter_engine')
    @patch('oaThreadManager.Workers.launcher.Config')
    @patch('oaThreadManager.Workers.launcher.importlib')
    def test_dynamic_snmp_loading(self, mock_importlib, mock_config, mock_init_filter,
                                mock_proto_router, mock_mqtt_manager, mock_sub_router,
                                mock_conn_manager, mock_logger_add):
        """Test that the SNMP manager is loaded when the config flag is True."""
        mock_config.get_instance.return_value.SCAN_SNMP = True
        
        # Ensure ProtocolRouter mock works as expected
        mock_proto_router.get_instance.return_value = MagicMock()
        
        mock_snmp_module = MagicMock()
        mock_snmp_manager_inst = MagicMock()
        
        # The launcher calls getattr(module, class_name)(**kwargs)
        # class_name is "get_manager" which returns the manager instance
        mock_snmp_module.get_manager.return_value = mock_snmp_manager_inst
        
        # This setup is complex because of the dynamic import logic
        # We need to mock both find_spec and import_module to simulate module presence
        def import_side_effect(module_path):
            if "oaComProtocols.oaComSNMP" in module_path:
                return mock_snmp_module
            return MagicMock() # Return a generic mock for other imports
            
        mock_importlib.import_module.side_effect = import_side_effect
        mock_importlib.util.find_spec.return_value = True
        
        managers = launch_core_managers(MagicMock(), MagicMock())
        
        # Check that the SNMP manager was instantiated and started
        mock_snmp_module.get_manager.assert_called()
        mock_snmp_manager_inst.start.assert_called_once()
        self.assertIsNotNone(managers['snmp_manager'])


if __name__ == '__main__':
    unittest.main()
