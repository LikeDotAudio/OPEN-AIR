# oaAudioMixer/Tests/test_mixer_smoke.py
# Author: Quality Assurance Lead
# Version: 20260407.2005.1
#
# Description: Smoke tests for oaAudioMixer Rust core binding.

import os
import sys
import unittest

# Add the module path so we can import the rust core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from oaRustCore import oa_audio_mixer_rs as oaaudiomixer_rs


class TestAudioMixerSmoke(unittest.TestCase):
    def test_core_loading(self):
        """
        BUILD: Ensure the environment is ready.
        OPERATE: Import/Check the rust core module.
        CHECK: Verify it exists and is callable.
        """
        self.assertIsNotNone(oaaudiomixer_rs, "Rust core failed to load.")
        self.assertTrue(hasattr(oaaudiomixer_rs, "__doc__"), "Core module seems malformed.")

if __name__ == '__main__':
    unittest.main()
