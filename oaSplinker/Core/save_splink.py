import orjson
from ..Constants.constants import Splinker_debug_enabled, splinker_logger

def save_splink(self, splink):
    try:
        splinker_logger.debug(f"💾 Splinker: Attempting to save splink {splink['id']}...")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        if not self.storage_path.exists():
            splinker_logger.error(f"❌ Splinker: Storage path {self.storage_path} DOES NOT EXIST after mkdir!")
            return

        file_path = self.storage_path / f"{splink['id']}.json"
        
        splinker_logger.info(f"💾 Splinker: Writing {splink['id']}.json to {file_path.absolute()}")
            
        with open(file_path, "wb") as f:
            f.write(orjson.dumps(splink, option=orjson.OPT_INDENT_2))
            
        splinker_logger.success(f"✅ Splinker: File saved successfully: {file_path.name}")
        self.publish_splinks()
    except Exception as e:
        splinker_logger.error(f"❌ Splinker: Save failed for {splink['id']}: {e}")
        import traceback
        splinker_logger.error(traceback.format_exc())
