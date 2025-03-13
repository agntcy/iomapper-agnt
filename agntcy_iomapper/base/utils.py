import json
import logging
from typing import Any, Dict, List, Optional, Type

import jsonref
from openapi_pydantic import Schema

logger = logging.getLogger(__name__)


def _create_type_from_schema(
    json_schema: Dict[str, Any], json_paths: List[str]
) -> Optional[Type]:
    """
    Creates a new Pydantic model with only the specified fields from a JSON schema.

    Args:
        schema: The JSON schema of the original object.
        fields: A list of field names to include in the new model.

    Returns:
        A new Pydantic model class containing only the specified fields.
    """

    flatten_json = jsonref.loads(json.dumps(json_schema))

    properties = flatten_json.get("properties", {})

    filtered_properties = {}

    for path in json_paths:
        parts = path.split(".")
        curr_key = parts[0]

        if curr_key in properties:
            curr_object_def = properties.get(curr_key)
            filtered_properties[curr_key] = curr_object_def

            if "anyOf" in curr_object_def:
                sub_schemas = curr_object_def.get("anyOf")
                filtered_properties[curr_key]["anyOf"] = []
                for sub_schema in sub_schemas:
                    if "properties" in sub_schema:
                        _props = sub_schema.get("properties", {})
                        filtered_properties[curr_key]["anyOf"].append(
                            _get_properties(1, parts, _props, flatten_json)
                        )

                    elif "items" in sub_schema:
                        _curr_items = curr_object_def.get("items", {})
                        filtered_properties[curr_key]["anyOf"].append(
                            _get_properties(1, parts, _curr_items, flatten_json)
                        )
            if "properties" in curr_object_def:
                props = curr_object_def.get("properties", {})
                filtered_properties[curr_key]["properties"] = _get_properties(
                    1, parts, props, flatten_json
                )
            elif "items" in curr_object_def:
                curr_items = curr_object_def.get("items", {})
                filtered_properties[curr_key]["items"] = _get_properties(
                    1, parts, curr_items, flatten_json
                )

        else:

            filtered_properties[curr_key] = {"type": "object", "properties": {}}
            if len(parts) == 1:
                filtered_properties[curr_key]["properties"] = flatten_json
            else:
                filtered_properties[curr_key]["properties"] = _get_properties(
                    1, parts, {}, flatten_json
                )

    return Schema.model_validate(filtered_properties)


def _get_properties(level, parts, properties, json_schema):
    if level >= len(parts):
        return properties

    curr_key = parts[level]
    if level >= len(parts) - 1 and len(properties) == 0:
        return {curr_key: json_schema}

    if curr_key in properties:
        curr_obj = properties.get(curr_key)
        if "properties" in curr_obj:
            curr_properties = curr_obj.get("properties", {})
            curr_obj["properties"] = _get_properties(
                level + 1, parts, curr_properties, json_schema
            )
        elif "items" in curr_obj:
            curr_properties = curr_obj.get("items", {})
            curr_obj["items"] = _get_properties(
                level + 1, parts, curr_properties, json_schema
            )
        elif "anyOf" in curr_obj:
            curr_obj["anyOf"] = []
            sub_schemas = curr_obj.get("anyOf")
            for sub_schema in sub_schemas:
                curr_obj["anyOf"].append(
                    _get_properties(level, sub_schema, json_schema)
                )

        return curr_obj
    else:
        curr_obj = {curr_key: {"type": "object", "properties": {}}}
        curr_obj[curr_key]["properties"] = _get_properties(
            level + 1, parts, {}, json_schema
        )
        return curr_obj

    return properties


def extract_nested_fields(data: Any, fields: List[str]) -> dict:
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
            logger.error(f"Error extracting field {field_path}: {e}")
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
