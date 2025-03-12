# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0"
import logging
from typing import Any, List

from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent
from llama_index.core.agent.workflow.workflow_events import (
    AgentOutput,
)
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.llms import ChatMessage
from llama_index.core.workflow import Context
from pydantic import Field

from agntcy_iomapper.base import AgentIOMapper, AgentIOMapperConfig, AgentIOMapperInput
from agntcy_iomapper.base.utils import (
    instantiate_input,
)

logger = logging.getLogger(__name__)


class LLamaIndexIOMapperConfig(AgentIOMapperConfig):
    llm: BaseLLM = (
        Field(
            ...,
            description="Model to be used for translation as llama-index.",
        ),
    )


class _LLmaIndexAgentIOMapper(AgentIOMapper):
    def __init__(
        self,
        config: LLamaIndexIOMapperConfig | None = None,
        **kwargs,
    ):
        if config is None:
            config = LLamaIndexIOMapperConfig()
        super().__init__(config, **kwargs)
        if not config.llm:
            raise ValueError("Llm must be configured")
        else:
            self.llm = config.llm

    def _invoke(
        self,
        input: AgentIOMapperInput,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> str:

        llama_index_messages = self._map_to_llama_index_messages(messages)
        response = self.llm.chat(llama_index_messages, **kwargs)
        return str(response)

    async def _ainvoke(
        self,
        input: AgentIOMapperInput,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> str:
        llama_index_messages = self._map_to_llama_index_messages(messages)
        response = await self.llm.achat(llama_index_messages, **kwargs)
        return str(response)

    def _map_to_llama_index_messages(self, messages: list[dict[str, str]]):
        return [ChatMessage(**message) for message in messages]


class LLamaIndexIOMapper:
    def __init__(self, config: LLamaIndexIOMapperConfig, input: AgentIOMapperInput):
        self._iomapper = _LLmaIndexAgentIOMapper(config)
        self._input = input

    async def ainvoke(self) -> dict:
        input = self._input
        response = await self._iomapper.ainvoke(input=input)
        if response is not None:
            return response.data
        else:
            return {}

    def invoke(self, state: dict[str, Any]) -> dict:
        input = self._input if self._input else state["input"]
        response = self._iomapper.invoke(input=input)

        if response is not None:
            return response.data
        else:
            return {}


class IOMapperAgent(BaseWorkflowAgent):
    llm: BaseLLM = Field(..., "")
    data: Any = Field(..., "")
    input_fields: List[str] = Field(..., "")
    output_fields: List[str] = Field(..., "")
    input_schema: dict[str, str] | None = Field(None, "")
    output_schema: dict[str, str] | None = Field(None, "")

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    """Function calling agent implementation."""

    scratchpad_key: str = "scratchpad"

    async def take_step(self, ctx: Context, **kwargs) -> AgentOutput:
        """Take a single step with the function calling agent."""
        if not self.llm:
            raise ValueError("LLM must be provided")

        input = instantiate_input(
            data=self.data,
            input_fields=self.input_fields,
            output_fields=self.output_fields,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
        )

        config = LLamaIndexIOMapperConfig(llm=self.llm)
        io_mapping = LLamaIndexIOMapper(config=config, input=input)
        mapping_res = await io_mapping.ainvoke()

        return AgentOutput(response=mapping_res, current_agent_name=self.name)

        # return AgentOutput(
        #     response=last_chat_response.message,
        #     tool_calls=tool_calls or [],
        #     raw=raw,
        #     current_agent_name=self.name,
        # )

        # scratchpad: List[ChatMessage] = await ctx.get(self.scratchpad_key, default=[])
        # current_llm_input = [*llm_input, *scratchpad]
        #
        # ctx.write_event_to_stream(
        #     AgentInput(input=current_llm_input, current_agent_name=self.name)
        # )
        #
        # response = await self.llm.astream_chat_with_tools(  # type: ignore
        #     tools, chat_history=current_llm_input, allow_parallel_tool_calls=True
        # )
        # # last_chat_response will be used later, after the loop.
        # # We initialize it so it's valid even when 'response' is empty
        # last_chat_response = ChatResponse(message=ChatMessage())
        # async for last_chat_response in response:
        #     tool_calls = self.llm.get_tool_calls_from_response(  # type: ignore
        #         last_chat_response, error_on_no_tool_call=False
        #     )
        #     raw = (
        #         last_chat_response.raw.model_dump()
        #         if isinstance(last_chat_response.raw, BaseModel)
        #         else last_chat_response.raw
        #     )
        #     ctx.write_event_to_stream(
        #         AgentStream(
        #             delta=last_chat_response.delta or "",
        #             response=last_chat_response.message.content or "",
        #             tool_calls=tool_calls or [],
        #             raw=raw,
        #             current_agent_name=self.name,
        #         )
        #     )
        #
        # tool_calls = self.llm.get_tool_calls_from_response(  # type: ignore
        #     last_chat_response, error_on_no_tool_call=False
        # )
        #
        # # only add to scratchpad if we didn't select the handoff tool
        # scratchpad.append(last_chat_response.message)
        # await ctx.set(self.scratchpad_key, scratchpad)
        #
        # raw = (
        #     last_chat_response.raw.model_dump()
        #     if isinstance(last_chat_response.raw, BaseModel)
        #     else last_chat_response.raw
        # )
        # return AgentOutput(
        #     response=last_chat_response.message,
        #     tool_calls=tool_calls or [],
        #     raw=raw,
        #     current_agent_name=self.name,
        # )
