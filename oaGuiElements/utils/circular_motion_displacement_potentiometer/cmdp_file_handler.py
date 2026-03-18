# workers/builder/circular_motion_displacement_potentiometer/cmdp_file_handler.py
import orjson
import pathlib
from datetime import datetime
from tkinter import filedialog
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger
from oaOchestration.project_paths import GLOBAL_PROJECT_ROOT

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file


class CMDPFileHandler:
    """Handles importing and exporting CMDP configurations."""
    def __init__(self, widget_ref):
        self.w = widget_ref

    def import_json(self):
        p = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not p: return
        try:
            with open(p, "rb") as f: data = orjson.loads(f.read())
            def find_data(d):
                if isinstance(d, dict):
                    if "channels" in d: return d
                    for v in d.values():
                        res = find_data(v)
                        if res: return res
                return None
            target = find_data(data)
            if not target: return
            
            # 1. Update Channels
            for ch_data in target.get("channels", []):
                idx = ch_data.get("id", 0) - 1
                if 0 <= idx < len(self.w.faders):
                    f = self.w.faders[idx]
                    f.val_var.set(ch_data.get("depth", 50.0))
                    f.rot_var.set(ch_data.get("level", 50.0))
                    f.angle_var.set(ch_data.get("angle", 0.0))
                    f.mute_var.set(ch_data.get("mute", False))
                    
                    if self.w.mixin_ref.state_mirror_engine:
                        sme = self.w.mixin_ref.state_mirror_engine
                        fp = f"{self.w.path}/ch{idx}"
                        for p_name in ["val", "rot", "angle", "mute"]:
                            sme.broadcast_gui_change_to_mqtt(f"{fp}/{p_name}")
                    self.w.update_tree(f)
            
            # 2. Update Group Metadata
            for g_cfg in target.get("group_configs", []):
                gn = g_cfg.get("name")
                if gn in self.w.group_name_vars:
                    self.w.group_vars[gn].set(g_cfg.get("visible", True))
                    self.w.group_color_vars[gn].set(g_cfg.get("color", "#00FF00"))
            
            self.w.refresh_pop_tree()
        except Exception as e:
            logger.exception("❌ Error importing CMDP JSON")

    def export_json(self):
        group_configs = []
        for gn in self.w.group_name_vars:
            group_configs.append({
                "name": self.w.group_name_vars[gn].get(),
                "color": self.w.group_color_vars[gn].get(),
                "visible": self.w.group_vars[gn].get()
            })
        
        channels = []
        for f in self.w.faders:
            channels.append({
                "id": f.widget_id+1,
                "name": f.label,
                "group": f.group_name,
                "angle": f.angle_var.get(),
                "level": f.rot_var.get(),
                "depth": f.val_var.get(),
                "mute": f.mute_var.get()
            })
            
        inner = self.w.widget_config.copy()
        inner["group_configs"] = group_configs
        inner["channels"] = channels
        # Cleanup
        for k in ["state_mirror_engine", "subscriber_router"]: inner.pop(k, None)
        
        full_data = {
            "mdp_demo": {
                "type": "OcaBlock",
                "description": "Exported CMDP",
                "layout": {"sticky": "nsew", "weight_y": 1},
                "fields": {"cmdp_1": inner}
            }
        }
        
        # ⚡ OPTIMIZATION: Use GLOBAL_PROJECT_ROOT instead of Path.cwd()
        default_dir = GLOBAL_PROJECT_ROOT / "DATA" / "state"
        if not default_dir.exists(): default_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        p = filedialog.asksaveasfilename(
            initialdir=str(default_dir),
            initialfile=f"CMDP_{timestamp}.json",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if p:
            try:
                with open(p, "wb") as f:
                    f.write(orjson.dumps(full_data, option=orjson.OPT_INDENT_2))
            except Exception as e:
                logger.exception("❌ Error exporting CMDP JSON")
