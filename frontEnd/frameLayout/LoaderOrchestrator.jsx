import React from 'react';
import WidgetFactory from './WidgetFactory';
import { MqttProvider } from '../comMQTT/MqttProvider';

/**
 * LoaderOrchestrator: The main entry point for the React-based GUI engine.
 * It wraps the layout in an MqttProvider and starts the recursive rendering via WidgetFactory.
 */
const LoaderOrchestrator = ({ layoutJson, brokerUrl }) => {
    if (!layoutJson) {
        return (
            <div style={{ color: '#888', padding: '40px', textAlign: 'center', background: '#121212', height: '100vh' }}>
                <div style={{ fontSize: '24px', marginBottom: '10px' }}>⚖️ OPEN-AIR</div>
                <div>Waiting for layout configuration...</div>
            </div>
        );
    }

    return (
        <MqttProvider brokerUrl={brokerUrl}>
            <div className="loader-orchestrator" style={{ width: '100%', height: '100vh', backgroundColor: '#121212', color: '#eee' }}>
                {Object.entries(layoutJson).map(([key, node]) => (
                    <WidgetFactory key={key} nodeName={key} node={node} />
                ))}
            </div>
        </MqttProvider>
    );
};

export default LoaderOrchestrator;

// Compatibility for legacy global script loading
if (typeof window !== 'undefined') {
    window.LoaderOrchestrator = LoaderOrchestrator;
}
