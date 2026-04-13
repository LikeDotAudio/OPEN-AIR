
import os
import re

def expand_abbreviations(content, file_ext, file_path):
    # 1. Expand 'configuration' -> 'configuration'
    if file_ext == '.rs':
        # Avoid #[configuration(...)], #[cfg_attr(...)], and configuration!(...)
        # We use a lambda to check the surrounding context
        def cfg_repl(match):
            prefix = content[max(0, match.start()-10):match.start()]
            suffix = content[match.end():match.end()+1]
            if "#[" in prefix and "configuration" in prefix:
                # This is likely inside an attribute
                return "configuration"
            if suffix == '!':
                # This is a macro configuration!(...)
                return "configuration"
            # Check if it's # [ configuration
            if re.search(r'#\s*\[\s*$', content[:match.start()]):
                return "configuration"
            return "configuration"
        
        content = re.sub(r'\bcfg\b', cfg_repl, content)
    else:
        content = re.sub(r'\bcfg\b', 'configuration', content)
    
    # 2. Expand 'timestamp' -> 'timestamp'
    content = re.sub(r'\bts\b', 'timestamp', content)
    
    # 3. Expand 'value' -> 'value'
    content = re.sub(r'\bval\b', 'value', content)
    
    return content

def process_directory(root_dir):
    updated_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip oaData* folders
        dirs[:] = [d for d in dirs if not d.startswith('oaData')]
        
        for file in files:
            if file.endswith(('.py', '.rs', '.md')):
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1]
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = expand_abbreviations(content, file_ext, file_path)
                    
                    if content != new_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        updated_files.append(file_path)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    print(f"Updated {len(updated_files)} files.")
    for f in updated_files[:10]: # Print first 10
        print(f" - {f}")
    if len(updated_files) > 10:
        print(f" ... and {len(updated_files) - 10} more.")

if __name__ == "__main__":
    process_directory('/home/anthony/Documents/OPEN-AIR')
