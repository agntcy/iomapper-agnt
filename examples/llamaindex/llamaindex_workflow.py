# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
from typing import List, Optional

from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from pydantic import BaseModel, Field

from agntcy_iomapper import IOMappingAgent, IOMappingAgentMetadata
from agntcy_iomapper.llamaindex import (
    IOMappingInputEvent,
    IOMappingOutputEvent,
    LLamaIndexIOMapperConfig,
)
from examples.llm import Framework, get_azure
from examples.models import Campaign, Statistics, User
from examples.models.data import users


class PickUsersEvent(Event):
    prompt: str


class CreateCampaignEvent(Event):
    list_users: List[User]


class CampaignCreatedEvent(Event):
    campaign: Campaign


class OverallState(BaseModel):
    campaign_details: Campaign
    stats: Optional[Statistics] = Field(None)
    selected_users: List[User]


class CampaignWorkflow(Workflow):
    @step
    async def prompt_step(self, ctx: Context, ev: StartEvent) -> PickUsersEvent:
        await ctx.set("llm", ev.get("llm"))
        return PickUsersEvent(prompt=ev.get("prompt"))

    @step
    async def pick_users_step(
        self, ctx: Context, ev: PickUsersEvent
    ) -> CreateCampaignEvent:
        return CreateCampaignEvent(list_users=users)

    @step
    async def create_campaign(
        self, ctx: Context, ev: CreateCampaignEvent
    ) -> IOMappingInputEvent:
        prompt = f"""
        You are a campaign builder for company XYZ. Given a list of selected users and a user prompt, create an engaging campaign. 
        Return the campaign details as a JSON object with the following structure:
        {{
            "name": "Campaign Name",
            "content": "Campaign Content",
            "is_urgent": yes/no
        }}
        Selected Users: {ev.list_users}
        User Prompt: Create a campaign for all users
        """
        parser = PydanticOutputParser(output_cls=Campaign)
        llm = await ctx.get("llm", default=None)

        llm_response = llm.complete(prompt)
        try:
            campaign_details = parser.parse(str(llm_response))
            metadata = IOMappingAgentMetadata(
                input_fields=["selected_users", "campaign_details.name"],
                output_fields=["stats"],
            )
            config = LLamaIndexIOMapperConfig(llm=llm)

            io_mapping_input_event = IOMappingInputEvent(
                metadata=metadata,
                config=config,
                data=OverallState(
                    campaign_details=campaign_details,
                    selected_users=ev.list_users,
                ),
            )
            return io_mapping_input_event
        except Exception as e:
            print(f"Error parsing campaign details: {e}")
            return StopEvent(result=f"{e}")

    @step
    async def after_translation(self, evt: IOMappingOutputEvent) -> StopEvent:
        return StopEvent(result="Done")


async def main():
    llm = get_azure(framework=Framework.LLAMA_INDEX)
    w = CampaignWorkflow()

    IOMappingAgent.as_worfklow_step(workflow=w)
    result = await w.run(prompt="Create a campaign for all users", llm=llm)

    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
