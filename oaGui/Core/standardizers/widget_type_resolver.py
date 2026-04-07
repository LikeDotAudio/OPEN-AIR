# standardizers/widget_type_resolver.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

class WidgetTypeResolver:
    """
    Maps "Smart" and aliased widget types to concrete implementations.
    """
    TYPE_MAP = {
        "_SmartMeter": ("cosmetics", "style_flags", "visualization", "bar"),
        "_SmartKnob": "_Knob",
        "_SmartFader": "ORIENTATION_DEPENDENT",
        "_DataGraph": "plot_widget",
        "_SmartGraph": "plot_widget",
        "_Plot": "plot_widget",
        "_GuiGraph": "plot_widget",
        "_SmartVUKnob": "_VUMeterKnob",
        "_BarGraphKnob": "_VUMeterKnob",
        "_VUMeterKnobKnob": "_VUMeterKnob",
        "_SmartToggle": "_GuiButtonToggle",
        "_SmartToggler": "_GuiButtonToggler",
        "_SmartCheckbox": "_GuiCheckbox",
        "_GuiActuator": "_GuiActuator",
        "_SmartActuator": "_GuiActuator",
        "_ButtonActuator": "_GuiActuator",
        "_Value": "_Value",
        "_SmartValue": "_Value",
        "_ValueBox": "_Value",
        "_GuiValue": "_Value",
        "OcaTable": "OcaTable",
        "GuiTable": "OcaTable",
        "DynamicGuiTable": "OcaTable",
        "_Table": "OcaTable",
        "Block": "OcaBlock",
        "_SmartIncDec": "_IncDecButtons",
        "_SmartNav": "_DirectionalButtons",
        "_SmartList": "_GuiListbox",
        "_SmartInput": "_TextInput",
        "_SmartLabel": "_Label",
        "_SmartLink": "_WebLink",
        "_SmartProgress": "_ProgressBar",
        "_SmartImage": "_ImageDisplay",
        "_SmartAnimation": "_AnimationDisplay",
        "_SmartLight": "_HeaderStatusLight"
    }

    @classmethod
    def resolve_type(cls, config, orientation="vertical"):
        """
        Detects the implementation type based on aliases and context.
        """
        widget_type = config.get("type") or config.get("widget_type", "")
        
        if widget_type == "_SmartMeter":
            cosmetics = config.get("cosmetics", {})
            viz = cosmetics.get("style_flags", {}).get("visualization", "bar").lower()
            return "_NeedleVUMeter" if viz == "needle" else "_BarGraph"
            
        if widget_type == "_SmartFader":
            return "_CustomHorizontalFader" if orientation == "horizontal" else "_CustomFader"
            
        resolved = cls.TYPE_MAP.get(widget_type, widget_type)
        return resolved