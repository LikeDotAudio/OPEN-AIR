const MidiKeyboard = ({ value, onChange, config }) => {
    const w = config?.geometry?.width || config?.layout?.width || 800;
    const h = config?.geometry?.height || config?.layout?.height || 120;

    const numOctaves = 6;
    const startNote = 36; // C1
    const numKeys = (numOctaves * 12) + 1; // 73 keys

    const [activeNotes, setActiveNotes] = React.useState({});

    // Resistor Color Code Mapping
    const RESISTOR_COLORS = {
        0: "#000000", 1: "#8B4513", 2: "#FF0000", 3: "#FF8C00", 4: "#FFFF00",
        5: "#00FF00", 6: "#0000FF", 7: "#EE82EE", 8: "#808080", 9: "#FFFFFF"
    };

    const WRAP_COLORS = ["#FF0000", "#FF8C00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#EE82EE", "#FFFFFF"];

    const getMidiColor = (channel) => {
        const ch = (channel || 0) + 1;
        if (ch <= 9) return RESISTOR_COLORS[ch] || "#FFFFFF";
        return WRAP_COLORS[(ch - 10) % WRAP_COLORS.length];
    };

    React.useEffect(() => {
        if (value) {
            // Assume value is a MIDI message object { type: 'note_on', note: 60, channel: 0, velocity: 127 }
            if (value.type === 'note_on' && value.velocity > 0) {
                setActiveNotes(prev => ({ ...prev, [value.note]: getMidiColor(value.channel) }));
            } else if (value.type === 'note_off' || (value.type === 'note_on' && value.velocity === 0)) {
                setActiveNotes(prev => {
                    const next = { ...prev };
                    delete next[value.note];
                    return next;
                });
            }
        }
    }, [value]);

    const numWhiteKeys = (numOctaves * 7) + 1;
    const kw = w / numWhiteKeys;

    const whiteKeys = [];
    const blackKeys = [];

    let currentX = 0;
    for (let i = 0; i < numKeys; i++) {
        const note = startNote + i;
        const noteInOctave = note % 12;
        const isBlack = [1, 3, 6, 8, 10].includes(noteInOctave);

        if (!isBlack) {
            const isActive = activeNotes[note];
            whiteKeys.push(
                <rect 
                    key={note}
                    x={currentX} y={0} width={kw} height={h}
                    fill={isActive || "#ffffff"}
                    stroke="#333"
                    onPointerDown={() => onChange({ type: 'note_on', note, velocity: 127, channel: 0 })}
                    onPointerUp={() => onChange({ type: 'note_off', note, velocity: 0, channel: 0 })}
                />
            );
            currentX += kw;
        }
    }

    currentX = 0;
    for (let i = 0; i < numKeys; i++) {
        const note = startNote + i;
        const noteInOctave = note % 12;
        const isBlack = [1, 3, 6, 8, 10].includes(noteInOctave);

        if (isBlack) {
            const isActive = activeNotes[note];
            const bx = currentX - (kw * 0.3);
            blackKeys.push(
                <rect 
                    key={note}
                    x={bx} y={0} width={kw * 0.6} height={h * 0.6}
                    fill={isActive || "#000000"}
                    stroke="#333"
                    onPointerDown={() => onChange({ type: 'note_on', note, velocity: 127, channel: 0 })}
                    onPointerUp={() => onChange({ type: 'note_off', note, velocity: 0, channel: 0 })}
                />
            );
        } else {
            currentX += kw;
        }
    }

    return (
        <div style={{ padding: '10px', backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#1a1a1a') : '#1a1a1a'), borderRadius: '4px', border: '1px solid #333' }}>
            <svg width={w} height={h} style={{ cursor: 'pointer', touchAction: 'none' }}>
                {whiteKeys}
                {blackKeys}
            </svg>
        </div>
    );
};
window.MidiKeyboard = MidiKeyboard;