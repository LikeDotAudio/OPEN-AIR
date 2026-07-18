/**
 * boot.tsx — the app boot sequence, extracted from FrontEnd/index.html's
 * inline <script type="text/babel"> block (which gen-legacy cannot capture:
 * it has no src). Converted TSX from day one: with browser-Babel gone there
 * is no compile to hide, so the 2.5 s splash-minimum shrinks to a plain
 * loading gate (Phase 2 §4.4 deletes the splash entirely at cutover).
 *
 * The legacy page keeps its inline copy until cutover — the §4 overlap
 * window runs both by design; this file is the bundle's boot half.
 *
 * No service-worker registration here on purpose: the legacy sw.js +
 * ?v=N era ends at cutover with the self-unregistering SW (§4.3a).
 */
import React from 'react'
import { createRoot } from 'react-dom/client'

// Window shapes come from src/globals.d.ts — the generated inventory, where
// MqttProvider / WindowManager / oaGetMqttConfig are hand-typed (3 of 182
// globals burned down from `any` so far).
interface MqttConfig {
  brokerUrl: string
  username: string
  password: string
}

function defaultMqttConfig(): MqttConfig {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return {
    brokerUrl: `${proto}://${window.location.hostname || 'localhost'}:9001`,
    username: 'guest',
    password: 'guest',
  }
}

function App() {
  const [directoryTree, setDirectoryTree] = React.useState<unknown>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    // Live tree first (orchestrator GET /api/tree); static snapshot only as
    // the FTPS-host fallback — same policy as the legacy page (Phase 0 item 2).
    fetch('./api/tree?t=' + Date.now())
      .then((res) => {
        if (!res.ok) throw new Error('live /api/tree unavailable')
        return res.json()
      })
      .catch(() =>
        fetch('./api/tree.json?t=' + Date.now()).then((res) => {
          if (!res.ok) throw new Error('Failed to fetch layout tree (live /api/tree and static ./api/tree.json both unavailable)')
          return res.json()
        }),
      )
      .then((data: unknown) => setDirectoryTree(data))
      .catch((err: unknown) => {
        console.error(err)
        setError(String(err))
      })
  }, [])

  if (error) {
    return (
      <div style={{ padding: '20px', color: '#ff5252' }}>
        <h3>Boot Sequence Error</h3>
        <p>{error}</p>
        <p>Ensure the orchestrator is running (GET /api/tree), or deploy the static tree snapshot.</p>
      </div>
    )
  }

  if (!directoryTree) {
    return (
      <div
        style={{
          display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
          height: '100vh', width: '100vw', backgroundColor: 'black', color: '#f4902c', fontFamily: 'sans-serif',
        }}
      >
        <img
          src="./assets/splash_logo.gif"
          alt="OPEN-AIR Splash"
          style={{ maxWidth: '80%', maxHeight: '60vh', objectFit: 'contain', marginBottom: '20px' }}
        />
        <h2 style={{ letterSpacing: '2px', textTransform: 'uppercase' }}>Booting OPEN-AIR Kernel...</h2>
      </div>
    )
  }

  const mqttCfg = window.oaGetMqttConfig ? window.oaGetMqttConfig() : defaultMqttConfig()

  return (
    <window.MqttProvider brokerUrl={mqttCfg.brokerUrl} username={mqttCfg.username} password={mqttCfg.password}>
      <window.WindowManager directoryTree={directoryTree} />
    </window.MqttProvider>
  )
}

export function boot(): void {
  const el = document.getElementById('root')
  if (!el) throw new Error('boot: #root element missing')
  createRoot(el).render(<App />)
}
