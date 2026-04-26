
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

print(f"Scanning widgets from {project_root}...")
WidgetRegistry.scan_widgets()

registry = WidgetRegistry.get_registry()
print(f"Discovered {len(registry)} types.")
for w_type in sorted(registry.keys()):
    print(f" - {w_type}: {registry[w_type].__name__}")
