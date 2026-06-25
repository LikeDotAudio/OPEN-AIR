const ImageDisplay = ({ value, config }) => {
    const title = config?.label_active?.En || config?.label?.En || "";
    const imagePath = value || config?.value_default || "";
    
    // Geometry
    const w = config?.geometry?.width || config?.layout?.width || 'auto';
    const h = config?.geometry?.height || config?.layout?.height || 'auto';

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '5px' }}>
            {title && <div style={{ color: '#aaa', fontSize: '10px' }}>{title}</div>}
            <div style={{ 
                border: '1px solid #333', 
                padding: '5px', 
                backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#111') : '#111'), 
                borderRadius: '4px',
                width: w,
                height: h,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden'
            }}>
                {imagePath ? (
                    <img 
                        src={`/api/image?path=${encodeURIComponent(imagePath)}`} 
                        alt={title}
                        style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                        onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.parentNode.innerText = 'Image Not Found';
                            e.target.parentNode.style.color = '#666';
                            e.target.parentNode.style.fontSize = '10px';
                        }}
                    />
                ) : (
                    <div style={{ color: '#444', fontSize: '10px' }}>No Image</div>
                )}
            </div>
        </div>
    );
};
window.ImageDisplay = ImageDisplay;