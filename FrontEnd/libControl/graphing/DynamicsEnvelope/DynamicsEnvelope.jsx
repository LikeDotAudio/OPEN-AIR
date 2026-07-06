/**
 * Header: DynamicsEnvelope.jsx
 * Purpose: DynamicsEnvelope component
 */

const DynamicsEnvelope = ({ topic, config }) => {
    const useMqttStateHook = window.useMqttState || React.useState;
    
    // Fallback topic if none provided, though usually it's passed
    const baseTopic = topic || config?.topic || "OpenAir/Gui/Dyn_Params";

    const [attack] = useMqttStateHook(`${baseTopic}/Attack`, 20, config);
    const [hold] = useMqttStateHook(`${baseTopic}/Hold`, 20, config);
    const [release] = useMqttStateHook(`${baseTopic}/Release`, 100, config);
    
    // Geometry
    const heightVal = config?.geometry?.height || 400;
    const height = typeof heightVal === 'number' ? heightVal : parseInt(heightVal) || 400;
    
    const widthVal = config?.geometry?.width || 800;
    const width = typeof widthVal === 'number' ? widthVal : parseInt(widthVal) || 800;

    // Fixed time scale: 1 pixel = 2ms (0.5px per ms)
    const pixelsPerMs = 0.5;

    // Use my component logic here
    const baselineY = height * 0.75;
    const peakX = width * 0.20; // Move peak slightly left to give more room for release (160px = 320ms pre-delay)
    const peakY = height * 0.2;
    const tailY = height * 0.65;
    const thresholdY = height * 0.45;
    
    const envelopeStartY = height * 0.125; 
    const maxReductionY = envelopeStartY + 80;

    // Static waveform
    const waveformPath = React.useMemo(() => {
      return `M 40 ${baselineY} 
              L ${peakX - 10} ${baselineY} 
              L ${peakX} ${peakY} 
              L ${peakX + 40} ${tailY} 
              L ${width} ${tailY}`;
    }, [baselineY, peakX, peakY, tailY, width]);

    const envelopePath = React.useMemo(() => {
      const att = parseFloat(attack) || 20;
      const hld = parseFloat(hold) || 20;
      const rel = parseFloat(release) || 100;

      const attackDistance = Math.max(1, att * pixelsPerMs); 
      const maxReductionX = peakX + attackDistance;

      const holdDistance = Math.max(0, hld * pixelsPerMs);
      const holdEndX = maxReductionX + holdDistance;

      const releaseDistance = Math.max(1, rel * pixelsPerMs);
      const releaseEndX = holdEndX + releaseDistance;

      return `M 40 ${envelopeStartY} 
              L ${peakX} ${envelopeStartY} 
              Q ${maxReductionX - (attackDistance/2)} ${maxReductionY}, ${maxReductionX} ${maxReductionY} 
              L ${holdEndX} ${maxReductionY}
              Q ${holdEndX + (releaseDistance / 2)} ${maxReductionY}, ${releaseEndX} ${envelopeStartY}
              L ${width} ${envelopeStartY}`;
    }, [attack, hold, release, peakX, envelopeStartY, maxReductionY, width]);

    return (
      <div style={{ width: '100%', height: '100%', backgroundColor: '#050505', borderRadius: '4px', overflow: 'hidden', position: 'relative', border: '1px solid #444' }}>
        {/* Title like ECharts */}
        <div style={{ position: 'absolute', top: 10, left: 10, color: '#888', fontSize: '12px', fontWeight: 'normal', zIndex: 10 }}>
          Time Envelope
        </div>
        
        <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%" style={{ display: 'block' }}>
          
          {/* Y Axis Grid Lines for Gain Reduction */}
          <line x1="40" y1={envelopeStartY} x2={width} y2={envelopeStartY} stroke="#333" strokeWidth="1" />
          <text x="35" y={envelopeStartY + 4} fill="#ddd" fontSize="10" textAnchor="end" fontWeight="bold">0 dB</text>

          <line x1="40" y1={envelopeStartY + 40} x2={width} y2={envelopeStartY + 40} stroke="#333" strokeWidth="1" />
          <text x="35" y={envelopeStartY + 40 + 4} fill="#ddd" fontSize="10" textAnchor="end" fontWeight="bold">-3 dB</text>

          <line x1="40" y1={envelopeStartY + 80} x2={width} y2={envelopeStartY + 80} stroke="#333" strokeWidth="1" />
          <text x="35" y={envelopeStartY + 80 + 4} fill="#ddd" fontSize="10" textAnchor="end" fontWeight="bold">-6 dB</text>

          {/* X Axis Grid and Labels (Time) */}
          <line x1="40" y1={height - 25} x2={width} y2={height - 25} stroke="#333" strokeWidth="1" />
          
          {/* Primary Time = 0 Line at Peak */}
          <line x1={peakX} y1="0" x2={peakX} y2={height - 25} stroke="#555" strokeWidth="2" strokeDasharray="4,2" opacity="0.8" />
          <text x={peakX} y={height - 10} fill="#ddd" fontSize="10" textAnchor="middle" fontWeight="bold">0ms</text>

          {/* Post-peak ms grid */}
          {Array.from({length: 15}, (_, i) => (i + 1) * 100).map(ms => {
            const x = peakX + (ms * pixelsPerMs);
            if (x > width) return null;
            return (
              <React.Fragment key={`post-${ms}`}>
                <line x1={x} y1="0" x2={x} y2={height - 25} stroke="#333" strokeWidth="1" />
                <text x={x} y={height - 10} fill="#ddd" fontSize="10" textAnchor="middle" fontWeight="bold">{ms}ms</text>
              </React.Fragment>
            );
          })}

          {/* Pre-peak ms grid */}
          {Array.from({length: 5}, (_, i) => (i + 1) * 100).map(ms => {
            const x = peakX - (ms * pixelsPerMs);
            if (x < 40) return null; // Don't draw over Y axis
            return (
              <React.Fragment key={`pre-${ms}`}>
                <line x1={x} y1="0" x2={x} y2={height - 25} stroke="#333" strokeWidth="1" />
                <text x={x} y={height - 10} fill="#ddd" fontSize="10" textAnchor="middle" fontWeight="bold">-{ms}ms</text>
              </React.Fragment>
            );
          })}

          {/* Threshold Line */}
          <line 
            x1="40" y1={thresholdY} 
            x2={width} y2={thresholdY} 
            stroke="#ff5555" 
            strokeWidth="2" 
            strokeDasharray="8,4" 
            opacity="0.6"
          />
          <text x="45" y={thresholdY - 10} fill="#ff5555" fontSize="12" opacity="0.8">
            Threshold
          </text>

          {/* Audio Waveform */}
          <path 
            d={waveformPath} 
            fill="none" 
            stroke="#4caf50" 
            strokeWidth="3" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
          <text x="45" y={baselineY - 10} fill="#4caf50" fontSize="12" opacity="0.8">
            Input Audio
          </text>

          {/* Gain Reduction Envelope */}
          <path 
            d={envelopePath} 
            fill="none" 
            stroke="#2196f3" 
            strokeWidth="4" 
            strokeLinecap="round" 
          />

        </svg>
      </div>
    );
};

window.DynamicsEnvelope = DynamicsEnvelope;
