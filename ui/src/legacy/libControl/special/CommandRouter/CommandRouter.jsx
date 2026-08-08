/**
 * Header: CommandRouter.jsx
 * Purpose: CommandRouter component or utility.
 * Description: Handles logic and rendering for CommandRouter component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// React implementation for CommandRouter
// Replaces left_50/top_100/3_Commands/1_Router/1_Router/command_router.py

window._CommandRouter = (props) => {
    // Attempt to hook into the MQTT state. If not available in this environment, fallback to React.useState.
    const useMqtt = window.useMqttState || React.useState;
    const [inVal] = useMqtt("OpenAir/System/Protocols/yak/monitor/in", null, props.config);
    const [outVal] = useMqtt("OpenAir/System/Protocols/yak/monitor/out", null, props.config);
    
    const [messages, setMessages] = React.useState([]);

    React.useEffect(() => {
        if (inVal) {
            setMessages(prev => {
                const text = typeof inVal === 'object' ? JSON.stringify(inVal) : String(inVal);
                const time = new Date().toLocaleTimeString();
                const newMsgs = [`[IN  - ${time}] ${text}`, ...prev];
                return newMsgs.length > 50 ? newMsgs.slice(0, 50) : newMsgs;
            });
        }
    }, [inVal]);

    React.useEffect(() => {
        if (outVal) {
            setMessages(prev => {
                const text = typeof outVal === 'object' ? JSON.stringify(outVal) : String(outVal);
                const time = new Date().toLocaleTimeString();
                const newMsgs = [`[OUT - ${time}] ${text}`, ...prev];
                return newMsgs.length > 50 ? newMsgs.slice(0, 50) : newMsgs;
            });
        }
    }, [outVal]);

    return (
        <div style={{ padding: '10px', color: '#fff', backgroundColor: '#1a1a1a', borderRadius: '4px', border: '1px solid #333', height: '100%', width: '100%', display: 'flex', flexDirection: 'column', boxSizing: 'border-box' }}>
            <h4 style={{ color: '#f4902c', margin: '0 0 10px 0', fontSize: '14px', flexShrink: 0, textTransform: 'uppercase', letterSpacing: '1px' }}>YAK / VISA Command Router</h4>
            <div style={{ flexGrow: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {messages.length === 0 && (
                    <div style={{ color: '#666', fontStyle: 'italic', fontSize: '12px' }}>Awaiting MQTT traffic on OpenAir/System/Protocols/yak/monitor/...</div>
                )}
                {messages.map((msg, idx) => {
                    const isOut = msg.startsWith('[OUT');
                    const color = isOut ? '#00e5ff' : '#00ff66';
                    return (
                        <div key={idx} style={{ 
                            fontSize: '11px', 
                            color: color, 
                            fontFamily: '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace', 
                            padding: '6px 8px', 
                            backgroundColor: '#0a0a0a', 
                            borderRadius: '3px', 
                            wordBreak: 'break-all',
                            borderLeft: `3px solid ${color}`,
                            boxShadow: 'inset 0 0 4px rgba(0,0,0,0.5)'
                        }}>
                            {msg}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// Register with WYSIWYG Editor
if (!window.OA_COMPONENTS) window.OA_COMPONENTS = {};
window.OA_COMPONENTS['_CommandRouter'] = window._CommandRouter;
