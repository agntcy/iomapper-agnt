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
    model_name: SupportedModelName,
    model_args: dict[str, Any] = {},
    **kwargs,
) -> Agent:
    """
    Creates and returns an `Agent` instance for the given model.

    Args:
        model_name (SupportedModelName): The name of the model to be used.
            If the name starts with "azure:", an `AsyncAzureOpenAI` client is used.
        model_args (dict[str, Any], optional): Additional arguments for model 
            initialization. Defaults to an empty dictionary.
        **kwargs: Additional keyword arguments passed to the `Agent` constructor.

    Returns:
        Agent: An instance of the `Agent` class configured with the specified model.

    Notes:
        - The `pydantic-ai` package does not currently pass `model_args` to the 
          inferred model in the constructor, but this behavior might change in 
          the future.
    """
    if model_name.startswith("azure:"):
        client = AsyncAzureOpenAI(**model_args)
        model = OpenAIModel(model_name[6:], openai_client=client)
        return Agent(model, **kwargs)

    return Agent(model_name, **kwargs)
