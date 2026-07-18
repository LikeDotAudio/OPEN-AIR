/**
 * Header: MqttProvider.jsx
 * Purpose: MqttProvider component or utility.
 * Description: Handles logic and rendering for MqttProvider component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

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

// Max outbound publish rate (ms) for live control values. A knob/fader/GCA drag
// fires onChange on every pointer tick; without coalescing, each intermediate
// value (27→28→29→…) round-trips through the Python broker and fans out to
// MIDI/NMOS/SMPTE/settling, flooding the bus. setValue (below) throttles to one
// publish per interval with a guaranteed trailing publish so the final resting
// value is never lost. ~22ms ≈ 45 Hz: smooth for remote viewers, ~95% fewer
// messages than raw per-tick publishing. Override via window.OA_PUBLISH_INTERVAL_MS.
const PUBLISH_INTERVAL_MS = 22;

window.MqttProvider = ({ brokerUrl = 'ws://localhost:9001', username = 'guest', password = 'guest', children }) => {
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

        const guidPart = SESSION_FULL_ID.split(':')[0];
        const hbTopic = `OpenAir/System/Failover/WEB/Heartbeat/${guidPart}`;
        const startTs = Date.now() / 1000;

        // v41 AgentHeartbeat channel (contracts H1/H2/H3) — dual-published
        // alongside the legacy Failover beat until Phase 2 migrates failover.
        // MQTT allows ONE Last Will per connection; per contract H2 it targets
        // the Agents channel (the Failover channel has no in-repo subscriber —
        // see 4_Contracts_Structural_Guidelines §2). The LWT is the ghost-tab
        // fix: a killed tab's retained status flips to "offline" within
        // keepalive, no clean unmount required. Payload shape must match
        // @openair/contracts AgentHeartbeatSchema (schemaVersion 1).
        const agentId = `web-${guidPart}`;
        const agentTopic = `OpenAir/System/Agents/${agentId}`;
        const startedAtIso = new Date().toISOString();
        const agentBeat = (status) => JSON.stringify({
            schemaVersion: 1,
            agent: agentId,
            status,
            partition: 'WEB',
            startedAt: startedAtIso,
            lastBeat: new Date().toISOString(),
        });

        // Only send credentials when a username is provided. Public test brokers
        // (test.mosquitto.org :8080/:8081) are anonymous — sending empty creds
        // there can be rejected, so we connect without them.
        const connectOptions = {
            keepalive: 60,
            reconnectPeriod: 5000, // Wait 5 seconds between retries
            connectTimeout: 30 * 1000,
            will: {
                topic: agentTopic,
                payload: agentBeat('offline'),
                retain: true,
                qos: 1
            }
        };
        if (username) {
            connectOptions.username = username;
            if (password) connectOptions.password = password;
        }

        const mqttClient = window.mqtt.connect(brokerUrl, connectOptions);

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

        // Mirror Python's Failover heartbeat (1Hz). Lets the broker and other
        // instances see this browser as a live participant under the WEB
        // partition. Topic shape mirrors `OpenAir/System/Failover/<partition>/Heartbeat/<guid>`.
        const hbInterval = setInterval(() => {
            if (!mqttClient.connected) return;
            const payload = JSON.stringify({
                guid: guidPart,
                full_id: SESSION_FULL_ID,
                partition: 'WEB',
                active: true,
                start_ts: startTs,
                timestamp: Date.now() / 1000,
            });
            mqttClient.publish(hbTopic, payload, { retain: true });
            // v41 twin (AgentHeartbeat schema, retained, same 1 Hz cadence)
            mqttClient.publish(agentTopic, agentBeat('online'), { retain: true, qos: 1 });
        }, 1000);

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
            clearInterval(hbInterval);
            // Publish one final "offline" heartbeat so subscribers see the
            // session drop instead of relying on retain-message staleness.
            try {
                mqttClient.publish(hbTopic, JSON.stringify({
                    guid: guidPart,
                    full_id: SESSION_FULL_ID,
                    partition: 'WEB',
                    active: false,
                    start_ts: startTs,
                    timestamp: Date.now() / 1000,
                }), { retain: true });
                // v41 twin: clean shutdown announces itself, then leaves the
                // same retained "offline" the LWT would have delivered.
                mqttClient.publish(agentTopic, agentBeat('stopping'), { retain: true, qos: 1 });
                mqttClient.publish(agentTopic, agentBeat('offline'), { retain: true, qos: 1 });
            } catch (e) {}
            mqttClient.end();
        };
    }, [brokerUrl, username, password]);

    // Retained by default (config/state topics); pass { retain: false } for
    // live-event traffic — contracts T5: retain class belongs to the topic
    // family, not the call-site whim. High-rate control values use it below.
    const publish = React.useCallback((topic, payload, opts) => {
        if (client && client.connected) {
            client.publish(topic, String(payload), { retain: !(opts && opts.retain === false) });
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

window.useMqttMessages = () => {
    const context = React.useContext(MqttContext);
    return context ? context.messages : {};
};

// Returns the raw retained-publish function for components that need to publish
// to an arbitrary topic (not the per-widget topic useMqttState manages) — e.g.
// the protocol panels publishing their config.ini to OpenAir/Config/<proto>.
// No-op (returns false) when there is no provider / no connection.
window.useMqttPublish = () => {
    const context = React.useContext(MqttContext);
    return React.useCallback((topic, payload) => {
        if (context && context.publish) {
            context.publish(topic, typeof payload === 'string' ? payload : JSON.stringify(payload));
            return true;
        }
        return false;
    }, [context]);
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
                if (typeof parsed === 'object' && parsed !== null && Object.keys(parsed).some(k => k !== 'value' && k !== 'full_id')) {
                    next = parsed;
                } else {
                    next = parsed.value !== undefined ? parsed.value : parsed;
                }
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
                const payload = (typeof defaultValue === 'object' && defaultValue !== null) ? { ...defaultValue, full_id: SESSION_FULL_ID } : { value: defaultValue, full_id: SESSION_FULL_ID };
                publish(topic, JSON.stringify(payload));
            }
            initialPublishDone.current = true;
        }
    }, [publish, topic, nodeJson, defaultValue, messages]);

    // Per-topic outbound throttle (see PUBLISH_INTERVAL_MS). `pending` holds the
    // latest value awaiting a trailing publish; `last` is the wall-clock time of
    // the most recent publish. Cleared on unmount/topic change so a drag that
    // ends as the widget unmounts can't fire a publish into a dead client.
    const throttle = React.useRef({ timer: null, pending: false, value: undefined, last: 0, settleTimer: null });
    React.useEffect(() => {
        const state = throttle.current;
        return () => {
            if (state.timer) { clearTimeout(state.timer); state.timer = null; }
            if (state.settleTimer) { clearTimeout(state.settleTimer); state.settleTimer = null; }
            state.pending = false;
        };
    }, [topic]);

    const setValue = (newValue) => {
        // Optimistic UI Update: instantly snap the local React component
        setLocalValue(newValue);
        if (!publish) return;

        // Throttle the actual publish. full_id identifies this browser session so
        // Python's broker treats it as a foreign source, not a self-echo. The
        // leading edge publishes immediately for responsiveness; rapid follow-up
        // changes coalesce onto a single trailing publish, so the bus sees at most
        // one message per interval and always the final resting value.
        const state = throttle.current;
        state.value = newValue;
        state.pending = true;

        const makePayload = () => (typeof state.value === 'object' && state.value !== null)
            ? { ...state.value, full_id: SESSION_FULL_ID }
            : { value: state.value, full_id: SESSION_FULL_ID };

        // Phase 0 item 5 / contracts T5: control values are LIVE-EVENTS —
        // the throttled stream publishes retain:false so a 45 Hz fader drag
        // no longer leaves 45 retained messages/second on the broker. One
        // settle-delayed RETAINED publish of the resting value preserves
        // late-joiner state sync (reload still restores the last position).
        const flush = () => {
            state.timer = null;
            if (!state.pending) return;
            state.pending = false;
            state.last = Date.now();
            publish(topic, JSON.stringify(makePayload()), { retain: false });
        };

        const RETAIN_SETTLE_MS = 400;
        if (state.settleTimer) clearTimeout(state.settleTimer);
        state.settleTimer = setTimeout(() => {
            state.settleTimer = null;
            publish(topic, JSON.stringify(makePayload())); // retained: the resting value
        }, RETAIN_SETTLE_MS);

        const interval = window.OA_PUBLISH_INTERVAL_MS || PUBLISH_INTERVAL_MS;
        const elapsed = Date.now() - state.last;
        if (!state.timer && elapsed >= interval) {
            flush();
        } else if (!state.timer) {
            state.timer = setTimeout(flush, interval - elapsed);
        }
        // else: a trailing publish is already scheduled and will pick up state.value.
    };

    return [localValue, setValue, lang];
};

window.useMqttLang = () => {
    const context = React.useContext(MqttContext);
    if (!context) return ['En', () => {}];
    return [context.lang, context.setLang];
};
