
import os
import re

MODULE_MAPPING = {
    "oaGuiElements": ("UI", "GUI_ELEMENTS"),
    "oaGuiManager": ("UI", "GUI_MANAGER"),
    "oaTranslator": ("UI", "TRANSLATOR"),
    "oaGuiShowtime": ("UI", "SHOWTIME"),
    "oaPTP": ("CORE", "PTP")
}

LOGGER_NAMES = ["logger", "builder_logger", "LAYOUT_LOGGER", "GUI_LOGGER", "FACTORY_LOGGER", "RADAR_BUILDER_LOGGER", "LAYOUT_LOGGER"]
DEBUG_CONSTS = ["LOCAL_DEBUG", "BUILDER_DEBUG", "RADAR_BUILDER_DEBUG", "LAYOUT_DEBUG", "debug_enabled", "self.debug_enabled", "self.builder_debug"]

def process_file(file_path, system, element):
    with open(file_path, 'r') as f:
        content = f.read()

    changed = False

    # 1. Remove specific debug constants (only if they are top-level assignments)
    for const in ["LOCAL_DEBUG", "BUILDER_DEBUG", "RADAR_BUILDER_DEBUG", "LAYOUT_DEBUG"]:
        pattern = re.compile(rf'^{const}\s*=\s*(True|False).*$', re.MULTILINE)
        if pattern.search(content):
            content = pattern.sub('', content)
            changed = True

    # 2. Replace gated logs (both single and multi-line)
    # We'll use a regex that finds 'if <DEBUG_CONST>: <logger>.<level>(...)'
    for const in DEBUG_CONSTS:
        for logger_name in LOGGER_NAMES:
            # Single line: if const: logger.level(...)
            # We use \s* to handle indentation
            pattern = re.compile(rf'^(\s*)if\s+{re.escape(const)}:\s+{re.escape(logger_name)}\.(success|info|debug|trace|log)\((.*?)\)\s*$', re.MULTILINE | re.DOTALL)
            def replace_gated(match):
                indent = match.group(1)
                level = match.group(2).upper()
                if level == "LOG": level = "DEBUG"
                msg = match.group(3)
                # If msg is multi-line, we might need to be careful, but matrix_log should handle it.
                return f'{indent}matrix_log("{system}", "{element}", inspect.currentframe().f_code.co_name, {msg}, level="{level}")'
            
            if pattern.search(content):
                content = pattern.sub(replace_gated, content)
                changed = True

            # Multi-line: if const:\n    logger.level(...)
            # This is harder with regex if there are multiple lines. 
            # Let's try to match the if line and then the next line if it's indented and is a log.
            pattern_multi = re.compile(rf'^(\s*)if\s+{re.escape(const)}:\s*\n(\s+){re.escape(logger_name)}\.(success|info|debug|trace|log)\((.*?)\)\s*$', re.MULTILINE | re.DOTALL)
            def replace_gated_multi(match):
                indent = match.group(1)
                log_indent = match.group(2)
                level = match.group(3).upper()
                if level == "LOG": level = "DEBUG"
                msg = match.group(4)
                return f'{indent}matrix_log("{system}", "{element}", inspect.currentframe().f_code.co_name, {msg}, level="{level}")'
            
            if pattern_multi.search(content):
                content = pattern_multi.sub(replace_gated_multi, content)
                changed = True

    # 3. Replace direct logs (not yet replaced)
    for logger_name in LOGGER_NAMES:
        # Match logger.level(...) but NOT if it's part of a larger expression or already matrix_log
        # We also want to avoid error, warning, exception
        pattern = re.compile(rf'(?<!matrix_log\()(?<!def\s)\b{re.escape(logger_name)}\.(success|info|debug|trace)\((.*?)\)', re.DOTALL)
        def replace_direct(match):
            level = match.group(1).upper()
            msg = match.group(2)
            # Find the indentation of the current line
            return f'matrix_log("{system}", "{element}", inspect.currentframe().f_code.co_name, {msg}, level="{level}")'
        
        if pattern.search(content):
            content = pattern.sub(replace_direct, content)
            changed = True

    # 4. Replace print statements
    # Only if it's a functional log (contains a string literal)
    print_pattern = re.compile(r'(?<!def\s)\bprint\((f?["\'].*?["\'])\)', re.DOTALL)
    if print_pattern.search(content):
        def replace_print(match):
            msg = match.group(1)
            return f'matrix_log("{system}", "{element}", inspect.currentframe().f_code.co_name, {msg}, level="INFO")'
        content = print_pattern.sub(replace_print, content)
        changed = True

    if changed:
        # 5. Ensure imports
        if 'from oaLogging.Methods.matrix_gate import matrix_log' not in content:
            import_line = 'from oaLogging.Methods.matrix_gate import matrix_log\nimport inspect'
            if 'import ' in content:
                content = re.sub(r'(import .*?\n)', r'\1' + import_line + '\n', content, count=1)
            else:
                content = import_line + '\n' + content
        elif 'import inspect' not in content:
            content = re.sub(r'(from oaLogging.Methods.matrix_gate import matrix_log)', r'\1\nimport inspect', content)

        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    for module, (system, element) in MODULE_MAPPING.items():
        print(f"Processing module: {module}")
        for root, dirs, files in os.walk(module):
            for file in files:
                if file.endswith(".py") and not file.startswith("__init__"):
                    file_path = os.path.join(root, file)
                    try:
                        if process_file(file_path, system, element):
                            print(f"  Updated: {file_path}")
                    except Exception as e:
                        print(f"  Error processing {file_path}: {e}")

if __name__ == "__main__":
    main()
