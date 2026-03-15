import pandas as pd
import orjson

class CSVConverterEngine:
    """
    Handles the logic for converting CSV dataframes into nested JSON structures.
    Supports hierarchical grouping, value-as-key mappings, and recursive nesting.
    """

    @staticmethod
    def build_hierarchy(df, header_map, parent_key, original_headers):
        """
        Recursively builds the JSON structure from the grouped DataFrame.
        """
        output_list = []

        # Get all headers nested under the current parent_key
        current_level_configs = sorted(
            [h for h in header_map.values() if h["nested_under"] == parent_key and h["role"] != "Skip"],
            key=lambda x: original_headers.index(x["original_header"])
        )

        # Find the first grouping key for this level
        first_grouping_key_config = next(
            (h for h in current_level_configs if h["role"] in ["Hierarchical Key", "Value as Key", "Key Name and Value"]),
            None
        )

        # Base case: No more grouping keys at this level
        if first_grouping_key_config is None:
            if not df.empty:
                simple_configs = [h for h in current_level_configs if h["role"] in ["Simple Value", "Sub Key"]]
                for _, row in df.iterrows():
                    node = {}
                    for h_cfg in simple_configs:
                        val = row[h_cfg["original_header"]]
                        if pd.notna(val) and val != "":
                            if isinstance(val, bool): val = str(val).lower()
                            node[h_cfg["json_key"]] = val
                    if node: output_list.append(node)
            return output_list

        first_grouping_key = first_grouping_key_config["original_header"]
        grouped_df = df.groupby(first_grouping_key, sort=False)

        for key_value, group in grouped_df:
            node = {}
            if first_grouping_key_config["role"] == "Value as Key":
                children = CSVConverterEngine.build_hierarchy(group, header_map, first_grouping_key, original_headers)
                merged = {}
                if isinstance(children, list):
                    for c in children: merged.update(c)
                elif isinstance(children, dict): merged.update(children)
                node[key_value] = merged

            elif first_grouping_key_config["role"] == "Hierarchical Key":
                if isinstance(key_value, bool): key_value = str(key_value).lower()
                node[first_grouping_key_config["json_key"]] = key_value
                node[first_grouping_key_config["part_name"]] = CSVConverterEngine.build_hierarchy(group, header_map, first_grouping_key, original_headers)

            elif first_grouping_key_config["role"] == "Key Name and Value":
                node[first_grouping_key_config["json_key"]] = {
                    first_grouping_key_config["part_name"]: key_value,
                    "parts": CSVConverterEngine.build_hierarchy(group, header_map, first_grouping_key, original_headers)
                }
            output_list.append(node)

        return output_list
