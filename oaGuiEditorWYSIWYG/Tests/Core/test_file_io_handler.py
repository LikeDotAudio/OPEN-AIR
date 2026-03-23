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
#        self.handler = FileIOHandler()
#
#    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
#        data = self.handler.read_json("dummy_path.json")
#        self.assertEqual(data, {"key": "value"})
#        mock_file.assert_called_once_with("dummy_path.json", 'r')
#
#    @patch("builtins.open", new_callable=mock_open)
#        data_to_write = {"key": "new_value"}
#        self.handler.write_json("dummy_path.json", data_to_write)
#        mock_file.assert_called_once_with("dummy_path.json", 'w')
#        # Extracting the call arguments from the mock
#        handle = mock_file()
#        written_data = handle.write.call_args[0][0]
#        self.assertEqual(json.loads(written_data), data_to_write)
#
#    @patch("builtins.open", side_effect=FileNotFoundError)
#            self.handler.read_json("non_existent.json")
#
#    @patch("builtins.open", side_effect=IOError)
#            self.handler.write_json("unwritable.json", {})
#
#    unittest.main()
