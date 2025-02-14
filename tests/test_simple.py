# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
from deepdiff import diff
import pytest
from openapi_pydantic import DataType, Schema

from agntcy_iomapper import IOMapper, IOMapperInput, IOMapperOutput
from agntcy_iomapper.base import ArgumentsDescription
from utils import compare_outputs, compare_outputs_async

SIMPLE_TEST_PARAMETERS = [
    (
        IOMapperInput(
            input = ArgumentsDescription(description="Text in English."),
            output = ArgumentsDescription(description="Text in French."),
            data = "Would you please tell me where I can buy some snails?",
        ), 
        IOMapperOutput(
            data = "Pourriez-vous s'il vous plaît me dire où je peux acheter des escargots?",
        ),
    ),
    (
        IOMapperInput(
            input = ArgumentsDescription(description=""),
            output = ArgumentsDescription(description=""),
            data = "Would you please tell me where I can buy some snails?",
            message_template="Translate from English to French the following data: {{ data }}",
        ), 
        IOMapperOutput(
            data = "Pourriez-vous s'il vous plaît me dire où je peux acheter des escargots?",
        ),
    ),
    (
        IOMapperInput(
            input = ArgumentsDescription(json_schema=Schema(
                properties={
                    "description": Schema(
                        type=DataType.STRING,
                        description="A description of the object.",
                        example="It is a right triangle with a hypotenuse of 5 cm.",
                    ),
                },
            )),
            output = ArgumentsDescription(json_schema=Schema(
                properties={
                    "length": Schema(
                        type=DataType.STRING,
                        description="The length as a measure with units.",
                        example="5 cm",
                    ),
                    "width": Schema(
                        type=DataType.STRING,
                        description="The width as a measure with units.",
                        example="5 cm",
                    ),
                    "height": Schema(
                        type=DataType.STRING,
                        description="The height as a measure with units.",
                        example="5 cm",
                    ),
                },
            )),
            data = {"description": "The object is a purple cube with sides of 1 m."},
        ), 
        IOMapperOutput(
            data = {"length": "1 m", "width": "1 m", "height": "1 m"},
        ),
    ),
    (
        IOMapperInput(
            input = ArgumentsDescription(json_schema=Schema(
                properties={
                    "description": Schema(
                        type=DataType.STRING,
                        description="A description of the object.",
                        example="It is a blue, right triangle with a hypotenuse of 5 cm.",
                    ),
                },
            )),
            output = ArgumentsDescription(json_schema=Schema(
                properties={
                    "length": Schema(
                        type=DataType.NUMBER,
                        description="The length as a number without units.",
                        example="5",
                    ),
                    "width": Schema(
                        type=DataType.NUMBER,
                        description="The width as a number without units.",
                        example="5",
                    ),
                    "height": Schema(
                        type=DataType.NUMBER,
                        description="The height as a number without units.",
                        example="5",
                    ),
                },
            )),
            data = {"description": "The object is a purple cube with sides of 1.5 m."},
        ), 
        IOMapperOutput(
            data = {"length": 1.5, "width": 1.5, "height": 1.5},
        ),
    ),
]

@pytest.mark.parametrize (
    "input, expected_output", SIMPLE_TEST_PARAMETERS,
)
@pytest.mark.llm
async def test_simple_mapping_async(llm_iomapper_config, jinja_env_async, input, expected_output):
    llmIOMapper = IOMapper(llm_iomapper_config, jinja_env_async=jinja_env_async)
    output = await llmIOMapper.ainvoke(input)
    if isinstance(output.data, str):        
        equalp = await compare_outputs_async(llmIOMapper, output.data, expected_output.data)
        assert equalp
        return

    outputs = output.model_dump(exclude_unset=True, exclude_none=True)
    expects = expected_output.model_dump(exclude_unset=True, exclude_none=True)
    mapdiff = diff.DeepDiff(outputs, expects)
    assert len(mapdiff.affected_paths) == 0

@pytest.mark.parametrize (
    "input, expected_output", SIMPLE_TEST_PARAMETERS,
)
@pytest.mark.llm
def test_simple_mapping(llm_iomapper_config, jinja_env, input, expected_output):
    llmIOMapper = IOMapper(llm_iomapper_config, jinja_env=jinja_env)
    output = llmIOMapper.invoke(input)
    if isinstance(output.data, str):        
        equalp = compare_outputs(llmIOMapper, output.data, expected_output.data)
        assert equalp
        return

    outputs = output.model_dump(exclude_unset=True, exclude_none=True)
    expects = expected_output.model_dump(exclude_unset=True, exclude_none=True)
    mapdiff = diff.DeepDiff(outputs, expects)
    assert len(mapdiff.affected_paths) == 0

