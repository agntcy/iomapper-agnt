# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, List, Optional, Sequence

from jinja2 import Environment
from llama_index.core.agent.workflow import (
    FunctionAgent,
)
from llama_index.core.agent.workflow.workflow_events import (
    AgentOutput,
)
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import BaseMemory
from llama_index.core.tools import AsyncBaseTool, BaseTool
from llama_index.core.workflow import (
    Context,
    Workflow,
    step,
)
from pydantic import Field

from agntcy_iomapper.base import AgentIOMapperInput, ArgumentsDescription, BaseIOMapper
from agntcy_iomapper.base.models import AgentIOMapperOutput, IOMappingAgentMetadata
from agntcy_iomapper.base.utils import extract_nested_fields, get_io_types
from agntcy_iomapper.llamaindex.models import (
    IOMappingInputEvent,
    IOMappingOutputEvent,
    LLamaIndexIOMapperConfig,
)

logger = logging.getLogger(__name__)


class _LLmaIndexAgentIOMapper(BaseIOMapper):
    def __init__(
        self,
        config: Optional[LLamaIndexIOMapperConfig] = None,
        jinja_env: Optional[Environment] = None,
        jinja_env_async: Optional[Environment] = None,
    ):
        if config is None:
            config = LLamaIndexIOMapperConfig()

        super().__init__(
            config=config, jinja_env=jinja_env, jinja_env_async=jinja_env_async
        )

        if not config.llm:
            raise ValueError("Llm must be configured")
        else:
            self.llm = config.llm

    def invoke(
        self,
        input: AgentIOMapperInput,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> str:

        llama_index_messages = self._map_to_llama_index_messages(messages)
        response = self.llm.chat(llama_index_messages, **kwargs)
        return str(response)

    async def ainvoke(
        self,
        input: AgentIOMapperInput,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> str:
        llama_index_messages = self._map_to_llama_index_messages(messages)
        response = await self.llm.achat(llama_index_messages, **kwargs)
        return response.message.content

    def _map_to_llama_index_messages(self, messages: list[dict[str, str]]):
        return [ChatMessage(**message) for message in messages]


class LLamaIndexIOMapper(FunctionAgent):
    mapping_metadata: IOMappingAgentMetadata = Field(
        ...,
        description="Object used to describe the input fields, output fields schema and any relevant information to be used in the mapping",
    )

    def __init__(self, tools: List[BaseTool] = [], **kwargs: Any) -> None:
        super().__init__(
            tools=tools,
            **kwargs,
        )

    async def take_step(
        self,
        ctx: Context,
        llm_input: List[ChatMessage],
        tools: Sequence[AsyncBaseTool],
        memory: BaseMemory,
    ) -> AgentOutput:
        """Take a single step with the agent."""
        res = await self._run_step(llm_input=llm_input, ctx=ctx)
        super_res = await super().take_step(
            ctx=ctx, llm_input=llm_input, tools=tools, memory=memory
        )
        # calling the super to be able to get the tools passed
        res.tool_calls = super_res.tool_calls

        return res

    async def _run_step(
        self, llm_input: List[ChatMessage], ctx: Context, **kwargs
    ) -> AgentOutput:
        """Take a single step with the function calling agent."""

        config = LLamaIndexIOMapperConfig(llm=self.llm)
        curr_state = await ctx.get("state")
        mapping_result = await self._get_output(
            config=config, metadata=self.mapping_metadata, input_data=curr_state
        )

        curr_state.update(mapping_result.data)
        await ctx.set("state", curr_state)

        return AgentOutput(
            response=mapping_result.data,
            tool_calls=[],
            raw=mapping_result,
            current_agent_name=self.name,
        )

    @classmethod
    async def _get_output(
        cls,
        config: LLamaIndexIOMapperConfig,
        metadata: IOMappingAgentMetadata,
        input_data: Any,
    ) -> AgentIOMapperOutput:
        """method used to invoke the llm to get the maping result"""

        _iomapper = _LLmaIndexAgentIOMapper(config)

        input_type, output_type = get_io_types(data=input_data, metadata=metadata)

        data_to_be_mapped = extract_nested_fields(
            input_data, fields=metadata.input_fields
        )

        input = AgentIOMapperInput(
            input=ArgumentsDescription(
                json_schema=input_type,
            ),
            output=ArgumentsDescription(json_schema=output_type),
            data=data_to_be_mapped,
        )

        mapping_result = await _iomapper._ainvoke(input)
        return mapping_result

    @classmethod
    def llamaindex_mapper(cls, workflow: Workflow):
        """Adds a step to the given workflow"""

        @step(workflow=workflow)
        async def io_mapper_step(
            input_event: IOMappingInputEvent,
        ) -> IOMappingOutputEvent:
            mapping_res = await cls._get_output(
                config=input_event.config,
                metadata=input_event.metadata,
                input_data=input_event.data,
            )

            return IOMappingOutputEvent(mapping_result=mapping_res.data)
