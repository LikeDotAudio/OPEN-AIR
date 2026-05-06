/**
 * LoaderOrchestrator: The main entry point for the React-based GUI engine.
 */
window.LoaderOrchestrator = ({ layoutJson }) => {
    if (!layoutJson) {
        return (
            <div style={{ color: '#888', padding: '40px', textAlign: 'center', background: '#121212', height: '100%' }}>
                <div>Waiting for layout configuration...</div>
            </div>
        );
    }

    return (
        <div className="loader-orchestrator" style={{ width: '100%', height: '100%', backgroundColor: '#121212', color: '#eee' }}>
            {Object.entries(layoutJson).map(([key, node]) => (
                <window.WidgetFactory key={key} nodeName={key} node={node} />
            ))}
        </div>
    );
};
