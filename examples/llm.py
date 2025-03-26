# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from enum import Enum

from langchain_openai.chat_models.azure import AzureChatOpenAI
from llama_index.llms.azure_openai import AzureOpenAI

os.environ["AZURE_OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""


class Framework(Enum):
    LANGCHAIN = 1
    LLAMA_INDEX = 2


def get_azure(framework: Framework = Framework.LANGCHAIN):
    api_version = "2024-07-01-preview"
    model_version = "gpt-4o-mini"
    if framework == Framework.LANGCHAIN:
        return AzureChatOpenAI(
            model=model_version,
            api_version=api_version,
            seed=42,
            temperature=0,
        )
    elif framework == Framework.LLAMA_INDEX:
        return AzureOpenAI(
            engine=model_version,
            model=model_version,
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=api_version,
        )
