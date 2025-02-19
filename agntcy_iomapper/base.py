# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod
from typing import Any

from openapi_pydantic import Schema
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self


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


class BaseIOMapperInput(BaseModel):
    input: ArgumentsDescription = Field(description="Input data descriptions")
    output: ArgumentsDescription = Field(description="Output data descriptions")
    data: Any = Field(description="Data to translate")


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
        config: BaseIOMapperConfig | None = None,
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
