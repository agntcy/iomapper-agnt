from typing import Any

from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.workflow import (
    Event,
)
from pydantic import Field, model_validator
from typing_extensions import Self

from agntcy_iomapper.base.models import (
    BaseIOMapperConfig,
    FieldMetadata,
    IOMappingAgentMetadata,
)


class LLamaIndexIOMapperConfig(BaseIOMapperConfig):
    llm: BaseLLM = (
        Field(
            ...,
            description="Model to be used for translation as llama-index.",
        ),
    )


class IOMappingOutputEvent(Event):
    mapping_result: dict = Field(
        ..., description="This is where the mapping result will be populated"
    )


class IOMappingInputEvent(Event):
    metadata: IOMappingAgentMetadata = Field(
        ...,
        description="this object represents information relative to input fields output fields and other io mapping related information",
    )
    config: LLamaIndexIOMapperConfig = Field(
        ...,
        description="this object contains information such as the llm instance that will be used to perform the translation",
    )
    data: Any = Field(
        ..., description="represents the input data to be used in the translation"
    )

    @model_validator(mode="after")
    def _validate_obj(self) -> Self:

        if not self.metadata.input_fields or len(self.metadata.input_fields) == 0:
            raise ValueError("input_fields not found in the metadata")
        # input fields must have a least one non empty string
        valid_input = [
            field
            for field in self.metadata.input_fields
            if (isinstance(field, str) and len(field.strip()) > 0)
            or (isinstance(field, FieldMetadata) and len(field.json_path.strip()) > 0)
        ]

        if not len(valid_input):
            raise ValueError("input_fields must have at least one field")
        else:
            self.metadata.input_fields = valid_input

        if not self.metadata.output_fields:
            raise ValueError("output_fields not found in the metadata")

        # output fields must have a least one non empty string
        valid_output = [
            field
            for field in self.metadata.output_fields
            if (isinstance(field, str) and len(field.strip()) > 0)
            or (isinstance(field, FieldMetadata) and len(field.json_path.strip()) > 0)
        ]

        if not len(valid_output):
            raise ValueError("output_fields must have at least one field")
        else:
            self.metadata.output_fields = valid_output

        return self
