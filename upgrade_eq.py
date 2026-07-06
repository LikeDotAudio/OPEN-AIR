import re
import json

jsx_file = "/home/anthony/Documents/OPEN-AIR/FrontEnd/libControl/graphing/Equalization/Equalization.jsx"

with open(jsx_file, "r") as f:
    jsx_code = f.read()

# Replace the React.useEffect that handles mqttData
old_effect = """    // Handle real-time MQTT updates
    React.useEffect(() => {
        if (!mqttData || !chartInstance.current) return;
        try {
            if (typeof mqttData === 'string' && mqttData.includes(',')) {
                const newData = parseCsv("x,y\\n" + mqttData);
                if (newData.length) {
                    chartInstance.current.setOption({
                        series: [{}, { data: newData }]
                    });
                }
            }
        } catch (e) {
            console.error(e);
        }
    }, [mqttData]);"""

new_effect = """    // Handle real-time MQTT updates
    React.useEffect(() => {
        if (!mqttData || !chartInstance.current) return;
        try {
            if (typeof mqttData === 'string' && mqttData.includes(',')) {
                const newData = parseCsv("x,y\\n" + mqttData);
                if (newData.length) {
                    chartInstance.current.setOption({
                        series: [{ data: [[20,0],[20000,0]] }, { data: newData }]
                    });
                }
            } else if (typeof mqttData === 'object') {
                // Determine if it's a collection of EQ bands
                const bands = [];
                for (const key in mqttData) {
                    const band = mqttData[key];
                    if (band && typeof band === 'object') {
                        const freq = parseFloat(band.Freq || band.freq || band.Frequency || band.frequency);
                        const gain = parseFloat(band.Gain || band.gain);
                        const q = parseFloat(band.Q || band.q);
                        if (!isNaN(freq) && !isNaN(gain) && !isNaN(q)) {
                            bands.push({ name: key, freq, gain, q });
                        }
                    }
                }
                
                if (bands.length > 0) {
                    // Generate points logarithmically from 20 to 20k
                    const steps = 200;
                    const minF = Math.log10(20);
                    const maxF = Math.log10(20000);
                    
                    const totalData = [];
                    const bandDataArray = bands.map(() => []);
                    
                    for (let i = 0; i <= steps; i++) {
                        const f = Math.pow(10, minF + (maxF - minF) * (i / steps));
                        let totalGain = 0;
                        
                        bands.forEach((b, bIdx) => {
                            let bandGain = 0;
                            if (b.gain !== 0) {
                                const w = f / b.freq;
                                const denom = 1 + (b.q * b.q) * Math.pow(w - 1/w, 2);
                                bandGain = b.gain / denom;
                                totalGain += bandGain;
                            }
                            bandDataArray[bIdx].push([parseFloat(f.toFixed(1)), parseFloat(bandGain.toFixed(2))]);
                        });
                        
                        totalData.push([parseFloat(f.toFixed(1)), parseFloat(totalGain.toFixed(2))]);
                    }
                    
                    const bandColors = ['#FF5722', '#4CAF50', '#03A9F4', '#E91E63', '#9C27B0', '#FFEB3B'];
                    
                    const series = [
                        {
                            name: '0dB Ref',
                            type: 'line',
                            data: [[20, 0], [20000, 0]],
                            lineStyle: { color: '#888', width: 1, type: 'dashed' },
                            showSymbol: false,
                            animation: false,
                            z: 1
                        }
                    ];
                    
                    // Add individual band shaded regions
                    bands.forEach((b, i) => {
                        series.push({
                            name: b.name || `Band ${i+1}`,
                            type: 'line',
                            data: bandDataArray[i],
                            smooth: true,
                            lineStyle: { color: bandColors[i % bandColors.length], width: 1 },
                            itemStyle: { color: bandColors[i % bandColors.length] },
                            areaStyle: {
                                color: bandColors[i % bandColors.length],
                                opacity: 0.15
                            },
                            showSymbol: false,
                            animation: false,
                            z: 2
                        });
                    });
                    
                    // Add the total curve on top
                    series.push({
                        name: 'Total EQ Curve',
                        type: 'line',
                        data: totalData,
                        smooth: true,
                        lineStyle: { color: '#FFFFFF', width: 3 },
                        itemStyle: { color: '#FFFFFF' },
                        showSymbol: false,
                        animationDuration: 100,
                        z: 10
                    });
                    
                    chartInstance.current.setOption({
                        series: series
                    }, { replaceMerge: ['series'] });
                }
            }
        } catch (e) {
            console.error(e);
        }
    }, [mqttData]);"""

jsx_code = jsx_code.replace(old_effect, new_effect)

with open(jsx_file, "w") as f:
    f.write(jsx_code)

print("Equalization.jsx updated.")

# Now, create the new Dynamics.json
demo_json = {
  "Zoo_Metering_Dynamics": {
    "type": "OcaBin",
    "behavior": {
      "overflow_ns": "auto",
      "overflow_ew": "auto",
      "fluid_ew": True
    },
    "blocks": {
      "Parametric_EQ_Demo": {
        "type": "OcaBlock",
        "description": {
          "En": "Parametric Equalizer Demo"
        },
        "layout_columns": 1,
        "fields": {
          "EQ_Graph": {
            "type": "_Equalization",
            "label": {
              "En": "Master Bus Parametric EQ"
            },
            "command": "EQ_Params",
            "geometry": {
              "width": "100%",
              "height": 400
            }
          },
          "Band_Controls": {
            "type": "OcaBlock",
            "description": { "En": "" },
            "layout_columns": 5,
            "column_sizing": [
                {"weight": 1}, {"weight": 1}, {"weight": 1}, {"weight": 1}, {"weight": 1}
            ],
            "fields": {}
          }
        }
      }
    }
  }
}

# Add 5 bands
bands = ["Low", "LowMid", "Mid", "HighMid", "High"]
default_freqs = [60, 250, 1000, 4000, 12000]
default_gains = [2.5, -4.0, 1.5, 0.0, 3.0]
default_qs = [0.7, 1.2, 2.0, 1.5, 0.7]

colors = ['#FF5722', '#4CAF50', '#03A9F4', '#E91E63', '#9C27B0']

for i, b in enumerate(bands):
    demo_json["Zoo_Metering_Dynamics"]["blocks"]["Parametric_EQ_Demo"]["fields"]["Band_Controls"]["fields"][f"Band_{i}"] = {
        "type": "OcaBlock",
        "layout_columns": 3,
        "description": { "En": f"{b} Band" },
        "fields": {
            f"Freq_{i}": {
                "type": "_FaderKnob",
                "command": f"EQ_Params/{b}/Freq",
                "label": { "En": "Freq" },
                "domain": {
                    "primary": { "min": 20.0, "max": 20000.0, "value_default": default_freqs[i] }
                },
                "cosmetics": { "colors": { "pointer": colors[i] }, "style_overrides": { "scale_type": "log" } }
            },
            f"Gain_{i}": {
                "type": "_FaderKnob",
                "command": f"EQ_Params/{b}/Gain",
                "label": { "En": "Gain" },
                "domain": {
                    "primary": { "min": -24.0, "max": 24.0, "value_default": default_gains[i] }
                },
                "cosmetics": { "colors": { "pointer": colors[i] } }
            },
            f"Q_{i}": {
                "type": "_FaderKnob",
                "command": f"EQ_Params/{b}/Q",
                "label": { "En": "Q" },
                "domain": {
                    "primary": { "min": 0.1, "max": 10.0, "value_default": default_qs[i] }
                },
                "cosmetics": { "colors": { "pointer": colors[i] } }
            }
        }
    }

with open("/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/5_Samples/2_Metering/7_Dynamics/Dynamics.json", "w") as f:
    json.dump(demo_json, f, indent=2)

print("Dynamics.json replaced with new EQ demo.")
