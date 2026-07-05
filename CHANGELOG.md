# Changelog

## 2026-07-05 - Fader scaling, Web Splash, and Mobile PWA Enhancements

- **FaderDial Overhaul**: Fixed an issue where horizontal fader elements overlapped their dial components due to unconstrained flex layout shrinking on smaller screens.
- **Dynamic Fader Sizing Fix**: Removed artificial constraints on the FaderDial knob size, while gracefully capping automatic font growth. Explicit JSON layout fonts (e.g. `"font": 10`) are now correctly honored.
- **Left Padding Optimization**: Corrected `frequency.json` configs where excessive `"padx": 20` shifted faders too far right, causing layout compression.
- **Desktop Splash Screen**: Implemented a native desktop boot splash screen (`splash.py`) featuring an animated GIF to mask the Rust kernel boot time.
- **Web PWA Splash Screen**: Synchronized the Web App experience by embedding the same animated splash GIF natively into `index.html`.
- **Background Lazy Loading**: Optimized the web splash sequence so the React `LoaderOrchestrator` mounts secretly in the background, aggressively downloading UI components while the 2.5s visual animation plays.
- **Mobile Cache Management**: Deployed a "FLUSH CACHE & RELOAD" button deep in the Settings menu (tap OPEN-AIR logo) to give standalone mobile/PWA users a native way to bypass Service Worker caches and hard-refresh their interface.
