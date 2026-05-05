import React from 'react';

export const MqttContext = React.createContext();

export const MqttProvider = ({ brokerUrl = 'ws://localhost:9001', children }) => {
    const [client, setClient] = React.useState(null);
    const [messages, setMessages] = React.useState({});

    React.useEffect(() => {
        console.log(`📡📥📥 [MQTT] Connecting to broker at ${brokerUrl}`);
        // We check if mqtt is defined in window (loaded via CDN)
        if (typeof window.mqtt === 'undefined') {
            console.error("🛑 [ERROR] MQTT.js not loaded.");
            return;
        }
        
        const mqttClient = window.mqtt.connect(brokerUrl);

        mqttClient.on('connect', () => {
            console.log(`📡📥📥 [MQTT] Connected to WebSockets`);
            setClient(mqttClient);
            // Subscribe to all GUI topics
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
        <MqttContext.Provider value={{ client, messages, publish }}>
            {children}
        </MqttContext.Provider>
    );
};

export const useMqttState = (topic, defaultValue, nodeJson) => {
    const context = React.useContext(MqttContext);
    
    // If not wrapped in MqttProvider (fallback safety)
    if (!context) {
        const [fallbackVal, setFallbackVal] = React.useState(defaultValue);
        return [fallbackVal, setFallbackVal];
    }

    const { messages, publish } = context;
    
    // Parse incoming message or use default
    let currentValue = defaultValue;
    if (messages[topic] !== undefined) {
        try {
            const parsed = JSON.parse(messages[topic]);
            currentValue = parsed.value !== undefined ? parsed.value : parsed;
        } catch (e) {
            const num = parseFloat(messages[topic]);
            currentValue = isNaN(num) ? messages[topic] : num;
        }
    }

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
        const payload = JSON.stringify({ value: newValue });
        publish(topic, payload);
    };

    return [currentValue, setValue];
};

// Compatibility for legacy global script loading
if (typeof window !== 'undefined') {
    window.MqttProvider = MqttProvider;
    window.useMqttState = useMqttState;
}
