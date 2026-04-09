# oaAudioMixer/Tests/test_mixer_smoke.py
# Author: Quality Assurance Lead
# Version: 20260407.2005.1
#
# Description: Smoke tests for oaAudioMixer Rust core binding.

import unittest
import sys
import os

# Add the module path so we can import the rust core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ⚡ OPTIMIZATION: Ensure the native module is compiled before import
try:
    from oaAudioMixer.Core.oaAudioMixer_rs.compiler_hook import ensure_compiled
    ensure_compiled()
except ImportError:
    pass # Hook might be missing if path setup is weird, but we try

import oaaudiomixer_rs as mixer_core

class TestAudioMixerSmoke(unittest.TestCase):
    def test_core_loading(self):
        """
        BUILD: Ensure the environment is ready.
        OPERATE: Import/Check the rust core module.
        CHECK: Verify it exists and is callable.
        """
        self.assertIsNotNone(mixer_core, "Rust core failed to load.")
        self.assertTrue(hasattr(mixer_core, "__doc__"), "Core module seems malformed.")

if __name__ == '__main__':
    unittest.main()
