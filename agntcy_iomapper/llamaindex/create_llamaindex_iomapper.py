# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0"
from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from openapi_pydantic import Schema
from pydantic import BaseModel

from agntcy_iomapper.base import AgentIOMapperInput, ArgumentsDescription
from agntcy_iomapper.base.utils import _extract_nested_fields, create_type_from_schema
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

        input_type = None
        output_type = None

        if isinstance(data, BaseModel):
            input_data_schema = data.model_json_schema()
            output_type = Schema.validate_model(
                create_type_from_schema(input_data_schema, output_fields)
            )
            input_type = Schema.validate_model(
                create_type_from_schema(input_data_schema, input_fields)
            )
        else:
            # Read the optional fields
            input_schema = evt.get("input_schema", None)
            output_schema = evt.get("output_schema", None)
            if not input_schema or not output_schema:
                raise ValueError(
                    "input_schema, and or output_schema are missing from the metadata, for a better accuracy you are required to provide them in this scenario"
                )
            output_type = Schema.model_validate(output_schema)
            input_type = Schema.model_validate(input_schema)

        data_to_be_mapped = _extract_nested_fields(data, fields=input_fields)

        input = AgentIOMapperInput(
            input=ArgumentsDescription(
                json_schema=input_type,
            ),
            output=ArgumentsDescription(
                json_schema=output_type,
            ),
            data=data_to_be_mapped,
        )

        llm = await ctx.get("llm", None)
        if not llm:
            return StopEvent(result="You missed to config the llm")

        config = LLamaIndexIOMapperConfig(llm=llm)
        io_mapping = LLamaIndexIOMapper(config=config, input=input)
        mapping_res = await io_mapping.ainvoke()

        return StopEvent(result=mapping_res)
