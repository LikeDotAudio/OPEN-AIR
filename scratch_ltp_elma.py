import re

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'r') as f:
    code = f.read()

old_elma = """                {(kc?.knob_style === 'wbs-elma') && window.KnobCapWBSElma && (
                    <div style={{
                        position: 'absolute',
                        left: (isHorizontal ? getHandlePos(linearVal) : width / 2) - capRadius,
                        top: (isHorizontal ? height / 2 : getHandlePos(linearVal)) - capRadius,
                        width: capRadius * 2,
                        height: capRadius * 2,
                        pointerEvents: 'none'
                    }}>
                        <window.KnobCapWBSElma 
                            val={currentRotVal} 
                            min={rotMin} 
                            max={rotMax} 
                            width={capRadius * 2}
                            height={capRadius * 2}
                            cosmetics={{
                                styling: {
                                    fill_color: "#546E7A",
                                    cap_color: kc?.cap_color || capAccent,
                                    outline_color: "#000",
                                    outline_thickness: 1
                                },
                                flutes: 18,
                                cap: { show: true, color: kc?.cap_color || capAccent },
                                wing: { show: false },
                                pointer_tip: { show: true, color: "#546E7A", length: 0.2 },
                                line: { color: "#ffffff" }
                            }}
                        />
                    </div>
                )}"""

new_elma = """                {(kc?.knob_style === 'wbs-elma') && window.KnobCapWBSElma && (
                    <svg style={{
                        position: 'absolute',
                        left: (isHorizontal ? getHandlePos(linearVal) : width / 2) - capRadius,
                        top: (isHorizontal ? height / 2 : getHandlePos(linearVal)) - capRadius,
                        width: capRadius * 2,
                        height: capRadius * 2,
                        pointerEvents: 'none',
                        overflow: 'visible'
                    }}>
                        <window.KnobCapWBSElma 
                            center={capRadius}
                            radius={capRadius}
                            angle={-(((currentRotVal - rotMin) / ((rotMax - rotMin) || 200)) * 2 - 1) * 135}
                            config={{
                                cosmetics: {
                                    styling: {
                                        fill_color: "#546E7A",
                                        cap_color: kc?.cap_color || capAccent,
                                        outline_color: "#000",
                                        outline_thickness: 1
                                    },
                                    flutes: 18,
                                    cap: { show: true, color: kc?.cap_color || capAccent },
                                    wing: { show: false },
                                    pointer_tip: { show: true, color: "#546E7A", length: 0.2 },
                                    line: { color: "#ffffff" }
                                }
                            }}
                        />
                    </svg>
                )}"""

code = code.replace(old_elma, new_elma)

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'w') as f:
    f.write(code)

