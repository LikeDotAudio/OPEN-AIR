
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from oaGui.Core.factory.Core.factory_mapping import get_core_factory_mapping


def test_adapter_import():
    print("Testing plot_widget_adapter import via factory mapping...")

    # Mock self for get_core_factory_mapping
    mock_self = MagicMock()
    mock_self._lazy_wrap = lambda mod, cls, meth: (mod, cls, meth)

    mapping = get_core_factory_mapping(mock_self)

    try:
        # Get the lazy wrapper info
        mod_path, cls_name, meth_name = mapping["plot_widget"]
        print(f"✅ SUCCESS: Mapping found: {mod_path}.{cls_name}.{meth_name}")

        # Try importing it
        import importlib
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        print(f"✅ SUCCESS: Class {cls_name} imported from {mod_path}")

    except Exception as e:
        print(f"❌ FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_adapter_import()
