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
            mqttClient.subscribe('OpenAir/Gui/#', (err) => {
                if (!err) console.log(`📡📥📥 [MQTT] Subscribed to OpenAir/Gui/#`);
            });
        });

        mqttClient.on('message', (topic, message) => {
            const payload = message.toString();
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
        <MqttContext.Provider value={{ client, messages, publish, lang, setLang }}>
            {children}
        </MqttContext.Provider>
    );
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
            try {
                const parsed = JSON.parse(messages[topic]);
                setLocalValue(parsed.value !== undefined ? parsed.value : parsed);
            } catch (e) {
                const num = parseFloat(messages[topic]);
                setLocalValue(isNaN(num) ? messages[topic] : num);
            }
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
