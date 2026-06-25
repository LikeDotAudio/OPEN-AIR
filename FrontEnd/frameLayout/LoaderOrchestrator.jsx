/**
 * LoaderOrchestrator: The main entry point for the React-based GUI engine.
 *
 * MQTT topic alignment: the topic prefix is derived from the frame's FOLDER PATH
 * (window.OaTopicMaker), so the broker tree mirrors the Gui_Frames hierarchy —
 *   /Window_1/left_50/top_100/0_Spectrum/10_YAK/1_N9340B/0_Frequency/x.json
 *   ->  OpenAir/Gui/Spectrum/YAK/N9340B/Frequency
 * Each folder is a topic level instead of the old flat, underscore-joined key
 * (`OpenAir/Gui/Spectrum_YAK_N9340B_Frequency`). When no filePath is available
 * (WYSIWYG preview, grab-bag tiles) we fall back to the bare `OpenAir/Gui` base
 * and keep the JSON root key as the first segment.
 */
window.LoaderOrchestrator = ({ layoutJson, filePath }) => {
    if (!layoutJson) {
        return (
            <div style={{ color: '#888', padding: '40px', textAlign: 'center', background: '#121212', height: '100%' }}>
                <div>Waiting for layout configuration...</div>
            </div>
        );
    }

    // Hierarchical prefix from the folder path, e.g.
    // "OpenAir/Gui/Spectrum/YAK/N9340B/Frequency". Null when there's no filePath
    // (preview/grab-bag) — then we keep the legacy flat-key behaviour.
    const folderPrefix = (window.OaTopicMaker && filePath)
        ? window.OaTopicMaker.buildGuiPrefix(filePath)
        : null;
    const rootPathPrefix = folderPrefix || 'OpenAir/Gui';

    // A frame file's content is EITHER a single node (its root has a `type`, e.g.
    // an unwrapped OcaBin with a `background`) OR a map of named nodes
    // ({ "Frame_Name": { type: ... } }). Detect which so unwrapped roots render as
    // their container (and trigger its background panel) instead of having their
    // own properties (type/geometry/blocks/background) iterated as stray widgets.
    const isSingleNode = typeof layoutJson === 'object' && typeof layoutJson.type === 'string';

    // The folder hierarchy already fully encodes the frame's identity, so the flat
    // JSON root key (which duplicates the whole path, e.g. "Spectrum_YAK_N9340B_Frequency")
    // must NOT be appended again — passing nodeName='' makes the root container
    // skip the `${path_prefix}/${nodeName}` append. We only collapse the key when
    // there is exactly one frame in the file; multiple roots stay disambiguated by
    // their key beneath the shared folder prefix.
    const entries = isSingleNode ? null : Object.entries(layoutJson);
    const collapseRootKey = !!folderPrefix && (isSingleNode || (entries && entries.length === 1));

    return (
        <div className="loader-orchestrator" style={{ width: '100%', height: '100%', backgroundColor: '#121212', color: '#eee' }}>
            {isSingleNode
                ? <window.WidgetFactory nodeName={collapseRootKey ? '' : (layoutJson.id || 'root')} node={layoutJson} path_prefix={rootPathPrefix} jsonPath="" />
                : entries.map(([key, node]) => (
                    <window.WidgetFactory key={key} nodeName={collapseRootKey ? '' : key} node={node} path_prefix={rootPathPrefix} jsonPath={key} />
                ))}
        </div>
    );
};
