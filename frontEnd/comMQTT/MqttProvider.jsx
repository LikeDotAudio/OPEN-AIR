const MqttContext = React.createContext();

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
                publish(topic, JSON.stringify({ value: defaultValue }));
            }
            initialPublishDone.current = true;
        }
    }, [publish, topic, nodeJson, defaultValue, messages]);

    const setValue = (newValue) => {
        // Optimistic UI Update: instantly snap the local React component
        setLocalValue(newValue);

        // Push to global store
        const payload = JSON.stringify({ value: newValue });
        publish(topic, payload);
    };

    return [localValue, setValue, lang];
};

window.useMqttLang = () => {
    const context = React.useContext(MqttContext);
    if (!context) return ['En', () => {}];
    return [context.lang, context.setLang];
};
