import re

with open('FrontEnd/libControl/graphing/AudioDynamics/AudioDynamics.jsx', 'r') as f:
    code = f.read()

# 1. Add publishFn inside component
publish_code = """    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};
    const publishFn = window.useMqttPublisher ? window.useMqttPublisher() : null;"""
code = code.replace("    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};", publish_code)

# 2. Update useEffect dependency array to include messages
code = code.replace("    }, [mqttData]);", "    }, [mqttData, messages, publishFn, config]);")

# 3. Add graphic definition and chartInstance.current.setOption update
old_setOption = """            chartInstance.current.setOption({
                series: ["""

new_setOption = """            const pos = chartInstance.current.convertToPixel({seriesIndex: 0}, [thresh, thresh + gain]);
            const graphics = [];
            if (pos) {
                graphics.push({
                    type: 'circle',
                    id: 'thresh_handle',
                    position: pos,
                    shape: { r: 12 },
                    style: { fill: '#e74c3c', stroke: '#fff', lineWidth: 2, shadowBlur: 4, shadowColor: '#000' },
                    invisible: false,
                    draggable: true,
                    z: 100,
                    ondrag: function (e) {
                        const pt = chartInstance.current.convertFromPixel({seriesIndex: 0}, [this.x, this.y]);
                        let newThresh = Math.max(-90, Math.min(0, pt[0]));
                        let newGain = Math.max(-24, Math.min(24, pt[1] - newThresh));
                        if (publishFn) {
                            publishFn(`${baseTopic}/Thresh`, newThresh);
                            publishFn(`${baseTopic}/Gain`, newGain);
                        }
                    }
                });
            }

            chartInstance.current.setOption({
                graphic: graphics,
                series: ["""

code = code.replace(old_setOption, new_setOption)

with open('FrontEnd/libControl/graphing/AudioDynamics/AudioDynamics.jsx', 'w') as f:
    f.write(code)
