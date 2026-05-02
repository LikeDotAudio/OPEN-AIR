# oaGui/Assets/Window_2/left_50/top_100/3_Commands/1_Router/1_Router/command_router.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Proxy frame for the CommandRouter implementation.
# Delegates actual implementation to oaComBroker.Interface.

import tkinter as tk
from oaComBroker.Interface.command_router import CommandRouter

class CommandRouterProxy(CommandRouter):
    """
    Asset-level proxy for the CommandRouter.
    """
    pass

def get_gui_class():
    return CommandRouterProxy
