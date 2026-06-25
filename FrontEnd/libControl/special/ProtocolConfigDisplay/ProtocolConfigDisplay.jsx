// ProtocolConfigDisplay.jsx
//
// Displays a protocol's config.ini (read from the per-crate file under
// BackEnd/ComProtocols/openair-<proto>/config.ini via the /api/config endpoint)
// and publishes it, retained, to the MQTT bus at OpenAir/System/Config/<proto>.
//
// Referenced from a protocol panel's JSON as:
//   { "type": "ProtocolConfigDisplay", "protocol_name": "osc" }
//
// `protocol_name` is the bare protocol token (osc, snmp, aes70, smpte2138, …);
// if omitted, we fall back to deriving it from the MQTT topic's last segment.
const ProtocolConfigDisplay = ({ config, topic }) => {
    const node = config || {};
    // Bare protocol token. Prefer the explicit JSON key; else last topic segment.
    const proto = String(
        node.protocol_name || node.proto ||
        (topic ? topic.split('/').filter(Boolean).pop() : '')
    ).toLowerCase();

    const [data, setData] = React.useState(null);   // {section: {k: v}}
    const [error, setError] = React.useState(null);
    const [loading, setLoading] = React.useState(false);

    const mqttPublish = (window.useMqttPublish ? window.useMqttPublish() : null);

    React.useEffect(() => {
        if (!proto) { setError('No protocol_name'); return; }
        let cancelled = false;
        setLoading(true);
        setError(null);
        fetch(`/api/config?proto=${encodeURIComponent(proto)}`)
            .then((res) => res.json())
            .then((json) => {
                if (cancelled) return;
                if (!json.ok) throw new Error(json.error || 'Failed to load config');
                setData(json.config);
                setLoading(false);
                // Publish the config (retained) to the bus so the backend /
                // other clients can consume it. full_id marks the web origin.
                if (mqttPublish) {
                    mqttPublish(`OpenAir/System/Config/${proto}`, {
                        value: json.config,
                        path: json.path,
                        full_id: window.OA_SESSION_FULL_ID,
                    });
                }
            })
            .catch((err) => {
                if (cancelled) return;
                setError(err.message);
                setLoading(false);
            });
        return () => { cancelled = true; };
    }, [proto, mqttPublish]);

    // ---- styles -----------------------------------------------------------
    const box = {
        boxSizing: 'border-box', width: '100%',
        height: node.layout?.height || 'auto',
        padding: '10px', overflow: 'auto',
        background: '#141414', border: '1px solid #444', borderRadius: '4px',
        fontFamily: 'monospace', fontSize: '12px', color: '#cfcfcf',
    };
    const header = { fontWeight: 'bold', color: '#f4902c', marginBottom: '8px' };
    const sectionName = { color: '#6fb3ff', marginTop: '6px' };
    const keyStyle = { color: '#9ad19a' };

    const label = node.label?.active?.text?.En || node.label?.En || `${proto} config.ini`;

    return (
        <div style={box} className="protocol-config-display">
            <div style={header}>⚙️ {label}</div>
            {loading && <div style={{ color: '#999' }}>Loading {proto} config…</div>}
            {error && <div style={{ color: '#f55' }}>Error: {error}</div>}
            {data && Object.entries(data).map(([section, kv]) => (
                <div key={section}>
                    <div style={sectionName}>[{section}]</div>
                    {Object.entries(kv).map(([k, v]) => (
                        <div key={k}>
                            <span style={keyStyle}>{k}</span> = {String(v)}
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
};

window.ProtocolConfigDisplay = ProtocolConfigDisplay;
if (!window.OA_COMPONENTS) window.OA_COMPONENTS = {};
window.OA_COMPONENTS['ProtocolConfigDisplay'] = ProtocolConfigDisplay;
