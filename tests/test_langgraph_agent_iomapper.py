# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import pytest
from deepdiff import diff
from langgraph.graph import END, START, StateGraph

from agntcy_iomapper.langgraph import (
    create_langraph_iomapper,
)
from tests.agentio_data import AGENTIO_TEST_PARAMETERS
from tests.util import State, compare_outputs, compare_outputs_async


@pytest.mark.parametrize(
    "input, expected_output",
    AGENTIO_TEST_PARAMETERS,
)
@pytest.mark.llm
async def test_agentio_mapping_async(llm_iomapper_config, input, expected_output):
    llmIOMapper = create_langraph_iomapper(llm_iomapper_config)

    workflow = StateGraph(State)
    workflow.add_node("mapper", llmIOMapper)
    workflow.add_edge(START, "mapper")
    workflow.add_edge("mapper", END)
    graph = workflow.compile()

    output_state = await graph.ainvoke(State(input=input))
    print(f"output_state: {output_state}")
    output = output_state["output"]

    if isinstance(output.data, str):
        equalp = await compare_outputs_async(
            llm_iomapper_config.llm, output.data, expected_output.data
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
def test_agentio_mapping(llm_iomapper_config, input, expected_output):
    llmIOMapper = create_langraph_iomapper(llm_iomapper_config)

    workflow = StateGraph(State)
    workflow.add_node("mapper", llmIOMapper)
    workflow.add_edge(START, "mapper")
    workflow.add_edge("mapper", END)
    graph = workflow.compile()

    output_state = graph.invoke(State(input=input))
    print(f"output_state: {output_state}")
    output = output_state["output"]

    if isinstance(output.data, str):
        equalp = compare_outputs(
            llm_iomapper_config.llm, output.data, expected_output.data
        )
        assert equalp
        return

    outputs = output.model_dump(exclude_unset=True, exclude_none=True)
    expects = expected_output.model_dump(exclude_unset=True, exclude_none=True)
    mapdiff = diff.DeepDiff(outputs, expects)
    assert len(mapdiff.affected_paths) == 0
