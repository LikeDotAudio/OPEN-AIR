import re

with open('FrontEnd/libControl/graphing/AudioDynamics/AudioDynamics.jsx', 'r') as f:
    code = f.read()

code = code.replace("""publishFn(`${baseTopic}/Thresh`, newThresh);
                            publishFn(`${baseTopic}/Gain`, newGain);""", """publishFn(`${baseTopic}/Thresh`, { value: newThresh });
                            publishFn(`${baseTopic}/Gain`, { value: newGain });""")

# add onmousewheel for ratio
code = code.replace("""if (publishFn) {
                            publishFn(`${baseTopic}/Thresh`, { value: newThresh });
                            publishFn(`${baseTopic}/Gain`, { value: newGain });
                        }
                    }
                });""", """if (publishFn) {
                            publishFn(`${baseTopic}/Thresh`, { value: newThresh });
                            publishFn(`${baseTopic}/Gain`, { value: newGain });
                        }
                    },
                    onmousewheel: function (e) {
                        e.event.preventDefault();
                        e.event.stopPropagation();
                        const delta = e.event.wheelDelta || -e.event.detail;
                        let r = ratio + (delta > 0 ? 0.1 : -0.1);
                        r = Math.max(1.0, Math.min(20.0, r));
                        if (publishFn) {
                            publishFn(`${baseTopic}/Ratio`, { value: r });
                        }
                    }
                });""")

with open('FrontEnd/libControl/graphing/AudioDynamics/AudioDynamics.jsx', 'w') as f:
    f.write(code)
