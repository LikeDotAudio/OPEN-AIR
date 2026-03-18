import os
import tomllib  # Built-in in Python 3.11+

def create_ultra_structure(config_path):
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
        
    root = config['settings']['root_name']
    standard_subs = config['subfolders']['standard']
    
    # Collect all categories that need subfolders (everything except 'vaults')
    module_categories = [cat for cat in config['domains'] if cat != 'vaults']
    
    # Define the 12-folder standard
    extra_subs = ["FileReaders", "FileWriters"]
    all_standard_subs = standard_subs + extra_subs
    
    for category in module_categories:
        for module in config['domains'][category]:
            # If root_name is ".", we join with current directory
            module_path = os.path.join(os.getcwd(), root, module)
            
            for sub in all_standard_subs:
                path = os.path.join(module_path, sub)
                os.makedirs(path, exist_ok=True)
                
                # Create __init__.py for modular imports
                if config['settings']['apply_init_py']:
                    init_path = os.path.join(path, "__init__.py")
                    if not os.path.exists(init_path):
                        with open(init_path, "w") as f:
                            pass
            
            print(f"✅ Created/Standardized Module: {module}")

    # Create Vaults (Flat structure, no 10-subs)
    if 'vaults' in config['domains']:
        for vault in config['domains']['vaults']:
            path = os.path.join(os.getcwd(), root, vault)
            os.makedirs(path, exist_ok=True)
            print(f"📦 Created Vault: {vault}")

if __name__ == "__main__":
    # Ensure it's run from the project root if that's where UltraFolder.toml is
    create_ultra_structure("UltraFolder.toml")
