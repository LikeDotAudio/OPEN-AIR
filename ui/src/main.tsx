/**
 * ui/ entry point — Phase 2 Step 1.
 *
 * The unconverted legacy graph (../FrontEnd, via ./legacy.ts) was written
 * for a world where React, ReactDOM, echarts, and mqtt arrive as CDN
 * globals before any app script runs. The bundle recreates that world from
 * the npm singletons — SAME React instance for converted imports and
 * unconverted window-readers — then imports the legacy graph in exact
 * script-tag order.
 *
 * NOTE: not the runtime yet. FrontEnd/index.html remains the only served
 * app until the §4 overlap window opens deliberately.
 */
import * as echarts from 'echarts'
import mqtt from 'mqtt'
import React from 'react'
import ReactDOM from 'react-dom'
import * as ReactDOMClient from 'react-dom/client'

// echarts-gl registers itself into echarts on import (side effect).
import 'echarts-gl'

declare global {
  interface Window {
    React: typeof React
    ReactDOM: typeof ReactDOM & Partial<typeof ReactDOMClient>
    echarts: typeof echarts
    mqtt: typeof mqtt
  }
}

window.React = React
// The legacy graph calls both ReactDOM.render-era and createRoot-era APIs.
window.ReactDOM = { ...ReactDOM, ...ReactDOMClient }
window.echarts = echarts
window.mqtt = mqtt

// Legacy graph LAST — globals above must exist first, exactly like the
// old <script> order guaranteed.
import('./legacy')

export {}
