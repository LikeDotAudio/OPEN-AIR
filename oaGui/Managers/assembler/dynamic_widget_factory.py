# oaGui/Managers/assembler/dynamic_widget_factory.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1001.1
#
# Description: Service for instantiating dynamic widgets using the BatchLayoutEngine.

from loguru import logger
from oaLogging.Methods.matrix_gate import is_debug_allowed
from oaGui.Workers.scheduling.engine_render_scheduler import EngineRenderScheduler
from oaGuiEditorWYSIWYG.Workers.batch_layout_engine import BatchLayoutEngine

def instantiate_dynamic_widgets(assembler_instance, parent_frame, data, path_prefix="", 
                                override_cols=None, on_complete=None, parent_bg_pil=None, context=None):
    """Main entry point for creating dynamic widgets via the batch engine."""
    if context is None:
        from oaGui.Core.context.cache_widget_context import WidgetContext
        context = WidgetContext(
            state_mirror_engine=getattr(assembler_instance, 'state_mirror_engine', None),
            subscriber_router=getattr(assembler_instance, 'subscriber_router', None),
            base_mqtt_topic_from_path=getattr(assembler_instance, 'base_mqtt_topic_from_path', ""),
            app_instance=getattr(assembler_instance, 'app_instance', None),
            builder_instance=assembler_instance
        )

    # ⚡ FACTORY SYNC: Ensure we always have the latest widget creators
    factory = getattr(assembler_instance, 'widget_factory', {})

    if not hasattr(assembler_instance, '_batch_layout_engine'):
        debug = is_debug_allowed(system="UI", element="GUI_BUILDER")
        scheduler = EngineRenderScheduler(assembler_instance, logger, debug)
        assembler_instance._batch_layout_engine = BatchLayoutEngine(factory, scheduler)
    else:
        # Update existing engine's factory reference
        assembler_instance._batch_layout_engine.factory = factory

    assembler_instance._batch_layout_engine.render(
        parent_frame, data, path_prefix, override_cols, on_complete, parent_bg_pil, context
    )
