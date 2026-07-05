import tkinter as tk
import urllib.request
import os
import sys

def check_server():
    try:
        # The Rust kernel starts the API server on 8000
        urllib.request.urlopen("http://127.0.0.1:8000/api/tree", timeout=0.1)
        return True
    except:
        return False

class SplashScreen:
    def __init__(self):
        import time
        self.start_time = time.time()
        self.min_display_time = 3.0 # Minimum seconds to show splash
        
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg='black')
        self.root.attributes('-topmost', True)
        
        # Try to load the original GIF we recovered
        script_dir = os.path.dirname(os.path.abspath(__file__))
        gif_path = os.path.join(script_dir, "FrontEnd", "assets", "splash_logo.gif")
        
        self.frames = []
        try:
            # Load all frames of the GIF
            idx = 0
            while True:
                frame = tk.PhotoImage(file=gif_path, format=f"gif -index {idx}")
                self.frames.append(frame)
                idx += 1
        except tk.TclError:
            pass # Reached end of frames
            
        if not self.frames:
            print("Could not load splash gif")
            sys.exit(0)
            
        # Set window size
        w = self.frames[0].width()
        h = self.frames[0].height() + 50 # Add space for text
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw/2) - (w/2)
        y = (sh/2) - (h/2)
        self.root.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
        
        self.label = tk.Label(self.root, bg='black')
        self.label.pack(pady=10)
        
        self.text = tk.Label(self.root, text="Booting OPEN-AIR Kernel...", fg="#f4902c", bg="black", font=("Arial", 14, "bold"))
        self.text.pack(pady=5)
        
        self.current_frame = 0
        self.attempts = 0
        
        self.root.after(0, self.update_frame)
        self.root.after(500, self.poll)
        
    def update_frame(self):
        frame = self.frames[self.current_frame]
        self.label.configure(image=frame)
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.root.after(50, self.update_frame) # 20fps = 50ms
        
    def poll(self):
        import time
        self.attempts += 1
        elapsed = time.time() - self.start_time
        
        server_ready = check_server()
        time_met = elapsed >= self.min_display_time
        
        if (server_ready and time_met) or self.attempts > 120: # 60 seconds max timeout
            self.root.destroy()
        else:
            self.root.after(500, self.poll)

if __name__ == "__main__":
    app = SplashScreen()
    app.root.mainloop()
