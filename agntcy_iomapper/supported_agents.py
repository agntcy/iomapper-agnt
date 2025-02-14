# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
from typing import Literal, Any
from openai import AsyncAzureOpenAI
from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName
from pydantic_ai.models.openai import OpenAIModel

SupportedModelName = (
    KnownModelName
    | Literal[
        "azure:gpt-4o-mini",
        "azure:gpt-4o",
        "azure:gpt-4",
    ]
)


def get_supported_agent(
    is_async: bool,
    model_name: SupportedModelName,
    model_args: dict[str, Any] = {},
    **kwargs,
) -> Agent:
    if model_name.startswith("azure:"):
        # Note: the client is always async even if you call run_sync
        client = AsyncAzureOpenAI(**model_args)
        model = OpenAIModel(model_name[6:], openai_client=client)
        return Agent(model, **kwargs)

    # Note: The constructor (in pydantic-ai package) does not pass any model args
    # to the inferred model. This might change in the future.
    return Agent(model_name, **kwargs)
