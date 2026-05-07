/**
 * NeedleMeter Component
 * Author: Anthony Peter Kuzub / Gemini (Collaborator)
 * Version: 20260507.1300.1
 *
 * Description: Analog-style needle meter with ballistics and high-fidelity bezel shapes.
 * Robust parameter extraction for diverse JSON configurations.
 */

const BEZEL_CONFIGS = {
    "gem": { expansion: 3.06, yShift: 0.5 },
    "parking_meter": { expansion: 4.32, yShift: 0.5 },
    "hotdog": { expansion: 1.0, yShift: 1.30 },
    "squircle": { expansion: 1.0, yShift: 0.4 },
    "trapezoid": { expansion: 1.0, yShift: 0.3 },
    "default": { expansion: 1.0, yShift: 0.0 }
};

function getBezelPath(ctx, shape, centerX, centerY, radius) {
    const cfg = BEZEL_CONFIGS[shape] || BEZEL_CONFIGS.default;
    const r = radius * cfg.expansion;
    const yShift = cfg.yShift * radius;

    ctx.beginPath();
    if (shape === 'gem') {
        const wF = 0.51 * r; const bH = 0.3 * r; const sW = 0.69 * r; const sH = 0.6 * r; const pH = 0.98 * r;
        ctx.moveTo(centerX, centerY - (bH + yShift));
        ctx.lineTo(centerX + wF, centerY - (bH + yShift));
        ctx.lineTo(centerX + sW, centerY - (sH + yShift));
        ctx.lineTo(centerX, centerY - (pH + yShift));
        ctx.lineTo(centerX - sW, centerY - (sH + yShift));
        ctx.lineTo(centerX - wF, centerY - (bH + yShift));
    } else if (shape === 'parking_meter') {
        const arcR = r * 0.8;
        ctx.arc(centerX, centerY - yShift, arcR, -Math.PI * 0.8, -Math.PI * 0.2);
        ctx.lineTo(centerX, centerY - yShift);
    } else if (shape === 'hotdog') {
        const wS = 0.9 * r; const rC = 1.01 * r; const cY = 1.01 * r;
        ctx.moveTo(centerX - wS, centerY + yShift);
        ctx.arc(centerX + wS, centerY - (cY - yShift), rC, Math.PI/2, -Math.PI/2, true);
        ctx.arc(centerX - wS, centerY - (cY - yShift), rC, -Math.PI/2, Math.PI/2, true);
    } else if (shape === 'trapezoid') {
        const bW = 1.3 * r; const tW = 1.6 * r; const tH = 1.6 * r;
        ctx.moveTo(centerX - bW, centerY + yShift);
        ctx.lineTo(centerX + bW, centerY + yShift);
        ctx.lineTo(centerX + tW, centerY - (tH - yShift));
        ctx.lineTo(centerX - tW, centerY - (tH - yShift));
    } else {
        ctx.arc(centerX, centerY, radius + 5, Math.PI, 0);
        ctx.lineTo(centerX, centerY);
    }
    ctx.closePath();
}

function useNeedleBallistics(rawValueRef, canvasRef, min, max, width, height, config) {
    React.useEffect(() => {
        let displayValue = min;
        let animationFrameId;

        const render = () => {
            const raw = typeof rawValueRef.current === 'number' ? rawValueRef.current : parseFloat(rawValueRef.current || min);
            const attack = config?.dynamics?.attack_ms ? (100 / config.dynamics.attack_ms) * 0.5 : 0.3;
            const release = config?.dynamics?.release_ms ? (100 / config.dynamics.release_ms) * 0.5 : 0.1;

            if (raw > displayValue) displayValue += (raw - displayValue) * attack;
            else displayValue -= (displayValue - raw) * release;

            if (canvasRef.current) {
                const ctx = canvasRef.current.getContext('2d');
                ctx.clearRect(0, 0, width, height);

                const styleOv = config?.cosmetics?.style_overrides || {};
                const colors = config?.cosmetics?.colors || {};

                const centerX = width / 2 + (styleOv.pivot_offset_x || 0);
                const centerY = height / 2 + (styleOv.pivot_offset_y || 0);
                const meterSize = Math.min(width, height);
                const arcRadius = meterSize / 2 * (styleOv.arc_radius_factor || 0.8);
                const bezelShape = (styleOv.bezel_shape || config?.bezel_shape || 'default').toLowerCase();

                ctx.fillStyle = colors.background || config?.bg_color || '#2b2b2b';
                ctx.fillRect(0, 0, width, height);

                ctx.save();
                getBezelPath(ctx, bezelShape, centerX, centerY, arcRadius);
                
                ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = 10; ctx.shadowOffsetX = 2; ctx.shadowOffsetY = 2;
                ctx.fillStyle = colors.bezel || '#111';
                ctx.fill();
                ctx.shadowColor = 'transparent';

                ctx.clip();

                const faceColor = colors.faceplate || colors.meter_face_colour || '#111';
                if (faceColor !== 'transparent') {
                    ctx.fillStyle = faceColor;
                    ctx.fillRect(0, 0, width, height);
                }

                const minVal = min; const maxVal = max; const range = maxVal - minVal || 1;
                const viewAngle = config?.meter_viewable_angle || 90;
                const centerAngle = config?.meter_center_angle || 90;
                const sang = centerAngle + viewAngle / 2;
                
                const toRad = (deg) => -deg * Math.PI / 180;
                const boundedVal = Math.max(minVal, Math.min(maxVal, displayValue));
                const nAng = toRad(sang - ((boundedVal - minVal) / range) * viewAngle);

                const upperRange = styleOv.upper_range !== undefined ? styleOv.upper_range : (config?.upper_range || 0.0);
                const uAng = toRad(sang - ((upperRange - minVal) / range) * viewAngle);
                
                ctx.lineWidth = styleOv.curve_thickness || 3;
                ctx.strokeStyle = colors.primary || '#E0E0E0';
                ctx.beginPath(); ctx.arc(centerX, centerY, arcRadius, toRad(sang), uAng, true); ctx.stroke();
                
                if (upperRange < maxVal) {
                    ctx.strokeStyle = colors.alert || '#CC3333';
                    ctx.beginPath(); ctx.arc(centerX, centerY, arcRadius, uAng, toRad(sang - viewAngle), true); ctx.stroke();
                }

                ctx.font = 'bold 9px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                const step = config?.domain?.primary?.step || config?.step || 10.0;
                for (let i = 0; i <= range / step; i++) {
                    const val = minVal + i * step;
                    const tRad = toRad(sang - ((val - minVal) / range) * viewAngle);
                    const isAlert = val >= upperRange;
                    ctx.strokeStyle = ctx.fillStyle = isAlert ? colors.alert || '#C33' : colors.primary || '#EEE';
                    
                    const x1 = centerX + arcRadius * Math.cos(tRad);
                    const y1 = centerY + arcRadius * Math.sin(tRad);
                    const x2 = centerX + (arcRadius - 8) * Math.cos(tRad);
                    const y2 = centerY + (arcRadius - 8) * Math.sin(tRad);
                    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
                    
                    const tx = centerX + (arcRadius - 20) * Math.cos(tRad);
                    const ty = centerY + (arcRadius - 20) * Math.sin(tRad);
                    ctx.fillText(Math.round(val), tx, ty);
                }

                const needleLen = arcRadius * 0.95;
                ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 5; ctx.shadowOffsetX = 3; ctx.shadowOffsetY = 3;
                ctx.strokeStyle = colors.pointer || '#fff'; ctx.lineWidth = 2; ctx.lineCap = 'round';
                ctx.beginPath(); ctx.moveTo(centerX, centerY);
                ctx.lineTo(centerX + needleLen * Math.cos(nAng), centerY + needleLen * Math.sin(nAng));
                ctx.stroke();
                ctx.shadowColor = 'transparent';

                ctx.fillStyle = colors.pivot || '#000';
                ctx.beginPath(); ctx.arc(centerX, centerY, 10, 0, Math.PI * 2); ctx.fill();
                ctx.strokeStyle = '#444'; ctx.lineWidth = 2; ctx.stroke();

                ctx.restore();
            }
            animationFrameId = requestAnimationFrame(render);
        };
        render();
        return () => cancelAnimationFrame(animationFrameId);
    }, [min, max, width, height, config]);
}

const NeedleMeter = ({ value, config }) => {
    const getNum = (v, fallback) => {
        if (typeof v === 'number') return v;
        if (typeof v === 'string') {
            const p = parseFloat(v);
            return isNaN(p) ? fallback : p;
        }
        return fallback;
    };

    const min = getNum(config?.domain?.primary?.min, getNum(config?.min, -60));
    const max = getNum(config?.domain?.primary?.max, getNum(config?.max, 10));
    
    const width = config?.geometry?.width || config?.layout?.width || 150;
    const height = config?.geometry?.height || config?.layout?.height || 150;

    const canvasRef = React.useRef(null);
    const rawValueRef = React.useRef(value !== undefined ? value : min);

    React.useEffect(() => { rawValueRef.current = value !== undefined ? value : min; }, [value, min]);

    useNeedleBallistics(rawValueRef, canvasRef, min, max, width, height, config);

    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];
    const title = config?.label_active?.[lang] || config?.label_active?.En || 
                  config?.label?.[lang] || config?.label?.En || 
                  (typeof config?.label === 'string' ? config.label : null);

    return (
        <div style={{ width: width, height: height, position: 'relative', overflow: 'hidden' }}>
            <canvas ref={canvasRef} width={width} height={height} style={{ display: 'block' }} />
            {title && (
                <div style={{ 
                    position: 'absolute', bottom: '5px', left: '50%', transform: 'translateX(-50%)',
                    color: '#888', fontSize: '9px', fontWeight: 'bold', pointerEvents: 'none',
                    textAlign: 'center', width: '90%'
                }}>
                    {title.toUpperCase()}
                </div>
            )}
        </div>
    );
};
window.NeedleMeter = NeedleMeter;
