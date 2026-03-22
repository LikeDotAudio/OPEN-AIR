# text_web_link/text_web_link.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: text_web_link/dynamic_guimake_text_web_link.py

import tkinter as tk
from tkinter import ttk
import webbrowser
import os

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin


class BuilderTextWebLinkCreator(TransparencyMixin):
    # Creates a clickable web link widget that opens a URL in a web browser.
    # This method sets up a Tkinter Label styled as a hyperlink. When clicked,
    # it opens the configured URL in the system's default web browser.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the web link, including the URL and label.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Frame: The created frame containing the web link widget, or None on failure.
        def make_text_web_link(
            self, parent_widget, config_data, context=None, **kwargs
        ):  # Updated signature
            """Creates a web link widget."""
            if BUILDER_DEBUG: 
                builder_logger.trace(f"🔬🏗️📑 [BUILDER] Entering make_text_web_link")
                builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")
    
            current_function_name = "make_text_web_link"
    
            # Extract only widget-specific config from config_data
            label = config_data.get("label_active") or config_data.get("label", "Link")
            config = config_data
            path = config_data.get("path")
    
            # ⚡ HARDENED INTERFACE: Extract from context if available
            if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
            if context:
                state_mirror_engine = context.state_mirror_engine
                subscriber_router = context.subscriber_router
                base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
                builder_instance = context.builder_instance
                if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
            else:
                state_mirror_engine = self.state_mirror_engine
                subscriber_router = self.subscriber_router
                base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
                builder_instance = kwargs.get("builder_instance") or self
                if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.")
    
            if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️📑 [BUILDER] Opening portal (web link) for '{label}' at path '{path}'.")
    
            # ⚡ HIGH-FIDELITY: Use tk.Canvas for transparency support
            try:
                p_bg = parent_widget.cget("bg")
                if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
            except:
                p_bg = "#2b2b2b"
    
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating canvas for web link '{label}'")
            canvas = tk.Canvas(
                parent_widget,
                bd=0,
                highlightthickness=0,
                relief="flat",
                height=30,
                bg=p_bg
            )
            
            # Apply Industrial Transparency
            if hasattr(self, '_apply_transparency'):
                if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to link canvas.")
                self._apply_transparency(canvas, canvas, config, builder_instance)
    
            try:
                layout_config = config.get("layout", {})
                font_size = layout_config.get("font", 10)
                custom_font = ("Helvetica", font_size, "underline")
                custom_colour = layout_config.get("colour", "blue")
                if BUILDER_DEBUG: builder_logger.debug(f"📐📏🎨 [STYLE] Link style: Font size {font_size}, Color: {custom_colour}")
    
                url = config.get("url", "#")
                
                def redraw_link(*args):
                    if not canvas.winfo_exists(): return
                    if BUILDER_DEBUG: builder_logger.trace(f"🔄🎨🔤 [REDRAW] Redrawing link text for '{label}'")
                    canvas.delete("industrial_text")
                    w, h = canvas.winfo_width(), canvas.winfo_height()
                    if w <= 1: return
                    
                    canvas.create_text(
                        5, h/2, text=label, anchor="w",
                        fill=custom_colour, font=custom_font,
                        tags="industrial_text"
                    )
    
                def sync_bg():
                    redraw_link()
                
                canvas._draw = sync_bg
                canvas.render = sync_bg
                canvas.bind("<Configure>", lambda e: redraw_link(), add="+")
    
                def _open_url(event):
                    try:
                        if BUILDER_DEBUG: builder_logger.info(f"🖱️🚀📑 [INPUT] User clicked link '{label}'. Opening URL: {url}")
                        webbrowser.open_new(url)
                    except Exception as e:
                        if BUILDER_DEBUG:
                            builder_logger.exception(f"❌🚫🛑 [ERROR] failure opening URL '{url}' for '{label}': {e}")
    
                if BUILDER_DEBUG: builder_logger.trace("🖱️👆🔗 [EVENTS] Binding link activation protocols.")
                canvas.bind("<Button-1>", _open_url)
    
                if BUILDER_DEBUG: builder_logger.success(f"✅🆗📑 [SUCCESS] The web link portal for '{label}' has materialized!")
                return canvas
            except Exception as e:
                if BUILDER_DEBUG:
                    builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure creating web link '{label}'")
                return None
    
