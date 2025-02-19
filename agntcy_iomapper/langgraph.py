# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.utils.runnable import RunnableCallable
from pydantic import Field

from .agent_iomapper import (
    AgentIOMapper,
    AgentIOMapperConfig,
    AgentIOMapperInput,
    AgentIOMapperOutput,
)

logger = logging.getLogger(__name__)

LangGraphIOMapperInput = AgentIOMapperInput
LangGraphIOMapperOutput = AgentIOMapperOutput


class LangGraphIOMapperConfig(AgentIOMapperConfig):
    llm: BaseChatModel | str = Field(
        default="anthropic:claude-3-5-sonnet-latest",
        description="Model to use for translation as LangChain description or model class.",
    )


class _LangGraphAgentIOMapper(AgentIOMapper):
    def __init__(
        self,
        config: LangGraphIOMapperConfig | None = None,
        **kwargs,
    ):
        if config is None:
            config = LangGraphIOMapperConfig()
        super().__init__(config, **kwargs)
        if isinstance(config.llm, str):
            self.llm = init_chat_model(config.llm)
        else:
            self.llm = config.llm

    def _invoke(
        self,
        input: LangGraphIOMapperInput,
        messages: list[dict[str, str]],
        *,
        config: RunnableConfig | None = None,
        **kwargs,
    ) -> str:
        response = self.llm.invoke(messages, config, **kwargs)
        return response.content

    async def _ainvoke(
        self,
        input: LangGraphIOMapperOutput,
        messages: list[dict[str, str]],
        *,
        config: RunnableConfig | None = None,
        **kwargs,
    ) -> str:
        response = await self.llm.ainvoke(messages, config, **kwargs)
        return response.content


class LangGraphIOMapper:
    def __init__(self, config: LangGraphIOMapperConfig):
        self._iomapper = _LangGraphAgentIOMapper(config)

    async def ainvoke(self, state: dict[str, Any], config: RunnableConfig) -> dict:
        response = await self._iomapper.ainvoke(input=state["input"], config=config)
        if response is not None:
            return {"output": response}
        else:
            return {}

    def invoke(self, state: dict[str, Any], config: RunnableConfig) -> dict:
        response = self._iomapper.invoke(input=state["input"], config=config)
        if response is not None:
            return {"output": response}
        else:
            return {}

    def as_runnable(self):
        return RunnableCallable(self.invoke, self.ainvoke, name="extract", trace=False)


def create_iomapper(
    config: LangGraphIOMapperConfig,
) -> Runnable[LangGraphIOMapperInput, LangGraphIOMapperOutput]:
    return LangGraphIOMapper(config).as_runnable()
