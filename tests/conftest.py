# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
import pytest

from dotenv import load_dotenv, find_dotenv
from jinja2.sandbox import SandboxedEnvironment
from agntcy_iomapper import IOMapperConfig, IOModelSettings, IOModelArgs

load_dotenv(dotenv_path=find_dotenv(usecwd=True))

@pytest.fixture
def jinjaEnv() -> SandboxedEnvironment:
    return SandboxedEnvironment(
        loader=None,
        enable_async=False,
        autoescape=False,
    )

@pytest.fixture
def jinjaEnvAsync() -> SandboxedEnvironment:
    return SandboxedEnvironment(
        loader=None,
        enable_async=True,
        autoescape=False,
    )

@pytest.fixture
def noLlmIOMapperConfig() -> IOMapperConfig:
    return IOMapperConfig(
        models = {},
        validate_json_input=True,
        validate_json_output=True,
    )

@pytest.fixture
def llmIOMapperConfig() -> IOMapperConfig:
    return IOMapperConfig(
        models={
            "azure:gpt-4o-mini": IOModelArgs(
                api_version="2024-07-01-preview",
                azure_endpoint="https://smith-project-agents.openai.azure.com",
            ),
        },
        default_model_settings={
            "azure:gpt-4o-mini": IOModelSettings(
                seed=42, 
                temperature=0,
            ),
        },
        validate_json_input=True,
        validate_json_output=True,
    )
