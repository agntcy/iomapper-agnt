# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import TypedDict

import pytest
from langgraph.graph import END, START, StateGraph

from agntcy_iomapper.base import (
    AgentIOMapperInput,
)
from agntcy_iomapper.langgraph import (
    create_langraph_iomapper,
)
from tests.agentio_data import (
    AGENTIO_TEST_PARAMETERS,
    AGENTIO_TEST_PARAMETERS_TRANSLATIONS,
)


class StateTranslation(TypedDict):
    input: AgentIOMapperInput
    translation: str


@pytest.mark.parametrize(
    "input, expected_output",
    AGENTIO_TEST_PARAMETERS_TRANSLATIONS,
)
@pytest.mark.llm
async def test_agentio_mapping_async(llm_iomapper_config, input, expected_output):
    llmIOMapper = create_langraph_iomapper(llm_iomapper_config)

    workflow = StateGraph(StateTranslation)
    workflow.add_node("mapper", llmIOMapper)
    workflow.add_edge(START, "mapper")
    workflow.add_edge("mapper", END)
    graph = workflow.compile()

    output_state = await graph.ainvoke(StateTranslation(input=input))
    output = output_state["translation"]
    assert output is not None


class StateMeasures(TypedDict):
    input: AgentIOMapperInput
    length: str
    width: str
    height: str


@pytest.mark.parametrize(
    "input, expected_output",
    AGENTIO_TEST_PARAMETERS,
)
@pytest.mark.llm
def test_agentio_mapping(llm_iomapper_config, input, expected_output):
    llmIOMapper = create_langraph_iomapper(llm_iomapper_config)

    workflow = StateGraph(StateMeasures)
    workflow.add_node("mapper", llmIOMapper)
    workflow.add_edge(START, "mapper")
    workflow.add_edge("mapper", END)
    graph = workflow.compile()

    output_state = graph.invoke({"input": input})
    expects = expected_output.model_dump(exclude_unset=True, exclude_none=True)
    assert expects["data"]["length"] == output_state["length"]
    assert expects["data"]["width"] == output_state["width"]
    assert expects["data"]["height"] == output_state["height"]
