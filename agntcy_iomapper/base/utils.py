from typing import Any, Dict, List, Optional, Type

from openapi_pydantic import Schema


def _create_type_from_schema(
    json_schema: Dict[str, Any], pick_fields: List[str]
) -> Optional[Type]:
    """
    Creates a new Pydantic model with only the specified fields from a JSON schema.

    Args:
        schema: The JSON schema of the original object.
        fields: A list of field names to include in the new model.

    Returns:
        A new Pydantic model class containing only the specified fields.
    """
    defs = json_schema.get("$defs", {})
    properties = json_schema.get("properties", {})
    filtered_properties = {}

    for path in pick_fields:
        parts = path.split(".")
        root_item = parts[0]
        prop = properties[root_item]

        if "anyOf" in prop:
            final_schema = []
            filtered_properties[root_item] = {}
            _extract_schema(prop, defs, final_schema)
            filtered_properties[root_item]["anyOf"] = final_schema

        elif "items" in prop:
            final_schema = []
            _extract_schema(prop, defs, final_schema)
            filtered_properties[root_item] = {"type": "array", "items": final_schema}

        elif "$ref" in prop:
            resolved_def = resolve_ref(prop.get("$ref"), defs)
            filtered_properties[root_item] = resolved_def

        else:
            final_schema = []
            filtered_properties[root_item] = {}
            _extract_schema(prop, defs, final_schema)
            filtered_properties[root_item] = final_schema
    # TODO - remove fields not selected from the output
    # filtered_properties = _refine_schema(filtered_properties, pick_fields)

    return Schema.model_validate(filtered_properties)


def _extract_schema(json_schema, defs, schema):
    if "anyOf" in json_schema:
        for val in json_schema.get("anyOf"):
            _extract_schema(val, defs, schema)
    elif "items" in json_schema:
        item = json_schema.get("items")
        _extract_schema(item, defs, schema)
    elif "$ref" in json_schema:
        ref = json_schema.get("$ref")
        schema.append(resolve_ref(ref, defs))
    elif "type" in json_schema:
        schema.append(json_schema)
    else:
        return


def _extract_nested_fields(data: Any, fields: List[str]) -> dict:
    """Extracts specified fields from a potentially nested data structure
    Args:
        data: The input data (can be any type)
        fields: A list of fields path (e.g.. "fielda.fieldb")
    Returns:
        A dictionary containing the extracted fields and their values.
        Returns empty dictionary if there are errors
    """
    if not fields:
        return {}

    results = {}

    for field_path in fields:
        try:
            value = _get_nested_value(data, field_path)
            results[field_path] = value
        except (KeyError, TypeError, AttributeError, ValueError) as e:
            print(f"Error extracting field {field_path}: {e}")
    return results


def _get_nested_value(data: Any, field_path: str) -> Optional[Any]:
    """
    Recursively retrieves a value from a nested data structure
    """
    current = data
    parts = field_path.split(".")

    for part in parts:
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list) and part.isdigit():
            current = current[int(part)]
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            current = None

    return current


def resolve_ref(ref, current_defs):
    ref_parts = ref.split("/")
    current = current_defs
    for part in ref_parts[2:]:
        current = current.get(part)
    return current


def _refine_schema(schema, paths):
    filtered_schema = {}
    print(f"{paths}-{schema}")

    for path in paths:
        path_parts = path.split(".")
        if path_parts[0] in schema:
            key = path_parts[0]
            root_schema = schema.get(key)
            properties = {}
            if "anyOf" in root_schema:
                filtered_schema[key] = {}
                sub_schemas = root_schema.get("anyOf")

                for sub_schema in sub_schemas:
                    if "properties" in sub_schema:
                        curr_properties = sub_schema.get("properties")
                        properties = _filter_properties(
                            sub_schema, curr_properties, path_parts[1:]
                        )
                        if key in filtered_schema:
                            if "anyOf" not in filtered_schema:
                                filtered_schema[key]["anyOf"] = [
                                    {"properties": properties}
                                ]
                            else:
                                filtered_schema[key]["anyOf"]

            elif "items" in root_schema:
                sub_schemas = root_schema.get("items")
            elif "properties" in root_schema:
                curr_properties = root_schema.get("properties")
                properties = _filter_properties(
                    root_schema, curr_properties, path_parts[1:]
                )
    print(f" after {paths}-{filtered_schema}")
    return filtered_schema


def _filter_properties(schema, properties, paths):
    filtered_schema = {}

    if len(paths) == 0:
        return schema

    for path in paths:
        if path in properties:
            filtered_schema[path] = properties.get(path)
            if "properties" in filtered_schema[path]:
                return _filter_properties(
                    schema, filtered_schema[path].get("properties"), paths[1:]
                )
            elif path in schema:
                filtered_schema[path] = schema.get(path)
            else:
                continue

    return filtered_schema
