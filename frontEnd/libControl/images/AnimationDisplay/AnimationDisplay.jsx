/**
 * AnimationDisplay — animated image widget (mirror of
 * oaGuiElements/Core/images/images_animation_display, type `AnimationDisplay`).
 *
 * The library config carries `gif_path`; a .gif served through the existing
 * `/api/image` endpoint animates natively in an <img>, so this is essentially
 * ImageDisplay pointed at the gif source (value overrides gif_path when a live
 * frame/path arrives over MQTT).
 */
const AnimationDisplay = ({ value, config }) => {
    const c = config || {};
    const title = c.label_active?.En || c.label?.En || "";
    const src = (typeof value === 'string' && value) || c.gif_path || c.value_default || "";

    const w = c.geometry?.width || c.layout?.width || 'auto';
    const h = c.geometry?.height || c.layout?.height || 'auto';
    const px = (v) => (typeof v === 'number' ? `${v}px` : v);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '5px' }}>
            {title && <div style={{ color: '#aaa', fontSize: '10px' }}>{title}</div>}
            <div style={{
                border: '1px solid #333', padding: '5px', backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#111') : '#111'), borderRadius: '4px',
                width: px(w), height: px(h), display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden'
            }}>
                {src ? (
                    <img
                        src={`/api/image?path=${encodeURIComponent(src)}`}
                        alt={title || 'animation'}
                        style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                        onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.parentNode.innerText = 'Animation Not Found';
                            e.target.parentNode.style.color = '#666';
                            e.target.parentNode.style.fontSize = '10px';
                        }}
                    />
                ) : (
                    <div style={{ color: '#444', fontSize: '10px' }}>No Animation</div>
                )}
            </div>
        </div>
    );
};
window.AnimationDisplay = AnimationDisplay;
