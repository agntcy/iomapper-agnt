# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0"

from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

from agntcy_iomapper.base.utils import (
    instantiate_input,
)
from agntcy_iomapper.llamaindex.llamaindex import (
    LLamaIndexIOMapper,
    LLamaIndexIOMapperConfig,
)


class IOMappingWorkflow(Workflow):
    @step
    async def llamaindex_iomapper(self, evt: StartEvent) -> StopEvent:
        """Generate a step to be included in a llamaindex workflow
        ARGS:
        workflow: The workflow where the step will be included at
        Rerturns
        a step to be included in the workflow
        """
        ctx = evt.get("context", None)

        if not ctx:
            return ValueError(
                "A context must be present with the configuration of the llm"
            )
        data = evt.get("data", None)
        if not data:
            return ValueError("data is required. Invalid or no data was passed")

        input_fields = evt.get("input_fields")
        if not input_fields:
            return ValueError("input_fields not set")

        output_fields = evt.get("output_fields")
        if not output_fields:
            return ValueError("output_fields not set")

        input = instantiate_input(
            data=data,
            input_fields=input_fields,
            output_fields=output_fields,
            input_schema=evt.get("input_schema", None),
            output_schema=evt.get("output_schema", None),
        )

        llm = await ctx.get("llm", None)
        if not llm:
            return StopEvent(result="You missed to config the llm")

        config = LLamaIndexIOMapperConfig(llm=llm)
        io_mapping = LLamaIndexIOMapper(config=config, input=input)
        mapping_res = await io_mapping.ainvoke()

        return StopEvent(result=mapping_res)
