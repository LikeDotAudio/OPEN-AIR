# oaSupervisor/Methods/direct_launch.py
#
# Developer escape-hatch: launch ONE partition directly (Core / UI / Web) when
# the supervisor is invoked with `--core`, `--ui`, or `--web` on the command
# line. Returns True if a direct launch was handled — the caller should `return`
# from main(). Otherwise returns False and main() proceeds with the normal
# supervised multi-partition boot.

import importlib.util
import sys
from pathlib import Path


def handle_direct_launch(argv, project_root, log):
    """Returns True if argv[1] triggered a direct partition launch (and ran it)."""
    if len(argv) <= 1:
        return False
    mode = argv[1]
    if mode == "--core":
        import oaComBroker.Core.open_air_core as core_mod
        core_mod.main()
        return True
    if mode == "--ui":
        import oaGui.Managers.orchestration.loader_main_service as ui_mod
        ui_mod.main()
        return True
    if mode == "--web":
        web_path = Path(project_root) / "frontEnd" / "Entry.py"
        if not web_path.exists():
            log(f"🛑 CRITICAL FAILURE: Web launcher not found at {web_path}")
            sys.exit(1)
        spec = importlib.util.spec_from_file_location("frontend_entry", web_path)
        web_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_mod)
        web_mod.run()
        return True
    return False
