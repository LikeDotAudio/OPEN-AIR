import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

old_btn1 = """                            id: 'btn_export',
                            right: 20,
                            top: 20,"""

new_btn1 = """                            id: 'btn_export',
                            right: 20,
                            bottom: 20,"""

old_btn2 = """                            id: 'btn_export_csv',
                            right: 120,
                            top: 20,"""

new_btn2 = """                            id: 'btn_export_csv',
                            right: 120,
                            bottom: 20,"""

code = code.replace(old_btn1, new_btn1)
code = code.replace(old_btn2, new_btn2)

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
    f.write(code)

