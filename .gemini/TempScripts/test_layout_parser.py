import pathlib
from oaGuiManager.Core.parser.layout_parser import LayoutParser

def test():
    parser = LayoutParser("20260401")
    path = pathlib.Path("oaGuiDefinitions/Assets/right_50/bottom_90")
    layout = parser.parse_directory(path)
    print(f"Layout Type: {layout['type']}")
    if layout['type'] == 'notebook':
        print("Tabs found:")
        for tab in layout['data']['tabs']:
            print(f"  - {tab['display_name']} ({tab['path']})")
    else:
        print(f"Layout Data: {layout['data']}")

if __name__ == "__main__":
    test()
