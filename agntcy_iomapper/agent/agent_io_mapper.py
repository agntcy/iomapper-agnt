# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Callable, List, Optional, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.tools import BaseTool
from llama_index.core.workflow import (
    Workflow,
)
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from agntcy_iomapper.base.models import (
    AgentIOMapperInput,
    ArgumentsDescription,
    FieldMetadata,
    IOMappingAgentMetadata,
)
from agntcy_iomapper.base.utils import extract_nested_fields, get_io_types
from agntcy_iomapper.imperative import (
    ImperativeIOMapper,
    ImperativeIOMapperInput,
)
from agntcy_iomapper.langgraph import LangGraphIOMapper, LangGraphIOMapperConfig
from agntcy_iomapper.llamaindex.llamaindex import (
    LLamaIndexIOMapper,
)

logger = logging.getLogger(__name__)


class IOMappingAgent(BaseModel):
    """This class exposes all
    The IOMappingAgent class is designed for developers building sophisticated multi-agent software that require seamless integration and interaction between
    the different agents and workflow steps.
    By utilizing the methods provided, developers can construct complex workflows and softwares.
    The IOMappingAgent class is intended to serve as a foundational component in applications requiring advanced IO mapping agents in multi-agent systems.
    """

    metadata: Optional[IOMappingAgentMetadata] = Field(
        ...,
        description="Details about the fields to be used in the translation and about the output",
    )
    llm: Optional[Union[BaseChatModel, str]] = Field(
        None,
        description="Model to use for translation as LangChain description or model class.",
    )

    @model_validator(mode="after")
    def _validate_obj(self) -> Self:
        if not self.metadata:
            return self

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

    def langgraph_node(self, data: Any, config: Optional[dict] = None) -> Runnable:
        """This method is used to add a language graph node to a langgraph multi-agent software.
        It leverages language models for IO mapping, ensuring efficient communication between agents.
        """

        input_type, output_type = get_io_types(data, self.metadata)

        data_to_be_mapped = extract_nested_fields(
            data, fields=self.metadata.input_fields
        )

        input = AgentIOMapperInput(
            input=ArgumentsDescription(
                json_schema=input_type,
            ),
            output=ArgumentsDescription(json_schema=output_type),
            data=data_to_be_mapped,
        )

        if not self.llm and config:
            configurable = config.get("configurable", None)
            if configurable is None:
                raise ValueError("llm instance not provided")

            llm = configurable.get("llm", None)

            if llm is None:
                raise ValueError("llm instance not provided")

            self.llm = llm

        if not self.llm:
            raise ValueError("llm instance not provided")

        iomapper_config = LangGraphIOMapperConfig(llm=self.llm)
        return LangGraphIOMapper(iomapper_config, input).as_runnable()

    def langgraph_imperative(
        self, data: Any, config: Optional[dict] = None
    ) -> Runnable:
        """
        Description: Similar to langgraph_node, this method adds a language graph node to a multi-agent software.
        However, it does not utilize a language model for IO mapping, offering an imperative approach to agent integration.
        """

        input_type, output_type = get_io_types(data, self.metadata)

        data_to_be_mapped = extract_nested_fields(
            data, fields=self.metadata.input_fields
        )

        input = ImperativeIOMapperInput(
            input=ArgumentsDescription(
                json_schema=input_type,
            ),
            output=ArgumentsDescription(json_schema=output_type),
            data=data_to_be_mapped,
        )

        if not self.metadata.field_mapping:
            raise ValueError(
                "In order to use imperative mapping field_mapping must be provided in the metadata"
            )

        imperative_io_mapper = ImperativeIOMapper(
            input=input, field_mapping=self.metadata.field_mapping
        )
        return imperative_io_mapper.as_runnable()

    @staticmethod
    def as_worfklow_step(workflow: Workflow) -> Callable:
        """This static method allows for the addition of a step to a LlamaIndex workflow.
        It integrates seamlessly into workflows, enabling structured progression and task execution.
        """
        io_mapper_step = LLamaIndexIOMapper.llamaindex_mapper(workflow)
        return io_mapper_step

    @staticmethod
    def as_workflow_agent(
        mapping_metadata: IOMappingAgentMetadata,
        llm: BaseLLM,
        name: str,
        description: str,
        can_handoff_to: Optional[List[str]] = None,
        tools: Optional[List[Union[BaseTool, Callable]]] = [],
    ):
        """This static method returns an instance of an agent that can be integrated into a Multi AgentWorkflow.
        It provides robust IO mapping capabilities essential for complex multi agent workflow interactions.
        """
        return LLamaIndexIOMapper(
            mapping_metadata=mapping_metadata,
            llm=llm,
            tools=tools,
            name=name,
            description=description,
            can_handoff_to=can_handoff_to,
        )
