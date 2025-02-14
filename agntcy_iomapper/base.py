# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
from abc import abstractmethod, ABC
from pydantic import BaseModel, model_validator, Field
from typing import Any
from openapi_pydantic import Schema
from typing_extensions import Self
from typing import TypedDict


class ArgumentsDescription(BaseModel):
    json_schema: Schema | None = Field(
        default=None, description="Data format JSON schema"
    )
    description: str | None = Field(
        default=None, description="Data (semantic) natural language description"
    )

    @model_validator(mode="after")
    def _validate_obj(self) -> Self:
        if self.json_schema is None and self.description is None:
            raise ValueError(
                'Either the "schema" field and/or the "description" field must be specified.'
            )
        return self


class IOModelSettings(TypedDict, total=False):
    max_tokens: int
    temperature: float
    top_p: float
    parallel_tool_calls: bool
    seed: int
    presence_penalty: float
    frequency_penalty: float
    logit_bias: dict[str, int]


class IOMapperInput(BaseModel):
    input: ArgumentsDescription = Field(description="Input data descriptions")
    output: ArgumentsDescription = Field(description="Output data descriptions")
    data: Any = Field(description="Data to translate")
    message_template: str | None = Field(
        max_length=4096,
        default=None,
        description="Message (user) to send to LLM to effect translation.",
    )
    model_settings: IOModelSettings | None = Field(
        default=None,
        description="Specific arguments for LLM transformation.",
    )
    model: str | None = Field(
        default=None,
        description="Specific model out of those configured to handle request.",
    )


class IOMapperOutput(BaseModel):
    data: Any = Field(default=None, description="Data after translation")
    error: str | None = Field(
        max_length=4096, default=None, description="Description of error on failure."
    )


class BaseIOMapper(ABC):
    """Abstract base class for interfacing with io mapper.
    All io mappers wrappers inherited from BaseIOMapper.
    """

    @abstractmethod
    def invoke(self, input: IOMapperInput) -> IOMapperOutput:
        """Pass input data
        to be mapped and returned represented in the output schema
        Args:
            input: the data to be mapped
        """

    @abstractmethod
    async def ainvoke(self, input: IOMapperInput) -> IOMapperOutput:
        """Pass input data
        to be mapped and returned represented in the output schema
        Args:
            input: the data to be mapped
        """
