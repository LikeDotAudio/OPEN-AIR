# oaComProtocols.oaComREST/interface/interface.py
# Author: Gemini (Collaborator)
# Version: 20260405.1959.1
# Description: Public interface for the oaComProtocols.oaComREST module.

from .gui_REST import RESTInterface
from .routes import RESTRoutes

__all__ = [
    "RESTInterface",
    "RESTRoutes",
]
