# oaComVisa/Tests/test_visa_manager.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the VisaManagerOrchestrator class.

import unittest
from unittest.mock import MagicMock, patch

from oaComVisa.Managers.visa_manager import VisaManagerOrchestrator

class TestVisaManagerOrchestrator(unittest.TestCase):

    @patch('oaComVisa.Managers.visa_manager.VisaRebootManager')
    @patch('oaComVisa.Managers.visa_manager.VisaResetManager')
    @patch('oaComVisa.Managers.visa_manager.VisaMqttListener')
    @patch('oaComVisa.Managers.visa_manager.VisaDisconnector')
    @patch('oaComVisa.Managers.visa_manager.VisaConnector')
    @patch('oaComVisa.Managers.visa_manager.VisaDeviceSearcher')
    @patch('oaComVisa.Managers.visa_manager.VisaGuiPublisher')
    @patch('oaComVisa.Managers.visa_manager.VisaProxy')
    def test_initialization(self, MockVisaProxy, MockGuiPublisher, MockDeviceSearcher, MockConnector, MockDisconnector, MockMqttListener, MockResetManager, MockRebootManager):
        """
        BUILD: Mock all the dependent classes. Create mock MQTT connection and subscriber router.
        OPERATE: Instantiate VisaManagerOrchestrator.
        CHECK: Verify that all internal managers are instantiated correctly and get_managers returns them.
        """
        mock_mqtt_conn = MagicMock()
        mock_sub_router = MagicMock()

        # Instantiate the orchestrator
        orchestrator = VisaManagerOrchestrator(
            mqtt_connection_manager=mock_mqtt_conn,
            subscriber_router=mock_sub_router
        )

        # Assert that the classes were instantiated with correct arguments
        MockVisaProxy.assert_called_once_with(mqtt_controller=mock_mqtt_conn, subscriber_router=mock_sub_router)
        MockGuiPublisher.assert_called_once_with(mqtt_controller=mock_mqtt_conn)
        MockDeviceSearcher.assert_called_once_with()
        MockConnector.assert_called_once_with(visa_proxy=orchestrator.visa_proxy, gui_publisher=orchestrator.gui_publisher)
        MockDisconnector.assert_called_once_with(visa_proxy=orchestrator.visa_proxy, gui_publisher=orchestrator.gui_publisher)
        MockMqttListener.assert_called_once_with(
            subscriber_router=mock_sub_router,
            searcher=orchestrator.device_searcher,
            connector=orchestrator.connector,
            disconnector=orchestrator.disconnector,
            gui_publisher=orchestrator.gui_publisher
        )
        MockResetManager.assert_called_once_with(
            mqtt_connection_manager=mock_mqtt_conn,
            subscriber_router=mock_sub_router,
            visa_proxy=orchestrator.visa_proxy
        )
        MockRebootManager.assert_called_once_with(
            mqtt_connection_manager=mock_mqtt_conn,
            subscriber_router=mock_sub_router,
            visa_proxy=orchestrator.visa_proxy
        )

        # Check that get_managers returns the expected dictionary
        managers = orchestrator.get_managers()
        self.assertIn("visa_proxy", managers)
        self.assertIn("visa_gui_publisher", managers)
        self.assertIn("visa_device_searcher", managers)
        self.assertIn("visa_connector", managers)
        self.assertIn("visa_disconnector", managers)
        self.assertIn("visa_mqtt_listener", managers)
        self.assertIn("visa_reset_manager", managers)
        self.assertIn("visa_reboot_manager", managers)

        self.assertEqual(managers["visa_proxy"], orchestrator.visa_proxy)

if __name__ == '__main__':
    unittest.main()
