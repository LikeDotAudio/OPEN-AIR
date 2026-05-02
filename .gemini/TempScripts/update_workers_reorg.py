import os
import re

mapping = {
    "oaGui.Workers.assembly.engine_structural_assembler": "oaGui.Workers.assembly.engine_structural_assembler",
    "oaGui.Workers.orchestration.loader_orchestrator": "oaGui.Workers.orchestration.loader_orchestrator",
    "oaGui.Workers.scheduling.engine_render_scheduler": "oaGui.Workers.scheduling.engine_render_scheduler",
    "oaGui.Workers.compositing": "oaGui.Workers.compositing",
    "oaGui.Workers.layout_building": "oaGui.Workers.layout_building",
    "oaGui.Workers.orchestration": "oaGui.Workers.orchestration",
    "oaGui.Workers.assembly.engine_structural_assembler": "oaGui.Workers.assembly.engine_structural_assembler",
    "oaGui.Workers.orchestration.loader_orchestrator": "oaGui.Workers.orchestration.loader_orchestrator",
    "oaGui.Workers.scheduling.engine_render_scheduler": "oaGui.Workers.scheduling.engine_render_scheduler",
}

# Individual module names within the folders
inner_mapping = {
    "engine_visual_effects": "engine_visual_effects",
    "engine_texture_mapper": "engine_texture_mapper",
    "sync_behavior": "sync_behavior",
    "scaffolding_builder": "scaffolding_builder",
    "builder_initializer": "builder_initializer",
    "base_layout_builder": "base_layout_builder",
    "default_layout_builder": "default_layout_builder",
    "multi_window_builder": "multi_window_builder",
    "notebook_layout_builder": "notebook_layout_builder",
    "recursive_layout_builder": "recursive_layout_builder",
    "split_layout_builder": "split_layout_builder",
    "compositing/": "compositing/",
    "layout_building/": "layout_building/",
    "orchestration/": "orchestration/"
}

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Update full module paths (specific to general)
    sorted_mapping = sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True)
    for old, new in sorted_mapping:
        content = content.replace(old, new)
    
    # 2. Update inner module names and folder names
    for old, new in inner_mapping.items():
        if old.endswith('/'):
            content = content.replace(old, new)
        else:
            content = re.sub(r'\b' + old + r'\b', new, content)
        
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")

def main():
    ignore_dirs = {'.git', '.venv', '__pycache__', '.crawler', '.pytest_cache'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('oaData')]
        for file in files:
            if file.endswith('.py') or file.endswith('.md') or file.endswith('.json'):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
