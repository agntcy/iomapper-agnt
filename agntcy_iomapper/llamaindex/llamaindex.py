# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0"
import logging
from typing import Any, Optional

from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.llms import ChatMessage
from pydantic import Field

from agntcy_iomapper.base import AgentIOMapper, AgentIOMapperConfig, AgentIOMapperInput

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
        config: Optional[LLamaIndexIOMapperConfig] = None,
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
