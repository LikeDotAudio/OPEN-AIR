# Web-Based Sampler Implementation Strategy (React & HTML5)

Building a modern software sampler in the browser requires bridging the gap between declarative UI (React) and the imperative, time-critical nature of digital signal processing (Web Audio API). Based on our audit of the MPC architecture, here is a technical blueprint for implementing a powerful, browser-based sampler.

## 1. Core Technologies
*   **UI Framework:** React (utilizing functional components and hooks for modular architecture).
*   **State Management:** Zustand or Redux. A sampler has a deeply nested state (Project -> Programs -> Pads -> Layers -> Envelopes). React Context alone will cause too many unnecessary re-renders.
*   **Audio Engine:** HTML5 Web Audio API.
*   **Advanced DSP:** `AudioWorklet` (for custom effects, bit-crushing, and time-stretching).
*   **Waveform Rendering:** HTML5 `<canvas>`.
*   **Storage:** IndexedDB (via localForage) for caching decoded audio buffers and saving projects locally.

## 2. The Audio Engine (Web Audio API)
React is too slow and unpredictable for precise audio timing. The audio engine must live outside the React render cycle, acting as an imperative layer that React simply sends commands to.

### The Signal Chain (Per Voice)
When a pad is hit, a "Voice" is instantiated. The Web Audio graph for a single pad hit looks like this:
1.  **`AudioBufferSourceNode`**: Holds the decoded audio sample in memory. Handles sample playback rate (pitching), start/end points, and looping.
2.  **`BiquadFilterNode`**: Applies low-pass, high-pass, or band-pass filtering.
3.  **`GainNode` (Amp Envelope)**: Controls the volume over time (ADSR). We use `gain.setValueAtTime()` and `gain.exponentialRampToValueAtTime()`.
4.  **`GainNode` (Velocity)**: Scales the overall volume based on how hard the pad was hit.
5.  **Master `GainNode` / PannerNode**: Routes to the main mix and handles stereo panning.

### Voice Management & Polyphony
We need a `VoiceManager` class to handle polyphony limits and **Mute Groups** (Choke Groups).
*   If an "Open Hi-Hat" pad is hit, the `VoiceManager` checks if it shares a Mute Group with the "Closed Hi-Hat". If so, it finds the active `AudioBufferSourceNode` for the open hat, ramps its `GainNode` to 0 very quickly (e.g., 10ms) to avoid a digital click, and stops the node.

## 3. The Sequencer Engine (Rock-Solid Timing)
You **cannot** use `setInterval` or `setTimeout` for a musical sequencer; they drift, are tied to the UI thread, and get throttled by the browser when the tab is inactive.

*   **The Lookahead Scheduler (Web Audio Clock)**: The sequencer must use `audioContext.currentTime`.
*   A `requestAnimationFrame` loop or a dedicated Web Worker constantly checks the current time.
*   It looks slightly ahead in the sequence (e.g., a 25ms "scheduling window").
*   It finds any notes falling within that window and schedules their `AudioBufferSourceNode.start(scheduledTime)`.
*   This guarantees sample-accurate playback, even if the React UI drops frames or lags.

## 4. State Management Architecture
The React state should act as the "Source of Truth" for the project parameters. 

```javascript
// Example State Tree Structure
{
  transport: { tempo: 90, isPlaying: true, swing: 50 },
  programs: [
    {
      id: 'prog_drum_1',
      type: 'DRUM',
      pads: {
        'A01': { // Pad 1, Bank A
          muteGroup: 1,
          layers: [
            {
              sampleId: 'kick_01',
              startPoint: 0.05, // seconds
              endPoint: 0.45,
              pitchOffset: 0,
              filterCutoff: 1500, // Hz
              ampEnvelope: { attack: 0.01, decay: 0.2, sustain: 0, release: 0.1 }
            }
          ]
        }
      }
    }
  ],
  sequence: [
    // Scheduled events
    { time: 0, pad: 'A01', velocity: 127 },    // Kick on beat 1
    { time: 0.5, pad: 'A03', velocity: 100 }   // Snare on beat 2
  ]
}
```

## 5. UI Components & Interaction

### The 4x4 Pad Grid
*   **Touch/Mouse Events**: Use `onPointerDown` and `onPointerUp` rather than `onClick` for the absolute lowest latency.
*   **Velocity Simulation**: Since mouse and most touch screens lack velocity sensitivity, you can simulate it:
    *   *Y-Axis Mapping*: Tapping lower on the pad equals higher velocity.
    *   *Hardware Modes*: Implement toggleable UI buttons for "Full Level" (always 127 velocity) or "16 Levels" (spreads one sound across 16 pads at ascending velocities).

### The Sample Editor (Waveform & Chopping)
*   **Rendering**: Do not render the waveform with DOM elements (like thousands of thin `div`s); it will destroy performance. Use the HTML5 `<canvas>` API.
*   **Drawing Data**: Extract channel data using `audioBuffer.getChannelData(0)`. Calculate min/max values for chunks of the audio to draw a compressed representation of the waveform.
*   **Slicing UI**: Implement an interactive overlay on the canvas. When a user drags a slice marker, update the `startPoint` and `endPoint` of the respective pad in the Zustand/Redux store.

### 5.1 Code Example: Rendering Waveform to Canvas
```javascript
const drawWaveform = (audioBuffer, canvas) => {
    const ctx = canvas.getContext('2d');
    const data = audioBuffer.getChannelData(0); // Left channel
    const step = Math.ceil(data.length / canvas.width);
    const amp = canvas.height / 2;

    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.strokeStyle = '#f4902c';
    ctx.beginPath();
    for (let i = 0; i < canvas.width; i++) {
        let min = 1.0;
        let max = -1.0;
        for (let j = 0; j < step; j++) {
            const datum = data[(i * step) + j]; 
            if (datum < min) min = datum;
            if (datum > max) max = datum;
        }
        // Draw vertical line for the min/max amplitude at this pixel
        ctx.moveTo(i, (1 + min) * amp);
        ctx.lineTo(i, (1 + max) * amp);
    }
    ctx.stroke();
};
```

### 5.2 Code Example: Audio Playback with Cropping (Non-Destructive)
```javascript
const playSlice = (audioContext, audioBuffer, startSec, endSec) => {
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    
    // Web Audio API handles the start offset and duration!
    const duration = endSec - startSec;
    source.start(audioContext.currentTime, startSec, duration);
};
```

### File Handling
*   Use the HTML5 File API (`<input type="file" accept="audio/*">`) or the Drag and Drop API.
*   Read the file as an `ArrayBuffer` and decode it using `audioContext.decodeAudioData()`.

## 6. Advanced Challenges & Solutions

1.  **Time Stretching (Warping without Pitch Shifting)**
    *   *Challenge*: The Web Audio API's native `playbackRate` alters both pitch and time (like a vinyl record).
    *   *Solution*: Implement a Phase Vocoder or Granular Synthesis algorithm inside an `AudioWorklet`. This runs entirely on a separate audio thread, allowing for real-time stretching without blocking the main UI thread.
2.  **Audio Export (Bouncing)**
    *   *Challenge*: Users will want to export their finished beat as a `.wav` file.
    *   *Solution*: Use an `OfflineAudioContext`. You can schedule the entire sequence to play into this context instantly (it processes as fast as the CPU allows, not in real-time). Extract the resulting `AudioBuffer`, encode it to a `.wav` blob, and trigger a browser download.
3.  **Memory Management**
    *   *Challenge*: Loading 50 drum kits into browser RAM will crash the tab.
    *   *Solution*: Eagerly decode only the active program. Keep inactive samples stored as raw ArrayBuffers in `IndexedDB`. When a user switches programs, quickly swap the buffers.
4.  **Hardware Integration (Web MIDI)**
    *   *Implementation*: Use the `navigator.requestMIDIAccess()` API. Map incoming MIDI Note On/Off messages to trigger your `VoiceManager` and highlight the UI pads in React.
