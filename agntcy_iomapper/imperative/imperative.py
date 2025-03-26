# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
The deterministic I/O mapper is a component
designed to translate specific inputs into
corresponding outputs in a predictable and consistent manner.
When configured with a JSONPath definition,
this mapper utilizes the JSONPath query language
to extract data from JSON-formatted input,
transforming it into a structured output based on predefined rules.
The deterministic nature of the mapper ensures that given the same input and
JSONPath configuration, the output will always be the same,
providing reliability and repeatability.
This is particularly useful in scenarios where
consistent data transformation is required.
"""

import json
import logging
from typing import Any, Callable, Optional, Union

import jsonschema
from jsonpath_ng.ext import parse
from langgraph.utils.runnable import RunnableCallable

from agntcy_iomapper.base import (
    BaseIOMapper,
    BaseIOMapperConfig,
    BaseIOMapperInput,
    BaseIOMapperOutput,
)

logger = logging.getLogger(__name__)


ImperativeIOMapperInput = BaseIOMapperInput
ImperativeIOMapperOutput = BaseIOMapperOutput


class ImperativeIOMapper(BaseIOMapper):

    def __init__(
        self,
        input: ImperativeIOMapperInput,
        field_mapping: dict[str, Union[str, Callable]],
        config: Optional[BaseIOMapperConfig] = None,
    ) -> None:
        super().__init__(config)
        self.field_mapping = field_mapping
        self.input = input

    def invoke(self, data: any) -> dict:
        _input = self.input if self.input else None

        if _input is None or _input.data is None:
            return None
        if self.field_mapping is None:
            return _input.data

        data = self._imperative_map(_input)
        return json.loads(data)

    async def ainvoke(self, state: any) -> dict:
        return self.invoke()

    def _imperative_map(self, input_definition: ImperativeIOMapperInput) -> Any:
        """
        Converts input data to a desired output type.

        This function attempts to convert the provided data into the specified
        target type. It performs validation using a JSON schema and raises a
        ValidationError if the data does not conform to the expected schema for
        the target type.

        The function assumes that the caller provides a valid `input_schema`.
        Unsupported target types should be handled as needed within the function.
        """
        data = input_definition.data
        input_schema = input_definition.input.json_schema

        jsonschema.validate(
            instance=data,
            schema=input_schema.model_dump(exclude_none=True, mode="json"),
        )

        mapped_output = {}

        for output_field, json_path_or_func in self.field_mapping.items():
            if isinstance(json_path_or_func, str):
                jsonpath_expr = parse(json_path_or_func)
                match = jsonpath_expr.find(data)
                expect_value = match[0].value if match else None
            elif callable(json_path_or_func):
                expect_value = json_path_or_func(data)
            else:
                raise TypeError(
                    "Mapping values must be strings (JSONPath) or callables (functions)."
                )

            self._set_jsonpath(mapped_output, output_field, expect_value)
        jsonschema.validate(
            instance=mapped_output,
            schema=input_definition.output.json_schema.model_dump(
                exclude_none=True, mode="json"
            ),
        )
        # return a serialized version of the object
        return json.dumps(mapped_output)

    def _set_jsonpath(
        self, data: dict[str, Any], path: str, value: Any
    ) -> dict[str, Any]:
        """set value for field based on its json path
        Args:
            data: Data so far
            path: the json path
            value: the value to set the json path to
        Returns:
        -----
        dict[str,Any]
            The mapped filed with the value
        """
        copy_data: dict[str, Any] = data
        # Split the path into parts and remove the leading root
        parts = path.strip("$.").split(".")
        # Add value to corresponding path
        for part in parts[:-1]:
            if part not in copy_data:
                copy_data[part] = {}

            copy_data = copy_data[part]

        copy_data[parts[-1]] = value

        return copy_data

    def as_runnable(self):
        return RunnableCallable(self.invoke, self.ainvoke, name="extract", trace=False)
