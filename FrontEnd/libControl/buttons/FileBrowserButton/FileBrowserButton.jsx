/**
 * Header: FileBrowserButton.jsx
 * Purpose: FileBrowserButton library control component.
 * Description: Renders a native browser file picker button for selecting files/folders
 *              and publishes the chosen path via MQTT and React state.
 *
 * Version: 26.08.11.1
 */

const FileBrowserButton = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const [val, setVal] = useMqtt ? useMqttState(topic, value || '', nodeJson) : [value || '', onChange, 'En'];
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];
    const publish = window.useMqttPublish ? window.useMqttPublish() : null;

    const fileInputRef = React.useRef(null);

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const label = getLocalizedText(config?.identity?.label || config?.label, "SELECT FILE");
    const activeText = getLocalizedText(config?.identity?.label?.active || config?.label_active, "SELECTING FILE...");
    const inactiveText = getLocalizedText(config?.identity?.label?.inactive || config?.label_inactive, label || "BROWSE FILE");

    const layout = config?.layout || config?.geometry || {};
    const cssLen = window.oaCssLen || ((v) => (typeof v === 'number' ? `${v}px` : String(v)));
    const width = cssLen(layout.width != null ? layout.width : 280);
    const height = cssLen(layout.height != null ? layout.height : 45);

    const cosmetics = config?.cosmetics || {};
    const fileDialog = config?.file_dialog || {};
    const acceptExts = (fileDialog.allowed_extensions || []).join(',');

    const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB max limit

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.size > MAX_FILE_SIZE_BYTES) {
                alert(`File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds the 10 MB limit.`);
                return;
            }

            const targetTopic = config?.dynamics?.topic_publish_path || topic;
            const reader = new FileReader();

            reader.onload = (evt) => {
                const arrayBuffer = evt.target.result;
                // Convert binary buffer to Base64 string blob for raw transmission
                let binary = '';
                const bytes = new Uint8Array(arrayBuffer);
                const len = bytes.byteLength;
                for (let i = 0; i < len; i++) {
                    binary += String.fromCharCode(bytes[i]);
                }
                const base64Data = window.btoa(binary);

                const fileBlobPayload = JSON.stringify({
                    filename: file.name,
                    size_bytes: file.size,
                    encoding: "base64",
                    raw_blob: base64Data
                });

                if (publish && targetTopic) {
                    publish(targetTopic, fileBlobPayload, { retain: true });
                }
                if (setVal && typeof setVal === 'function') {
                    setVal(file.name);
                }
                if (onChange && typeof onChange === 'function') {
                    onChange(file.name);
                }
            };

            reader.readAsArrayBuffer(file);
        }
    };

    const handleClick = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
            <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                accept={acceptExts} 
                style={{ display: 'none' }} 
            />
            <button
                onClick={handleClick}
                style={{
                    width,
                    height,
                    maxWidth: '100%',
                    boxSizing: 'border-box',
                    backgroundColor: cosmetics.button_color || '#1A2634',
                    border: `1px solid ${cosmetics.border_color || '#00FFCC'}`,
                    borderRadius: '4px',
                    color: cosmetics.text_color || '#00FFCC',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    gap: '8px',
                    boxShadow: '0 2px 5px rgba(0,0,0,0.4)',
                    transition: 'all 0.15s ease'
                }}
            >
                <span style={{ fontSize: '14px' }}>📁</span>
                <span>{inactiveText}</span>
            </button>
        </div>
    );
};

window.FileBrowserButton = FileBrowserButton;
