# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod
from typing import Any, Optional

from openapi_pydantic import Schema
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self


class ArgumentsDescription(BaseModel):
    """
    ArgumentsDescription a pydantic model that defines
    the details necessary to perfom io mapping between two agents
    """

    json_schema: Optional[Schema] = Field(
        default=None, description="Data format JSON schema"
    )
    description: Optional[str] = Field(
        default="", description="Data (semantic) natural language description"
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
    data: Any = Field(default=None, description="Data after translation")
    error: str | None = Field(
        max_length=4096, default=None, description="Description of error on failure."
    )


class BaseIOMapperConfig(BaseModel):
    validate_json_input: bool = Field(
        default=False, description="Validate input against JSON schema."
    )
    validate_json_output: bool = Field(
        default=False, description="Validate output against JSON schema."
    )


class BaseIOMapper(ABC):
    """Abstract base class for interfacing with io mapper.
    All io mappers wrappers inherited from BaseIOMapper.
    """

    def __init__(
        self,
        config: Optional[BaseIOMapperConfig] = None,
    ):
        self.config = config if config is not None else BaseIOMapperConfig()

    @abstractmethod
    def invoke(self, input: BaseIOMapperInput) -> BaseIOMapperOutput:
        """Pass input data
        to be mapped and returned represented in the output schema
        Args:
            input: the data to be mapped
        """

    @abstractmethod
    async def ainvoke(self, input: BaseIOMapperInput) -> BaseIOMapperOutput:
        """Pass input data
        to be mapped and returned represented in the output schema
        Args:
            input: the data to be mapped
        """
