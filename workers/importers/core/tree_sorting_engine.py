from loguru import logger

class TreeSortingEngine:
    """Handles logic for sorting hierarchical and flat data models based on column keys."""

    @staticmethod
    def sort(data_model, column_name, ascending=True):
        """Sorts the internal data model in-place."""
        def get_sort_key(item):
            value = item.get(column_name, "")
            try: return float(value)
            except (ValueError, TypeError): return str(value)

        data_model.sort(key=get_sort_key, reverse=not ascending)
        logger.debug(f"📊 Data model sorted by '{column_name}' (Asc: {ascending})")
