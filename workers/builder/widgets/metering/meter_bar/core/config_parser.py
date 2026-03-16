# workers/builder/meter_bar/core/config_parser.py

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
from workers.styling.style import THEMES, DEFAULT_THEME


@dataclass
class MeterConfig:
    # Top-Level / Identity
    label: str = ""
    path: str = ""
    
    # Labels Block
    show_label: bool = True
    label_position: str = "top"
    label_width: Optional[int] = None
    show_scale_labels: bool = True
    
    # Scale Block
    scale_position: str = "bottom"
    min_val: float = -40.0
    max_val: float = 10.0
    value_default: float = -40.0
    upper_range: float = 0.0
    middle_range: float = -10.0
    
    # Geometry & Graph Style
    orientation: str = "horizontal"
    rotation_angle: float = 0.0
    is_vertical: bool = False
    width: int = 200
    height: int = 20
    tick_size: int = 5
    font_size: int = 8
    peak_size: int = -1
    show_ticks: bool = False
    tick_both_sides: bool = False
    sub_ticks: int = 0
    tick_grid_overlay: bool = False
    tick_sub_grid_overlay: bool = False
    fill_bar_shape: bool = True
    fill_with_value: bool = False
    
    # Ballistics
    attack_ms: float = 100.0
    release_ms: float = 300.0
    glide_time: float = 100.0
    dwell_time: float = 100.0
    hold_time: float = 0.0
    fall_time: float = 100.0
    
    # Overload Sub-Block
    peak_display: bool = True
    peak_flag: bool = True
    show_peak_hold: bool = True
    peak_hold_time: float = 1000.0
    overload_fade_time: float = 500.0
    peak_display_fall_time: float = 1000.0
    peak_display_style: str = "line"
    
    # Colors
    bg_color: str = "#2b2b2b"
    canvas_bg: str = "#2b2b2b"
    lower_colour: str = "green"
    middle_colour: str = "yellow"
    upper_colour: str = "red"
    peak_display_colour: str = "red"
    pointer_colour: str = "white"
    tick_colour: str = "#E0E0E0"
    sub_tick_colour: str = "#E0E0E0"
    grid_colour: str = "#444444"
    scale_text_colour: str = "#E0E0E0"
    label_colour: str = "#E0E0E0"
    bar_track_bg: str = "#2b2b2b"

    def get_requested_dimensions(self) -> Tuple[int, int]:
        """Calculates the total required width and height for the canvas."""
        scale_text_buffer = 15
        
        tick_h = self.tick_size if (self.show_ticks or self.tick_both_sides) else 0
        if self.is_vertical:
            label_thick = (self.font_size * 3) if (self.scale_position != "none" and self.show_scale_labels) else 0
        else:
            label_thick = (self.font_size + 4) if (self.scale_position != "none" and self.show_scale_labels) else 0
            
        side_a = tick_h + label_thick
        if self.peak_display: side_a += 6
        side_b = tick_h if self.tick_both_sides else 0
        
        if not self.is_vertical:
            req_w = self.width + (scale_text_buffer * 2)
            req_h = self.height + side_a + side_b
        else:
            req_w = self.width + side_a + side_b
            req_h = self.height + (scale_text_buffer * 2)
            
        return int(req_w), int(req_h)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]):

        # 1. Resolve Theme
        theme_colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        base_bg = theme_colors.get("bg", "#2b2b2b")
        
        # 2. Config Flattening & Block Extraction
        cosmetics = config.get("cosmetics", {})
        style_flags = cosmetics.get("style_flags", {})
        style_overrides = cosmetics.get("style_overrides", {})
        graph_style = cosmetics.get("Graph_Style", config.get("Graph_Style", {}))
        labels_cfg = config.get("labels", {})
        scale_group = config.get("scale", {})
        if isinstance(scale_group, str): scale_group = {}
        geometry_cfg = config.get("geometry", {})
        
        # Priority merging for flat lookups
        flat_cfg = config.copy()
        for d in [cosmetics, style_flags, style_overrides, labels_cfg, graph_style, scale_group, geometry_cfg]:
            for k, v in d.items():
                flat_cfg[k] = v
        
        # 3. Domain
        domain_cfg = config.get("domain", {}).get("primary", config)
        def safe_float(v, default):
            try: return float(v)
            except: return float(default)

        min_v = safe_float(domain_cfg.get("min"), -40.0)
        max_v = safe_float(domain_cfg.get("max"), 10.0)
        val_def = safe_float(domain_cfg.get("value_default"), min_v)
        
        # 4. Orientation Math
        orient_val = geometry_cfg.get("orientation", flat_cfg.get("Orientation", flat_cfg.get("orientation", "horizontal"))).lower()
        angle = 0.0
        if orient_val in ["vert", "vertical"]: angle = 90.0
        elif orient_val in ["horiz", "horizontal"]: angle = 0.0
        else:
            try: angle = float(orient_val)
            except ValueError: angle = 0.0
        is_vert = (abs(angle - 90) < 0.1) or (abs(angle - 270) < 0.1)
        
        # 5. Ballistics & Overload
        ballistics_cfg = config.get("ballistics", config.get("dynamics", {}))
        
        # Overload can be nested in ballistics or top-level (sometimes called 'peak' or 'overload')
        overload_cfg = ballistics_cfg.get("overload", ballistics_cfg.get("peak", config.get("overload", config.get("peak", {}))))
        
        # User specified defaults and aliases
        peak_disp = overload_cfg.get("Overload_display", overload_cfg.get("Peak_display", True))
        peak_flg = overload_cfg.get("Overload_flag", overload_cfg.get("Peak_flag", True))
        show_ovl = overload_cfg.get("show_overload", overload_cfg.get("show_peak_hold", True))
        
        # 6. Colors
        c_colors = cosmetics.get("colors", {})
        def_fg = "#E0E0E0"
        
        # Logic for fill
        # Default: traditional growing bar (f_bar_shape=False, fill_with_value=True)
        # "UP FULL" style (f_bar_shape=True, fill_with_value=False)
        f_bar_shape = flat_cfg.get("fill_bar_shape", flat_cfg.get("fill_shape", False))
        if "fill_With_Value" in flat_cfg or "fill_with_value" in flat_cfg:
            f_bar_shape = not flat_cfg.get("fill_With_Value", flat_cfg.get("fill_with_value", True))
        
        # Grid logic
        s_grid = flat_cfg.get("show_grid", False)
        t_grid = flat_cfg.get("tick_grid_overlay", flat_cfg.get("Tick_Divisions", s_grid))
        ts_grid = flat_cfg.get("Tick_sub_grid_overlay", flat_cfg.get("tick_sub_grid_overlay", s_grid))
        
        # If show_grid is explicitly True, it should force both grids on
        if s_grid:
            t_grid = True
            ts_grid = True

        return cls(

            label=config.get("label_active", config.get("label", "")),
            path=config.get("path", ""),
            
            show_label=labels_cfg.get("show_label", config.get("show_label", True)),
            label_position=labels_cfg.get("label_position", config.get("label_position", "top")).lower(),
            label_width=labels_cfg.get("label_width", config.get("label_width", None)),
            show_scale_labels=labels_cfg.get("show_scale_labels", config.get("show_scale_labels", True)),
            
            scale_position=scale_group.get("position", config.get("scale_position", "bottom")).lower(),
            min_val=min_v,
            max_val=max_v,
            value_default=val_def,
            upper_range=float(scale_group.get("upper_range", config.get("upper_range", 0.0))),
            middle_range=float(scale_group.get("middle_range", config.get("middle_range", -10.0))),
            
            orientation=orient_val,
            rotation_angle=angle,
            is_vertical=is_vert,
            width=int(geometry_cfg.get("width", config.get("width", 200))),
            height=int(geometry_cfg.get("height", config.get("height", 20))),
            tick_size=int(geometry_cfg.get("tick_size", flat_cfg.get("tick_size", 5))),
            font_size=int(geometry_cfg.get("font_size", 8)),
            peak_size=int(geometry_cfg.get("peak_size", -1)),
            show_ticks=flat_cfg.get("show_ticks", False),
            tick_both_sides=flat_cfg.get("tick_both_sides", False),
            sub_ticks=int(flat_cfg.get("sub_ticks", flat_cfg.get("ticks_sub_divisions", 0))),
            tick_grid_overlay=t_grid,
            tick_sub_grid_overlay=ts_grid,
            fill_bar_shape=f_bar_shape,
            fill_with_value=not f_bar_shape,
            
            attack_ms=float(ballistics_cfg.get("attack_ms", ballistics_cfg.get("Attack_ms", 100))),
            release_ms=float(ballistics_cfg.get("release_ms", ballistics_cfg.get("Release_ms", 300))),
            glide_time=float(ballistics_cfg.get("glide_time", 100)),
            dwell_time=float(ballistics_cfg.get("dwell_time", 100)),
            hold_time=float(ballistics_cfg.get("hold_time", 0)),
            fall_time=float(ballistics_cfg.get("fall_time", ballistics_cfg.get("release_ms", ballistics_cfg.get("Release_ms", 300)))),
            
            peak_display=peak_disp,
            peak_flag=peak_flg,
            show_peak_hold=show_ovl,
            peak_hold_time=float(overload_cfg.get("overload_hold_ms", overload_cfg.get("peak_hold_ms", ballistics_cfg.get("peak_hold_ms", 1000)))),
            overload_fade_time=float(overload_cfg.get("overload_fade_ms", 500)),
            peak_display_fall_time=float(overload_cfg.get("Peak_display_Fall_time", 1000)),
            peak_display_style=overload_cfg.get("Peak_display_line_style", "line"),
            
            bg_color=flat_cfg.get("bg", base_bg),
            canvas_bg=flat_cfg.get("bg", base_bg),
            lower_colour=c_colors.get("lower", c_colors.get("primary", config.get("Lower_range_colour", "green"))),
            middle_colour=c_colors.get("middle", c_colors.get("secondary", config.get("Middle_range_colour", "yellow"))),
            upper_colour=c_colors.get("upper", c_colors.get("alert", config.get("upper_range_Colour", "red"))),
            peak_display_colour=c_colors.get("Peak_alert", c_colors.get("Overload_alert", overload_cfg.get("Peak_display_colour", config.get("Peak_display_colour", "red")))),
            pointer_colour=c_colors.get("pointer", config.get("Pointer_colour", "white")),
            tick_colour=c_colors.get("tick", config.get("tick_color", def_fg)),
            sub_tick_colour=c_colors.get("sub_tick", c_colors.get("tick", config.get("tick_color", def_fg))),
            grid_colour=c_colors.get("grid", "#444444"),
            scale_text_colour=c_colors.get("scale", c_colors.get("tick", config.get("tick_color", def_fg))),
            label_colour=c_colors.get("label", def_fg),
            bar_track_bg=c_colors.get("background", flat_cfg.get("bg", base_bg))
        )
