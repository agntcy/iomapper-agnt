# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0"
from langchain_core.runnables import Runnable

from .langgraph import (
    LangGraphIOMapper,
    LangGraphIOMapperConfig,
    LangGraphIOMapperInput,
    LangGraphIOMapperOutput,
)


def create_langraph_iomapper(
    config: LangGraphIOMapperConfig,
) -> Runnable[LangGraphIOMapperInput, LangGraphIOMapperOutput]:
    """Creates a langgraph agent
    Args:
      config: The configuration of the llm that would be used during the mapping
    Returns:
      A runnable representing an agent. It returns as output the mapping result
    """
    return LangGraphIOMapper(config).as_runnable()
