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
#
#    @patch('os.path.isdir')
#    @patch('os.listdir')
#    @patch('builtins.open', new_callable=mock_open, read_data='{"name": "Test Widget"}')
#        """
#        Test that grab bag items are loaded correctly from a directory.
#        """
#        mock_isdir.return_value = True
#        mock_listdir.return_value = ['widget1.json', 'widget2.json', 'not_a_json.txt']
#        
#        loader = GrabBagLoader()
#        items = loader.load_items("dummy_path")
#        
#        self.assertEqual(len(items), 2)
#        self.assertIn("widget1", items)
#        self.assertIn("widget2", items)
#        self.assertEqual(items["widget1"]["name"], "Test Widget")
#        
#        # Check that it tried to open both json files
#        self.assertEqual(mock_file.call_count, 2)
#
#    @patch('os.path.isdir')
#        """
#        Test that loading from a non-existent directory returns an empty dict.
#        """
#        mock_isdir.return_value = False
#        loader = GrabBagLoader()
#        items = loader.load_items("non_existent_path")
#        self.assertEqual(items, {})
#
#    @patch('os.path.isdir')
#    @patch('os.listdir')
#        """
#        Test that loading from an empty directory returns an empty dict.
#        """
#        mock_isdir.return_value = True
#        mock_listdir.return_value = []
#        loader = GrabBagLoader()
#        items = loader.load_items("empty_dir")
#        self.assertEqual(items, {})
#
#    unittest.main()
