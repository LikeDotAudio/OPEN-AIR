# oaGuiDefinitions/right_50/bottom_90/2_monitors/23_Showtime/gui_Showtime.py
#
# Unified entry point for the Showtime tab.
# Bridges the Framework ModuleLoader to the refactored Showtime logic.

from oaGuiShowtime.core.tab import ShowtimeTab

# The ModuleLoader expects a class that inherits from tk.Frame or ttk.Frame.
# ShowtimeTab already does this.
Showtime = ShowtimeTab
