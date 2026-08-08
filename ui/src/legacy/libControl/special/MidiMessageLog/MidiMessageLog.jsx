/**
 * Header: MidiMessageLog.jsx
 * Purpose: MidiMessageLog component or utility.
 * Description: Handles logic and rendering for MidiMessageLog component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// React implementation for MidiMessageLog

window.MidiMessageLog = ({ value, config }) => {
    const [messages, setMessages] = React.useState([]);

    React.useEffect(() => {
        if (value) {
            setMessages(prev => {
                // Prepend new message, keep max 50
                const newMsgs = [value, ...prev];
                if (newMsgs.length > 50) return newMsgs.slice(0, 50);
                return newMsgs;
            });
        }
    }, [value]);

    const formatMessage = (msg) => {
        if (typeof msg === 'object') {
            return JSON.stringify(msg);
        }
        return String(msg);
    };

    return (
        <div style={{ padding: '10px', backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#1a1a1a') : '#1a1a1a'), borderRadius: '4px', border: '1px solid #333', height: '100%', width: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
            <h4 style={{ color: '#fff', margin: '0 0 10px 0', fontSize: '12px' }}>MIDI Messages</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {messages.map((msg, idx) => (
                    <div key={idx} style={{ fontSize: '11px', color: '#00ff00', fontFamily: 'monospace', padding: '4px', backgroundColor: '#222', borderRadius: '3px' }}>
                        {formatMessage(msg)}
                    </div>
                ))}
            </div>
        </div>
    );
};
