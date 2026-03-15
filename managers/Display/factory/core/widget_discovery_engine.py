from loguru import logger
from managers.Display.factory.widget_registry import WidgetRegistry

class WidgetDiscoveryEngine:
    """Handles merging auto-discovered widgets from the Registry into the Factory."""

    @staticmethod
    def merge_registry(factory, builder_instance):
        registry_items = WidgetRegistry._registry
        if not registry_items: return factory

        logger.debug(f"🧩 Merging {len(registry_items)} widgets from Registry into Factory.")
        for widget_type, creator_class in registry_items.items():
            factory[widget_type] = WidgetDiscoveryEngine._make_wrapper(creator_class, builder_instance)
        return factory

    @staticmethod
    def _make_wrapper(cls_ref, builder_instance):
        def wrapper(parent_widget, config_data, context=None, **kwargs):
            if not hasattr(cls_ref, 'make'):
                logger.warning(f"⚠️ Registry class {cls_ref} missing static 'make' method.")
                return None
            
            # Ensure builder instance is passed if missing from context
            if context and not hasattr(context, 'app_instance'): kwargs['builder_instance'] = builder_instance
            elif not context: kwargs['builder_instance'] = builder_instance
            
            return cls_ref.make(parent_widget, config_data, context, **kwargs)
        return wrapper
