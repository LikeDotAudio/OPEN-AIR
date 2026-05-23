# oaGui/Workers/rendering/high_res_render_service.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for instantiating fully functional GUI widgets using specialized creators.

def render_functional_widget(parent, widget_data, path, builder, context, logger, debug):
    """Orchestrates the construction of a functional widget via the factory."""
    widget_type = widget_data.get("type", widget_data.get("widget_type"))
    creator = builder.widget_factory.get(widget_type)

    if not creator:
        logger.error(f"❌ Unknown functional widget: '{widget_type}' at {path}")
        return None

    if debug:
        logger.debug(f"  └─ 🔨 Creating '{widget_type}' at '{path}'")

    # Inject path for MQTT/System tracking
    widget_data["path"] = path

    widget = creator(
        parent_widget=parent,
        configuration=widget_data,
        context=context
    )

    if widget:
        widget._oca_path = path
        if hasattr(builder, 'bind_to_widget'):
            builder.bind_to_widget(widget)

    return widget
