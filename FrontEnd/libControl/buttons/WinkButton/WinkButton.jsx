/**
 * Header: WinkButton.jsx
 * Purpose: WinkButton component or utility.
 * Description: Handles logic and rendering for WinkButton component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Inline comment: Logic for OcaWinkButton
const OcaWinkButton = ({ label, value, onChange, config }) => {
    const isOn = value === 1 || value === true;
    
    // Configuration Parsing (matching wink_config.py)
    const w = config?.geometry?.width || config?.layout?.width || config?.width || 60;
    const h = config?.geometry?.height || config?.layout?.height || config?.height || 60;
    const isHoriz = w > h;
    
    const shapeType = config?.shape_type || (w === h ? 'round' : 'rounded_rect');
    const radius = config?.radius || 10;
    
    const bgColor = config?.color || config?.cosmetics?.colors?.active || '#39FF14';
    const shutterColor = config?.shutter_color || config?.cosmetics?.colors?.secondary || 'black';
    const borderColor = config?.border_color || '#333333';
    const borderThickness = config?.border_thickness || 2;
    
    const textClosed = config?.text_closed || '';
    const textClosedColor = config?.text_closed_color || (shutterColor.toLowerCase() === 'black' ? 'white' : 'black');
    
    const textInside = config?.text_inside || '';
    const textInsideColor = config?.text_inside_color || 'black';
    
    const useGlassLens = config?.use_glass_lens !== false;
    
    const openDuration = config?.open_speed || 150;
    const closeDuration = config?.close_speed || 300;
    const openInc = openDuration > 0 ? (16 / openDuration) : 1.0;
    const closeInc = closeDuration > 0 ? (16 / closeDuration) : 1.0;
    
    const blinkInterval = config?.blink_interval || 0;
    const isLatching = config?.latching !== false;
    const isLockedInit = config?.LOCKED || false;
    const labelPos = config?.label_position || 'top';
    
    // Physics State for Shutters
    const [currentOpen, setCurrentOpen] = React.useState(isOn ? 1.0 : 0.0);
    const [isHovering, setIsHovering] = React.useState(false);
    const [isLocked, setIsLocked] = React.useState(isLockedInit);
    
    // Blink state
    const [blinkState, setBlinkState] = React.useState(isOn);
    
    // Physics Loop
    React.useEffect(() => {
        let frameId;
        const targetOpen = (blinkInterval > 0 ? blinkState : isOn) ? 1.0 : 0.0;
        
        const updatePhysics = () => {
            setCurrentOpen(prev => {
                if (prev < targetOpen) {
                    return Math.min(targetOpen, prev + openInc);
                } else if (prev > targetOpen) {
                    return Math.max(targetOpen, prev - closeInc);
                }
                return prev;
            });
            frameId = requestAnimationFrame(updatePhysics);
        };
        
        frameId = requestAnimationFrame(updatePhysics);
        return () => cancelAnimationFrame(frameId);
    }, [isOn, blinkState, blinkInterval, openInc, closeInc]);

    // Blink Loop
    React.useEffect(() => {
        let timer;
        if (isOn && blinkInterval > 0) {
            timer = setInterval(() => {
                setBlinkState(prev => !prev);
            }, blinkInterval);
        } else {
            setBlinkState(isOn);
        }
        return () => clearInterval(timer);
    }, [isOn, blinkInterval]);

    const handleClick = () => {
        if (isLocked) return;
        
        if (isLatching) {
            onChange(isOn ? 0 : 1);
        } else {
            // Momentary not strictly defined for wink, but usually they are latched
            onChange(isOn ? 0 : 1);
        }
    };

    const gap = (isHoriz ? h : w) * currentOpen;
    const effShutterColor = (isHovering && currentOpen < 0.5 && shutterColor.toLowerCase() === 'black') ? '#333' : shutterColor;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', cursor: isLocked ? 'not-allowed' : 'pointer' }}
             onClick={handleClick}
             onMouseEnter={() => setIsHovering(true)}
             onMouseLeave={() => setIsHovering(false)}
        >
            {label && labelPos === 'top' && !textInside && (
                <div style={{ fontSize: '10px', color: '#fff', marginBottom: '4px', fontWeight: 'bold' }}>{label}</div>
            )}
            
            <div style={{
                position: 'relative',
                width: w,
                height: h,
                borderRadius: shapeType === 'round' ? '50%' : `${radius}px`,
                overflow: 'hidden',
                backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, bgColor) : bgColor),
                border: useGlassLens ? 'none' : `${borderThickness}px solid ${borderColor}`,
                boxShadow: useGlassLens ? `inset 0 0 15px rgba(0,0,0,0.9)` : 'none'
            }}>
                {/* Inside Text */}
                {textInside && (
                    <div style={{
                        position: 'absolute',
                        top: 0, left: 0, right: 0, bottom: 0,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: textInsideColor,
                        fontWeight: 'bold',
                        fontSize: `${Math.min(w,h) * 0.3}px`,
                        zIndex: 1,
                        whiteSpace: 'pre-wrap',
                        textAlign: 'center'
                    }}>
                        {textInside}
                    </div>
                )}
                
                {/* Shutters */}
                {isHoriz ? (
                    <>
                        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: `${(h - gap)/2}px`, backgroundColor: effShutterColor, zIndex: 2, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', overflow: 'hidden' }}>
                            {textClosed && <div style={{ color: textClosedColor, fontSize: `${Math.min(w,h) * 0.25}px`, fontWeight: 'bold', marginBottom: '2px', whiteSpace: 'pre-wrap', textAlign: 'center' }}>{textClosed}</div>}
                        </div>
                        <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: `${(h - gap)/2}px`, backgroundColor: effShutterColor, zIndex: 2, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', overflow: 'hidden' }} />
                    </>
                ) : (
                    <>
                        <div style={{ position: 'absolute', top: 0, left: 0, width: `${(w - gap)/2}px`, height: '100%', backgroundColor: effShutterColor, zIndex: 2, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', overflow: 'hidden' }}>
                            {textClosed && <div style={{ color: textClosedColor, fontSize: `${Math.min(w,h) * 0.25}px`, fontWeight: 'bold', marginRight: '2px', whiteSpace: 'pre-wrap', textAlign: 'center' }}>{textClosed}</div>}
                        </div>
                        <div style={{ position: 'absolute', top: 0, right: 0, width: `${(w - gap)/2}px`, height: '100%', backgroundColor: effShutterColor, zIndex: 2, display: 'flex', alignItems: 'center', justifyContent: 'flex-start', overflow: 'hidden' }} />
                    </>
                )}

                {/* Glass Lens Highlight Overlay */}
                {useGlassLens && (
                    <div style={{
                        position: 'absolute',
                        top: 0, left: 0, right: 0, bottom: 0,
                        borderRadius: shapeType === 'round' ? '50%' : `${radius}px`,
                        border: `${borderThickness}px solid rgba(40,40,40,0.4)`,
                        zIndex: 3,
                        pointerEvents: 'none'
                    }}>
                        <div style={{
                            position: 'absolute',
                            top: '5%', left: '10%',
                            width: '80%', height: '40%',
                            background: 'linear-gradient(to bottom, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 100%)',
                            borderRadius: shapeType === 'round' ? '50%' : `${radius}px`,
                            filter: 'blur(1px)'
                        }} />
                    </div>
                )}
                
                {/* Lock Icon */}
                {isLocked && (
                    <div style={{ position: 'absolute', top: '2px', right: '4px', zIndex: 4, color: 'white', fontSize: '10px' }}>
                        🔒
                    </div>
                )}
            </div>

            {label && labelPos === 'bottom' && !textInside && (
                <div style={{ fontSize: '10px', color: '#fff', marginTop: '4px', fontWeight: 'bold' }}>{label}</div>
            )}
        </div>
    );
};
window.OcaWinkButton = OcaWinkButton;