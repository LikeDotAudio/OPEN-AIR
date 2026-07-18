/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** MQTT-over-WebSocket broker URL (default ws://localhost:9001). */
  readonly VITE_MQTT_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
