# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import pytest
from dotenv import find_dotenv, load_dotenv
from langchain_openai.chat_models.azure import AzureChatOpenAI

from agntcy_iomapper.langgraph import LangGraphIOMapperConfig


@pytest.fixture
def llm_iomapper_config() -> LangGraphIOMapperConfig:
    return LangGraphIOMapperConfig(
        llm=AzureChatOpenAI(
            model="gpt-4o-mini",
            api_version="2024-07-01-preview",
            seed=42,
            temperature=0,
        ),
        validate_json_input=True,
        validate_json_output=True,
    )


@pytest.fixture
def llm_instance() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        model="gpt-4o-mini",
        api_version="2024-07-01-preview",
        seed=42,
        temperature=0,
    )


load_dotenv(dotenv_path=find_dotenv(usecwd=True))
