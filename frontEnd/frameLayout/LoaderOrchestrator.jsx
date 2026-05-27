/**
 * LoaderOrchestrator: The main entry point for the React-based GUI engine.
 *
 * MQTT topic alignment: this side uses the JSON root key as the first sub-segment
 * under `OpenAir/Gui/`, matching Python's TopicCalculator output
 * (`OpenAir/Gui/<json_root>/<sub_block>/<leaf>`). filePath is intentionally
 * NOT injected here — Python's TopicCalculator collapses the file-walker
 * hierarchy to just `Gui`, so adding the file walk on the web side would
 * desync the two trees. The `filePath` prop is still accepted in case other
 * features want it later.
 */
window.LoaderOrchestrator = ({ layoutJson, filePath }) => {
    if (!layoutJson) {
        return (
            <div style={{ color: '#888', padding: '40px', textAlign: 'center', background: '#121212', height: '100%' }}>
                <div>Waiting for layout configuration...</div>
            </div>
        );
    }

    const rootPathPrefix = 'OpenAir/Gui';

    // A frame file's content is EITHER a single node (its root has a `type`, e.g.
    // an unwrapped OcaBin with a `background`) OR a map of named nodes
    // ({ "Frame_Name": { type: ... } }). Detect which so unwrapped roots render as
    // their container (and trigger its background panel) instead of having their
    // own properties (type/geometry/blocks/background) iterated as stray widgets.
    const isSingleNode = typeof layoutJson === 'object' && typeof layoutJson.type === 'string';

    return (
        <div className="loader-orchestrator" style={{ width: '100%', height: '100%', backgroundColor: '#121212', color: '#eee' }}>
            {isSingleNode
                ? <window.WidgetFactory nodeName={layoutJson.id || 'root'} node={layoutJson} path_prefix={rootPathPrefix} jsonPath="" />
                : Object.entries(layoutJson).map(([key, node]) => (
                    <window.WidgetFactory key={key} nodeName={key} node={node} path_prefix={rootPathPrefix} jsonPath={key} />
                ))}
        </div>
    );
};
