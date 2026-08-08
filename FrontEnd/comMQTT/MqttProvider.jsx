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

// Where an instrument's answer lands: the VISA daemon publishes whatever the
// hardware replied to `.../Device/<type>/<model>/<dev>/Read`, and `yak_readout`
// binds a display widget to exactly that topic.
//
// The page subscribed to OpenAir/Gui/# and nothing else, so a readout was bound
// to a topic the browser never received — every reply arrived on the bus and no
// widget could see it. Pressing READ IDENTITY worked end to end and still showed
// "---".
//
// Scoped to the reply leaf rather than the device tree: the discovery topics
// under it are already delivered as Discovered table rows, and subscribing to
// the whole tree would put every attribute of every instrument through the
// React store for nothing.
const OA_VISA_READ_FILTER = 'OpenAir/System/Protocols/visa/Device/+/+/+/Read';

// Named readings — one retained topic per value the instrument reported, split
// out of a compound reply by YAK using the command's declared `returns` block
// (BackEnd/openair-yak/src/readings.rs). A `yak_listen` control binds to one of
// these BY NAME. Without this subscription every listener sits at its authored
// default while the readings it wants are on the bus, which is the same failure
// `/Read` had before it was subscribed.
const OA_VISA_READING_FILTER = 'OpenAir/System/Protocols/visa/Device/+/+/+/Reading/#';
const OA_ACTIVITY_TOPICS = new Set([OA_SCAN_LOG_TOPIC, OA_DISCOVERY_ACTIVITY_TOPIC, OA_YAK_ACTIVITY_TOPIC]);

// ── Discovery activity store ────────────────────────────────────────────────
//
// Deliberately OUTSIDE React state. Scan narration arrives in bursts of dozens
// of lines; holding it in the provider's context would re-render the whole
// widget tree per line. Components that want it subscribe individually via
// window.useDiscoveryActivity(), so a burst only re-renders the feed itself.
const OA_ACTIVITY_MAX = 300;

// Unit conversion, so a control can be told a value in the instrument's units
// and display it in its own.
//
// An instrument answers in its native unit — the N9340B reports frequency in Hz
// — while the panel is built in MHz. Without this the readback either shows
// 8e+08 in a box labelled MHz, or every widget carries a hand-computed scale
// factor that nobody can audit. A unit is a fact about the value; a scale factor
// is a guess about the reader.
//
// Ratios to a base unit per quantity. Conversion is only defined WITHIN a
// quantity: Hz→MHz is arithmetic, Hz→dBm is not, and returning the value
// unchanged is the honest answer for the latter.
window.OaUnits = (() => {
    const FAMILIES = [
        { base: 'Hz', units: { hz: 1, khz: 1e3, mhz: 1e6, ghz: 1e9 } },
        { base: 'V',  units: { uv: 1e-6, mv: 1e-3, v: 1, kv: 1e3 } },
        { base: 's',  units: { ns: 1e-9, us: 1e-6, ms: 1e-3, s: 1 } },
        { base: 'W',  units: { uw: 1e-6, mw: 1e-3, w: 1, kw: 1e3 } },
    ];
    const norm = (u) => String(u == null ? '' : u).trim().toLowerCase().replace('μ', 'u');
    const familyOf = (u) => FAMILIES.find(f => Object.prototype.hasOwnProperty.call(f.units, norm(u)));

    // Scale a decimal by a power of ten by MOVING THE POINT, not by multiplying.
    //
    // Every unit pair in the table above is a power of ten apart, and that is
    // exactly the multiplication binary floating point cannot do: 665551000 Hz
    // / 1e6 is 665.5509999999999, and 2057.515 MHz * 1e6 is 2057514999.9999998
    // — which is what a centre-frequency write actually carried to the N9340B.
    // Rounding the product afterwards only replaces the artefact with a
    // different one on the next value. Shifting the digit string is exact for
    // every input, because a power of ten IS the decimal point's position.
    //
    // Mirrors shift_decimal() in BackEnd/openair-yak/src/converters.rs — the
    // same value crosses both, and they must agree digit for digit.
    const shiftDecimal = (text, power) => {
        const s = String(text).trim();
        const m = /^([+-]?)(\d*)(?:\.(\d*))?$/.exec(s);
        if (!m) return null;                       // exponent form, unit, keyword
        const sign = m[1] === '-' ? '-' : '';
        const int = m[2] || '';
        const frac = m[3] || '';
        if (!int && !frac) return null;

        const digits = int + frac;
        const point = int.length + power;
        let whole, fraction;
        if (point <= 0) {
            whole = '0';
            fraction = '0'.repeat(-point) + digits;
        } else if (point >= digits.length) {
            whole = digits + '0'.repeat(point - digits.length);
            fraction = '';
        } else {
            whole = digits.slice(0, point);
            fraction = digits.slice(point);
        }
        whole = whole.replace(/^0+(?=\d)/, '');
        fraction = fraction.replace(/0+$/, '');
        const out = sign + whole + (fraction ? `.${fraction}` : '');
        return out === '-0' ? '0' : out;
    };

    // Returns the numeric value expressed in `to`, or the input unchanged when
    // the pair is not convertible (unknown unit, different quantity, non-numeric).
    const convert = (value, from, to) => {
        const n = Number(value);
        if (!Number.isFinite(n)) return value;
        const f = norm(from), t = norm(to);
        if (!f || !t || f === t) return n;
        const fam = familyOf(f);
        if (!fam || fam !== familyOf(t)) return n;
        // log10 of the ratio is an integer for every pair in FAMILIES; Math.round
        // absorbs the float error in the log itself, not in the value.
        const power = Math.round(Math.log10(fam.units[f] / fam.units[t]));
        const shifted = shiftDecimal(value, power);
        // Number() of an exact decimal string is the nearest f64 to it, which
        // prints back as that same string — the artefact only ever came from
        // the arithmetic, never from holding the value.
        if (shifted !== null) return Number(shifted);
        return n * (fam.units[f] / fam.units[t]);
    };
    return { convert, norm, familyOf, shiftDecimal };
})();

// What a `<topic>/config` message is allowed to contain.
//
// A widget node carries its layout, both style blocks, and four-language label
// sets for every option. YAK — the ONLY subscriber to this family — reads
// `yak_handler` and discards the rest, so nine tenths of every config message
// measured on the wire was presentation data that nothing opens. Worse, 22 of
// the 30 configs in that capture had no `yak_handler` at all: publishes that
// could not be consumed by anyone, under any circumstance.
//
// Returning null for those is the point, not an edge case — the caller skips
// the publish entirely rather than sending an empty envelope.
//
// If a second consumer of `<topic>/config` ever appears, widen this projection
// rather than reverting to the whole node. Style and i18n already live in the
// panel JSON on disk, which the GUI loads over HTTP; putting them on the broker
// duplicated a source of truth with its own lifetime.
window.oaConfigForBus = (node) =>
    (node && node.yak_handler) ? { yak_handler: node.yak_handler } : null;
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

window.MqttProvider = ({ brokerUrl = 'wss://test.mosquitto.org:8081/ws', username = '', password = '', children }) => {
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
            // Instrument replies, so `yak_readout` widgets can show them.
            mqttClient.subscribe(OA_VISA_READING_FILTER, (err) => {
                if (!err) console.log(`📥 [VISA] watching ${OA_VISA_READING_FILTER} — named readings feed listening controls`);
            });
            mqttClient.subscribe(OA_VISA_READ_FILTER, (err) => {
                if (!err) console.log(`📥 [VISA] watching ${OA_VISA_READ_FILTER} — instrument replies will fill readouts`);
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
// Is this widget a trigger rather than a state?
//
// Canonical here because MqttProvider owns publish semantics and loads before
// anything renders; ButtonToggle asks at render time. An ACTUATOR fires once per
// press and has no value to rest at — which decides both how it publishes and
// whether it may be seeded at all.
window.OaIsMomentaryControl = (node) => {
    if (node && typeof node.momentary === 'boolean') return node.momentary;
    return String((node && node.type) || '').toLowerCase().includes('actuator');
};

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

    // A widget INSTANCE is reused when the panel moves between device
    // instantiations: same component, same position in the tree, different
    // topic. React keeps its state across that, which broke two things at once.
    //
    // The visible one: the previous instrument's button positions bleed into the
    // next instrument's tab — eight 34401As each showing whatever the meter
    // before it was set to. The sync effect above cannot correct it, because it
    // only fires once the NEW topic already has a value.
    //
    // The invisible one, and the worse of the two: `initialPublishDone` stayed
    // true, so the new topic's `/config` was never published. That config is how
    // YAK learns a control's yak_handler, so every device after the first had no
    // handler cached and its buttons did nothing at all — which is exactly how
    // it looked from the outside.
    const previousTopic = React.useRef(topic);
    if (previousTopic.current !== topic) {
        previousTopic.current = topic;
        initialPublishDone.current = false;
        // Adopt the new topic's own value if it has one; otherwise fall back to
        // the default rather than showing the last instrument's state.
        if (messages[topic] === undefined) setLocalValue(defaultValue);
    }

    React.useEffect(() => {
        if (publish && nodeJson && !initialPublishDone.current) {
            // Only the handler goes on the bus — see oaConfigForBus. The seeding
            // below is unconditional regardless, because a widget with no
            // yak_handler still has a position a late joiner needs to see.
            const busConfig = window.oaConfigForBus(nodeJson);
            if (busConfig) publish(`${topic}/config`, JSON.stringify(busConfig));

            // Ask the instrument where it is, once, as the panel comes up.
            //
            // Otherwise every control opens showing its authored default and
            // stays wrong until someone touches it — the panel asserting a state
            // it never verified. Gated on yak_type "nab" AND an explicit opt-in:
            // a query is safe to fire unbidden, a SET or DO is emphatically not.
            // Momentary controls are never seeded for that same reason, and this
            // must not become a loophole around it.
            if (nodeJson.yak_nab_on_load === true
                && nodeJson.yak_handler
                && String(nodeJson.yak_handler.yak_type).toLowerCase() === 'nab') {
                publish(topic, JSON.stringify({ value: 1, full_id: SESSION_FULL_ID }), { retain: false });
            }
            // A trigger is never seeded. The seed exists so a late joiner sees a
            // control's initial position, which is meaningless for something that
            // has no position — and actively harmful once the value is a command:
            // YAK executes on ANY value reaching a bound topic, so seeding
            // `{value:false}` on mount fired the widget's command simply because
            // its tab was opened. On an instrument Setup page that is a `*RST`
            // for walking into the room.
            // Nor is a READOUT seeded, for a sharper reason: `yak_readout`
            // points the widget at the instrument's `/Read` topic, so seeding
            // publishes the placeholder ("---") ON TOP of whatever the
            // instrument last answered. A display-only widget must never write
            // to the topic it displays.
            const seedable = !(window.OaIsMomentaryControl
                && window.OaIsMomentaryControl(nodeJson))
                && nodeJson.yak_readout !== true;
            if (seedable && messages[topic] === undefined) {
                // Include full_id so Python's broker doesn't mistake this
                // for one of its own reflections (see SESSION_FULL_ID above).
                const payload = (typeof defaultValue === 'object' && defaultValue !== null) ? { ...defaultValue, full_id: SESSION_FULL_ID } : { value: defaultValue, full_id: SESSION_FULL_ID };
                publish(topic, JSON.stringify(payload));
            }
            initialPublishDone.current = true;
        }
    }, [publish, topic, nodeJson, defaultValue, messages]);

    // Hydrate from what the instrument reported.
    //
    // A control's own topic only ever carries what the PANEL last sent, so on a
    // fresh load every slider showed its authored default — 500 MHz centre while
    // the instrument was actually at 800. `yak_hydrate` points a control at the
    // device's `/Read` topic (stamped by instruments.rs, same as yak_readout),
    // `yak_hydrate_index` picks its field out of the compound reply, and
    // `yak_hydrate_unit` declares the unit the INSTRUMENT answered in — a raw
    // SCPI reply cannot carry one, so the panel states it. The value is then
    // converted into whatever unit this control displays.
    //
    // This NEVER publishes. The instrument telling the panel where it is must
    // not read as the operator asking it to move: publishing here would return
    // through YAK as a fresh command, and the panel would command the instrument
    // to the value it just reported, forever.
    // `yak_listen_topic` is the NAMED reading this control listens to — one
    // value, already split out and carrying the unit the instrument reported in
    // (see BackEnd/openair-yak/src/readings.rs). It supersedes the positional
    // `yak_hydrate_index`, which counted separators and pointed at the wrong
    // quantity the moment a reply gained a field. The index path is kept only
    // for panels not yet migrated.
    // A DERIVED state: on only when every named reading matches its expected
    // value. Shares the same readback as the controls it overlaps, so all of
    // them refresh from one instrument round trip and none can drift out of
    // agreement with the hardware.
    const listenAll = nodeJson && nodeJson.yak_listen_all_topics;
    const listenAllKey = listenAll
        ? Object.keys(listenAll).map(t => `${t}=${messages[t]}`).join('|')
        : null;
    React.useEffect(() => {
        if (!listenAll) return;
        const entries = Object.entries(listenAll);
        if (entries.some(([t]) => messages[t] === undefined)) return;   // not all in yet
        const matches = entries.every(([t, want]) => {
            let v = messages[t];
            try { const p = JSON.parse(v); if (p && p.value !== undefined) v = p.value; } catch (e) {}
            return String(v).trim() === String(want).trim();
        });
        const grace = window.OA_CAPTURE_GRACE_MS || 600;
        if (throttle.current.lastLocal && (Date.now() - throttle.current.lastLocal) < grace) return;
        setLocalValue(matches ? 'ON' : 'OFF');
    }, [listenAllKey]);

    const listenTopic = nodeJson && (nodeJson.yak_listen_topic || nodeJson.yak_hydrate_topic);
    const hydrateRaw = listenTopic ? messages[listenTopic] : undefined;
    React.useEffect(() => {
        if (hydrateRaw === undefined) return;
        const text = String(hydrateRaw);

        let raw;
        let sourceUnit = nodeJson.yak_hydrate_unit;
        // A named reading arrives as a ControlValue: {value, unit, ...}. The
        // unit travels WITH the value, so the panel no longer has to assert what
        // the instrument meant — see contracts/src/control-value.ts.
        let parsed;
        try { parsed = JSON.parse(text); } catch (e) { parsed = undefined; }
        if (parsed && typeof parsed === 'object' && parsed.value !== undefined) {
            raw = parsed.value;
            if (parsed.unit) sourceUnit = parsed.unit;
        } else {
            const idx = nodeJson.yak_hydrate_index;
            const field = (idx === undefined || idx === null) ? text : text.split(';')[idx];
            if (field === undefined) return;
            raw = String(field).trim();
        }
        const n = Number(raw);

        // Same mouse-capture rule as the sync effect: a reply that lands mid-drag
        // must not yank the control out from under the hand.
        const grace = window.OA_CAPTURE_GRACE_MS || 600;
        if (throttle.current.lastLocal && (Date.now() - throttle.current.lastLocal) < grace) return;

        // NOT every reading is a number.
        //
        // `:TRACe1:MODE?` answers `WRIT`, `:INSTrument:SELect?` answers `SA`.
        // Bailing on !isFinite meant no ENUMERATED reading ever reached a
        // control: all four trace-mode dropdowns sat on their first option
        // while the instrument was in four different modes, and nothing in the
        // UI ever contradicted them. A non-numeric reading is passed through
        // verbatim — there is no unit to convert and no precision to round, and
        // the widget matches it against its own options.
        //
        // Only a control that DECLARES a set of choices takes this path. A
        // slider or a number box has nothing to do with a word, and the VISA
        // daemon answers a failed query with the literal text `ERROR: …` —
        // which decomposes into field 0 of the reply and would otherwise be
        // shown as a value.
        //
        // `positions` counts as declaring them. A rotary selector spells its
        // choices that way (SelectorSwitch.jsx) rather than as `options`, so
        // gating on `options` alone silently dropped every word aimed at one:
        // the generator's waveform dial sat on SINE while `FUNCtion?` answered
        // SQU, with nothing on screen to contradict it — the same failure the
        // trace-mode dropdowns had before this branch existed.
        //
        // A READOUT counts as declaring them too, and for the same reason the
        // dial does: `FUNCtion?` answers SIN, and the Instrument Readback row's
        // Shape box sat on its authored 0 forever because a word could not
        // reach it. A display with no `yak_handler` commands nothing, so there
        // is no wrong value for it to send — the only question is whether it
        // shows what the instrument said, and a number-only rule answers no to
        // every enumerated reply on the panel.
        if (!Number.isFinite(n)) {
            const s = String(raw).trim();
            const kind = String((nodeJson && nodeJson.type) || '');
            const isReadout = !nodeJson.yak_handler
                && /value|label|text|readout|display/i.test(kind);
            if (!s || !(nodeJson.options || nodeJson.positions || isReadout)) return;
            setLocalValue(s);
            return;
        }

        // A LEVEL in dB, from a reading the instrument gives in volts.
        //
        // No scope on this bench answers a dB query — `MEAS:DB?` was a panel
        // literal the YAK crawler copied back, not a command on either family —
        // so a dB box bound to a dB reading could never fill. It is the same
        // quantity either way: 20·log10(Vrms / 1 V) is the RMS reading in dBV,
        // and the widget's units name that reference rather than leaving an
        // unstated one. Zero or below has no logarithm and stays a dash; a
        // silent 0 dB would read as a measurement.
        if (nodeJson.yak_listen_transform === 'dbv') {
            const volts = window.OaUnits.convert(n, sourceUnit || 'V', 'V');
            setLocalValue(volts > 0 ? Number((20 * Math.log10(volts)).toFixed(3)) : '—');
            return;
        }

        // ONE BIT OF A STATUS REGISTER, as the thing that bit means.
        //
        // `STAT:OPER:COND?` answers 1024 when a supply is holding its current
        // limit and 256 when it is holding its voltage. Bound raw, an indicator
        // shows "1024", which is not a state anyone reads — and the two are not
        // even ordered, so no threshold widget can tell them apart either.
        // `{op:"bit", index:10, set:"red", clear:"green"}` says which bit and
        // what it looks like, and the panel names the register once.
        const tf = nodeJson.yak_listen_transform;
        if (tf && typeof tf === 'object' && tf.op === 'bit') {
            const on = (Math.trunc(Math.abs(n)) & (1 << Number(tf.index || 0))) !== 0;
            setLocalValue(on ? (tf.set ?? 1) : (tf.clear ?? 0));
            return;
        }

        const target = nodeJson.units || (nodeJson.domain && nodeJson.domain.units);
        // 665551000 Hz / 1e6 used to be 665.5509999999999 in the box, and the
        // fix was to round to 9 significant figures. That hid the artefact
        // rather than removing it — and it also silently discarded real
        // resolution, since a centre frequency in Hz is already 10 digits.
        // OaUnits.convert now moves the decimal point instead of multiplying,
        // so the value is exact and there is nothing left to round away.
        setLocalValue(window.OaUnits.convert(n, sourceUnit, target));
    }, [hydrateRaw, listenTopic]);

    // Per-topic outbound throttle (see PUBLISH_INTERVAL_MS). `pending` holds the
    // latest value awaiting a trailing publish; `last` is the wall-clock time of
    // the most recent publish. Cleared on unmount/topic change so a drag that
    // ends as the widget unmounts can't fire a publish into a dead client.
    const throttle = React.useRef({ timer: null, pending: false, value: undefined, last: 0, settleTimer: null, lastLocal: 0, lastSent: undefined });
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

            // Publish only what is NEW.
            //
            // The throttle above bounds the RATE; it never asked whether the
            // value MOVED. At 22 ms that is ~45 publishes a second of whatever
            // the control currently reads — so a drag that lingers on one step,
            // or a widget that re-fires setValue with an unchanged value, put
            // the same number on the bus over and over. On a bound control every
            // one of those is a real instrument write: a single Reference Level
            // drag sent `:DISPlay:WINDow:TRACe:Y:RLEVel -40` to the N9340B
            // dozens of times, each a round trip over VXI-11 to set a value the
            // instrument was already at.
            //
            // Momentary controls are exempt, and must be: pressing a trigger
            // twice is two intended actions carrying an identical payload, and
            // collapsing them would silently swallow the second press.
            const serialized = JSON.stringify(makePayload());
            if (!isMomentary && serialized === state.lastSent) return;

            state.lastSent = serialized;
            state.last = Date.now();
            publish(topic, serialized, { retain: false });
        };

        // The settle publish exists so a late joiner can restore a control's
        // resting position. A COMMAND topic has no resting position to restore,
        // and sending one costs a second execution: YAK fires on any value
        // arriving at a bound topic, and MQTT clears the retain flag on delivery
        // to an already-subscribed client, so the settle arrives looking exactly
        // like a fresh press. Every bound control was therefore running its
        // command twice per change — visible in the agent log as each RX EXECUTE
        // appearing twice with an identical payload and full_id.
        //
        // Retain class belongs to the topic family (contracts T5), and a command
        // topic's family is live-event.
        const isCommand = !!(nodeJson && nodeJson.yak_handler);
        // Read once per change, not inside flush: a trailing flush can run after
        // the widget's props have moved on, and the exemption must reflect the
        // control that was actually being operated.
        const isMomentary = !!(window.OaIsMomentaryControl && window.OaIsMomentaryControl(nodeJson));
        if (!isCommand) {
            const RETAIN_SETTLE_MS = 400;
            if (state.settleTimer) clearTimeout(state.settleTimer);
            state.settleTimer = setTimeout(() => {
                state.settleTimer = null;
                publish(topic, JSON.stringify(makePayload())); // retained: the resting value
            }, RETAIN_SETTLE_MS);
        }

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
