# oaGuiEditorWYSIWYG/Tests/test_core_components.py
# Author: Gemini
# Version: 20260404.1.0
#
# Description: Unit tests for core GUI components: EventBus, StateManager, and OverlayManager.

import unittest
from unittest.mock import MagicMock, patch

# --- Patch tkinter classes with MagicMock directly ---
# We mock the classes themselves, and also configure their instances (what the class returns) to be MagicMocks
# This allows us to assert on class instantiation (e.g., Canvas was called) and also on instance methods (e.g., canvas.place)
# For tkinter.Frame, we need its mock instance to have winfo_exists etc.
mock_tk_frame_class = MagicMock()
mock_tk_frame_instance = MagicMock()
mock_tk_frame_instance.winfo_exists.return_value = True
mock_tk_frame_instance.winfo_children.return_value = []
mock_tk_frame_class.return_value = mock_tk_frame_instance

mock_tk_label_class = MagicMock()
mock_tk_label_instance = MagicMock()
mock_tk_label_class.return_value = mock_tk_label_instance

mock_tk_canvas_class = MagicMock()
mock_tk_canvas_instance = MagicMock()
mock_tk_canvas_instance.bind.return_value = None # to avoid error for bind.called
mock_tk_canvas_class.return_value = mock_tk_canvas_instance

mock_tk_booleanvar_class = MagicMock(return_value=True)

mock_ttk_entry_class = MagicMock()
mock_ttk_entry_instance = MagicMock()
mock_ttk_entry_instance.insert.return_value = None
mock_ttk_entry_instance.delete.return_value = None
mock_ttk_entry_instance.get.return_value = "mock_value"
mock_ttk_entry_class.return_value = mock_ttk_entry_instance

mock_ttk_button_class = MagicMock()
mock_ttk_checkbutton_class = MagicMock()


with (patch('tkinter.Frame', mock_tk_frame_class),
      patch('tkinter.Label', mock_tk_label_class),
      patch('tkinter.Canvas', mock_tk_canvas_class),
      patch('tkinter.BooleanVar', mock_tk_booleanvar_class),
      patch('tkinter.ttk.Entry', mock_ttk_entry_class),
      patch('tkinter.ttk.Button', mock_ttk_button_class),
      patch('tkinter.ttk.Checkbutton', mock_ttk_checkbutton_class),
      patch('tkinter.ttk', MagicMock()) as MockTtkModule): # Patch the ttk module itself as well



    # Explicitly import patched modules for internal use

    # --- Import modules after patching ---
    from oaComBroker.Core.event_bus import event_bus
    from oaGuiEditorWYSIWYG.Core.state import StateManager
    from oaGuiEditorWYSIWYG.Interface.layout_engine.overlay_manager import OverlayManager


    class TestEventBus(unittest.TestCase):
        def setUp(self):
            event_bus.reset() # Ensure a clean slate for each test

        def test_subscribe_and_publish(self):
            mock_handler = MagicMock()
            event_bus.subscribe("TEST_EVENT", mock_handler)
            event_bus.publish("TEST_EVENT", data="test_data")
            mock_handler.assert_called_once_with(data="test_data")

        def test_unsubscribe(self):
            mock_handler = MagicMock()
            event_bus.subscribe("TEST_EVENT", mock_handler)
            event_bus.unsubscribe("TEST_EVENT", mock_handler)
            event_bus.publish("TEST_EVENT", data="test_data")
            mock_handler.assert_not_called()

        def test_publish_no_subscribers(self):
            mock_handler = MagicMock()
            event_bus.publish("NON_EXISTENT_EVENT", data="test_data")
            mock_handler.assert_not_called()

        def test_multiple_subscribers(self):
            mock_handler1 = MagicMock()
            mock_handler2 = MagicMock()
            event_bus.subscribe("MULTI_EVENT", mock_handler1)
            event_bus.subscribe("MULTI_EVENT", mock_handler2)
            event_bus.publish("MULTI_EVENT", value=123)
            mock_handler1.assert_called_once_with(value=123)
            mock_handler2.assert_called_once_with(value=123)

    class TestStateManager(unittest.TestCase):
        def setUp(self):
            # Ensure _instance exists, then set to None to force re-initialization
            StateManager._instance = None
            self.state_manager = StateManager()
            self.state_manager.initialize({}) # Initialize with empty data

        def test_initialization(self):
            self.assertEqual(self.state_manager.get_state(), {})

        def test_update_state_adds_new_node(self):
            self.state_manager.update_state({"button": {"color": "#FFF"}}, path="elements.button1", source="test")
            expected_state = {"elements": {"button1": {"button": {"color": "#FFF"}}}}
            self.assertEqual(self.state_manager.get_state(), expected_state)

        def test_update_state_modifies_existing_node(self):
            self.state_manager.initialize({"elements": {"button1": {"color": "#FFF"}}})
            self.state_manager.update_state("#000", path="elements.button1.color", source="test")
            expected_state = {"elements": {"button1": {"color": "#000"}}}
            self.assertEqual(self.state_manager.get_state(), expected_state)

        def test_get_state_returns_deep_copy(self):
            initial_state = {"a": {"b": 1}}
            self.state_manager.initialize(initial_state)
            retrieved_state = self.state_manager.get_state()
            self.assertIsNot(initial_state, retrieved_state) # Should be different objects
            self.assertIsNot(initial_state["a"], retrieved_state["a"])
            self.assertEqual(initial_state, retrieved_state)

            # Modify retrieved_state and ensure original state is unaffected
            retrieved_state["a"]["b"] = 2
            self.assertEqual(self.state_manager.get_state()["a"]["b"], 1)

        @patch('oaComBroker.Core.event_bus.event_bus.publish')
        def test_update_state_broadcasts_state_updated(self, mock_publish):
            self.state_manager.update_state({"new": "data"}, path="root", source="test")
            mock_publish.assert_called_once_with("STATE_UPDATED", json_data=self.state_manager.get_state(), source="test")

        @patch('oaComBroker.Core.event_bus.event_bus.publish')
        def test_add_component_request_handler(self, mock_publish):
            mock_component_schema = {"type": "button", "props": {"text": "Hello"}}
            self.state_manager._handle_add_component_request(
                component_name="myButton",
                component_schema=mock_component_schema,
                target_path="elements.container",
                source="test_grab_bag"
            )
            expected_state = {
                "elements": {
                    "container": {
                        "type": "button",
                        "props": {"text": "Hello"}
                    }
                }
            }
            self.assertEqual(self.state_manager.get_state(), expected_state)
            # Ensure STATE_UPDATED was called after the update
            mock_publish.assert_called_with("STATE_UPDATED", json_data=self.state_manager.get_state(), source="test_grab_bag")

    class TestOverlayManager(unittest.TestCase):
        def setUp(self):
            self.mock_workspace = MagicMock()

            # Patch tk.Canvas and tk.Frame within the overlay module
            # (Note: tk and ttk are imported as aliases in overlay.py)
            self.patch_canvas = patch('oaGuiEditorWYSIWYG.Interface.layout_engine.overlay_manager.tk.Canvas', mock_tk_canvas_class)
            self.patch_frame = patch('oaGuiEditorWYSIWYG.Interface.layout_engine.overlay_manager.tk.Frame', mock_tk_frame_class)

            self.mock_canvas = self.patch_canvas.start()
            self.mock_frame = self.patch_frame.start()

            self.overlay_manager = OverlayManager(self.mock_workspace)

        def tearDown(self):
            self.patch_canvas.stop()
            self.patch_frame.stop()

        def test_create_event_blocker(self):
            mock_parent_widget = MagicMock() # Simply a MagicMock
            mock_parent_widget.winfo_width.return_value = 100
            mock_parent_widget.winfo_height.return_value = 100
            self.overlay_manager.create_event_blocker(mock_parent_widget)

            self.assertIsNotNone(self.overlay_manager.event_blocker_canvas)
            self.mock_canvas.assert_called_once_with(mock_parent_widget, highlightthickness=0, bd=0)
            self.overlay_manager.event_blocker_canvas.bind.assert_called()
            self.overlay_manager.event_blocker_canvas.place_forget.assert_called_once()

        def test_show_event_blocker(self):
            mock_parent_widget = MagicMock() # Simply a MagicMock
            mock_parent_widget.winfo_width.return_value = 100
            mock_parent_widget.winfo_height.return_value = 100
            self.overlay_manager.create_event_blocker(mock_parent_widget)
            self.overlay_manager.event_blocker_canvas.reset_mock() # Reset all mocks on event_blocker_canvas after initial hide

            # Ensure the master of the canvas (parent) also returns valid dimensions
            self.overlay_manager.event_blocker_canvas.master.winfo_width.return_value = 100
            self.overlay_manager.event_blocker_canvas.master.winfo_height.return_value = 100

            self.overlay_manager.show_event_blocker(True)
            self.overlay_manager.event_blocker_canvas.place.assert_called_once()
            self.overlay_manager.event_blocker_canvas.place_forget.assert_not_called()

            self.overlay_manager.show_event_blocker(False)
            self.overlay_manager.event_blocker_canvas.place_forget.assert_called_once()
            # place is called once for show(True), and should not be called again for show(False)
            # Check the total calls to place.
            # If we call it once for True and it's not called for False, it should still be 1.
            # So, assert_called_once is correct after the first call.
            # For the second call, we just need to assert that place_forget is called.
            # mock_tk_canvas_instance.place.assert_called_once() # This won't work if place is called again


if __name__ == '__main__':
    unittest.main()
