# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
from openapi_pydantic import DataType, Schema

from agntcy_iomapper.base import (
    AgentIOMapperInput,
    AgentIOMapperOutput,
    ArgumentsDescription,
)

AGENTIO_TEST_PARAMETERS = [
    (
        AgentIOMapperInput(
            input=ArgumentsDescription(description="Text in English."),
            output=ArgumentsDescription(description="Text in French."),
            data="Would you please tell me where I can buy some snails?",
        ),
        AgentIOMapperOutput(
            data="Pourriez-vous s'il vous plaît me dire où je peux acheter des escargots?",
        ),
    ),
    (
        AgentIOMapperInput(
            input=ArgumentsDescription(description=""),
            output=ArgumentsDescription(description=""),
            data="Would you please tell me where I can buy some snails?",
            message_template="Translate from English to French the following data: {{ data }}",
        ),
        AgentIOMapperOutput(
            data="Pourriez-vous s'il vous plaît me dire où je peux acheter des escargots?",
        ),
    ),
    (
        AgentIOMapperInput(
            input=ArgumentsDescription(
                json_schema=Schema(
                    properties={
                        "description": Schema(
                            type=DataType.STRING,
                            description="A description of the object.",
                            example="It is a right triangle with a hypotenuse of 5 cm.",
                        ),
                    },
                )
            ),
            output=ArgumentsDescription(
                json_schema=Schema(
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
                )
            ),
            data={"description": "The object is a purple cube with sides of 1 m."},
        ),
        AgentIOMapperOutput(
            data={"length": "1 m", "width": "1 m", "height": "1 m"},
        ),
    ),
    (
        AgentIOMapperInput(
            input=ArgumentsDescription(
                json_schema=Schema(
                    properties={
                        "description": Schema(
                            type=DataType.STRING,
                            description="A description of the object.",
                            example="It is a blue, right triangle with a hypotenuse of 5 cm.",
                        ),
                    },
                )
            ),
            output=ArgumentsDescription(
                json_schema=Schema(
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
                )
            ),
            data={"description": "The object is a purple cube with sides of 1.5 m."},
        ),
        AgentIOMapperOutput(
            data={"length": 1.5, "width": 1.5, "height": 1.5},
        ),
    ),
]
