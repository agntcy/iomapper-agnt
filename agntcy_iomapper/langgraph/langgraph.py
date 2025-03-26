# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Optional, Union

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langgraph.utils.runnable import RunnableCallable
from pydantic import Field

from agntcy_iomapper.base import BaseIOMapper, BaseIOMapperConfig
from agntcy_iomapper.base.models import (
    AgentIOMapperInput,
    AgentIOMapperOutput,
)

logger = logging.getLogger(__name__)

LangGraphIOMapperInput = AgentIOMapperInput
LangGraphIOMapperOutput = AgentIOMapperOutput


class LangGraphIOMapperConfig(BaseIOMapperConfig):
    llm: Union[BaseChatModel, str] = (
        Field(
            ...,
            description="Model to use for translation as LangChain description or model class.",
        ),
    )


class _LangGraphAgentIOMapper(BaseIOMapper):
    def __init__(
        self,
        config: Optional[LangGraphIOMapperConfig] = None,
        **kwargs,
    ):
        if config is None:
            config = LangGraphIOMapperConfig()
        super().__init__(config, **kwargs)
        if isinstance(config.llm, str):
            self.llm = init_chat_model(config.llm)
        else:
            self.llm = config.llm

    def invoke(
        self,
        input: LangGraphIOMapperInput,
        messages: list[dict[str, str]],
        *,
        config: Optional[RunnableConfig] = None,
        **kwargs,
    ) -> str:
        response = self.llm.invoke(messages, config, **kwargs)
        return response.content

    async def ainvoke(
        self,
        input: LangGraphIOMapperOutput,
        messages: list[dict[str, str]],
        *,
        config: Optional[RunnableConfig] = None,
        **kwargs,
    ) -> str:
        response = await self.llm.ainvoke(messages, config, **kwargs)
        return response.content


class LangGraphIOMapper:
    def __init__(
        self,
        config: LangGraphIOMapperConfig,
        input: Optional[LangGraphIOMapperInput] = None,
    ):
        self._iomapper = _LangGraphAgentIOMapper(config)
        self._input = input

    async def ainvoke(self, state: dict[str, Any], config: RunnableConfig) -> dict:
        input = self._input if self._input else state["input"]
        response = await self._iomapper._ainvoke(input=input, config=config)
        if response is not None:
            return response.data
        else:
            return {}

    def invoke(self, state: dict[str, Any], config: RunnableConfig) -> dict:
        input = self._input if self._input else state["input"]
        response = self._iomapper._invoke(input=input, config=config)

        if response is not None:
            return response.data
        else:
            return {}

    def as_runnable(self):
        return RunnableCallable(self.invoke, self.ainvoke, name="extract", trace=False)
