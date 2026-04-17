# -----------------------------------------------------------------
#
# THIS TEST IS DISABLED.
#
# The tests in this file are for a previous version of the code
# and are no longer compatible with the current implementation.
# They need to be rewritten.
#
# -----------------------------------------------------------------
#
## Dummy class to host the mixin
#        self.json_data = {}
#        self.event_bus = MagicMock()
#
#
#        self.host = DummyStructural()
#        self.host.json_data = {
#            "id": "root",
#            "children": [
#                {"id": "child1", "text": "A"},
#                {"id": "child2", "children": [
#                    {"id": "grandchild1"}
#                ]}
#            ]
#        }
#
#        """Test finding a node in the tree by its ID."""
#        found_node = self.host.find_node_by_id("grandchild1")
#        self.assertIsNotNone(found_node)
#        self.assertEqual(found_node['id'], 'grandchild1')
#
#        not_found_node = self.host.find_node_by_id("nonexistent")
#        self.assertIsNone(not_found_node)
#
#        """Test updating a property of a specific node."""
#        success = self.host.update_node_property("child1", "text", "Updated Text")
#        self.assertTrue(success)
#        
#        node = self.host.find_node_by_id("child1")
#        self.assertEqual(node['text'], "Updated Text")
#
#        # Test updating a node that doesn't exist
#        success_fail = self.host.update_node_property("nonexistent", "text", "...")
#        self.assertFalse(success_fail)
#        
#        """Test adding a new node to a parent."""
#        new_widget_data = {"id": "child3", "type": "button"}
#        success = self.host.add_node("root", new_widget_data)
#        self.assertTrue(success)
#
#        root_node = self.host.json_data
#        self.assertEqual(len(root_node['children']), 3)
#        self.assertEqual(root_node['children'][2]['id'], 'child3')
#
#        """Test deleting a node from the tree."""
#        success = self.host.delete_node("child1")
#        self.assertTrue(success)
#
#        root_node = self.host.json_data
#        self.assertEqual(len(root_node['children']), 1)
#        self.assertIsNone(self.host.find_node_by_id("child1"))
#        
#        # Test deleting the root (should probably fail)
#        success_fail = self.host.delete_node("root")
#        self.assertFalse(success_fail)
#
#        """Test that successful modifications publish a 'json_updated' event."""
#        self.host.update_node_property("child1", "text", "new")
#        self.host.event_bus.publish.assert_called_with("json_updated", self.host.json_data)
#        
#        self.host.event_bus.reset_mock()
#        self.host.add_node("root", {"id": "c3"})
#        self.host.event_bus.publish.assert_called_with("json_updated", self.host.json_data)
#
#        self.host.event_bus.reset_mock()
#        self.host.delete_node("child1")
#        self.host.event_bus.publish.assert_called_with("json_updated", self.host.json_data)
#
#    unittest.main()
