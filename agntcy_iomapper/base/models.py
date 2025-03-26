# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Callable, List, Optional, Union

from openapi_pydantic import Schema
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

logger = logging.getLogger(__name__)


class ArgumentsDescription(BaseModel):
    """
    ArgumentsDescription a pydantic model that defines
    the details necessary to perfom io mapping between two agents
    """

    json_schema: Optional[Schema] = Field(
        default=None, description="Data format JSON schema"
    )
    description: Optional[str] = Field(
        default=None, description="Data (semantic) natural language description"
    )
    agent_manifest: Optional[dict[str, Any]] = Field(
        default=None,
        description="Agent Manifest definition as per https://agntcy.github.io/acp-spec/openapi.html#model/agentmanifest",
    )

    @model_validator(mode="after")
    def _validate_obj(self) -> Self:
        if (
            self.json_schema is None
            and self.description is None
            and self.agent_manifest
        ):
            raise ValueError(
                'Either the "schema" field and/or the "description" or agent_manifest field must be specified.'
            )
        return self


class BaseIOMapperInput(BaseModel):
    input: ArgumentsDescription = Field(
        description="Input data descriptions",
    )
    output: ArgumentsDescription = Field(
        description="Output data descriptions",
    )
    data: Any = Field(description="Data to translate")

    @model_validator(mode="after")
    def _validate_obj(self) -> Self:
        if self.input.agent_manifest is not None:
            # given an input agents manifest map its ouput definition
            # because the data to be mapped is the result of calling the input agent
            self.input.json_schema = Schema.model_validate(
                self.input.agent_manifest["specs"]["output"]
            )

        if self.output.agent_manifest:
            # given an output agents manifest map its input definition
            # because the data to be mapped would be mapped to it's input
            self.output.json_schema = Schema.model_validate(
                self.output.agent_manifest["specs"]["input"]
            )

        return self


class BaseIOMapperOutput(BaseModel):
    data: Optional[Any] = Field(default=None, description="Data after translation")
    error: Optional[str] = Field(
        max_length=4096, default=None, description="Description of error on failure."
    )


class BaseIOMapperConfig(BaseModel):
    validate_json_input: bool = Field(
        default=False, description="Validate input against JSON schema."
    )
    validate_json_output: bool = Field(
        default=False, description="Validate output against JSON schema."
    )
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


class AgentIOMapperInput(BaseIOMapperInput):
    message_template: Union[str, None] = Field(
        max_length=4096,
        default=None,
        description="Message (user) to send to LLM to effect translation.",
    )


AgentIOMapperOutput = BaseIOMapperOutput


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
    field_mapping: Optional[dict[str, Union[str, Callable]]] = Field(
        default=None,
        description="A dictionary representing how the imperative mapping should be done where the keys are fields of the output object and values are JSONPath (strings)",
    )
