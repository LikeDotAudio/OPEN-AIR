# Methods/folder_path_resolver.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Resolves initial path prefixes for Dynamic GUI Builds.

class BuilderPathResolver:
    """Resolves initial path prefixes for Dynamic GUI Builds."""
    @staticmethod
    def resolve_prefix(configuration):
        """Determine the initial prefix based on the project state structure."""
        path_prefix = ""
        if isinstance(configuration, dict) and len(configuration) == 1:
            root_key = next(iter(configuration))
            # If the root object is an anonymous container, use its key as the prefix
            if isinstance(configuration[root_key], dict) and "type" not in configuration[root_key]:
                path_prefix = root_key
        return path_prefix
