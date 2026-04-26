# oaGuiEditorWYSIWYG/Tests/Managers/test_wysiwyg_editor.py
# Author: Gemini (Collaborator)
# Version: 20260322.1430.1
#
# Description: Unit tests for WYSIWYG editor interactions with event_bus and state_manager,
# focusing on granular updates vs. global rebuild events.

import unittest
from unittest.mock import MagicMock

# Placeholder for actual imports if classes were available in the project.
# For testing purposes, we'll use mocks and a dummy editor class.
# from oaGuiEditorWYSIWYG.Managers.event_bus import EventBus
# from oaGuiEditorWYSIWYG.Managers.state_manager import StateManager
# from oaGuiEditorWYSIWYG.Managers.wysiwyg_editor import WYSIWYGEditor

class TestWYSIWYGEditorInteractions(unittest.TestCase):
    """
    Tests for interactions between the WYSIWYG editor, event bus, and state manager,
    specifically focusing on distinguishing granular updates from global rebuild triggers.
    """

    def setUp(self):
        """Set up mock dependencies for tests."""
        self.mock_event_bus = MagicMock()
        self.mock_state_manager = MagicMock()
        self.global_rebuild_event_name = "GLOBAL_REBUILD_REQUIRED" # Assumed event name

        # Dummy editor class simulating the behavior described in the instruction.
        # In a real scenario, this would be the actual WYSIWYGEditor class.
        class DummyEditor:
            def __init__(self, event_bus, state_manager, global_rebuild_event_name):
                self.event_bus = event_bus
                self.state_manager = state_manager
                self.global_rebuild_event_name = global_rebuild_event_name

            def modify_sub_node_color(self, node_id: str, new_color: str):
                """
                Simulates updating a specific node's property (color).
                This operation should NOT trigger a global rebuild.
                """
                print(f"DEBUG: Updating color for node {node_id} to {new_color}") # Example debug log
                self.state_manager.update_node_property(node_id=node_id, property_name="color", value=new_color)
                # No explicit global event emission here.

            def update_global_setting(self, setting_name: str, value: any):
                """
                Simulates updating a global setting.
                This operation SHOULD trigger a global rebuild.
                """
                print(f"DEBUG: Updating global setting {setting_name} to {value}") # Example debug log
                self.state_manager.update_global_property(setting_name=setting_name, value=value)
                self.event_bus.emit(self.global_rebuild_event_name, {"setting": setting_name, "value": value})

        self.editor = DummyEditor(event_bus=self.mock_event_bus, state_manager=self.mock_state_manager, global_rebuild_event_name=self.global_rebuild_event_name)

    def test_sub_node_modification_does_not_trigger_global_rebuild(self):
        """
        Verify that modifying a specific sub-node's property (e.g., color)
        does not result in a global rebuild event being emitted.
        """
        node_id_to_modify = "button_123"
        new_color = "#FF0000" # Example new color

        print("TEST: Starting test_sub_node_modification_does_not_trigger_global_rebuild")
        self.editor.modify_sub_node_color(node_id=node_id_to_modify, new_color=new_color)

        # Assert that the state manager was called to update the specific node property
        self.mock_state_manager.update_node_property.assert_called_once_with(
            node_id=node_id_to_modify,
            property_name="color",
            value=new_color
        )

        # Assert that NO global rebuild event was emitted.
        # We check if 'emit' was called with the specific global rebuild event name.
        # This is a negative assertion.
        for call_args in self.mock_event_bus.emit.call_args_list:
            self.assertNotEqual(call_args[0][0], self.global_rebuild_event_name,
                                "Global rebuild event was emitted unexpectedly.")
        print("TEST: Finished test_sub_node_modification_does_not_trigger_global_rebuild")


    def test_global_setting_modification_triggers_global_rebuild(self):
        """
        Verify that modifying a global setting *does* trigger a global rebuild event.
        This serves as a positive control test.
        """
        setting_name = "canvas_size"
        new_value = {"width": 1920, "height": 1080}

        print("TEST: Starting test_global_setting_modification_triggers_global_rebuild")
        self.editor.update_global_setting(setting_name=setting_name, value=new_value)

        # Assert state manager update for global property
        self.mock_state_manager.update_global_property.assert_called_once_with(
            setting_name=setting_name,
            value=new_value
        )

        # Assert that the global rebuild event was emitted exactly once
        self.mock_event_bus.emit.assert_called_once_with(
            self.global_rebuild_event_name,
            {"setting": setting_name, "value": new_value}
        )
        print("TEST: Finished test_global_setting_modification_triggers_global_rebuild")
