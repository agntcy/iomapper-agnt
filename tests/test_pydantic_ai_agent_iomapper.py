# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
import re

import pytest
from deepdiff import diff
from jinja2.sandbox import SandboxedEnvironment

from agntcy_iomapper import AgentIOMapper
from agntcy_iomapper.pydantic_ai import (
    AgentIOModelArgs,
    AgentModelSettings,
    PydanticAIAgentIOMapperConfig,
    PydanticAIIOAgentIOMapper,
    get_supported_agent,
)
from tests.agentio_data import AGENTIO_TEST_PARAMETERS


@pytest.fixture
def jinja_env() -> SandboxedEnvironment:
    return SandboxedEnvironment(
        loader=None,
        enable_async=False,
        autoescape=False,
    )


@pytest.fixture
def jinja_env_async() -> SandboxedEnvironment:
    return SandboxedEnvironment(
        loader=None,
        enable_async=True,
        autoescape=False,
    )


@pytest.fixture
def llm_iomapper_config() -> PydanticAIAgentIOMapperConfig:
    return PydanticAIAgentIOMapperConfig(
        models={
            "azure:gpt-4o-mini": AgentIOModelArgs(
                api_version="2024-07-01-preview",
                azure_endpoint="https://smith-project-agents.openai.azure.com",
            ),
        },
        default_model_settings={
            "azure:gpt-4o-mini": AgentModelSettings(
                seed=42,
                temperature=0,
            ),
        },
        validate_json_input=True,
        validate_json_output=True,
    )


@pytest.mark.parametrize(
    "input, expected_output",
    AGENTIO_TEST_PARAMETERS,
)
@pytest.mark.llm
async def test_agent_mapping_async(
    llm_iomapper_config, jinja_env_async, input, expected_output
):
    llmIOMapper = PydanticAIIOAgentIOMapper(
        llm_iomapper_config, jinja_env_async=jinja_env_async
    )
    output = await llmIOMapper.ainvoke(input)
    if isinstance(output.data, str):
        equalp = await compare_outputs_async(
            llmIOMapper, output.data, expected_output.data
        )
        assert equalp
        return

    outputs = output.model_dump(exclude_unset=True, exclude_none=True)
    expects = expected_output.model_dump(exclude_unset=True, exclude_none=True)
    mapdiff = diff.DeepDiff(outputs, expects)
    assert len(mapdiff.affected_paths) == 0


@pytest.mark.parametrize(
    "input, expected_output",
    AGENTIO_TEST_PARAMETERS,
)
@pytest.mark.llm
def test_agent_mapping(llm_iomapper_config, jinja_env, input, expected_output):
    llmIOMapper = PydanticAIIOAgentIOMapper(llm_iomapper_config, jinja_env=jinja_env)
    output = llmIOMapper.invoke(input)
    if isinstance(output.data, str):
        equalp = compare_outputs(llmIOMapper, output.data, expected_output.data)
        assert equalp
        return

    outputs = output.model_dump(exclude_unset=True, exclude_none=True)
    expects = expected_output.model_dump(exclude_unset=True, exclude_none=True)
    mapdiff = diff.DeepDiff(outputs, expects)
    assert len(mapdiff.affected_paths) == 0


__COMPARE_SYSTEM_PROMPT = """You are comparing two texts for similarity. 
First, write out in a step by step manner your reasoning to be sure that your conclusion is correct. Avoid simply stating the correct answer at the outset. Then print only a single choice from [true, false] (without quotes or punctuation) on its own line corresponding to the correct answer. At the end, repeat just the answer by itself on a new line.
"""
__COMPARE_USER_PROMPT = """Here is the data:
[BEGIN DATA]
************
[First text]: {text1}
************
[Second text]: {text2}
************
[END DATA]

Compare the factual content of the texts. Ignore any differences in style, grammar, or punctuation.
Answer the question by selecting one of the following options:
(true) The first text is largely the same as the second and fully consistent with it.
(false) There is a disagreement between the first text and the second.

Reasoning
"""


async def compare_outputs_async(
    iomapper: AgentIOMapper, text1: str, text2: str
) -> bool:
    model_name = iomapper.config.default_model
    agent = get_supported_agent(
        model_name,
        system_prompt=__COMPARE_SYSTEM_PROMPT,
        model_args=iomapper.config.models[model_name],
    )
    user_prompt = __COMPARE_USER_PROMPT.format(**locals())
    response = await agent.run(
        user_prompt=user_prompt,
        model_settings=iomapper.config.default_model_settings[model_name],
    )
    matches = re.search("(true|false)\\s*$", response.data, re.IGNORECASE)
    match = matches.group(1)
    return match is not None and match.startswith("t")


def compare_outputs(iomapper: AgentIOMapper, text1: str, text2: str) -> bool:
    model_name = iomapper.config.default_model
    agent = get_supported_agent(
        model_name,
        system_prompt=__COMPARE_SYSTEM_PROMPT,
        model_args=iomapper.config.models[model_name],
    )
    user_prompt = __COMPARE_USER_PROMPT.format(**locals())
    response = agent.run_sync(
        user_prompt=user_prompt,
        model_settings=iomapper.config.default_model_settings[model_name],
    )
    matches = re.search("(true|false)\\s*$", response.data, re.IGNORECASE)
    match = matches.group(1)
    return match is not None and match.startswith("t")
