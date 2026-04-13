# oaLogging/Methods/config_retrieval.py
# Author: Gemini (Collaborator)
# Version: 20260413.1000.1
#
# Description: Helper for retrieving application configuration with caching.

# --- Global State and Caches ---
_config_instance_cache = None

def _get_cached_config():
    """
    Retrieves the application configuration singleton with local caching.

    Lead with action: Fetches the 'Config' instance to determine verbosity
    and feature flags. Uses a local cache to avoid redundant singleton
    accesses during early boot phases.

    Inputs:
        None.

    Outputs:
        Config: The active configuration instance, or a 'DummyConfig' fallback.
    """
    global _config_instance_cache
    if _config_instance_cache:
        return _config_instance_cache
    
    try:
        from oaConfigurationManager.FileReaders.config_reader import Config
        if hasattr(Config, "_instance") and Config._instance:
            _config_instance_cache = Config._instance
            return _config_instance_cache
    except ImportError:
        pass
    
    # Fallback to allow logging before the configuration system is fully online.
    class DummyConfig:
        ENABLE_DEBUG_MODE = True 
        ENABLE_DEBUG_SCREEN = True
        global_settings = {"debug_enabled": True}
        # Added DEBUG_MATRIX for matrix-aware logs
        DEBUG_MATRIX = {}
        
    return DummyConfig()
