const MqttContext = React.createContext();

// Per-session identity. Matches Python's FULL_INSTANCE_ID shape ("<8-byte-hex>:<partition>:<pid>")
// from oaConfigurationManager/Core/identity.py so the Python broker's reflection
// check (ingest.py:187, dispatch.py:85) sees this browser as a distinct origin
// instead of stamping anonymous web publishes with Python's own GUID and
// dropping them as self-echoes. Random per page load — survives a Python
// restart but rotates on every browser refresh.
const SESSION_FULL_ID = (() => {
    const bytes = new Uint8Array(8);
    (window.crypto || window.msCrypto).getRandomValues(bytes);
    const guid = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
    return `${guid}:WEB:${Date.now()}`;
})();
window.OA_SESSION_FULL_ID = SESSION_FULL_ID;
console.log(`🆔 [MQTT] Session full_id = ${SESSION_FULL_ID}`);

window.MqttProvider = ({ brokerUrl = 'ws://localhost:9001', children }) => {
    const [client, setClient] = React.useState(null);
    const [messages, setMessages] = React.useState({});
    const [lang, setLang] = React.useState('En'); // Default to English
    const [connected, setConnected] = React.useState(false);

    React.useEffect(() => {
        console.log(`📡📥📥 [MQTT] Connecting to broker at ${brokerUrl}`);
        if (typeof window.mqtt === 'undefined') {
            console.error("🛑 [ERROR] MQTT.js not loaded.");
            return;
        }

        const mqttClient = window.mqtt.connect(brokerUrl, {
            username: 'guest',
            password: 'guest',
            keepalive: 60,
            reconnectPeriod: 5000, // Wait 5 seconds between retries
            connectTimeout: 30 * 1000,
        });

        mqttClient.on('connect', () => {
            console.log(`📡📥📥 [MQTT] Connected to WebSockets`);
            setClient(mqttClient);
            setConnected(true);
            mqttClient.subscribe('OpenAir/Gui/#', (err) => {
                if (!err) console.log(`📡📥📥 [MQTT] Subscribed to OpenAir/Gui/#`);
            });
        });
        mqttClient.on('reconnect', () => setConnected(false));
        mqttClient.on('close',     () => setConnected(false));
        mqttClient.on('offline',   () => setConnected(false));

        mqttClient.on('message', (topic, message) => {
            const payload = message.toString();
            // Debug diagnostic — enable in DevTools console with:
            //     window.OA_MQTT_DEBUG = true
            // Logs every incoming MQTT message with src identity so you can
            // verify Python's broadcasts reach the browser. Set
            // window.OA_MQTT_FILTER = 'center_freq' (substring) to limit.
            if (window.OA_MQTT_DEBUG) {
                const flt = window.OA_MQTT_FILTER;
                if (!flt || topic.indexOf(flt) >= 0) {
                    let _src;
                    try { _src = JSON.parse(payload)?.full_id || JSON.parse(payload)?.origin_source; } catch (e) {}
                    console.log(`📥 [MQTT-IN] ${topic} | ${payload.slice(0, 120)}${_src ? ` | Src=${_src}` : ''}`);
                }
            }
            // Mirror to window so you can inspect from console:
            //   window.OA_MQTT_LAST['<topic>']
            if (!window.OA_MQTT_LAST) window.OA_MQTT_LAST = {};
            window.OA_MQTT_LAST[topic] = payload;
            setMessages(prev => ({ ...prev, [topic]: payload }));
        });

        mqttClient.on('error', (err) => {
            console.error(`🛑 [ERROR] MQTT Connection error:`, err);
        });

        return () => {
            mqttClient.end();
        };
    }, [brokerUrl]);

    const publish = React.useCallback((topic, payload) => {
        if (client && client.connected) {
            client.publish(topic, String(payload), { retain: true });
        }
    }, [client]);

    return (
        <MqttContext.Provider value={{ client, messages, publish, lang, setLang, connected, fullId: SESSION_FULL_ID }}>
            {children}
        </MqttContext.Provider>
    );
};

// Returns { connected, fullId } for the active MQTT session, so UI chrome can
// show the live connection state and this browser's session identity.
window.useMqttStatus = () => {
    const context = React.useContext(MqttContext);
    if (!context) return { connected: false, fullId: SESSION_FULL_ID };
    return { connected: context.connected, fullId: context.fullId };
};

window.useMqttState = (topic, defaultValue, nodeJson) => {
    const context = React.useContext(MqttContext);
    
    // We maintain a local state so the UI feels instantly responsive
    // even before the MQTT round-trip or if the broker is entirely offline.
    const [localValue, setLocalValue] = React.useState(defaultValue);

    if (!context) {
        return [localValue, setLocalValue, 'En'];
    }

    const { messages, publish, lang } = context;
    
    // Sync local state when a fresh MQTT message arrives for this topic
    React.useEffect(() => {
        if (messages[topic] !== undefined) {
            let next;
            try {
                const parsed = JSON.parse(messages[topic]);
                next = parsed.value !== undefined ? parsed.value : parsed;
            } catch (e) {
                const num = parseFloat(messages[topic]);
                next = isNaN(num) ? messages[topic] : num;
            }
            // Debug: confirm the effect fires for this widget's topic when
            // a Python-sourced update arrives. Enable in DevTools console:
            //     window.OA_MQTT_DEBUG = true
            if (window.OA_MQTT_DEBUG) {
                const flt = window.OA_MQTT_FILTER;
                if (!flt || topic.indexOf(flt) >= 0) {
                    console.log(`🔄 [useMqttState] ${topic} -> setLocalValue(${JSON.stringify(next)})`);
                }
            }
            setLocalValue(next);
        }
    }, [messages[topic], topic]);

    const initialPublishDone = React.useRef(false);

    React.useEffect(() => {
        if (publish && nodeJson && !initialPublishDone.current) {
            publish(`${topic}/config`, JSON.stringify(nodeJson));
            if (messages[topic] === undefined) {
                // Include full_id so Python's broker doesn't mistake this
                // for one of its own reflections (see SESSION_FULL_ID above).
                publish(topic, JSON.stringify({ value: defaultValue, full_id: SESSION_FULL_ID }));
            }
            initialPublishDone.current = true;
        }
    }, [publish, topic, nodeJson, defaultValue, messages]);

    const setValue = (newValue) => {
        // Optimistic UI Update: instantly snap the local React component
        setLocalValue(newValue);

        // Push to global store. full_id identifies this browser session so
        // Python's broker treats it as a foreign source, not a self-echo.
        const payload = JSON.stringify({ value: newValue, full_id: SESSION_FULL_ID });
        publish(topic, payload);
    };

    return [localValue, setValue, lang];
};

window.useMqttLang = () => {
    const context = React.useContext(MqttContext);
    if (!context) return ['En', () => {}];
    return [context.lang, context.setLang];
};
