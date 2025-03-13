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
        default="You are a translation machine. You translate both natural language and object formats for computers.",
        description="System prompt Jinja2 template used with LLM service for translation.",
    )
    message_template: str = Field(
        max_length=4096,
        default="The input is described {% if input.json_schema %}by the following JSON schema: {{ input.json_schema.model_dump(exclude_none=True) }}{% else %}as {{ input.description }}{% endif %}, and the output is explained by {{output.description}} and described by {% if output.json_schema %}by the following JSON schema: {{ output.json_schema.model_dump(exclude_none=True) }}{% else %}as {{ output.description }}{% endif %}. The data to translate is: {{ data }}",
        description="Default user message template. This can be overridden by the message request.",
    )


class IOMappingAgentMetadata(BaseModel):
    input_fields: List[str] = Field(
        ...,
        description="an array of json paths representing fields to be used by io mapper in the mapping",
    )
    output_fields: List[str] = Field(
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
