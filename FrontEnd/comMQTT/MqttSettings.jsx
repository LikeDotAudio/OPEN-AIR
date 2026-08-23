/**
 * Header: MqttSettings.jsx
 * Purpose: MQTT connection settings modal + shared config reader.
 * Description: Lets the user choose HOW the browser connects to a broker —
 *   host, port, WebSocket transport (ws vs wss/TLS), path, and optional auth —
 *   persisting the choice to localStorage. Browsers can only speak MQTT over
 *   WebSockets, so transport is always ws/wss (never raw TCP 1883/8883).
 *
 * Version: 26.07.10.1
 */

(function () {
  const KEY = 'oa_mqtt_settings';

  // Default broker used when there is no saved profile and no ?mqtt= override.
  //
  // Defaults to THIS HOST — the broker that `docker compose` (or a native
  // `mosquitto -c broker/mosquitto.conf`) publishes on :9001. That is the real
  // system: your agents, your instruments, your discovery. The public Eclipse
  // test broker is the *other* preset, for demos and UI work with no backend.
  //
  // Anonymous by default: both broker configs in this repo set
  // `allow_anonymous true` and neither defines a password file. If you enable
  // auth (see broker/acl.example), set credentials in the modal.
  const LOCAL_DEFAULTS = {
    host: 'test.mosquitto.org',
    port: 8081,
    encrypted: true,
    path: '',
    username: '', password: '',
  };
  const DEFAULTS = LOCAL_DEFAULTS;

  const read = () => {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; }
    catch (e) { return {}; }
  };

  // Shared by index.html to build the live broker URL + auth. Saved settings win;
  // ?mqtt= still overrides the host for quick shares; else fall back to DEFAULTS.
  window.oaGetMqttConfig = function () {
    const s = read();
    const params = new URLSearchParams(window.location.search);
    const hasSaved = localStorage.getItem(KEY) !== null;
    const host = params.get('mqtt') || s.host || DEFAULTS.host;
    const encrypted = (typeof s.encrypted === 'boolean') ? s.encrypted : DEFAULTS.encrypted;
    const proto = encrypted ? 'wss' : 'ws';
    const port = s.port || DEFAULTS.port;
    const path = s.path || DEFAULTS.path;
    // An explicit saved profile may carry credentials; the default is anonymous.
    const username = hasSaved ? (s.username || '') : DEFAULTS.username;
    const password = hasSaved ? (s.password || '') : DEFAULTS.password;
    return { brokerUrl: `${proto}://${host}:${port}${path}`, username, password };
  };

  // Two presets, because there are two real situations: run the actual system,
  // or poke at the UI with no backend.
  const PRESETS = [
    {
      label: 'Docker / this host · your broker (ws:9001)',
      hint: 'The real system — docker compose, or a native broker on :9001',
      host: (window.location.hostname || 'localhost'),
      port: 9001,
      encrypted: (window.location.protocol === 'https:'),
      path: '', username: '', password: '',   // anonymous: see broker configs
    },
    {
      label: 'Public test broker · test.mosquitto.org (wss:8081)',
      hint: 'Demo / UI-only. Public and unauthenticated — never send real data',
      host: 'test.mosquitto.org',
      port: 8081,
      encrypted: true,   // TLS works from both http and https pages
      path: '', username: '', password: '',
    },
  ];

  const fieldStyle = {
    background: '#111', color: '#eee', border: '1px solid #444',
    borderRadius: '3px', padding: '6px 8px', fontSize: '13px', width: '100%',
    boxSizing: 'border-box', fontFamily: 'monospace',
  };
  const labelStyle = { fontSize: '10px', color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'block' };

  window.MqttSettingsModal = ({ onClose }) => {
    const pageHttps = window.location.protocol === 'https:';
    const saved = read();

    const [host, setHost] = React.useState(saved.host || DEFAULTS.host);
    const [port, setPort] = React.useState(saved.port || DEFAULTS.port);
    const [encrypted, setEncrypted] = React.useState(typeof saved.encrypted === 'boolean' ? saved.encrypted : DEFAULTS.encrypted);
    const [path, setPath] = React.useState(saved.path || DEFAULTS.path);
    const [username, setUsername] = React.useState(saved.username || DEFAULTS.username);
    const [password, setPassword] = React.useState(saved.password || DEFAULTS.password);

    const url = `${encrypted ? 'wss' : 'ws'}://${host}:${port}${path || ''}`;
    const mixedContent = pageHttps && !encrypted;

    const applyPreset = (p) => {
      setHost(p.host); setPort(p.port); setEncrypted(p.encrypted);
      setPath(p.path || ''); setUsername(p.username || ''); setPassword(p.password || '');
    };

    const reloadTo = () => {
      const u = new URL(window.location.href);
      u.searchParams.delete('mqtt'); // saved settings win over a stale ?mqtt=
      window.location.href = u.toString();
    };

    const connect = () => {
      localStorage.setItem(KEY, JSON.stringify({
        host: host.trim(), port: Number(port) || 9001, encrypted,
        path: path.trim(), username: username.trim(), password,
      }));
      reloadTo();
    };

    const resetAuto = () => { localStorage.removeItem(KEY); reloadTo(); };

    return (
      <div
        onClick={onClose}
        style={{ position: 'fixed', inset: 0, zIndex: 10000, background: 'rgba(0,0,0,0.7)',
                 display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}
      >
        <div
          onClick={(e) => e.stopPropagation()}
          style={{ width: '460px', maxWidth: '92vw', maxHeight: '90vh', overflowY: 'auto',
                   background: '#1c1c1c', border: '1px solid #f4902c', borderRadius: '6px',
                   padding: '20px', color: '#eee', boxShadow: '0 10px 40px rgba(0,0,0,0.6)' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ margin: 0, color: '#f4902c', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '15px' }}>MQTT Connection</h3>
            <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#888', fontSize: '20px', cursor: 'pointer', lineHeight: 1 }}>×</button>
          </div>

          <div style={{ fontSize: '11px', color: '#999', marginBottom: '10px', lineHeight: 1.4 }}>
            Browsers speak MQTT only over <b>WebSockets</b> — pick a <code>ws</code> (plain) or <code>wss</code> (TLS) endpoint. Raw-TCP ports (1883 / 8883) are not reachable from a browser.
          </div>

          {/* Presets */}
          <label style={labelStyle}>Quick presets</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '16px' }}>
            {PRESETS.map((p) => {
              // Highlight the preset that matches what is currently in the form,
              // so it is obvious which of the two you are on.
              const active = (p.host === host && String(p.port) === String(port) && p.encrypted === encrypted);
              return (
              <button key={p.label} onClick={() => applyPreset(p)}
                style={{ textAlign: 'left', background: active ? '#2f2a20' : '#262626', color: '#ddd',
                         border: `1px solid ${active ? '#f4902c' : '#3a3a3a'}`,
                         borderRadius: '3px', padding: '7px 10px', fontSize: '12px', cursor: 'pointer' }}>
                <div style={{ color: active ? '#f4902c' : '#ddd' }}>
                  {active ? '● ' : ''}{p.label}
                </div>
                {p.hint && (
                  <div style={{ fontSize: '10px', color: '#8a8a8a', marginTop: '2px' }}>{p.hint}</div>
                )}
              </button>
              );
            })}
          </div>

          {/* Fields */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '10px', marginBottom: '10px' }}>
            <div>
              <label style={labelStyle}>Host</label>
              <input style={fieldStyle} value={host} onChange={(e) => setHost(e.target.value)} placeholder="test.mosquitto.org" />
            </div>
            <div>
              <label style={labelStyle}>Port</label>
              <input style={fieldStyle} type="number" value={port} onChange={(e) => setPort(e.target.value)} />
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '10px 0' }}>
            <input id="mqtt-enc" type="checkbox" checked={encrypted} onChange={(e) => setEncrypted(e.target.checked)} />
            <label htmlFor="mqtt-enc" style={{ fontSize: '12px', color: '#ccc' }}>Encrypted (TLS / <code>wss://</code>)</label>
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label style={labelStyle}>Path (optional)</label>
            <input style={fieldStyle} value={path} onChange={(e) => setPath(e.target.value)} placeholder="(blank for test.mosquitto.org)" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
            <div>
              <label style={labelStyle}>Username (blank = anonymous)</label>
              <input style={fieldStyle} value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>Password</label>
              <input style={fieldStyle} type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
          </div>

          {/* Live URL preview */}
          <div style={{ background: '#000', border: '1px solid #333', borderRadius: '3px', padding: '8px 10px',
                        fontFamily: 'monospace', fontSize: '12px', color: '#0f0', marginBottom: '10px', wordBreak: 'break-all' }}>
            {url}
          </div>

          {mixedContent && (
            <div style={{ background: '#3a1a1a', border: '1px solid #a33', borderRadius: '3px', padding: '8px 10px',
                          fontSize: '11px', color: '#f88', marginBottom: '12px', lineHeight: 1.4 }}>
              ⚠️ This page is served over HTTPS, so the browser will <b>block a plain <code>ws://</code></b> connection.
              Enable <b>Encrypted (wss)</b> — e.g. test.mosquitto.org port <b>8081</b> — or open the app over http/localhost.
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '6px' }}>
            <button onClick={resetAuto}
              style={{ background: 'none', color: '#888', border: '1px solid #444', borderRadius: '3px', padding: '8px 12px', fontSize: '12px', cursor: 'pointer' }}>
              Reset to auto
            </button>
            <button onClick={connect}
              style={{ background: '#f4902c', color: '#111', border: 'none', borderRadius: '3px', padding: '8px 16px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>
              Connect &amp; reload
            </button>
          </div>
        </div>
      </div>
    );
  };
})();
