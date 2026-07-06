with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    eq_code = f.read()

old_wheel = """                                    if (window.useMqttPublish) {
                                        const publish = window.useMqttPublish();
                                        const topic = config?.topics ? config.topics[b.name] : `OpenAir/Gui/${config?.command}/${b.name}`;
                                        publish(topic + '/Q', { value: newQ });
                                    }"""
new_wheel = """                                    if (publishFn) {
                                        const topic = config?.topics ? config.topics[b.name] : `OpenAir/Gui/${config?.command}/${b.name}`;
                                        publishFn(topic + '/Q', { value: newQ });
                                    }"""
eq_code = eq_code.replace(old_wheel, new_wheel)

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
    f.write(eq_code)

