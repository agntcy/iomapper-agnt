# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from agntcy_iomapper import FieldMetadata, IOMappingAgent, IOMappingAgentMetadata
from examples.llm import get_azure
from examples.models import Campaign, Communication, Statistics, User
from examples.models.data import users


class OverallState(BaseModel):
    user_prompt: Optional[str] = Field(None, description="The user's input prompt.")
    selected_users: List[User] = Field([], description="A list of selected users.")
    campaign_details: Optional[Campaign] = Field(
        None, description="Details of the created campaign."
    )
    stats: Optional[Statistics] = Field(
        None, description="status and information related to the campaign"
    )


def select_user_node(state: OverallState):
    """From a prompt select users that applies to the search criteria"""
    return {"selected_users": users}


def define_campaign_node(state: OverallState):
    prompt = f"""
    You are a campaign builder for company XYZ. Given a list of selected users and a user prompt, create an engaging campaign.
    Return the campaign details as a JSON object with the following structure:
    {{
        "name": "Campaign Name",
        "content": "Campaign Content",
        "is_urgent": yes/no
    }}

    Selected Users: {state.selected_users}
    User Prompt: {state.user_prompt}
    """
    parser = PydanticOutputParser(pydantic_object=Campaign)
    messages = [SystemMessage(content=prompt)]
    llm = get_azure()
    response = llm.invoke(messages)

    try:
        campaign_details = parser.parse(response.content)
        return {"campaign_details": campaign_details}
    except Exception as e:
        print(f"Error parsing campaign details: {e}")
        return {"campaign_details": None}


def create_communication(state: OverallState):
    prompt = f"""
    You are an email communication creator. Given a campaign and a list of selected users, create an email communication.
    Return the communication details as a JSON object with the following structure:
    {{
        "subject": "Email Subject",
        "body": "Email Body",
        "recipients": ["recipient1@example.com", "recipient2@example.com"]
    }}

    Campaign Details: {state.campaign_details}
    Selected Users: {state.selected_users}
    """
    parser = PydanticOutputParser(pydantic_object=Communication)
    messages = [SystemMessage(content=prompt)]
    llm = get_azure()
    response = llm.invoke(messages)

    try:
        communication = parser.parse(response.content)
        return {"communication": communication}
    except Exception as e:
        print(f"Error parsing communication details: {e}")
        return {"communication": None}


workflow = StateGraph(OverallState)
workflow.add_node("select_users", select_user_node)
workflow.add_node("create_campaign", define_campaign_node)
workflow.add_node("create_communication", create_communication)

llm = get_azure()

metadata = IOMappingAgentMetadata(
    input_fields=[
        FieldMetadata(
            json_path="selected_users", description="A list of users to be targeted"
        ),
        FieldMetadata(
            json_path="campaign_details.name",
            description="The name that can be used by the campaign",
        ),
    ],
    output_fields=["stats"],
)

mapping_agent = IOMappingAgent(metadata=metadata, llm=llm)

workflow.add_node("io_mapping", mapping_agent.langgraph_node)

workflow.add_edge("select_users", "create_campaign")
workflow.add_edge("create_campaign", "create_communication")
workflow.add_edge("create_communication", "io_mapping")
workflow.set_entry_point("select_users")
workflow.add_edge("io_mapping", END)

app = workflow.compile()

config = RunnableConfig(configurable={"llm": llm})
inputs = {"user_prompt": "Create a campaign for all users"}

result = app.invoke(inputs, config)

print(result)
