# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import copy
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import jsonref
from openapi_pydantic import Schema
from pydantic import BaseModel

from agntcy_iomapper.base.models import (
    FieldMetadata,
    IOMappingAgentMetadata,
)

logger = logging.getLogger(__name__)


def create_type_from_schema(
    json_schema: Dict[str, Any], json_paths: List[Union[str, FieldMetadata]]
) -> Optional[Type]:
    """
    Creates a new model with only the specified fields from a JSON schema.

    Args:
        json_schema: The JSON schema of the original object.
        json_paths: A list of field names to include in the new model.

    Returns:
        A new Pydantic model class containing only the specified fields.
    """

    # replace $refs with actual object definition
    flatten_json = jsonref.loads(json.dumps(json_schema))

    properties = flatten_json.get("properties", {})

    filtered_properties = {}
    curr_path_schema = {}

    for path in json_paths:
        curr_path = path if isinstance(path, str) else path.json_path
        field_description = None if isinstance(path, str) else path.description
        field_examples = None if isinstance(path, str) else path.examples

        parts = curr_path.split(".")
        curr_key = parts[0]

        if curr_key.isdigit():
            continue

        curr_path_schema.clear()

        if curr_key in properties:
            # perform a deepcopy to keep original properties intact
            curr_object_def = copy.deepcopy(properties.get(curr_key))

            curr_path_schema[curr_key] = copy.deepcopy(curr_object_def)

            if len(parts) == 1:
                if field_description:
                    curr_path_schema[curr_key]["description"] = field_description
                if field_examples:
                    curr_path_schema[curr_key]["examples"] = field_examples

            if "anyOf" in curr_object_def:
                sub_schemas = curr_object_def.get("anyOf")

                for i, sub_schema in enumerate(sub_schemas):
                    if "properties" in sub_schema:
                        _props = sub_schema.get("properties", {})
                        curr_path_schema[curr_key]["anyOf"][i]["properties"] = (
                            _get_properties(
                                1,
                                parts,
                                _props,
                                flatten_json,
                                field_description,
                                field_examples,
                            )
                        )
                    elif "items" in sub_schema:
                        _curr_items = curr_object_def.get("items", {})
                        curr_path_schema[curr_key]["anyOf"][i]["items"] = (
                            _get_properties(
                                1,
                                parts,
                                _curr_items,
                                flatten_json,
                                field_description,
                                field_examples,
                            )
                        )

            if "properties" in curr_object_def:
                props = curr_object_def.get("properties", {})
                curr_path_schema[curr_key]["properties"] = _get_properties(
                    1, parts, props, flatten_json, field_description, field_examples
                )
            elif "items" in curr_object_def:
                curr_items = curr_object_def.get("items", {})
                curr_path_schema[curr_key]["items"] = _get_properties(
                    1,
                    parts,
                    curr_items,
                    flatten_json,
                    field_description,
                    field_examples,
                )

        else:
            curr_path_schema[curr_key] = {"type": "object", "properties": {}}
            if len(parts) == 1:
                curr_path_schema[curr_key] = flatten_json
                if field_description:
                    curr_path_schema[curr_key]["description"] = field_description
            else:
                curr_path_schema[curr_key]["properties"] = _get_properties(
                    1, parts, {}, flatten_json, field_description, field_examples
                )

        if curr_key not in filtered_properties:
            filtered_properties[curr_key] = copy.deepcopy(curr_path_schema[curr_key])
        else:
            filtered_properties[curr_key] = _merge_paths(
                curr_path_schema, filtered_properties
            )[curr_key]

    return filtered_properties


def _merge_paths(d1: dict, d2: dict):
    """
    Merges two dictionaries recursively, combining values for common keys,
    and merging nested dictionaries at the same level.

    Args:
        d1 (dict): The first dictionary.
        d2 (dict): The second dictionary.

    Returns:
        dict: The merged dictionary.
    """
    merged = {}
    keys = set(d1.keys()) | set(d2.keys())

    for key in keys:
        if key in d1 and key in d2:
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                merged[key] = _merge_paths(d1[key], d2[key])
            elif isinstance(d1[key], list) and isinstance(d2[key], list):
                merged[key] = []
                for val1, val2 in zip(d1[key], d2[key]):
                    if isinstance(val1, dict) and isinstance(val2, dict):
                        merged[key].append(_merge_paths(val1, val2))
                    else:
                        merged[key].append(val2)

                merged[key].extend(d1[key][len(merged[key]) :])
                merged[key].extend(d2[key][len(merged[key]) :])

            else:
                merged[key] = d2[key]
        elif key in d1:
            merged[key] = d1[key]
        else:
            merged[key] = d2[key]

    return merged


def _get_properties(
    level, parts, props, json_schema, field_description, field_examples
):

    if level >= len(parts):
        return props

    curr_key = parts[level]

    if curr_key in props:
        curr_obj = props.get(curr_key)
        if "properties" in curr_obj:
            curr_properties = curr_obj.get("properties", {})
            curr_obj["properties"] = _get_properties(
                level + 1,
                parts,
                curr_properties,
                json_schema,
                field_description,
                field_examples,
            )

        elif "items" in curr_obj:
            curr_properties = curr_obj.get("items", {})
            curr_obj["items"] = _get_properties(
                level + 1,
                parts,
                curr_properties,
                json_schema,
                field_description,
                field_examples,
            )
        elif "anyOf" in curr_obj:
            sub_schemas = curr_obj.get("anyOf")
            anyOfs = []
            for sub_schema in sub_schemas:
                s = _get_properties(
                    level + 1,
                    parts,
                    sub_schema,
                    json_schema,
                    field_description,
                    field_examples,
                )
                anyOfs.append(s)

            curr_obj["anyOf"] = anyOfs

        if level == len(parts) - 1:
            if field_description:
                curr_obj["description"] = field_description
            if field_examples:
                curr_obj["examples"] = field_examples

        return {curr_key: curr_obj}

    elif "anyOf" in props:
        curr_obj = {curr_key: {"anyOf": []}}
        anyOf = []
        sub_schemas = props.get("anyOf")

        for sub_schema in sub_schemas:
            anyOf.append(
                _get_properties(
                    level,
                    parts,
                    sub_schema,
                    json_schema,
                    field_description,
                    field_examples,
                )
            )

        curr_obj[curr_key]["anyOf"] = anyOf
        return {curr_key: curr_obj}

    elif "properties" in props:
        curr_obj = copy.deepcopy(props)
        curr_properties = curr_obj.get("properties", {})
        curr_obj["properties"] = _get_properties(
            level,
            parts,
            curr_properties,
            json_schema,
            field_description,
            field_examples,
        )
        return curr_obj

    elif "items" in props:
        curr_obj = copy.deepcopy(props)
        curr_properties = props.get("items", {})
        curr_obj["items"] = _get_properties(
            level,
            parts,
            curr_properties,
            json_schema,
            field_description,
            field_examples,
        )
        return curr_obj

    else:
        return props


def extract_nested_fields(data: Any, fields: List[Union[str, FieldMetadata]]) -> dict:
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
            curr_path = (
                field_path if isinstance(field_path, str) else field_path.json_path
            )
            value = _get_nested_value(data, curr_path)
            results[curr_path] = value
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


def get_io_types(data: Any, metadata: IOMappingAgentMetadata) -> Tuple[Schema, Schema]:
    data_schema = None

    if isinstance(data, BaseModel):
        data_schema = data.model_json_schema()
    # If input schema is provided it overwrites the data schema
    input_schema = metadata.input_schema if metadata.input_schema else data_schema
    # If output schema is provided it overwrites the data schema
    output_schema = metadata.output_schema if metadata.output_schema else data_schema

    if not input_schema or not output_schema:
        raise ValueError(
            "input_schema, and or output_schema are missing from the metadata, for a better accuracy you are required to provide them in this scenario, or we  could not infer the type from the state"
        )

    input_type = Schema.model_validate(
        create_type_from_schema(input_schema, metadata.input_fields)
    )

    output_type = Schema.model_validate(
        create_type_from_schema(output_schema, metadata.output_fields)
    )

    return (input_type, output_type)
