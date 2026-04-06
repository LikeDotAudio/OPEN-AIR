# Core/knob_renderer_mixin.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import math
from .knob_renderer import draw_knob_visuals

class KnobRendererMixin:
    """
    Handles the modular rendering pipeline for the Rotary Knob.
    Delegates the heavy lifting to the standalone knob_renderer.
    """

    def _draw_visuals(self):
        """Modular rendering pipeline. Accesses state via self."""
        if not self.winfo_exists(): return
        
        # ⚡ Standardized Redraw: Clear and draw via the standalone engine
        draw_knob_visuals(
            canvas=self,
            state=self.state,
            config=self.widget_config,
            value=self.variable.get(),
            label_text=getattr(self, 'label_text', None)
        )