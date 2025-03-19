# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Tuple, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from openapi_pydantic import Schema
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from agntcy_iomapper.agent.models import AgentIOMapperInput, IOMappingAgentMetadata
from agntcy_iomapper.base import ArgumentsDescription
from agntcy_iomapper.base.utils import create_type_from_schema, extract_nested_fields
from agntcy_iomapper.langgraph import LangGraphIOMapper, LangGraphIOMapperConfig

logger = logging.getLogger(__name__)


class IOMappingAgent(BaseModel):
    llm: Union[BaseChatModel, str] = (
        Field(
            ...,
            description="Model to use for translation as LangChain description or model class.",
        ),
    )
    metadata: IOMappingAgentMetadata = Field(
        ...,
        description="Details about the fields to be used in the translation and about the output",
    )

    @model_validator(mode="after")
    def _validate_obj(self) -> Self:

        if not self.metadata.input_fields:
            raise ValueError("input_fields not found in the metadata")
        # input fields must have a least one non empty string
        valid_input = [
            field for field in self.metadata.input_fields if len(field.strip()) > 0
        ]

        if not len(valid_input):
            raise ValueError("input_fields must have at least one field")
        else:
            self.metadata.input_fields = valid_input

        if not self.metadata.output_fields:
            raise ValueError("output_fields not found in the metadata")

        # outpu fields must have a least one non empty string
        valid_output = [
            field for field in self.metadata.output_fields if len(field.strip()) > 0
        ]
        if not len(valid_output):
            raise ValueError("output_fields must have at least one field")
        else:
            self.metadata.output_fields = valid_output

        if not self.llm:
            raise ValueError(
                "to use io_mapper_node an llm config must be passed via langgraph runnable config"
            )

        return self

    def _get_io_types(self, data: Any) -> Tuple[Schema, Schema]:
        data_schema = None
        if isinstance(data, BaseModel):
            data_schema = data.model_json_schema()
        # If input schema is provided it overwrites the data schema
        input_schema = (
            self.metadata.input_schema if self.metadata.input_schema else data_schema
        )
        # If output schema is provided it overwrites the data schema
        output_schema = (
            self.metadata.output_schema if self.metadata.output_schema else data_schema
        )

        if not input_schema or not output_schema:
            raise ValueError(
                "input_schema, and or output_schema are missing from the metadata, for a better accuracy you are required to provide them in this scenario, or we  could not infer the type from the state"
            )

        input_type = Schema.model_validate(
            create_type_from_schema(input_schema, self.metadata.input_fields)
        )

        output_type = Schema.model_validate(
            create_type_from_schema(output_schema, self.metadata.output_fields)
        )

        return (input_type, output_type)

    def langgraph_node(self, data: Any) -> Runnable:

        # If there is a template for the output the output_schema is going to be ignored in the translation
        output_template = self.metadata.output_description_prompt
        input_type, output_type = self._get_io_types(data)

        data_to_be_mapped = extract_nested_fields(
            data, fields=self.metadata.input_fields
        )

        input = AgentIOMapperInput(
            input=ArgumentsDescription(
                json_schema=input_type,
            ),
            output=ArgumentsDescription(
                json_schema=output_type, description=output_template
            ),
            data=data_to_be_mapped,
        )

        iomapper_config = LangGraphIOMapperConfig(llm=self.llm)
        return LangGraphIOMapper(iomapper_config, input).as_runnable()
