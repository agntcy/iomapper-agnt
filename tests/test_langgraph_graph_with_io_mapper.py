# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
from typing import List, Optional

import pytest
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from agntcy_iomapper import FieldMetadata, IOMappingAgent, IOMappingAgentMetadata
from examples.models import Campaign, Communication, Statistics, User
from examples.models.data import users


class OverallState(BaseModel):
    user_prompt: Optional[str] = Field(None, description="The user's input prompt.")
    selected_users: List[User] = Field([], description="A list of selected users.")
    campaign_details: Optional[Campaign] = Field(
        None, description="Details of the created campaign."
    )
    stats: Optional[Statistics] = Field(
        None, description="Statistics for the running campaign"
    )


@pytest.mark.llm
def test_langgraph_agent_in_a_graph_application(llm_instance):
    graph = StateGraph(OverallState)
    graph.add_node("select_users", select_user_node)
    graph.add_node("create_campaign", define_campaign_node)
    graph.add_node("create_communication", create_communication)

    metadata = IOMappingAgentMetadata(
        input_fields=["selected_users", "campaign_details.name"],
        output_fields=[
            FieldMetadata(
                json_path="stats.status",
                description="the status value must contain value yes or no, if selected_users is not empty, than it should have yes otherwise no",
            )
        ],
    )

    mapping_agent = IOMappingAgent(metadata=metadata, llm=llm_instance)

    graph.add_node("io_mapping", mapping_agent.langgraph_node)
    graph.add_edge("select_users", "create_campaign")
    graph.add_edge("create_campaign", "create_communication")
    graph.add_edge("create_communication", "io_mapping")
    graph.set_entry_point("select_users")
    graph.add_edge("io_mapping", END)

    app = graph.compile()

    inputs = {"user_prompt": "Create a campaign for all users"}

    result = app.invoke(inputs)
    assert result["stats"]["status"] == "yes"


def select_user_node(state: OverallState):
    """From a prompt select users that applies to the search criteria"""
    return {"selected_users": users}


def define_campaign_node(state: OverallState):
    campaign = Campaign(name="Confidence", content="Confidence level", is_urgent="Yes")
    return {"campaign_details": campaign}


def create_communication(state: OverallState):
    communication = Communication(
        subject="Email Subject",
        body="Email Body",
        recipients=["recipient1@example.com", "recipient2@example.com"],
    )

    return communication
