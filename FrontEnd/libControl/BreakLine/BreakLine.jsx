/**
 * Header: BreakLine.jsx
 * Purpose: BreakLine component or utility.
 * Description: Handles logic and rendering for BreakLine component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Inline comment: Logic for BreakLine
const BreakLine = ({ config }) => {
    const orientation = config?.orientation || 'horizontal';
    const color = config?.color || config?.colour || '#333';
    const thickness = config?.thickness || config?.height || 1;
    const margin = config?.margin || '10px';
    const foldUp = config?.fold_up;
    const initialFolded = config?.is_folded || false;

    const [folded, setFolded] = React.useState(initialFolded);
    const containerRef = React.useRef(null);

    React.useEffect(() => {
        if (!foldUp || !containerRef.current) return;
        // The BreakLine is rendered inside a <window.FieldComponent> which is inside a <div className="widget-wrapper OcaBreakLine">
        // We need to traverse up to the widget-wrapper, then toggle next siblings.
        let wrapper = containerRef.current.closest('.widget-wrapper');
        if (!wrapper) return;

        let next = wrapper.nextElementSibling;
        while (next && !next.querySelector('.OcaBreakLine')) {
            // In a CSS grid, elements might be explicitly placed, but usually setting display: none works
            next.style.display = folded ? 'none' : '';
            next = next.nextElementSibling;
        }
    }, [folded, foldUp]);

    const style = orientation === 'horizontal' 
        ? { width: '100%', height: thickness, backgroundColor: color, margin: `${margin} 0`, position: 'relative' }
        : { height: '100%', width: thickness, backgroundColor: color, margin: `0 ${margin}`, position: 'relative' };

    if (!foldUp) {
        return <div style={style} className="OcaBreakLine" />;
    }

    return (
        <div ref={containerRef} style={{ ...style, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }} 
             className="OcaBreakLine"
             title={folded ? 'Unfold' : 'Fold up'}
             onClick={() => setFolded(!folded)}>
            <div style={{
                background: '#111', color: color, fontSize: 10, padding: '0 8px',
                border: `1px solid ${color}`, borderRadius: 10, lineHeight: 1, userSelect: 'none',
                transform: folded ? 'rotate(-90deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease-out'
            }}>
                ▾
            </div>
        </div>
    );
};
window.BreakLine = BreakLine;