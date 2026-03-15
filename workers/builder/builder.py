# builder/builder.py
#
# This file defines the main DynamicGuiBuilder class, which is responsible for constructing the application's GUI from a JSON configuration.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260222.Refactored.1

import os
import time
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.styling.style import DEFAULT_THEME, THEMES

# --- 1. CORE MIXINS ---
from managers.Display.styling.gui_style_manager import GuiStyleMixin
from managers.Display.factory.gui_widget_factory import GuiWidgetFactoryMixin
from managers.Display.builder.gui_mqtt_manager import GuiMqttManagerMixin
from managers.Display.loader.gui_file_loader import GuiFileLoaderMixin
from managers.Display.builder.gui_rebuilder import GuiRebuilderMixin
from managers.Display.builder.gui_batch_builder import GuiBatchBuilderMixin
from managers.Display.transparency.transparency_mixin import TransparencyMixin

# --- 2. DECOUPLED SERVICES ---
from managers.Display.transparency.transparency_manager import TransparencyManager
from managers.Display.telemetry.ui_tracking_service import UITrackingService

# --- 3. HIDDEN FEATURES (Core functionality) ---
from .breakoff_manager.hidden_breakoff_manager import HiddenBreakoffManagerMixin

# --- 4. UTILITIES ---
from workers.builder.input_mousewheel_mixin.input_mousewheel_mixin import (
    MousewheelScrollMixin,
)
from workers.builder.panels.panel_generator import PanelGenerator
from PIL import ImageTk

# --- 5. COMPLEX WIDGET MIXINS (Required for Event Handlers) ---
from workers.builder.composite_mdp.composite_mdp import BuilderCompositeMdpCreator
from workers.builder.circular_motion_displacement_potentiometer.circular_motion_displacement_potentiometer import BuilderCircularMotionDisplacementPotentiometerCreator
from workers.builder.button_actuator.button_actuator import BuilderButtonActuatorCreator
from workers.builder.button_wink.button_wink import BuilderButtonWinkCreator
from workers.builder.button_wink_toggler.button_wink_toggler import BuilderButtonWinkTogglerCreator
from managers.Display.array.array import BuilderArrayCreator
from managers.Display.array.collapsible_block.collapsible_block import CollapsibleBlockCreatorMixin
from managers.Display.context.widget_context import WidgetContext

class AutoScrollbar(ttk.Scrollbar):
    """A scrollbar that hides itself when it's not needed."""
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        ttk.Scrollbar.set(self, lo, hi)

class DynamicGuiBuilder(
    ttk.Frame,
    # 1. Specialized Creators (Subclasses must come before their bases)
    BuilderButtonWinkTogglerCreator,  # Subclass of BuilderButtonWinkCreator
    BuilderButtonWinkCreator,         
    BuilderCompositeMdpCreator,
    BuilderCircularMotionDisplacementPotentiometerCreator,
    BuilderButtonActuatorCreator,
    BuilderArrayCreator,
    CollapsibleBlockCreatorMixin,
    # 2. Framework Core Logic
    GuiMqttManagerMixin,
    GuiStyleMixin,
    GuiWidgetFactoryMixin,
    GuiFileLoaderMixin,
    GuiRebuilderMixin,
    GuiBatchBuilderMixin,
    TransparencyMixin, # ⚡ ENABLE INDUSTRIAL TRANSPARENCY
    # 3. Foundation Mixins (Last in MRO)
    MousewheelScrollMixin,
    HiddenBreakoffManagerMixin,
):
    # Class-level variables to track a SINGLE active editor process system-wide
    _editor_process = None
    _editor_file = None

    # Initializes the DynamicGuiBuilder, a comprehensive class that constructs a GUI from a JSON configuration.
    # It integrates various mixins for handling styling, widget creation, MQTT communication, and more.
    # The builder sets up the main frame, canvas for scrolling, and optionally a reload button.
    # It initializes all necessary components and triggers the GUI build process.
    def __init__(self, parent, json_path=None, tab_name=None, use_grid=False, *args, **kwargs):
        """
        Initializes the DynamicGuiBuilder.
        """
        config = kwargs.pop("config", {})
        super().__init__(master=parent)

        # State Initialization
        self.tab_name = tab_name
        self.on_complete_callback = config.get("on_complete")
        self.state_mirror_engine = config.get("state_mirror_engine")
        self.subscriber_router = config.get("subscriber_router")
        self.app_instance = config.get("app_instance")
        self.on_focus_widget = config.get("on_focus_widget") # Callback for jump-to-code
        self.is_editor = config.get("is_editor", False) # New attribute
        if not self.state_mirror_engine:
            if LOCAL_DEBUG: builder_logger.warning("🔬⚠️🚫 [BUILDER] DynamicGuiBuilder initialized without StateMirrorEngine! Widgets will be zombies.")
        self.json_filepath = Path(json_path) if json_path else None
        self.config_data = {}
        self.tk_vars = {}
        self.topic_widgets = {}
        self.last_build_hash = None
        self.gui_built = False
        self.panel_bg_image = None
        self.panel_bg_label = None
        # Registry for widgets that need to reslice when background changes
        self._slicing_registry = []
        
        # ⚡ VISIBILITY TRACKING: Initial state is hidden until Mapped
        self.is_visible = False
        
        # Initialize Telemetry Service
        self.tracking_service = UITrackingService()

        if LOCAL_DEBUG: 
            builder_logger.trace(f"🔬🏗️🟢 [BUILDER] Igniting DynamicGuiBuilder for '{self.tab_name}'")
            builder_logger.debug(f"📜📑💻 [CONFIG] JSON Path: {self.json_filepath}")

        # 1. Initialize Core Components
        if LOCAL_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Initializing MQTT context and widget factory...")
        self._initialize_mqtt_context(
            self.json_filepath,
            app_constants,
            config.get("base_mqtt_topic_from_path"),
        )
        self._initialize_widget_factory()
        
        # Start Tracking Telemetry
        self.tracking_service.track(
            self, 
            self.tab_name, 
            self.state_mirror_engine, 
            self.base_mqtt_topic_from_path
        )
        # self._setup_breakoff_snitch()

        # 2. GUI Scaffolding
        # self._apply_styles(theme_name=DEFAULT_THEME) # DEPRECATED: Theme is applied globally by the shell, not per-builder.
        if LOCAL_DEBUG: builder_logger.trace("🏗️🪟🎨 [SCAFFOLD] Setting up main content frames and canvas...")
        self.config(style="Dark.TFrame") # Root frame style
        
        if not use_grid:
            self.pack(fill=tk.BOTH, expand=True)
        
        # This frame should also be gridded to match its parent
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_content_frame = ttk.Frame(self, style="Dark.TFrame")
        self.main_content_frame.grid(row=0, column=0, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.canvas = tk.Canvas(
            self.main_content_frame, background=colors["bg"], bd=0, highlightthickness=0
        )
        
        # ⚡ HIGH-FIDELITY: Use tk.Canvas for scroll_frame to allow absolute transparency control
        # This ensures that gaps, padding, and empty columns show the sampled patina.
        self.scroll_frame = tk.Canvas(self.canvas, bd=0, highlightthickness=0, bg=colors["bg"])
        
        # ⚡ MANDATORY: Register the shared root frame for transparency!
        if LOCAL_DEBUG: builder_logger.debug("👻🌀🪟 [ALPHA] Applying root transparency to scroll_frame.")
        TransparencyManager.apply_transparency(self.scroll_frame, self.scroll_frame, {"transparent": True}, self)

        self.scrollbar_v = AutoScrollbar(
            self.main_content_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollbar_h = AutoScrollbar(
            self.main_content_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )

        # Store the ID of the canvas window item for later use
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        # ⚡ SCROLL SYNC: Trigger reslice on scroll to keep patina fixed relative to window
        def _on_scroll_sync():
            self._scroll_timer = None
            if getattr(self, '_is_rebuilding', False): return
            if LOCAL_DEBUG: builder_logger.trace("🖱️🔄📏 [SCROLL] Debounced reslice executing.")
            self._trigger_reslice_all()

        def _on_scroll_v(*args):
            self.scrollbar_v.set(*args)
            if getattr(self, '_is_rebuilding', False) or self._resize_timer: return
            if not self._scroll_timer:
                # Throttle reslice to ~20fps during active scroll
                self._scroll_timer = self.after(50, _on_scroll_sync)
        
        def _on_scroll_h(*args):
            self.scrollbar_h.set(*args)
            if getattr(self, '_is_rebuilding', False) or self._resize_timer: return
            if not self._scroll_timer:
                self._scroll_timer = self.after(50, _on_scroll_sync)

        self.canvas.configure(yscrollcommand=_on_scroll_v, xscrollcommand=_on_scroll_h)

        self._resize_timer = None
        self._scroll_timer = None

        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # ⚡ VISIBILITY SYNC: Late-ignition for background tabs
        self.bind("<Visibility>", self._on_visibility)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_v.grid(row=0, column=1, sticky="ns")
        self.scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        # 3. Reload Button
        if app_constants.RELOAD_CONFIG_DISPLAYED:
            if LOCAL_DEBUG: builder_logger.debug("🔄🔘🔳 [UI] Enabling Reload Config button.")
            self.button_frame = ttk.Frame(self)
            self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 10), padx=10)
            ttk.Button(
                self.button_frame, text="Reload Config", command=self._force_rebuild_gui
            ).pack(side=tk.LEFT, pady=10)
        else:
            self.button_frame = None

        # 4. Context Menu (WYSIWYG Editor & Reload)
        if LOCAL_DEBUG: builder_logger.trace("🍔🔽🖱️ [UI] Configuring right-click context menu.")
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="WYSIWYG Editor", command=self._show_wysiwyg_editor)
        self.context_menu.add_command(label="Check Dependencies", command=self._check_dependencies)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Reload", command=self._force_rebuild_gui)
        
        # Bind right-click to canvas and scroll frame
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.scroll_frame.bind("<Button-3>", self._on_right_click)

        # 5. Trigger Build
        if self.json_filepath:
            if LOCAL_DEBUG: builder_logger.info(f"🚀📑🔋 [BUILD] Triggering initial file load and build for '{self.tab_name}'")
            self._load_and_build_from_file()
        else:
            if LOCAL_DEBUG: builder_logger.info(f"🚀🔳🔋 [BUILD] Triggering initial empty build for '{self.tab_name}'")
            self._rebuild_gui()
            self.gui_built = True

    def _on_right_click(self, event):
        """Displays context menu on right click."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _show_wysiwyg_editor(self):
        """Opens the WYSIWYG Editor in a separate process, ensuring only ONE instance exists system-wide."""
        import subprocess
        import sys
        
        if not self.json_filepath:
            if LOCAL_DEBUG: builder_logger.error("🏗️🚫🛑 [BUILDER] DynamicGuiBuilder: Cannot launch editor without a valid JSON file path.")
            return

        # ⚡ SINGLETON CHECK: Verify if an editor process is already running
        if DynamicGuiBuilder._editor_process:
            # Check if process is still alive
            if DynamicGuiBuilder._editor_process.poll() is None:
                # Still running. Is it the same file?
                if str(DynamicGuiBuilder._editor_file) == str(self.json_filepath):
                    if LOCAL_DEBUG: builder_logger.info(f"🏗️📂⚠️ [BUILDER] Editor already active for '{self.json_filepath.name}'. Refocusing is up to the OS.")
                    return
                else:
                    # Different file requested. Close the old one first.
                    if LOCAL_DEBUG: builder_logger.info(f"🏗️📂♻️ [BUILDER] Closing previous editor for '{DynamicGuiBuilder._editor_file.name}' to open '{self.json_filepath.name}'.")
                    try:
                        DynamicGuiBuilder._editor_process.terminate()
                        # Wait a brief moment for it to clean up
                        DynamicGuiBuilder._editor_process.wait(timeout=1.0)
                    except Exception as e:
                        if LOCAL_DEBUG: builder_logger.warning(f"🏗️🚫⚠️ [BUILDER] Failed to gracefully close previous editor: {e}")
                        DynamicGuiBuilder._editor_process.kill()
            
            # Clear state for a fresh spawn
            DynamicGuiBuilder._editor_process = None
            DynamicGuiBuilder._editor_file = None

        if LOCAL_DEBUG: builder_logger.info(f"🏗️🚀💻 [BUILDER] DynamicGuiBuilder: Launching standalone WYSIWYG Editor process for {self.json_filepath}")
        
        # Path to the standalone runner
        runner_path = Path(__file__).resolve().parent.parent / "wysiwyg_editor" / "run_builder.py"
        
        try:
            # Launch as a separate process and track it globally
            DynamicGuiBuilder._editor_process = subprocess.Popen([
                sys.executable, 
                str(runner_path), 
                str(self.json_filepath)
            ])
            DynamicGuiBuilder._editor_file = self.json_filepath
            
            if LOCAL_DEBUG: builder_logger.success("🏗️🆗✅ [BUILDER] DynamicGuiBuilder: Standalone process spawned successfully.")
        except Exception as e:
            if LOCAL_DEBUG: builder_logger.exception("🏗️🚫🛑 [ERROR] DynamicGuiBuilder Error: Failed to launch standalone editor")
            DynamicGuiBuilder._editor_process = None
            DynamicGuiBuilder._editor_file = None

    def _check_dependencies(self):
        """Manually triggers the Installation/Setup script to verify dependencies."""
        from workers.initialization.path_initializer import GLOBAL_PROJECT_ROOT
        setup_path = GLOBAL_PROJECT_ROOT / "Installation" / "Setup.py"
        
        if not setup_path.exists():
            if LOCAL_DEBUG: builder_logger.error(f"🏗️🚫🛑 [BUILDER] Setup script not found at {setup_path}")
            return

        if LOCAL_DEBUG: builder_logger.info("🏗️🚀📦 [BUILDER] Launching Installation/Setup.py...")
        
        import subprocess
        import sys
        try:
            # Run setup and wait for completion
            result = subprocess.run([sys.executable, str(setup_path)], check=False)
            if result.returncode == 0:
                if LOCAL_DEBUG: builder_logger.success("🏗️🆗✅ [BUILDER] Dependency check/Setup completed successfully.")
            else:
                if LOCAL_DEBUG: builder_logger.error(f"🏗️🚫🛑 [BUILDER] Setup failed with exit code {result.returncode}")
        except Exception as e:
            if LOCAL_DEBUG: builder_logger.exception("🏗️🚫🛑 [ERROR] DynamicGuiBuilder: Failed to launch setup script")

    def _clear_panel_background(self):
        """Removes the generated panel background and restores the theme default."""
        if LOCAL_DEBUG: builder_logger.trace(f"🎨🧹✨ [BUILDER] Clearing panel background for '{self.tab_name}'")
        if hasattr(self, 'panel_bg_label') and self.panel_bg_label:
            try: self.panel_bg_label.destroy()
            except: pass
            self.panel_bg_label = None
        
        self.panel_bg_image = None
        self.panel_bg_pil = None
        if hasattr(self, '_last_bg_size'): del self._last_bg_size
        
        # Restore default background color
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.scroll_frame.configure(bg=colors["bg"])
        self._trigger_reslice_all()

    # Event handler called when the scrollable frame's size or position changes.
    # This function is crucial for ensuring the scrollable area of the canvas is
    # updated to match the total size of the content within the frame.
    # Inputs:
    #     event (tk.Event, optional): The event object passed by the tkinter framework.
    # Outputs: 
    #     None.
    def _on_frame_configure(self, event=None):
        """
        Event handler for when the scrollable frame is configured. It updates the scroll region of the canvas.
        """
        if LOCAL_DEBUG: builder_logger.trace(f"📐📏🔄 [LAYOUT] Frame configured for '{self.tab_name}'. Updating scroll region.")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # Event handler called when the canvas widget itself is resized.
    # This function adjusts the width of the frame window embedded within the canvas
    # to match the new width of the canvas, ensuring content flows correctly on resize.
    # Inputs:
    #     event (tk.Event, optional): The event object containing the new dimensions.
    # Outputs:
    #     None.
    def _on_canvas_configure(self, event=None):
        """
        Event handler for when the canvas is configured. It adjusts the width of the
        window item within the canvas to match the canvas's width.
        """
        if getattr(self, '_is_rebuilding', False): return
        
        # Use the width from the event if available, otherwise get it from the canvas
        width = event.width if event else self.canvas.winfo_width()
        
        # ⚡ HYSTERESIS: Ignore small jitter (e.g. scrollbar appearing/disappearing)
        # This prevents 'Layout Gallop' where the scrollbar triggers a resize loop.
        last_w = getattr(self, '_last_reported_width', 0)
        if abs(width - last_w) < 20: 
            return
            
        self._last_reported_width = width

        # Debounce the resize event to prevent jittery redrawing
        if self._resize_timer:
            self.after_cancel(self._resize_timer)
        
        if LOCAL_DEBUG: builder_logger.trace(f"📐📏⏳ [LAYOUT] Canvas configured for '{self.tab_name}' (Width: {width}). Debouncing resize.")
        # Schedule the actual resize logic
        self._resize_timer = self.after(150, self._perform_canvas_resize, width)

    def _perform_canvas_resize(self, width):
        """
        Performs the actual resizing of the canvas window item.
        """
        self._resize_timer = None
        self._scroll_timer = None
        
        if width > 1 and self.canvas_window_id: 
            req_width = self.scroll_frame.winfo_reqwidth()
            req_height = self.scroll_frame.winfo_reqheight()
            canvas_height = self.canvas.winfo_height()
            
            new_width = max(width, req_width)
            new_height = max(canvas_height, req_height)
            
            if LOCAL_DEBUG: builder_logger.debug(f"📐📏🔳 [LAYOUT] Executing canvas resize for '{self.tab_name}': {new_width}x{new_height}")
            self.canvas.itemconfig(self.canvas_window_id, width=new_width, height=new_height)
            
            # --- Regenerate Background to Fit (Optimized via Sync Trigger) ---
            self._trigger_background_sync()

    def _apply_panel_background(self, panel_config, width=None, height=None):
        """
        Generates and applies a procedural patina panel to the whole tab.
        Moves heavy PIL generation to a background thread.
        """
        import threading
        
        # ⚡ ROBUSTNESS: Handle 'none' explicitly
        if panel_config == "none":
            self._clear_panel_background()
            return
        
        # ⚡ OPTIMIZATION: Prevent 'Guess' backgrounds during build.
        if width is None or height is None:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            if w <= 1 or h <= 1:
                if LOCAL_DEBUG: builder_logger.trace(f"🎨📐🔳 [BUILDER] Skipping bg regen for '{self.tab_name}': Canvas not yet sized.")
                return
            width, height = w, h
            
        # ⚡ FINAL SAFETY: Never request 0x0 or negative
        width = max(50, width)
        height = max(50, height)

        if LOCAL_DEBUG: builder_logger.info(f"🎨🏗️🌀 [BUILDER] Spawning background generation thread for '{self.tab_name}' ({width}x{height})")

        # ⚡ RACE CONDITION PROTECTION: Track the latest task ID
        if not hasattr(self, "_bg_task_id"): self._bg_task_id = 0
        self._bg_task_id += 1
        current_task_id = self._bg_task_id

        def _bg_worker():
            try:
                # 1. Generate (or Load from Cache) in background
                panel_bg_pil = PanelGenerator.generate_panel(width, height, panel_config)
                
                # 2. Schedule UI update on main thread (only if this is still the active task)
                if self.winfo_exists() and self._bg_task_id == current_task_id:
                    self.after(0, lambda: self._apply_generated_background(panel_bg_pil, width, height, current_task_id))
            except Exception as e:
                if LOCAL_DEBUG: builder_logger.exception(f"❌🚫🛑 [ERROR] failure in background panel generation for '{self.tab_name}'")
                # ⚡ FALLBACK: Trigger reslice anyway so widgets can update their theme-matched colors
                if self.winfo_exists() and self._bg_task_id == current_task_id:
                    self.after(0, self._trigger_reslice_all)

        threading.Thread(target=_bg_worker, daemon=True).start()

    def _apply_generated_background(self, panel_bg_pil, width, height, task_id=None):
        """Applies the background PIL image to the UI (Main Thread)."""
        if not panel_bg_pil or not self.winfo_exists():
            return

        # ⚡ RACE CONDITION PROTECTION: Verify task ID still matches
        if task_id is not None and hasattr(self, "_bg_task_id") and self._bg_task_id != task_id:
            if LOCAL_DEBUG: builder_logger.debug(f"⚠️🗑️🌀 [BUILDER] Background Task {task_id} discarded (superseded by {self._bg_task_id})")
            return

        if LOCAL_DEBUG: builder_logger.success(f"🎨🆗✨ [BUILDER] Applying generated background ({width}x{height}) to '{self.tab_name}' UI.")
        self.panel_bg_pil = panel_bg_pil
        self.panel_bg_image = ImageTk.PhotoImage(self.panel_bg_pil)
        
        if self.panel_bg_image:
            # Extract base color from PIL (center pixel) for fallback
            try:
                base_rgb = self.panel_bg_pil.getpixel((width//2, height//2))
                base_hex = '#%02x%02x%02x' % base_rgb[:3]
                self.scroll_frame.configure(bg=base_hex)
                # ⚡ MANDATORY: Update canvas background too to avoid borders
                self.canvas.configure(bg=base_hex)
            except:
                pass

            if not self.panel_bg_label:
                self.panel_bg_label = tk.Label(self.scroll_frame, image=self.panel_bg_image, bd=0)
                self.panel_bg_label.place(x=0, y=0, width=width, height=height)
                self.panel_bg_label.lower()
                self.panel_bg_label.bind("<Button-3>", self._on_right_click)
            else:
                self.panel_bg_label.config(image=self.panel_bg_image)
                # Ensure the label size matches the image exactly
                self.panel_bg_label.place(x=0, y=0, width=width, height=height)
                self.panel_bg_label.bind("<Button-3>", self._on_right_click)
            
            # --- Trigger reslice for all registered widgets ---
            self._trigger_reslice_all()

    def register_for_slicing(self, callback):
        """Adds a callback to be executed when the background is updated."""
        if callback not in self._slicing_registry:
            if LOCAL_DEBUG: builder_logger.trace(f"👻🔗✨ [ALPHA] Registering widget for transparency slicing in '{self.tab_name}'")
            self._slicing_registry.append(callback)
            
            # ⚡ OPTIMIZATION: If background already exists, slice immediately 
            # so the widget doesn't stay 'grey' until the next global event.
            if hasattr(self, 'panel_bg_pil') and self.panel_bg_pil:
                try:
                    # Use root coords if available
                    rx, ry = None, None
                    if hasattr(self, 'scroll_frame') and self.scroll_frame:
                        rx, ry = self.scroll_frame.winfo_rootx(), self.scroll_frame.winfo_rooty()
                    
                    callback(
                        source_bg_pil=self.panel_bg_pil,
                        scroll_ref=self.scroll_frame,
                        scroll_root_x=rx,
                        scroll_root_y=ry
                    )
                except: pass

    def _on_visibility(self, event=None):
        """Triggered when the tab becomes visible. Handles late-ignition background sync."""
        if not self.winfo_exists(): return
        if not self.winfo_ismapped(): return
        
        if LOCAL_DEBUG: builder_logger.trace(f"💻✨🔄 [UI] Builder '{self.tab_name}' became visible.")
        
        # ⚡ LATE IGNITION: If we don't have a background yet, trigger sync now.
        if not hasattr(self, 'panel_bg_pil') or self.panel_bg_pil is None:
            if LOCAL_DEBUG: builder_logger.debug(f"🎨🏗️🌀 [UI] '{self.tab_name}' visible for first time. Triggering deferred background sync.")
            self._trigger_background_sync(force=True)
        else:
            # Just reslice to ensure transparency is correct for new position
            self._trigger_reslice_all()

    def _get_widget_context(self) -> WidgetContext:
        """Creates a strictly typed context object for widget creation."""
        # ⚡ Updated to include new managers
        return WidgetContext(
            state_mirror_engine=self.state_mirror_engine,
            subscriber_router=self.subscriber_router,
            base_mqtt_topic_from_path=self.base_mqtt_topic_from_path,
            app_instance=self.app_instance,
            builder_instance=self, # ⚡ CRITICAL: Pass the builder for transparency!
            transparency_manager=TransparencyManager,
            on_focus_widget=self.on_focus_widget
        )

    def _trigger_background_sync(self, force=False):
        """Calculates settled dimensions and triggers background regeneration with debouncing."""
        if not self.winfo_exists(): return
        
        # 🛡️ LOCK: Never trigger during the rebuild or mapping phase, unless FORCED (e.g. initial visibility).
        if not force and getattr(self, '_is_rebuilding', False):
            if LOCAL_DEBUG: builder_logger.trace(f"🎨📐🔳 [LAYOUT] BG Sync BLOCKED for '{self.tab_name}': Rebuild in progress.")
            return

        # ⚡ DEBOUNCE: Prevent rapid-fire syncs from triggering multiple threads
        if hasattr(self, '_bg_sync_timer') and self._bg_sync_timer:
            self.after_cancel(self._bg_sync_timer)
        
        if not force:
            self._bg_sync_timer = self.after(100, lambda: self._perform_background_sync(force=False))
        else:
            self._perform_background_sync(force=True)

    def _perform_background_sync(self, force=False):
        """Internal execution logic for background sync."""
        self._bg_sync_timer = None
        if not self.winfo_exists(): return
        
        # 🛡️ MAPPING GUARD: Never generate a background for a hidden or 1x1 widget.
        # Measurements taken while hidden are usually incorrect (e.g. 1x1 or 200x200).
        if not self.winfo_ismapped():
            return
        
        # ⚡ VIEWPORT AWARENESS: We must cover the entire Canvas (what the user sees)
        # and at least the required size of the content (for scrolling).
        canv_w = self.canvas.winfo_width()
        canv_h = self.canvas.winfo_height()
        req_w = self.scroll_frame.winfo_reqwidth()
        req_h = self.scroll_frame.winfo_reqheight()
        
        w = max(canv_w, req_w)
        h = max(canv_h, req_h)
        
        if LOCAL_DEBUG:
            builder_logger.trace(f"📏📐🔳 [LAYOUT] Measurement for '{self.tab_name}': Canvas({canv_w}x{canv_h}) ContentReq({req_w}x{req_h}) -> Result({w}x{h})")
        if w <= 1 or h <= 1: return
        # ⚡ OPTIMIZATION: Get current background dimensions
        last_w, last_h = getattr(self, '_last_bg_size', (0, 0))
        
        # 1. If not forced, check if we actually NEED more pixels.
        # If the new size is SMALLER than what we already have, we don't regenerate.
        # Tkinter's .place() will naturally clip the existing background label.
        needs_regen = False
        if force:
            needs_regen = True
        elif w > last_w or h > last_h:
            # Only regenerate if we are GROWING and the delta is significant (e.g. > 50px)
            dw = max(0, w - last_w)
            dh = max(0, h - last_h)
            if dw > 50 or dh > 50:
                needs_regen = True
        
        if not needs_regen:
            if LOCAL_DEBUG:
                builder_logger.trace(f"🎨📐🔳 [LAYOUT] BG Sync SKIPPED for '{self.tab_name}'. Current image ({last_w}x{last_h}) covers target ({w}x{h}).")
            
            # ⚡ MANDATORY: Even if we don't regenerate, we might still need to reslice 
            # if the widgets have shifted.
            self._trigger_reslice_all()
            return

        self._last_bg_size = (w, h)
        
        # ⚡ CONTAINER SYNC: Ensure the container matches the requested bg size 
        # BEFORE we generate it. This prevents screw clipping on first render.
        if self.canvas_window_id:
            if LOCAL_DEBUG: builder_logger.trace(f"📐📏🔳 [LAYOUT] Syncing container size for '{self.tab_name}' to {w}x{h}")
            self.canvas.itemconfig(self.canvas_window_id, width=w, height=h)

        bg_config = self.config_data.get("background")
        if bg_config and bg_config != "none":
            # ⚡ UNIQUE SEED: Ensure every tab has its own visual signature.
            # If the config doesn't provide a seed, we generate one based on the tab name
            # or a random integer to ensure no two panels look identical by default.
            if isinstance(bg_config, dict):
                params = bg_config.get("parameters", bg_config)
                if "random_seed" not in params:
                    import random
                    params["random_seed"] = random.randint(1, 1000000)

            # ⚡ SCREW FIX: Generate at exact viewport/content size.
            self._apply_panel_background(bg_config, w, h)
        else:
            self._clear_panel_background()
            self._trigger_reslice_all()

    def _trigger_reslice_all(self):
        """⚡ BATCH RESLICE ENGINE"""
        if hasattr(self, '_reslice_trigger_id') and self._reslice_trigger_id:
            try: self.after_cancel(self._reslice_trigger_id)
            except: pass
        delay = 150 if getattr(self, '_is_rebuilding', False) else 50
        self._reslice_trigger_id = self.after(delay, self._perform_batch_reslice)

    def _clear_coord_cache(self):
        """Internal optimization: clears cached screen coordinates."""
        self._root_coord_cache = {}

    def _perform_batch_reslice(self):
        """Executes the actual reslice for all widgets using cached shared context."""
        self._reslice_trigger_id = None
        if not self.winfo_exists(): return
        
        # 🛡️ RECURSION GUARD: Prevent infinite background generation loops
        if not hasattr(self, "_bg_regen_count"): self._bg_regen_count = 0
        
        # ⚡ OPTIMIZATION: Clear the coordinate cache once before the batch
        self._clear_coord_cache()

        # ⚡ FOLD SYNC: Collect all 'OcaFold' widget positions to update background creases
        # This ensures the patina background 'folds' at the same spot as the widgets.
        
        # 1. Skip expensive root coordinate updates during the batch.
        # Window-level Configure events already triggered this, and children
        # will have correct winfo_rootx once the event loop processes.
        # self.scroll_frame.update_idletasks() # ⚡ REMOVED: Blocks main thread!
        
        folds_detected = []
        scroll_ry = self.scroll_frame.winfo_rooty()
        wh = self.scroll_frame.winfo_height()
        
        # 2. Search ONLY direct children of the scroll_frame (Top-Level)
        # This ensures OcaBlocks don't generate folds, and internal separators
        # stay as simple lines without splitting the background panel.
        for child in self.scroll_frame.winfo_children():
            is_fold = False
            if hasattr(child, '_oca_path'):
                # Check top-level path segment for 'Fold' or 'fold' or 'OcaFold'
                path_segments = child._oca_path.split('.')
                # We only care about the last segment (the widget's own name)
                # being part of the top-level collection.
                if len(path_segments) == 1 and any('Fold' in s or 'fold' in s for s in path_segments):
                    is_fold = True
            
            if is_fold:
                try:
                    # Calculate relative position percentage (Use CENTER for better background alignment)
                    child_h = child.winfo_height()
                    child_ry = child.winfo_rooty() + (child_h / 2 if child_h > 1 else 0)
                    wy = child_ry - scroll_ry
                    if wh > 0:
                        pos_pct = wy / wh
                        # Only add if it's within the visible panel area
                        if 0.0 <= pos_pct <= 1.0:
                            folds_detected.append({"position_pct": pos_pct, "orientation": "horizontal"})
                except: pass

        # Sort by position for consistent hashing
        folds_detected.sort(key=lambda x: x["position_pct"])

        # 3. Check if we need to regenerate the background
        bg_config = self.config_data.get("background")
        if bg_config and isinstance(bg_config, dict):
            params = bg_config.get("parameters", bg_config)
            fold_params = params.get("metal_fold", {})
            existing_creases = [c for c in fold_params.get("creases", []) if c.get('orientation') == 'horizontal']
            
            # Compare using a small tolerance for the percentage
            needs_update = len(folds_detected) != len(existing_creases)
            if not needs_update and folds_detected:
                for f, e in zip(folds_detected, existing_creases):
                    if abs(f["position_pct"] - float(e["position_pct"])) > 0.005: # 0.5% tolerance
                        needs_update = True
                        break
            
            if needs_update:
                if self._bg_regen_count > 3:
                    if LOCAL_DEBUG: builder_logger.warning(f"🛑 [BUILDER] '{self.tab_name}': Background regeneration loop detected and suppressed.")
                    self._bg_regen_count = 0 # Reset for next major event
                else:
                    self._bg_regen_count += 1
                    if LOCAL_DEBUG: builder_logger.info(f"📐📏🔄 [BUILDER] '{self.tab_name}': Injecting {len(folds_detected)} OcaFold positions into background config.")
                    fold_params["enabled"] = True
                    # Merge with existing vertical creases
                    v_creases = [c for c in fold_params.get("creases", []) if c.get('orientation') == 'vertical']
                    fold_params["creases"] = v_creases + folds_detected
                    params["metal_fold"] = fold_params
                    
                    # Trigger background regeneration using FULL SCROLL FRAME dimensions
                    full_w = max(self.scroll_frame.winfo_width(), self.scroll_frame.winfo_reqwidth())
                    full_h = max(self.scroll_frame.winfo_height(), self.scroll_frame.winfo_reqheight())
                    
                    self._apply_panel_background(bg_config, full_w, full_h)
                    return # Background thread will trigger another reslice when done
            else:
                # Stable state reached
                self._bg_regen_count = 0
            
        # Context to share with all widgets to prevent redundant property lookups
        bg_pil = getattr(self, 'panel_bg_pil', None)
        scroll_ref = getattr(self, 'scroll_ref', None) # Note: Was scroll_frame in original but used scroll_ref in callback. Wait, scroll_ref IS the ref.
        # Actually it uses self.scroll_frame
        scroll_ref = self.scroll_frame
        
        # ⚡ OPTIMIZATION: Calculate shared root offsets once for the whole batch
        root_x, root_y = None, None
        if scroll_ref:
            try:
                # 🛡️ OPTIMIZATION: winfo_rootx is already accurate after the Configure event
                # calling update_idletasks() here causes massive UI stuttering.
                root_x = scroll_ref.winfo_rootx()
                root_y = scroll_ref.winfo_rooty()
            except Exception as e:
                if LOCAL_DEBUG: builder_logger.error(f"🧩🚫🛑 [ERROR] Batch Reslice: Error updating root coords: {e}")

        # ⚡ BATCH PROCESSING: Iterate all registered widgets
        count = 0
        # If we're still generating a background, we might want to skip the batch until it's ready
        # to avoid the 'jump' from flat color to texture.
        if bg_pil is None and getattr(self, '_bg_task_id', 0) > 0:
            if LOCAL_DEBUG: builder_logger.trace(f"🧩⏳🌀 [SYNC] Batch reslice for '{self.tab_name}' deferred: Background generation in progress.")
            return

        if LOCAL_DEBUG: builder_logger.debug(f"🧩🏗️✨ [SYNC] Executing batch reslice for {len(self._slicing_registry)} widgets in '{self.tab_name}'")
        
        # ⚡ BULK STATS: Track work done vs skipped
        skipped = 0
        processed = 0
        
        for callback in self._slicing_registry:
            try:
                # Call perform_reslice with provided optimization context
                work_done = callback(
                    source_bg_pil=bg_pil, 
                    scroll_ref=scroll_ref,
                    scroll_root_x=root_x,
                    scroll_root_y=root_y
                )
                if work_done is False: skipped += 1
                else: processed += 1
                count += 1
            except Exception as e:
                if LOCAL_DEBUG: builder_logger.error(f"🧩🚫🛑 [ERROR] Batch Reslice: Error in callback: {e}")
        
        if LOCAL_DEBUG:
            builder_logger.info(f"🧩🆗✅ [BUILDER] Reslice COMPLETE: {processed} updated, {skipped} skipped (Jitter Filter) for '{self.tab_name}'.")
