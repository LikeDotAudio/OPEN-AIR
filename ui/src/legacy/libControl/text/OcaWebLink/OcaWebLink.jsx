/**
 * Header: OcaWebLink.jsx
 * Purpose: OcaWebLink component or utility.
 * Description: Handles logic and rendering for OcaWebLink component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * OcaWebLink Component
 * Author: Gemini (Collaborator)
 * Version: 20260507.1200.1
 */

// Inline comment: Logic for OcaWebLink
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

export { OcaWebLink }
