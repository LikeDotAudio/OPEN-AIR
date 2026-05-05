# 23_Showtime/Showtime.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Unified entry point for the Showtime tab.

from oaGuiShowtime.Core.tab import ShowtimeTab

# The LoaderFacade expects a class that inherits from tk.Frame or ttk.Frame.
# ShowtimeTab already does this.
Showtime = ShowtimeTab
