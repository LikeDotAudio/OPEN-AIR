// Cap Component (3D Rendered Thumb)
// Author: Gemini (Collaborator)
// Version: 20260506.1200.1
//
// Description: Renders a high-fidelity 3D fader cap using HTML5 Canvas, 
// matching the Python CapDrawer's geometry and lighting.



const _FADER_ASSET_CACHE = {};

const Cap = ({ config, orientation, width, height, capColor, highlightColor }) => {
    const canvasRef = React.useRef(null);

    // Constants from Python cap.py
    const UPSCALE_FACTOR = 2;
    const LIGHT_DIRECTION = [0.3, -0.6, 0.8];
    const AMBIENT_LIGHT = 0.25;
    const SPECULAR_POWER = 1.5;
    const SPECULAR_INTENSITY = 0.3;
    const INDICATOR_LINE_COLOR_DEFAULT = [40, 40, 180];
    const CORNER_RADIUS = 3;
    const SHADOW_RADIUS = 4;
    const SHADOW_OPACITY = 110;
    const GAUSSIAN_BLUR_SHADOW = 3.5;
    const SPECULAR_HIGHLIGHT_VALUE = 150;

    useEffect(() => {
        if (!canvasRef.current) return;
        const ctx = canvasRef.current.getContext('2d');
        const w = Math.round(width);
        const h = Math.round(height);
        
        const cacheKey = `${w}-${h}-${capColor}-${highlightColor}-${orientation}`;
        if (_FADER_ASSET_CACHE[cacheKey]) {
            ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            ctx.drawImage(_FADER_ASSET_CACHE[cacheKey], 0, 0);
            return;
        }

        const upscale = UPSCALE_FACTOR;
        const uw = w * upscale;
        const uh = h * upscale;

        // Create a temporary canvas for 3D generation
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = uw;
        tempCanvas.height = uh;
        const tempCtx = tempCanvas.getContext('2d');
        const imgData = tempCtx.createImageData(uw, uh);
        const data = imgData.data;

        const hexToRgb = (hex) => {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return [r, g, b];
        };

        const bodyRgb = capColor ? hexToRgb(capColor) : [40, 40, 40];
        
        // Normalize light direction
        const lMag = Math.sqrt(LIGHT_DIRECTION[0]**2 + LIGHT_DIRECTION[1]**2 + LIGHT_DIRECTION[2]**2);
        const lDir = LIGHT_DIRECTION.map(v => v / lMag);

        // Pre-calculate 1D lighting strip along height
        const stripDiffuse = new Float32Array(uh);
        const stripSpec = new Float32Array(uh);
        const stripAO = new Float32Array(uh);
        const stripGroove = new Float32Array(uh);

        for (let y = 0; y < uh; y++) {
            const yCoord = y / (uh - 1);
            let slopeY = 0;
            let slopeZ = 1;

            if (yCoord < 0.10) {
                slopeY = -1.0; slopeZ = 0.0;
            } else if (yCoord < 0.20) {
                slopeY = -0.707; slopeZ = 0.707;
            } else if (yCoord >= 0.25 && yCoord < 0.75) {
                const interp = (yCoord - 0.25) / 0.5;
                slopeY = (interp - 0.5) * 2.0 * 0.55;
                slopeZ = Math.sqrt(Math.max(0, 1.0 - slopeY**2));
            } else if (yCoord >= 0.80 && yCoord < 0.90) {
                slopeY = 0.707; slopeZ = 0.707;
            } else if (yCoord >= 0.90) {
                slopeY = 1.0; slopeZ = 0.0;
            }

            // Lighting
            stripDiffuse[y] = Math.max(AMBIENT_LIGHT, slopeY * lDir[1] + slopeZ * lDir[2]);

            // Specular
            const hVecY = lDir[1];
            const hVecZ = lDir[2] + 1.0;
            const hMag = Math.sqrt(hVecY**2 + hVecZ**2);
            const hy = hVecY / hMag;
            const hz = hVecZ / hMag;
            const specDot = Math.max(0, slopeY * hy + slopeZ * hz);
            stripSpec[y] = Math.pow(specDot, SPECULAR_POWER) * SPECULAR_INTENSITY;

            // AO & Grooves
            stripAO[y] = 1.0;
            if (yCoord >= 0.25 && yCoord < 0.75) {
                const dist = 1.0 - (Math.abs(yCoord - 0.5) / 0.25);
                stripAO[y] = 1.0 - (Math.max(0, dist) * 0.4);
            }

            if (yCoord > 0.22 && yCoord < 0.78) {
                const gVal = Math.sin(((yCoord - 0.22) / 0.56) * Math.PI * 14 - Math.PI/2);
                stripDiffuse[y] += gVal * 0.25; // Deeper groove highlights/shadows
                stripAO[y] *= (1.0 + gVal * 0.20); // Stronger occlusion
            }
        }

        // Fill pixel data
        for (let y = 0; y < uh; y++) {
            const r = Math.min(255, bodyRgb[0] * stripDiffuse[y] * stripAO[y] + SPECULAR_HIGHLIGHT_VALUE * stripSpec[y]);
            const g = Math.min(255, bodyRgb[1] * stripDiffuse[y] * stripAO[y] + SPECULAR_HIGHLIGHT_VALUE * stripSpec[y]);
            const b = Math.min(255, bodyRgb[2] * stripDiffuse[y] * stripAO[y] + SPECULAR_HIGHLIGHT_VALUE * stripSpec[y]);
            
            for (let x = 0; x < uw; x++) {
                const idx = (y * uw + x) * 4;
                data[idx] = r;
                data[idx+1] = g;
                data[idx+2] = b;
                data[idx+3] = 255;
            }
        }

        // Indicator Line
        const centerY = Math.floor(uh / 2);
        const lineH = Math.max(2, upscale);
        const hRgb = highlightColor ? hexToRgb(highlightColor) : INDICATOR_LINE_COLOR_DEFAULT;
        for (let y = centerY - Math.floor(lineH/2); y < centerY + Math.ceil(lineH/2); y++) {
            for (let x = 0; x < uw; x++) {
                const idx = (y * uw + x) * 4;
                data[idx] = hRgb[0];
                data[idx+1] = hRgb[1];
                data[idx+2] = hRgb[2];
            }
        }

        tempCtx.putImageData(imgData, 0, 0);

        // Final composition with masking
        const finalCanvas = document.createElement('canvas');
        const padX = 10, padY = 15;
        finalCanvas.width = w + padX * 2;
        finalCanvas.height = h + padY * 2;
        const finalCtx = finalCanvas.getContext('2d');

        // Draw Shadow
        finalCtx.shadowColor = `rgba(0, 0, 0, ${SHADOW_OPACITY / 255})`;
        finalCtx.shadowBlur = GAUSSIAN_BLUR_SHADOW * 2;
        finalCtx.shadowOffsetX = 4;
        finalCtx.shadowOffsetY = 10;
        
        // Define path for rounded rect + scoops
        const drawMaskedCap = (c, x, y, cw, ch) => {
            c.beginPath();
            const radius = CORNER_RADIUS * upscale;
            c.roundRect(x, y, cw, ch, radius);
            c.fill();
            
            c.globalCompositeOperation = 'destination-out';
            const scoopW = cw * 0.15;
            // Left scoop
            c.beginPath();
            c.ellipse(x - scoopW/2, y + ch/2, scoopW, ch/2, 0, 0, 2 * Math.PI);
            c.fill();
            // Right scoop
            c.beginPath();
            c.ellipse(x + cw + scoopW/2, y + ch/2, scoopW, ch/2, 0, 0, 2 * Math.PI);
            c.fill();
            c.globalCompositeOperation = 'source-over';
        };

        // We use a separate canvas to create the masked cap image
        const maskedCapCanvas = document.createElement('canvas');
        maskedCapCanvas.width = uw;
        maskedCapCanvas.height = uh;
        const mCtx = maskedCapCanvas.getContext('2d');
        
        mCtx.fillStyle = 'white';
        const radius = CORNER_RADIUS * upscale;
        mCtx.beginPath();
        mCtx.roundRect(0, 0, uw, uh, radius);
        mCtx.fill();
        
        mCtx.globalCompositeOperation = 'destination-out';
        const scoopW = uw * 0.15;
        mCtx.beginPath();
        mCtx.ellipse(0, uh/2, scoopW, uh/2, 0, 0, 2 * Math.PI);
        mCtx.fill();
        mCtx.beginPath();
        mCtx.ellipse(uw, uh/2, scoopW, uh/2, 0, 0, 2 * Math.PI);
        mCtx.fill();
        
        mCtx.globalCompositeOperation = 'source-in';
        mCtx.drawImage(tempCanvas, 0, 0);

        // Draw shadow first using a solid rect with same mask
        finalCtx.fillStyle = `rgba(0, 0, 0, ${SHADOW_OPACITY / 255})`;
        finalCtx.beginPath();
        finalCtx.roundRect(padX, padY, w, h, CORNER_RADIUS);
        finalCtx.fill();

        // Draw the cap on top
        finalCtx.shadowColor = 'transparent';
        finalCtx.drawImage(maskedCapCanvas, padX, padY, w, h);

        _FADER_ASSET_CACHE[cacheKey] = finalCanvas;
        
        ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
        ctx.drawImage(finalCanvas, 0, 0);

    }, [width, height, capColor, highlightColor, orientation]);

    return (
        <canvas 
            ref={canvasRef} 
            width={width + padX * 2} 
            height={height + padY * 2} 
            style={{ 
                position: 'absolute', 
                left: '50%',
                top: '50%',
                transform: `translate(-50%, -50%)${orientation === 'horizontal' ? ' rotate(-90deg)' : ''}`,
                pointerEvents: 'none'
            }} 
        />
    );
};

window.FaderCap = Cap;
       }} 
        />
    );
};

window.FaderCap = Cap;
      }} 
        />
    );
};

window.FaderCap = Cap;
