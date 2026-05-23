# oaGuiElements/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260503.1545.1
#
# Description: Gatekeeper for the oaGuiElements module.

import sys
from pathlib import Path

# Standard project_root resolution
current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- Public API Exports ---

# Generators & Utilities
from oaGuiElements.Core.buttons.button_toggle.Core.button_toggle import BuilderButtonToggleCreator
from oaGuiElements.Core.buttons.button_toggler.Core.button_toggler import BuilderButtonTogglerCreator
from oaGuiElements.Core.buttons.button_wink.Core.button_wink import BuilderButtonWinkCreator
from oaGuiElements.Core.faders.fader.Core.fader import BuilderFaderCreator
from oaGuiElements.Core.faders.fader_bar_graph.Core.fader_bar_graph import BuilderFaderBarGraphCreator
from oaGuiElements.Core.faders.fader_horizontal.Core.fader_horizontal import BuilderFaderHorizontalCreator
from oaGuiElements.Core.input.checkbox.Core.checkbox import BuilderCheckboxCreator
from oaGuiElements.Core.input.composite_horizontal_dial_value.Core.composite_horizontal_dial_value import (
    BuilderCompositeHorizontalDialValueCreator,
)
from oaGuiElements.Core.input.json_tree.Core.json_tree import BuilderDataJsonTreeCreator
from oaGuiElements.Core.input.listbox.Core.listbox import BuilderListboxCreator
from oaGuiElements.Core.input.slider_value.Core.slider_value import BuilderSliderValueCreator

# Widget Creators (Core)
from oaGuiElements.Core.Knobs.knob.Core.knob import BuilderKnobCreator
from oaGuiElements.Core.metering.meter_bar.Core.meter_bar import BuilderMeterBarCreator
from oaGuiElements.Core.metering.meter_needle.Core.meter_needle import BuilderMeterNeedleCreator
from oaGuiElements.Core.panels.panel_creator import BuilderPanelCreator
from oaGuiElements.Core.panels.panel_generator import PanelGenerator
from oaGuiElements.Core.panels.panel_screw.screw_generator import ScrewGenerator
from oaGuiElements.Core.panels.tiled_panel_generator import TiledPanelGenerator
from oaGuiElements.Core.special.circular_motion_displacement_potentiometer.Core.circular_motion_displacement_potentiometer import (
    BuilderCircularMotionDisplacementPotentiometerCreator,
)
from oaGuiElements.Core.special.composite_mdp.Core.composite_mdp import BuilderCompositeMdpCreator
from oaGuiElements.Core.special.status_light.Core.status_light import BuilderStatusLightCreator
from oaGuiElements.Core.text.text_label.text_label import BuilderTextLabelCreator
from oaGuiElements.Core.text.text_table.Core.text_table import BuilderTextTableCreator
from oaGuiElements.Methods.utils import PanelUtils


# Module Interface methods
def start():
    """Initializes the GUI Elements module."""
    print("🎨 [GUI_ELEMENTS] Module Started.")

def stop():
    """Shuts down the GUI Elements module."""
    print("🎨 [GUI_ELEMENTS] Module Stopped.")

def status():
    """Returns the status of the GUI Elements module."""
    return "Running"

def run_tests():
    """Runs the module's unit tests."""
    import pytest
    test_path = current_dir / "Tests"
    pytest.main([str(test_path)])

# Standalone execution
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "start": start()
        elif cmd == "stop": stop()
        elif cmd == "status": print(status())
        elif cmd == "test": run_tests()
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default standalone action if no args
        start()

# Standardized exports
__all__ = [
    "start",
    "stop",
    "status",
    "run_tests",
    "PanelGenerator",
    "TiledPanelGenerator",
    "BuilderPanelCreator",
    "ScrewGenerator",
    "PanelUtils",
    "BuilderKnobCreator",
    "BuilderFaderCreator",
    "BuilderFaderHorizontalCreator",
    "BuilderFaderBarGraphCreator",
    "BuilderMeterNeedleCreator",
    "BuilderMeterBarCreator",
    "BuilderButtonWinkCreator",
    "BuilderButtonToggleCreator",
    "BuilderButtonTogglerCreator",
    "BuilderTextLabelCreator",
    "BuilderTextTableCreator",
    "BuilderCheckboxCreator",
    "BuilderListboxCreator",
    "BuilderSliderValueCreator",
    "BuilderDataJsonTreeCreator",
    "BuilderCompositeHorizontalDialValueCreator",
    "BuilderCircularMotionDisplacementPotentiometerCreator",
    "BuilderCompositeMdpCreator",
    "BuilderStatusLightCreator"
]
