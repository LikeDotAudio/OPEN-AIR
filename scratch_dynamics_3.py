import re

with open('FrontEnd/libControl/graphing/AudioDynamics/AudioDynamics.jsx', 'r') as f:
    code = f.read()

old_scatter = """                    {
                        name: 'Threshold Point',
                        type: 'scatter',
                        data: threshPoint,
                        itemStyle: { color: '#e74c3c' },
                        symbolSize: 10,
                        animationDuration: 300
                    }"""

code = code.replace(old_scatter, "")
# make sure not to leave trailing comma before the closing bracket of series array
code = code.replace("animationDuration: 300\n                    },\n                ]", "animationDuration: 300\n                    }\n                ]")

with open('FrontEnd/libControl/graphing/AudioDynamics/AudioDynamics.jsx', 'w') as f:
    f.write(code)
