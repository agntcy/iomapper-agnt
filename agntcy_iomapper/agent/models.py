# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field

from agntcy_iomapper.base import (
    BaseIOMapperConfig,
    BaseIOMapperInput,
    BaseIOMapperOutput,
)

logger = logging.getLogger(__name__)


class AgentIOMapperInput(BaseIOMapperInput):
    message_template: Union[str, None] = Field(
        max_length=4096,
        default=None,
        description="Message (user) to send to LLM to effect translation.",
    )


AgentIOMapperOutput = BaseIOMapperOutput


class AgentIOMapperConfig(BaseIOMapperConfig):
    system_prompt_template: str = Field(
        max_length=4096,
        default="You are a translation machine. You translate both natural language and object formats for computers. Response_format to { 'type': 'json_object' }",
        description="System prompt Jinja2 template used with LLM service for translation.",
    )
    message_template: str = Field(
        max_length=4096,
        default="The data is described {% if input.json_schema %}by the following JSON schema: {{ input.json_schema.model_dump(exclude_none=True) }}{% else %}as {{ input.description }}{% endif %}, and {%if output.json_schema %} the result must adhere strictly to the following JSON schema: {{ output.json_schema.model_dump(exclude_none=True) }}{% else %}as {{ output.description }}{% endif %}. The data to translate is: {{ data }}. It is absolutely crucial that each field and its type specified in the schema are followed precisely, without introducing any additional fields or altering types. Non-compliance will result in rejection of the output.",
        description="Default user message template. This can be overridden by the message request.",
    )


class FieldMetadata(BaseModel):
    json_path: str = Field(..., description="A json path to the field in the object")
    description: str = Field(
        ..., description="A description of what the field represents"
    )
    examples: Optional[List[str]] = Field(
        None,
        description="A list of examples that represents how the field in json_path is normaly populated",
    )


class IOMappingAgentMetadata(BaseModel):
    input_fields: List[Union[str, FieldMetadata]] = Field(
        ...,
        description="an array of json paths representing fields to be used by io mapper in the mapping",
    )
    output_fields: List[Union[str, FieldMetadata]] = Field(
        ...,
        description="an array of json paths representing firlds to be used by io mapper in the result",
    )
    input_schema: Optional[dict[str, Any]] = Field(
        default=None, description="defines the schema for the input data"
    )
    output_schema: Optional[dict[str, Any]] = Field(
        default=None, description="defines the schema for result of the mapping"
    )
    output_description_prompt: Optional[str] = Field(
        default=None,
        description="A prompt structured using a Jinja template that will be used by the llm for a better mapping",
    )
