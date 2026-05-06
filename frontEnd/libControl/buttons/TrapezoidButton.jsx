const OcaTrapezoidButton = ({ label, value, onChange, config }) => {
    const isLit = value === 1 || value === true;
    
    // Geometry
    const w = config?.geometry?.width || config?.layout?.width || 80;
    const h = config?.geometry?.height || config?.layout?.height || 50;
    
    // Cosmetics
    const baseColor = config?.cosmetics?.colors?.primary || config?.base_color || '#8B0000';
    const ledColor = config?.cosmetics?.colors?.active || config?.led_color || '#FF0000';
    const buttonText = config?.button_text || '';
    
    const [isPressed, setIsPressed] = React.useState(false);
    
    // Color math helpers
    const adjustColor = (color, factor) => {
        const hex = color.replace('#', '');
        const r = Math.min(255, Math.max(0, parseInt(hex.substring(0,2), 16) * factor));
        const g = Math.min(255, Math.max(0, parseInt(hex.substring(2,4), 16) * factor));
        const b = Math.min(255, Math.max(0, parseInt(hex.substring(4,6), 16) * factor));
        return `#${Math.round(r).toString(16).padStart(2,'0')}${Math.round(g).toString(16).padStart(2,'0')}${Math.round(b).toString(16).padStart(2,'0')}`;
    };

    const faceColor = adjustColor(baseColor, isPressed ? 0.8 : 1.0);
    const topBevel = adjustColor(baseColor, isPressed ? 0.9 : 1.2);
    const bottomBevel = adjustColor(baseColor, 0.5);
    const sideBevel = adjustColor(baseColor, 0.7);
    const indColor = isLit ? ledColor : '#330000';

    const handlePointerDown = (e) => {
        setIsPressed(true);
        e.target.setPointerCapture(e.pointerId);
    };

    const handlePointerUp = (e) => {
        if (isPressed) {
            setIsPressed(false);
            onChange(isLit ? 0 : 1);
        }
        e.target.releasePointerCapture(e.pointerId);
    };

    // Math for Trapezoid
    const topShrink = w * 0.1;
    const bevelWidth = w * 0.15;
    const offsetY = isPressed ? 4 : 0;

    const ptOuter = [
        0, h,
        topShrink, 0,
        w - topShrink, 0,
        w, h
    ];
    
    const ptInner = [
        bevelWidth, h - bevelWidth,
        topShrink + bevelWidth * 0.5, bevelWidth,
        w - topShrink - bevelWidth * 0.5, bevelWidth,
        w - bevelWidth, h - bevelWidth
    ];

    const toStr = (pts) => {
        let s = "";
        for(let i=0; i<pts.length; i+=2) {
            s += `${pts[i]},${pts[i+1]} `;
        }
        return s.trim();
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ fontSize: '10px', color: '#ccc', marginBottom: '4px', fontWeight: 'bold' }}>{label}</div>
            
            <svg 
                width={w} 
                height={h + 10} // Extra for shadow/press
                style={{ touchAction: 'none', cursor: 'pointer', overflow: 'visible' }}
                onPointerDown={handlePointerDown}
                onPointerUp={handlePointerUp}
                onPointerCancel={handlePointerUp}
            >
                <defs>
                    <filter id={`glow-trap-${config?.id || 'trap'}`} x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur stdDeviation="4" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                    </filter>
                </defs>

                <g transform={`translate(0, ${offsetY})`}>
                    {/* Shadow if not pressed */}
                    {!isPressed && (
                        <polygon points={toStr([
                            -2, h + 6,
                            topShrink - 2, 6,
                            w - topShrink + 2, 6,
                            w + 2, h + 6
                        ])} fill="#111" />
                    )}

                    {/* Outer Face */}
                    <polygon points={toStr(ptOuter)} fill={faceColor} stroke="#222" strokeWidth="1" />
                    
                    {/* Bevels */}
                    {/* Bottom */}
                    <polygon points={toStr([ptOuter[0], ptOuter[1], ptInner[0], ptInner[1], ptInner[6], ptInner[7], ptOuter[6], ptOuter[7]])} fill={bottomBevel} />
                    {/* Top */}
                    <polygon points={toStr([ptOuter[2], ptOuter[3], ptInner[2], ptInner[3], ptInner[4], ptInner[5], ptOuter[4], ptOuter[5]])} fill={topBevel} />
                    {/* Left */}
                    <polygon points={toStr([ptOuter[0], ptOuter[1], ptInner[0], ptInner[1], ptInner[2], ptInner[3], ptOuter[2], ptOuter[3]])} fill={sideBevel} />
                    {/* Right */}
                    <polygon points={toStr([ptOuter[6], ptOuter[7], ptInner[6], ptInner[7], ptInner[4], ptInner[5], ptOuter[4], ptOuter[5]])} fill={sideBevel} />

                    {/* Inner Face */}
                    <polygon points={toStr(ptInner)} fill={faceColor} />

                    {/* LED Indicator */}
                    <rect 
                        x={w/2 - (w * 0.4)/2} 
                        y={h * 0.75} 
                        width={w * 0.4} 
                        height={h * 0.15} 
                        fill={indColor} 
                        stroke="#111" 
                        filter={isLit ? `url(#glow-trap-${config?.id || 'trap'})` : ''}
                    />

                    {/* Text */}
                    {buttonText && (
                        <text x={w/2} y={h * 0.6} fill="#fff" fontSize="10" fontWeight="bold" fontFamily="Arial" textAnchor="middle">{buttonText}</text>
                    )}
                </g>
            </svg>
        </div>
    );
};
window.OcaTrapezoidButton = OcaTrapezoidButton;