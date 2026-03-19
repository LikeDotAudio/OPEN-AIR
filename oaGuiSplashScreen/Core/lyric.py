from loguru import logger

class LyricManager:
    """Handles rotating lines of text for display during startup."""

    def __init__(self, label_widget):
        self.lbl = label_widget
        self.lyrics, self.index = [], 0
        self._load()

    def _load(self):
        try:
            from ..lyrics import lyrics
            self.lyrics = lyrics if isinstance(lyrics, list) else ["...Loading..."]
        except (ImportError, AttributeError):
            self.lyrics = ["...Loading..."]
        self.update_display()

    def cycle(self):
        if not self.lyrics: return
        self.index = (self.index + 1) % len(self.lyrics)
        self.update_display()

    def update_display(self):
        if self.lbl and self.lbl.winfo_exists():
            self.lbl.config(text=self.lyrics[self.index])
