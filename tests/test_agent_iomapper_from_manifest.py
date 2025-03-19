# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0"
import json
from pathlib import Path
from typing import List, TypedDict

import pytest
from langgraph.graph import END, START, StateGraph

from agntcy_iomapper.agent.models import (
    AgentIOMapperInput,
    AgentIOMapperOutput,
)
from agntcy_iomapper.base import (
    ArgumentsDescription,
)
from agntcy_iomapper.langgraph import create_langraph_iomapper


class Email(TypedDict):
    direction: str
    subject: str
    content: str


class Agent1Model(TypedDict):
    instructions: str
    emailchain: List[Email]
    context: str


class Agent2Model(TypedDict):
    email: str
    audience: str


class State(TypedDict):
    input: Agent1Model
    email: str
    audience: str


HERE = Path(__file__).parent
mailwriter_manifest = json.load(
    open(HERE / "./data/manifests/agent_mailwriter.json", "rb")
)
mailreviewer_manifest = json.load(
    open(HERE / "./data/manifests/agent_mailreviewer.json")
)

input_data = {
    "instructions": "The recipient is a candidate for a job. Please tell the candidate that we selected them to have an online interview. Ask if the candidate is interested and say that details about the schedule will be communicated in further emails.",
    "emailchain": [
        {
            "direction": "sent",
            "subject": "Job application",
            "content": "Dear candidate, we are pleased to inform you that we selected you to have an online interview. Are you interested? Details about the schedule will be communicated in further emails.",
        },
    ],
    "context": "An experienced software developer",
}

input_data_multiple_exchange = {
    "instructions": "The recipient is a candidate for a job. Please tell the candidate that we selected them to have an online interview. Ask if the candidate is interested and say that details about the schedule will be communicated in further emails.",
    "emailchain": [
        {
            "direction": "sent",
            "subject": "Initial Approach",
            "content": "Dear Jonh, we've found your profile online and think that the follwoing position we're recruting for might be of your interest 'Job details'",
        },
        {
            "direction": "received",
            "subject": "RE:Initial",
            "content": "Dear candidate, we are pleased to inform you that we selected you to have an online interview. Are you interested? Details about the schedule will be communicated in further emails.",
        },
        {
            "direction": "sent",
            "subject": "Interview Schedule",
            "content": "We're very pleased that you are willing to move forward with your applicaiton, and this emails serves as an invitation for the next step which is a online assessment.",
        },
    ],
    "context": "An experienced software developer",
}
expected_output = {
    "email": "Dear candidate, we are pleased to inform you that we selected you to have an online interview. Are you interested? Details about the schedule will be communicated in further emails.",
    "audience": "general",
}

expected_output_chain = {
    "email": "Dear candidate, we are pleased to inform you that we selected you to have an online interview. Are you interested? Details about the schedule will be communicated in further emails.",
    "audience": "general",
}


@pytest.mark.parametrize(
    "source_agent_manifest, target_agent_manifest, input_data, expected_output",
    [
        (mailwriter_manifest, mailreviewer_manifest, input_data, expected_output),
        (
            mailwriter_manifest,
            mailreviewer_manifest,
            input_data_multiple_exchange,
            expected_output_chain,
        ),
    ],
)
@pytest.mark.llm
async def test_mapping_from_manifest(
    llm_iomapper_config,
    source_agent_manifest,
    target_agent_manifest,
    input_data,
    expected_output,
):
    # Convert the schemas to pydantic objects representing input and output respectively
    # Invoke
    llmIOMapper = create_langraph_iomapper(llm_iomapper_config)

    workflow = StateGraph(State)

    workflow.add_node("mapper", llmIOMapper)
    workflow.add_edge(START, "mapper")
    workflow.add_edge("mapper", END)
    graph = workflow.compile()

    input = AgentIOMapperInput(
        input=ArgumentsDescription(
            description="Agent that does write emails",
            agent_manifest=source_agent_manifest,
        ),
        output=ArgumentsDescription(
            description="Agent that reviews emails",
            agent_manifest=target_agent_manifest,
        ),
        data=input_data,
    )

    expected_mapp = AgentIOMapperOutput(data=expected_output)

    output_state = await graph.ainvoke({"input": input})
    expects = expected_mapp.model_dump(exclude_unset=True, exclude_none=True)
    assert output_state["email"] == expects["data"]["email"]
    assert output_state["audience"] == expects["data"]["audience"]
