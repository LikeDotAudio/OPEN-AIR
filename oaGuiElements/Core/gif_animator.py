# Core/gif_animator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from pathlib import Path

from loguru import logger

from oaGuiElements.Constants.splash_constants import DEFAULT_GIF_DURATION, MIN_GIF_DURATION

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class GifAnimator:
    """Manages GIF frame extraction and recursive animation scheduling."""

    def __init__(self, splash_window, label_widget):
        self.win, self.lbl = splash_window, label_widget
        self.frames, self.index, self.job = [], 0, None
        self.duration = DEFAULT_GIF_DURATION

    def load(self, filename):
        if not PIL_AVAILABLE: return False
        p = Path(__file__).parent.parent / "Assets" / filename
        if not p.exists(): return False

        try:
            with Image.open(p) as img:
                for i in range(img.n_frames):
                    img.seek(i)
                    self.frames.append(ImageTk.PhotoImage(img.copy().convert("RGBA")))
                self.duration = max(MIN_GIF_DURATION, img.info.get("duration", DEFAULT_GIF_DURATION))
                self.lbl.photo_images = self.frames # GC Protection
            return True
        except Exception as e:
            logger.error(f"🔴 GIF Load Failed: {e}"); return False

    def start(self, on_loop_callback=None):
        if not self.frames: return
        self.on_loop = on_loop_callback
        self._animate()

    def _animate(self):
        if not self.win or not self.win.winfo_exists(): return
        try:
            self.lbl.config(image=self.frames[self.index])
            self.index = (self.index + 1) % len(self.frames)
            if self.index == 0 and self.on_loop: self.on_loop()
            self.win.update_idletasks()
        except: pass
        self.job = self.win.after(self.duration, self._animate)

    def stop(self):
        if self.job: self.win.after_cancel(self.job); self.job = None
