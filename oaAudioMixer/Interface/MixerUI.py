# oaAudioMixer/Interface/MixerUI.py
# Author: Gemini (Collaborator)
# Version: 20260404.0045.8
#
# Description: TUI for the oaAudioMixer module with real-time controls for Inputs, Outputs, and Processes.
# Fixed style argument error by moving layout properties to CSS.

import sys
import os
import asyncio
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ProgressBar, Label, Button
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer, Grid
from textual.binding import Binding
from textual.message import Message
from textual import work

# Add project root to sys.path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from oaRustCore import oa_audio_mixer_rs as oaaudiomixer_rs
except ImportError:
    try:
        from oaRustCore import oa_audio_mixer_rs as oaaudiomixer_rs
    except ImportError as e:
        print(f"🛑 [FATAL] Rust oaaudiomixer_rs module missing: {e}")
        sys.exit(1)

class UniversalVolumeControl(Horizontal):
    """A volume control with UP/DOWN buttons for Inputs, Outputs, and Apps."""
    
    class Changed(Message):
        def __init__(self, target_id, value, type):
            super().__init__()
            self.target_id = target_id
            self.value = value
            self.type = type # 'device', 'source', 'app'

    def __init__(self, target_id, label, initial_vol, type, is_default=False, **kwargs):
        super().__init__(**kwargs)
        self.target_id = target_id
        self.display_label = label
        self.volume_percent = int(initial_vol * 100)
        self.type = type
        self.is_default = is_default

    def compose(self) -> ComposeResult:
        default_tag = " [DEF]" if self.is_default else ""
        yield Label(f"{self.display_label}{default_tag}", classes="v-label")
        yield Button("DN", id="dec", variant="default", classes="v-btn")
        yield ProgressBar(total=100, show_bar=True, show_percentage=False, id="v-bar")
        yield Button("UP", id="inc", variant="default", classes="v-btn")
        yield Label(f"{self.volume_percent}%", classes="v-pct", id="v-pct-label")

    def on_mount(self) -> None:
        self.query_one("#v-bar", ProgressBar).progress = self.volume_percent

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "dec":
            self.volume_percent = max(0, self.volume_percent - 5)
        elif event.button.id == "inc":
            self.volume_percent = min(100, self.volume_percent + 5)
        
        self.query_one("#v-bar", ProgressBar).progress = self.volume_percent
        self.query_one("#v-pct-label", Label).update(f"{self.volume_percent}%")
        self.post_message(self.Changed(self.target_id, self.volume_percent / 100.0, self.type))

class PCMBitMonitor(Static):
    """Vertical bit monitor."""
    def update_bits(self, content: str):
        self.update(content)

class MixerApp(App):
    """The main TUI for the Audio Mixer."""
    CSS = """
    Screen { background: #121212; }
    #main-container { padding: 0 1; }
    .section-title { text-style: bold; background: #222; color: #eee; padding: 0 1; margin-top: 1; }
    
    UniversalVolumeControl { height: 3; border: solid #333; padding: 0 1; }
    .v-label { width: 30%; content-align: left middle; }
    .v-btn { min-width: 5; width: 5; height: 1; margin: 1 0; padding: 0; }
    #v-bar { width: 1fr; margin: 1 1; }
    .v-pct { width: 6; content-align: right middle; }

    #pcm-monitor-grid { height: 18; grid-size: 2 1; margin-top: 1; }
    #pcm-monitor { width: 15; height: 16; border: solid #0f0; background: #000; color: #0f0; text-style: bold; padding: 0 1; content-align: center top; }
    #controls-panel { padding-left: 1; }
    #refresh-btn { width: 100%; margin-top: 1; }
    .scroll-list { height: 1fr; }

    .column-33 {
        width: 33%;
    }
    """

    BINDINGS = [Binding("q", "quit", "Quit"), Binding("r", "refresh", "Refresh")]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mixer = oaaudiomixer_rs.AudioMixer()
        self.visualizer_process = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Horizontal():
                with Vertical(classes="column-33"):
                    yield Label("HARDWARE INPUTS (SOURCES)", classes="section-title")
                    yield ScrollableContainer(id="source-list", classes="scroll-list")
                with Vertical(classes="column-33"):
                    yield Label("HARDWARE OUTPUTS (SINKS)", classes="section-title")
                    yield ScrollableContainer(id="sink-list", classes="scroll-list")
                with Vertical(classes="column-33"):
                    yield Label("SOFTWARE PROCESSES", classes="section-title")
                    yield ScrollableContainer(id="app-list", classes="scroll-list")

            with Grid(id="pcm-monitor-grid"):
                with Vertical():
                    yield Label("REAL-TIME PCM BITS", classes="section-title")
                    yield PCMBitMonitor("...", id="pcm-monitor")
                with Vertical(id="controls-panel"):
                    yield Label("SYSTEM CONTROL", classes="section-title")
                    yield Label("📡 PIPEWIRE ACTIVE\n🔬 BACKEND: RUST/WPCTL\n🔊 REAL-TIME DUPLEX")
                    yield Button("REFRESH DATA (R)", id="refresh-btn", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_data()
        self.start_pcm_visualizer()

    async def on_unmount(self) -> None:
        if self.visualizer_process:
            self.visualizer_process.terminate()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-btn": self.refresh_data()

    def on_universal_volume_control_changed(self, event: UniversalVolumeControl.Changed) -> None:
        self.apply_volume(event.target_id, event.value, event.type)

    @work(exclusive=True)
    async def apply_volume(self, target_id, value, type):
        try:
            if type == 'device' or type == 'source':
                self.mixer.set_device_volume(str(target_id), value)
            elif type == 'app':
                self.mixer.set_app_volume(int(target_id), value)
        except Exception as e:
            self.notify(f"Set Volume Failed: {e}", severity="error")

    def refresh_data(self) -> None:
        try:
            sinks = self.mixer.get_available_devices()
            sources = self.mixer.get_available_sources()
            apps = self.mixer.get_connected_software()

            # Clear and populate
            for list_id, items, type in [("#sink-list", sinks, 'device'), 
                                         ("#source-list", sources, 'source'),
                                         ("#app-list", apps, 'app')]:
                cont = self.query_one(list_id, ScrollableContainer)
                cont.remove_children()
                for item in items:
                    label = item['description'] if 'description' in item else item['name']
                    target_id = item['name'] if type != 'app' else item['pid']
                    cont.mount(UniversalVolumeControl(target_id, label, item['volume'], type, item.get('is_default', False)))
        except Exception as e:
            self.notify(f"Refresh Error: {e}", severity="error")

    @work
    async def start_pcm_visualizer(self) -> None:
        bin_path = project_root / "oaAudioMixer/Core/oaAudioMixer_rs/target/release/pcm_visualizer"
        monitor = self.query_one("#pcm-monitor", PCMBitMonitor)
        if not bin_path.exists(): return
        try:
            self.visualizer_process = await asyncio.create_subprocess_exec(str(bin_path), stdout=asyncio.subprocess.PIPE)
            current_frame = []
            while True:
                line_raw = await self.visualizer_process.stdout.readline()
                if not line_raw: break
                line = line_raw.decode('utf-8', errors='replace').strip()
                if line == "---FRAME---":
                    if current_frame: monitor.update_bits("\n".join(current_frame)); current_frame = []
                else:
                    if len(current_frame) < 16: current_frame.append(line)
        except: pass

if __name__ == "__main__":
    MixerApp().run()
