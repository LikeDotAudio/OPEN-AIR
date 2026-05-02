import pathlib
import sys
import os

# Ensure the project root is in sys.path
project_root = pathlib.Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaGui.FileReaders.scanner.folder_layout_interpreter import FolderLayoutInterpreter

def test_detection():
    interpreter = FolderLayoutInterpreter(current_version="1.0.0")
    
    assets_path = project_root / "oaGui" / "Assets"
    print(f"Testing Assets path: {assets_path}")
    res = interpreter.parse_directory(assets_path)
    print(f"Assets Layout: {res['type']}")
    
    if res['type'] == 'multi_window':
        for win in res['data']['windows']:
            win_path = win['path']
            print(f"\nTesting Window path: {win_path}")
            win_res = interpreter.parse_directory(win_path)
            print(f"Window Layout: {win_res['type']}")
            
            if win_res['type'] in ['horizontal_split', 'vertical_split']:
                for panel in win_res['data']['panels']:
                    panel_path = panel['path']
                    print(f"  Testing Panel path: {panel_path}")
                    panel_res = interpreter.parse_directory(panel_path)
                    print(f"  Panel Layout: {panel_res['type']}")
                    
                    if panel_res['type'] in ['horizontal_split', 'vertical_split']:
                        for sub_panel in panel_res['data']['panels']:
                            sub_path = sub_panel['path']
                            print(f"    Testing Sub-Panel path: {sub_path}")
                            sub_res = interpreter.parse_directory(sub_path)
                            print(f"    Sub-Panel Layout: {sub_res['type']}")

if __name__ == "__main__":
    test_detection()
