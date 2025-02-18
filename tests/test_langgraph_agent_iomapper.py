# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
from deepdiff import diff
import pytest
import re
from typing import TypedDict
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, START, END
from langchain_openai.chat_models.azure import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from agntcy_iomapper.langgraph import LangGraphIOMapperConfig, create_iomapper, LangGraphIOMapperInput, LangGraphIOMapperOutput

from tests.agentio_data import AGENTIO_TEST_PARAMETERS

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

class State(TypedDict):
    input: LangGraphIOMapperInput
    output: LangGraphIOMapperOutput

@pytest.mark.parametrize (
    "input, expected_output", AGENTIO_TEST_PARAMETERS,
)
@pytest.mark.llm
async def test_agentio_mapping_async(llm_iomapper_config, input, expected_output):
    llmIOMapper = create_iomapper(llm_iomapper_config)

    workflow = StateGraph(State)
    workflow.add_node("mapper", llmIOMapper)
    workflow.add_edge(START, "mapper")
    workflow.add_edge("mapper", END)
    graph = workflow.compile()

    output_state = await graph.ainvoke(State(input=input))
    print(f"output_state: {output_state}")
    output = output_state["output"]

    if isinstance(output.data, str):        
        equalp = await compare_outputs_async(llm_iomapper_config.llm, output.data, expected_output.data)
        assert equalp
        return

    outputs = output.model_dump(exclude_unset=True, exclude_none=True)
    expects = expected_output.model_dump(exclude_unset=True, exclude_none=True)
    mapdiff = diff.DeepDiff(outputs, expects)
    assert len(mapdiff.affected_paths) == 0

@pytest.mark.parametrize (
    "input, expected_output", AGENTIO_TEST_PARAMETERS,
)
@pytest.mark.llm
def test_agentio_mapping(llm_iomapper_config, input, expected_output):
    llmIOMapper = create_iomapper(llm_iomapper_config)

    workflow = StateGraph(State)
    workflow.add_node("mapper", llmIOMapper)
    workflow.add_edge(START, "mapper")
    workflow.add_edge("mapper", END)
    graph = workflow.compile()

    output_state = graph.invoke(State(input=input))
    print(f"output_state: {output_state}")
    output = output_state["output"]

    if isinstance(output.data, str):        
        equalp = compare_outputs(llm_iomapper_config.llm, output.data, expected_output.data)
        assert equalp
        return

    outputs = output.model_dump(exclude_unset=True, exclude_none=True)
    expects = expected_output.model_dump(exclude_unset=True, exclude_none=True)
    mapdiff = diff.DeepDiff(outputs, expects)
    assert len(mapdiff.affected_paths) == 0


__COMPARE_SYSTEM_PROMPT="""You are comparing two texts for similarity. 
First, write out in a step by step manner your reasoning to be sure that your conclusion is correct. Avoid simply stating the correct answer at the outset. Then print only a single choice from [true, false] (without quotes or punctuation) on its own line corresponding to the correct answer. At the end, repeat just the answer by itself on a new line.
"""
__COMPARE_USER_PROMPT="""Here is the data:
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

async def compare_outputs_async(llm: BaseChatModel, text1: str, text2: str) -> bool:
    user_prompt = __COMPARE_USER_PROMPT.format(**locals())
    response = await llm.ainvoke([
        SystemMessage(content=__COMPARE_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])
    matches = re.search("(true|false)\\s*$", response.content, re.IGNORECASE)
    match = matches.group(1)
    return match is not None and match.startswith("t")

def compare_outputs(llm: BaseChatModel, text1: str, text2: str) -> bool:
    user_prompt = __COMPARE_USER_PROMPT.format(**locals())
    response = llm.invoke([
        SystemMessage(content=__COMPARE_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])
    matches = re.search("(true|false)\\s*$", response.content, re.IGNORECASE)
    match = matches.group(1)
    return match is not None and match.startswith("t")
