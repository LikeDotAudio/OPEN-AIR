
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from oaGui.Core.factory.registry_widget_store import RegistryWidgetStore

print(f"Scanning widgets from {project_root}...")
RegistryWidgetStore.scan_widgets()

registry = RegistryWidgetStore.get_registry()
print(f"Discovered {len(registry)} types.")
for w_type in sorted(registry.keys()):
    print(f" - {w_type}: {registry[w_type].__name__}")
