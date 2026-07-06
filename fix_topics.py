import json

def fix_file(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    def traverse(node):
        if isinstance(node, dict):
            # If this is a fader/input and has a command like EQ_Params/ or Dyn_Params/
            if "command" in node and ("EQ_Params/" in node["command"] or "Dyn_Params/" in node["command"]):
                node["topic"] = "OpenAir/Gui/" + node["command"]
                del node["command"]
            for k, v in node.items():
                traverse(v)
        elif isinstance(node, list):
            for item in node:
                traverse(item)
                
    traverse(data)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

fix_file("FrontEnd/Gui_Frames/5_Samples/2_Metering/6_EQ/EQ.json")
fix_file("FrontEnd/Gui_Frames/5_Samples/2_Metering/7_Dynamics/Dynamics.json")
print("Fixed topics!")
