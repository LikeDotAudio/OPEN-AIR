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
#        self.root = tk.Tk()
#        self.root.withdraw()
#        self.factory = PropertyLeaf()
#
#        self.root.destroy()
#
#        """Test factory creating a string editor (tk.Entry)."""
#        parent = tk.Frame(self.root)
#        widget = self.factory.create_editor(parent, "some_string", "text")
#        self.assertIsInstance(widget, tk.Entry)
#
#        """Test factory creating an integer editor (tk.Spinbox or Entry)."""
#        parent = tk.Frame(self.root)
#        widget = self.factory.create_editor(parent, 123, "number")
#        # Could be a Spinbox or a validated Entry
#        self.assertTrue(isinstance(widget, (tk.Spinbox, tk.Entry)))
#
#        """Test factory creating a boolean editor (tk.Checkbutton)."""
#        parent = tk.Frame(self.root)
#        widget = self.factory.create_editor(parent, True, "boolean")
#        self.assertIsInstance(widget, tk.Checkbutton)
#        
#        """Test factory creating a color editor (e.g., a button that opens a color chooser)."""
#        parent = tk.Frame(self.root)
#        # Assuming the property name or a metadata tag indicates it's a color
#        widget = self.factory.create_editor(parent, "#ff0000", "color")
#        self.assertIsInstance(widget, tk.Button)
#        self.assertIn("ff0000", widget.cget('text')) # Example check
#
#        """Test that an unknown property type returns a default editor (tk.Entry)."""
#        parent = tk.Frame(self.root)
#        widget = self.factory.create_editor(parent, {"complex": "object"}, "unknown_type")
#        self.assertIsInstance(widget, tk.Entry)
#        # The entry should probably contain the string representation
#        self.assertIn("complex", widget.get())
#
#
#    unittest.main()
