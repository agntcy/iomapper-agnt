# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0"
from typing import Any

from langchain_core.runnables import Runnable
from openapi_pydantic import Schema
from pydantic import BaseModel

from agntcy_iomapper.base import AgentIOMapperInput, ArgumentsDescription
from agntcy_iomapper.base.utils import _create_type_from_schema, _extract_nested_fields

from .langgraph import (
    LangGraphIOMapper,
    LangGraphIOMapperConfig,
    LangGraphIOMapperInput,
    LangGraphIOMapperOutput,
)


def create_langraph_iomapper(
    config: LangGraphIOMapperConfig,
) -> Runnable[LangGraphIOMapperInput, LangGraphIOMapperOutput]:
    """Creates a langgraph agent
    Args:
      config: The configuration of the llm that would be used during the mapping
    Returns:
      A runnable representing an agent. It returns as output the mapping result
    """
    return LangGraphIOMapper(config).as_runnable()


def io_mapper_node(data: Any, config: dict) -> Runnable:
    """Creates a langgraph node
    Args:
      data: represents the state of the graph
      config: is the runnable config inject by langgraph framework
      metadata has the following structure
       - input_fields: Required, it expects an array of fields to be used in the mapping, this fields must be in the state eg: ["name", "address.street"]
       - input_fields: Required, it expects an array of fields to include in the mapping result, eg: ["full_name", "full_address"]
       - input_schema: Optional, defines the schema of the input_data, this is useful if your state is not a pydantic model, not required if you state is a pydantic model.
       - output_schema: Optional, defines the schema of the output_data, this is useful if your output is not a pydantic model, not required if your output model is a pydantic model.
         To understand better how and when to use any of these options check the examples folder
    Returns:
      A runnable, that can be included in the langgraph node
    """
    metadata = config["metadata"]
    if not metadata:
        return ValueError(
            "A metadata must be present with at least the configuration for input_fields and output_fields"
        )
    if not data:
        return ValueError("data is required. Invalid or no data was passed")

    input_fields = metadata["input_fields"]
    if not input_fields:
        return ValueError("input_fields not found in the metadata")

    output_fields = metadata["output_fields"]
    if not output_fields:
        return ValueError("output_fields not found in the metadata")

    llm = config["configurable"]["llm"]
    if not llm:
        return ValueError(
            "to use io_mapper_node an llm config must be passed via langgraph runnable config"
        )
    input_type = None
    output_type = None

    if isinstance(data, BaseModel):
        input_schema = data.model_json_schema()
    else:
        # Read the optional fields
        input_schema = metadata["input_schema"]
        output_schema = metadata["output_schema"]
        if not input_schema or not output_schema:
            raise ValueError(
                "input_schema, and or output_schema are missing from the metadata, for a better accuracy you are required to provide them in this scenario"
            )

    output_type = _create_type_from_schema(input_schema, output_fields)
    input_type = _create_type_from_schema(input_schema, input_fields)

    data_to_be_mapped = _extract_nested_fields(data, fields=input_fields)

    input = AgentIOMapperInput(
        input=ArgumentsDescription(
            json_schema=input_type,
        ),
        output=ArgumentsDescription(
            json_schema=output_type,
        ),
        data=data_to_be_mapped,
    )

    iomapper_config = LangGraphIOMapperConfig(llm=llm)
    return LangGraphIOMapper(iomapper_config, input).as_runnable()
