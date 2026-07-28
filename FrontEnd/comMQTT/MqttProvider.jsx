/**
 * Header: MqttProvider.jsx
 * Purpose: MqttProvider component or utility.
 * Description: Handles logic and rendering for MqttProvider component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Topic carrying live VISA scan narration. Non-retained event stream — see
// SCAN_LOG_TOPIC in BackEnd/Core/orchestrator/src/main.rs. Subscribed below,
// printed to the browser console AND fed to the activity store, because the
// orchestrator's own stdout is invisible to anyone actually using the UI.
const OA_SCAN_LOG_TOPIC = 'OpenAir/System/Protocols/visa/Scan/Log';

// Retained `scanning` | `idle` — the VISA scan's state, not its narration.
const OA_SCAN_STATE_TOPIC = 'OpenAir/System/Protocols/visa/Scan/State';

// Narration for EVERY discovery agent, not just VISA: the discovered-GUI
// watcher diffs the retained protocol tree and announces devices appearing,
// vanishing and changing state (Deployment/build_discovered_gui.py).
const OA_DISCOVERY_ACTIVITY_TOPIC = 'OpenAir/System/Discovery/Activity';

// Live table rows for the Discovered tab, one retained topic per category.
// Panels carry a cold-start snapshot; these carry the truth. WITHOUT this
// subscription every discovery table froze at whatever was baked into its
// panel file at build time — the tab looked static while the bus was busy.
const OA_DISCOVERED_ROWS_FILTER = 'OpenAir/System/Gui/Discovered/#';

// Topics handled by the activity store instead of the value store. They are an
// event stream: putting them in `messages` would re-render every widget on the
// page for each line of scan narration.
// What YAK did with a press: the command, the SCPI it resolved to, and the
// instrument it went to. Until this existed the agent narrated only to its own
// stdout, so pressing a bound button looked identical whether it had driven an
// instrument or found no command at all.
const OA_YAK_ACTIVITY_TOPIC = 'OpenAir/System/Protocols/yak/Activity';
const OA_ACTIVITY_TOPICS = new Set([OA_SCAN_LOG_TOPIC, OA_DISCOVERY_ACTIVITY_TOPIC, OA_YAK_ACTIVITY_TOPIC]);

// ── Discovery activity store ────────────────────────────────────────────────
//
// Deliberately OUTSIDE React state. Scan narration arrives in bursts of dozens
// of lines; holding it in the provider's context would re-render the whole
// widget tree per line. Components that want it subscribe individually via
// window.useDiscoveryActivity(), so a burst only re-renders the feed itself.
const OA_ACTIVITY_MAX = 300;
const ScanActivityStore = {
    lines: [],           // oldest first; capped at OA_ACTIVITY_MAX
    scanState: 'idle',   // 'scanning' | 'idle'
    listeners: new Set(),
    _pending: null,
    subscribe(fn) {
        this.listeners.add(fn);
        return () => this.listeners.delete(fn);
    },
    // Coalesced notify: a scan can emit many lines in one tick, and the feed
    // only needs to paint the result once.
    _emit() {
        if (this._pending) return;
        this._pending = setTimeout(() => {
            this._pending = null;
            this.listeners.forEach(fn => { try { fn(); } catch (e) {} });
        }, 60);
    },
    push(line) {
        const next = this.lines.concat([line]);
        this.lines = next.length > OA_ACTIVITY_MAX ? next.slice(next.length - OA_ACTIVITY_MAX) : next;
        this._emit();
    },
    setScanState(state) {
        if (state === this.scanState) return;
        this.scanState = state;
        this._emit();
    },
    clear() {
        this.lines = [];
        this._emit();
    },
};
window.OA_SCAN_ACTIVITY = ScanActivityStore;

// Subscribe to the discovery activity feed. Returns the current lines plus
// whether a VISA scan is in flight; re-renders only this component.
window.useDiscoveryActivity = () => {
    const [, force] = React.useReducer(x => x + 1, 0);
    React.useEffect(() => ScanActivityStore.subscribe(force), []);
    return {
        lines: ScanActivityStore.lines,
        scanning: ScanActivityStore.scanState === 'scanning',
        clear: () => ScanActivityStore.clear(),
    };
};

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
            // Live scan narration -> console AND the on-page activity feed. The
            // orchestrator's scan progress used to exist only in its own stdout,
            // which is invisible to anyone running the UI (doubly so in a
            // container) — "I see it in the terminal, not in the browser".
            mqttClient.subscribe(OA_SCAN_LOG_TOPIC, (err) => {
                if (!err) console.log(`🔎 [SCAN] watching ${OA_SCAN_LOG_TOPIC} — scan progress will appear here`);
            });
            // Narration from every OTHER discovery agent (DNS-SD, Cast, Dante,
            // PTP, RAVENNA, SAP, printers…), which is most of what scrolls past
            // in the terminal.
            mqttClient.subscribe(OA_DISCOVERY_ACTIVITY_TOPIC);
            // What YAK sent, and where — see OA_YAK_ACTIVITY_TOPIC.
            mqttClient.subscribe(OA_YAK_ACTIVITY_TOPIC, (err) => {
                if (!err) console.log(`⚙️ [YAK] watching ${OA_YAK_ACTIVITY_TOPIC} — bound commands will appear here`);
            });
            // Scan state, so the UI can say "scanning" rather than infer it.
            mqttClient.subscribe(OA_SCAN_STATE_TOPIC);
            // Live discovery table rows. These are what make the Discovered tab
            // move without a page reload.
            mqttClient.subscribe(OA_DISCOVERED_ROWS_FILTER, (err) => {
                if (!err) console.log(`📡📥📥 [MQTT] Subscribed to ${OA_DISCOVERED_ROWS_FILTER}`);
            });
        });
        // Activity lines are an event stream, not application state: routing
        // them to the store (and the console) keeps them out of `messages` and
        // off the whole-tree React render path.
        mqttClient.on('message', (topic, payload) => {
            if (topic === OA_SCAN_STATE_TOPIC) {
                ScanActivityStore.setScanState(payload.toString().trim());
                return;
            }
            if (!OA_ACTIVITY_TOPICS.has(topic)) return;
            let line = {};
            try { line = JSON.parse(payload.toString()); }
            catch (e) { line = { level: 'info', message: payload.toString() }; }
            if (!line.ts) line.ts = Date.now() / 1000;
            if (!line.source) line.source = topic === OA_SCAN_LOG_TOPIC ? 'visa' : 'discovery';
            ScanActivityStore.push(line);
            const style = {
                ok:    'color:#2ea043',
                warn:  'color:#d29922',
                error: 'color:#f85149',
                info:  'color:#58a6ff',
            }[line.level] || 'color:#58a6ff';
            const icon = line.source === 'yak'
                ? { ok: '⚙️', warn: '⚠️', error: '❌', info: '⚙️' }[line.level] || '⚙️'
                : { ok: '✅', warn: '⚠️', error: '❌', info: '🔎' }[line.level] || '🔎';
            console.log(`%c${icon} [${line.source.toUpperCase()}] ${line.message}`, style);
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
            // Handled by the activity store above. Kept out of `messages`
            // because every write there re-renders every widget on the page.
            if (OA_ACTIVITY_TOPICS.has(topic) || topic === OA_SCAN_STATE_TOPIC) return;
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
    return React.useCallback((topic, payload, opts) => {
        if (context && context.publish) {
            context.publish(topic, typeof payload === 'string' ? payload : JSON.stringify(payload), opts);
            return true;
        }
        return false;
    }, [context]);
};

// One-shot trigger publish: NON-retained, no settle, no resting value.
//
// `useMqttState` is the wrong tool for a momentary control. It follows every
// change with a retained publish of the resting value 400 ms later, so late
// joiners can restore a fader position — correct for state, wrong for an event.
// A retained `1` on a trigger topic is a command left lying on the broker: YAK
// replays it to itself on reconnect, which for a Setup page means `*RST` firing
// at an instrument because an agent restarted. Retain class belongs to the topic
// family (contracts T5), and a trigger's family is live-event.
window.useMqttTrigger = () => {
    const publish = window.useMqttPublish();
    return React.useCallback((topic, value) => publish(
        topic,
        JSON.stringify({ value, full_id: SESSION_FULL_ID }),
        { retain: false },
    ), [publish]);
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
            // Mouse-capture rule: while THIS control is being actively
            // adjusted locally, the hand owns it — nothing inbound (our own
            // stale broker echoes mid-drag, or a remote peer) may yank it
            // backwards ("jiggle"). Inbound state applies again once the
            // hand has rested for the grace window; by then our own
            // settle-retained echo carries the same value we already show.
            // Per-widget, so a shared_topic twin elsewhere on the page still
            // mirrors the drag live.
            const grace = window.OA_CAPTURE_GRACE_MS || 600;
            if (throttle.current.lastLocal && (Date.now() - throttle.current.lastLocal) < grace) return;
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
    const throttle = React.useRef({ timer: null, pending: false, value: undefined, last: 0, settleTimer: null, lastLocal: 0 });
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
        throttle.current.lastLocal = Date.now(); // mouse-capture marker
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
