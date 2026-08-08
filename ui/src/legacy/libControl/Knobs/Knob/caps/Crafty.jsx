/**
 * Header: Crafty.jsx
 * Purpose: Crafty component or utility.
 * Description: Handles logic and rendering for Crafty component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Crafty Knob Cap renderer
// Variants: 'spoked', 'metallic', 'led_ring'

window.KnobCapCrafty = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const variant = config?.cosmetics?.variant || 'metallic';
    
    // Derived norm (0 to 1) for LED ring from angle (assumes standard 240 to -60 range)
    // 240 = 0, -60 = 1.
    const norm = Math.max(0, Math.min(1, (240 - angle) / 300));

    if (variant === 'spoked' || variant === 'spoked_pan' || variant === 'spoked_spread') {
        const spokes = [];
        for (let i = 0; i < 12; i++) {
            const a = i * 30;
            const rad = a * Math.PI / 180;
            spokes.push(
                <line key={i} x1={center} y1={center} 
                      x2={center + radius * Math.cos(rad)} 
                      y2={center - radius * Math.sin(rad)} 
                      stroke="#5a3d7c" strokeWidth="2" />
            );
        }
        
        let slicePath = null;
        if (variant === 'spoked_pan') {
            const startA = 90; // 12 o'clock
            // If angle > 90, it's panning left. If angle < 90, it's panning right.
            // window.describeArc handles drawing from start to end correctly.
            // Wait, angle is 240 (left) to -60 (right).
            if (window.describeArc) {
                if (angle < 90) { // panning right
                    slicePath = <path d={window.describeArc(center, center, radius, angle, 90) + ` L ${center} ${center} Z`} fill={indicatorColor || "#9370db"} />;
                } else if (angle > 90) { // panning left
                    slicePath = <path d={window.describeArc(center, center, radius, 90, angle) + ` L ${center} ${center} Z`} fill={indicatorColor || "#9370db"} />;
                }
            }
        } else if (variant === 'spoked_spread') {
            const spread = 90 - angle; // If angle is -60, spread is 150.
            const startA = 90 + Math.abs(spread);
            const endA = 90 - Math.abs(spread);
            if (window.describeArc && startA !== endA) {
                slicePath = <path d={window.describeArc(center, center, radius, endA, startA) + ` L ${center} ${center} Z`} fill={indicatorColor || "#f4d03f"} />;
            }
        }

        const ptrRad = angle * Math.PI / 180;
        return (
            <g>
                <circle cx={center} cy={center} r={radius} fill="#111" stroke="#333" strokeWidth="2" />
                {slicePath}
                {spokes}
                {/* Pointer Needle */}
                <line x1={center} y1={center} 
                      x2={center + (radius - 5) * Math.cos(ptrRad)} 
                      y2={center - (radius - 5) * Math.sin(ptrRad)} 
                      stroke="#fff" strokeWidth="2" />
                <circle cx={center} cy={center} r={4} fill="#fff" />
            </g>
        );
    }
    
    if (variant === 'led_ring' || variant === 'led_ring_pan' || variant === 'led_ring_spread') {
        const segments = 15;
        const arcItems = [];
        const gap = 4; // degrees gap
        const step = 300 / segments;
        for (let i = 0; i < segments; i++) {
            const segStart = 240 - (i * step);
            const segEnd = segStart - step + gap;
            const segMid = (segStart + segEnd) / 2;
            
            let isLit = false;
            if (variant === 'led_ring') {
                isLit = (i / segments) <= norm;
            } else if (variant === 'led_ring_pan') {
                if (angle < 90) { // right side
                    isLit = segMid <= 90 && segMid >= angle;
                } else { // left side
                    isLit = segMid >= 90 && segMid <= angle;
                }
            } else if (variant === 'led_ring_spread') {
                const spread = Math.abs(90 - angle);
                isLit = segMid <= (90 + spread) && segMid >= (90 - spread);
            }

            if (window.describeArc) {
                arcItems.push(
                    <path key={i} 
                          d={window.describeArc(center, center, radius + 8, segEnd, segStart)}
                          fill="none" stroke={isLit ? (indicatorColor || "#88e077") : "#000"} strokeWidth="12" />
                );
            }
        }
        
        const ptrRad = angle * Math.PI / 180;
        return (
            <g>
                {/* Outer Ring Background */}
                <circle cx={center} cy={center} r={radius + 14} fill="#888" />
                {arcItems}
                <circle cx={center} cy={center} r={radius + 18} fill="none" stroke="#aaa" strokeWidth="1" strokeDasharray="2, 3" />
                
                {/* Inner Dome */}
                <circle cx={center} cy={center} r={radius} fill="url(#grad-led)" />
                <defs>
                    <radialGradient id="grad-led" cx="50%" cy="30%" r="70%">
                        <stop offset="0%" stopColor="#444" />
                        <stop offset="100%" stopColor="#111" />
                    </radialGradient>
                </defs>
                
                {/* Dimple Pointer on Dome */}
                <circle cx={center + (radius - 8) * Math.cos(ptrRad)} 
                        cy={center - (radius - 8) * Math.sin(ptrRad)} 
                        r={4} fill="#000" />
            </g>
        );
    }

    // Default: 'metallic'
    const dimples = [];
    for (let i = 0; i <= 10; i++) {
        const a = 240 - i * 30;
        const r = a * Math.PI / 180;
        dimples.push(
            <circle key={i} 
                    cx={center + (radius + 8) * Math.cos(r)} 
                    cy={center - (radius + 8) * Math.sin(r)} 
                    r={3} fill="#444" stroke="#666" strokeWidth="1" />
        );
    }
    const ptrRad = angle * Math.PI / 180;
    return (
        <g>
            <defs>
                <radialGradient id="grad-metal-dome" cx="40%" cy="30%" r="60%">
                    <stop offset="0%" stopColor="#eee" />
                    <stop offset="50%" stopColor="#888" />
                    <stop offset="100%" stopColor="#333" />
                </radialGradient>
            </defs>
            {/* Base Flange */}
            <circle cx={center} cy={center} r={radius + 15} fill="#555" />
            {dimples}
            
            {/* Main Dome */}
            <circle cx={center} cy={center} r={radius} fill="url(#grad-metal-dome)" filter={filterId ? `url(#sh-${filterId})` : ""} />
            
            {/* Pointer Dot */}
            <circle cx={center + (radius - 8) * Math.cos(ptrRad)} 
                    cy={center - (radius - 8) * Math.sin(ptrRad)} 
                    r={4} fill="#222" />
        </g>
    );
};
