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

    // A frame file's content is EITHER a single node (its root has a `type`, e.g.
    // an unwrapped OcaBin with a `background`) OR a map of named nodes
    // ({ "Frame_Name": { type: ... } }). Detect which so unwrapped roots render as
    // their container (and trigger its background panel) instead of having their
    // own properties (type/geometry/blocks/background) iterated as stray widgets.
    const isSingleNode = typeof layoutJson === 'object' && typeof layoutJson.type === 'string';

    return (
        <div className="loader-orchestrator" style={{ width: '100%', height: '100%', backgroundColor: '#121212', color: '#eee' }}>
            {isSingleNode
                ? <window.WidgetFactory nodeName={layoutJson.id || 'root'} node={layoutJson} jsonPath="" />
                : Object.entries(layoutJson).map(([key, node]) => (
                    <window.WidgetFactory key={key} nodeName={key} node={node} jsonPath={key} />
                ))}
        </div>
    );
};
