# Interface/Tabs/TreeRefactor/Methods/tree_populator.py
# Author: Gemini CLI
# Version: 20260417.001.0
#
# Description: Recursively populates the tree from JSON data.

def populate_tree(tree, parent_node, data):
    """Recursively populates the tree from JSON data."""

    # Handle List (e.g. OcaArray.data)
    if isinstance(data, list):
        for i, value in enumerate(data):
            node_text = f"[{i}]"
            node_type = "Data"

            # Heuristic: try to find an id or description for the list item
            if isinstance(value, dict):
                node_type = value.get("type", value.get("id", "Item"))
                node_text = f"[{i}] {value.get('description', value.get('id', 'Item'))}"

            # Path construction for list item
            parent_path = ""
            if parent_node != "":
                p_info = tree.item(parent_node, "values")
                if p_info: parent_path = p_info[0]

            full_path = f"{parent_path}.{i}" if parent_path else str(i)

            node_id = tree.insert(parent_node, "end", text=node_text, values=(full_path, node_type), open=False)
            if isinstance(value, (dict, list)) and len(value) > 0:
                tree.insert(node_id, "end", text="Loading...", values=("dummy", "dummy"))
        return

    if not isinstance(data, dict): return

    # Determine container items based on standard keys
    items = []

    # Standard Container Keys
    container_keys = ["fields", "items", "blocks", "blueprint", "data"]

    # ⚡ IMPROVED ROOT HANDLING
    if parent_node == "":
        root_keys = list(data.keys())
        if len(root_keys) == 1 and isinstance(data[root_keys[0]], dict):
            k = root_keys[0]
            items.append((k, data[k], k))
        else:
            for k, v in data.items():
                items.append((k, v, k))
    else:
        # Check for standard containers
        found_standard = False
        for ck in container_keys:
            if ck in data:
                items.append((ck, data[ck], ck))
                found_standard = True

        # Fallback for custom structures
        if not found_standard:
            exclude = ["type", "description", "layout", "geometry", "domain", "dynamics", "cosmetics", "behavior"]
            for k, v in data.items():
                if k not in exclude and isinstance(v, (dict, list)):
                    items.append((k, v, k))

    for key, value, relative_path in items:
        node_text = key
        node_type = "Element"

        if isinstance(value, dict):
            node_type = value.get("type", "Block")
            node_text = f"{key} ({node_type})"

        # Full path for state manager operations
        parent_path = ""
        if parent_node != "":
            p_info = tree.item(parent_node, "values")
            if p_info: parent_path = p_info[0]

        full_path = f"{parent_path}.{relative_path}" if parent_path else relative_path

        node_id = tree.insert(parent_node, "end", text=node_text, values=(full_path, node_type), open=False)

        if isinstance(value, (dict, list)) and len(value) > 0:
            tree.insert(node_id, "end", text="Loading...", values=("dummy", "dummy"))
