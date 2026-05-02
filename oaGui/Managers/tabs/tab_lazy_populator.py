# oaGui/Managers/tabs/tab_lazy_populator.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for lazy-loading and populating tab frames from directory structures.

import pathlib
from oaLogging.Methods.matrix_gate import matrix_log

def populate_tab_on_demand(display_instance, tab_frame, tab_name):
    """Checks if a tab requires population and triggers the build if necessary."""
    if getattr(tab_frame, "is_populated", False) or getattr(tab_frame, "is_populating", False):
        matrix_log("gui", "gui_shell", "tab_populate", f"ℹ️ Tab {tab_name} already populated or populating.", "DEBUG")
        return

    tab_frame.is_populating = True
    build_path = getattr(tab_frame, "build_path", None)
    
    if not build_path:
        tab_frame.is_populating = False
        return

    matrix_log("gui", "gui_manager", "tab_populate", f"🏗️ Populating tab {tab_name} from {build_path}", "INFO")

    if isinstance(build_path, str): 
        build_path = pathlib.Path(build_path)
    
    # ⚡ SIZING FIX: Ensure the tab frame itself allows the builder to expand
    tab_frame.grid_rowconfigure(0, weight=1)
    tab_frame.grid_columnconfigure(0, weight=1)

    def _execute_population():
        try:
            display_instance._build_from_directory(path=build_path, parent_widget=tab_frame)
            tab_frame.is_populated = True
            matrix_log("gui", "gui_shell", "tab_populate", f"✅ Tab {tab_name} population complete.", "SUCCESS")
        except Exception as error:
            matrix_log("gui", "gui_shell", "tab_populate", f"❌ Failed to populate tab {tab_name}: {error}", "ERROR")
        finally:
            tab_frame.is_populating = False

    display_instance.after(10, _execute_population)
