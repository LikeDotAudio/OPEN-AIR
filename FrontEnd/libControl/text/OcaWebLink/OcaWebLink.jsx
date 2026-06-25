/**
 * OcaWebLink Component
 * Author: Gemini (Collaborator)
 * Version: 20260507.1200.1
 */

const OcaWebLink = ({ config }) => {
    const url = config?.url || '#';
    const label = config?.label?.En || config?.label || 'Link';

    return (
        <div style={{ padding: '5px' }}>
            <a 
                href={url} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ 
                    color: '#33A1FD', 
                    textDecoration: 'none', 
                    fontWeight: 'bold',
                    fontSize: '12px'
                }}
            >
                {label.toUpperCase()}
            </a>
        </div>
    );
};

window.OcaWebLink = OcaWebLink;
