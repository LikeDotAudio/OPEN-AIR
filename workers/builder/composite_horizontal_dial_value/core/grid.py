class GridManager:
    """Calculates and configures column and row weights for the composite widget."""

    @staticmethod
    def configure(container, config_data, w_req):
        """Sets up the 3-column, 2-row grid structure and calculates safe pixel limits."""
        spacing = config_data.get("column_spacing", [80, 10, 10])
        if not isinstance(spacing, list) or len(spacing) < 3:
            spacing = [80, 10, 10]

        container.grid_columnconfigure(0, weight=int(spacing[0]), uniform="col")
        container.grid_columnconfigure(1, weight=int(spacing[1]), uniform="col")
        container.grid_columnconfigure(2, weight=int(spacing[2]), uniform="col")

        container.grid_rowconfigure(0, weight=3, minsize=25)
        container.grid_rowconfigure(1, weight=7, minsize=50)

        col_1_w = (w_req * spacing[1]) / sum(spacing)
        col_2_w = (w_req * spacing[2]) / sum(spacing)

        safe_knob_dim = int(col_1_w * 0.9) if col_1_w > 0 else 40
        safe_knob_dim = max(30, min(100, safe_knob_dim))

        v_width_limit = int(col_2_w / 8) - 1 if col_2_w > 0 else 8

        return safe_knob_dim, v_width_limit
