# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
import json
import logging
from datetime import datetime

from langchain_core.language_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from openapi_pydantic import Schema
from pydantic import BaseModel

from agntcy_iomapper import ImperativeIOMapper
from agntcy_iomapper.base import ArgumentsDescription, IOMapperInput

logger = logging.getLogger(__name__)


class ProfessorAgent:
    """
    This agent mission is to test it's students knowledges
    """

    predefined_questions = [
        "What is the capital of France?",
        "Who wrote 'To Kill a Mockingbird'?",
        "What is the largest planet in our solar system?",
        "What is the chemical symbol for gold?",
        "Who painted the Mona Lisa?",
    ]

    def __init__(self) -> None:
        self.model = FakeListChatModel(responses=self.predefined_questions)

    def ask_question(self) -> str:
        response = self.model.invoke([HumanMessage(content="Generate a question")])
        return str(response.content)


class InputQuiz(BaseModel):
    prof_question: str
    due_date: str


class StudentAgent:
    """
    This agent mission is to answer questions
    """

    predefined_answers = [
        "The capital of France is Paris.",
        "Harper Lee wrote 'To Kill a Mockingbird'.",
        "The largest planet in our solar system is Jupiter.",
        "The chemical symbol for gold is Au.",
        "Leonardo da Vinci painted the Mona Lisa.",
    ]

    def __init__(self) -> None:
        self.model = FakeListChatModel(responses=self.predefined_answers)

    def answer(self, quiz) -> str:
        response = self.model.invoke([HumanMessage(content=quiz.prof_question)])
        return str(response.content)


class MultiAgentApp:
    @staticmethod
    def run_app():
        agent_prof = ProfessorAgent()
        agent_student = StudentAgent()

        output_prof = agent_prof.ask_question()

        prof_agent_output_schema = {"question": {"type": "string"}}
        student_agent_schema = {
            "quiz": {
                "type": "object",
                "properties": {
                    "prof_question": {"type": "string"},
                    "due_date": {"type": "string"},
                },
            }
        }

        mapping_object = {
            "prof_question": "$.question",
            "due_date": lambda _: datetime.now().strftime("%x"),
        }

        input = IOMapperInput(
            input=ArgumentsDescription(
                json_schema=Schema.model_validate(prof_agent_output_schema)
            ),
            output=ArgumentsDescription(
                json_schema=Schema.model_validate(student_agent_schema)
            ),
            data={"question": output_prof},
        )

        imerative_mapp = ImperativeIOMapper(
            field_mapping=mapping_object,
        )

        print(f"professors question was {output_prof}")

        mapping_result = imerative_mapp.invoke(input=input)

        print(f"the mapping_result was {mapping_result}")

        response = agent_student.answer(InputQuiz(**(json.loads(mapping_result.data))))

        print(f"student response was {response}")
        # map data between agents


def run():
    MultiAgentApp.run_app()


if __name__ == "__main__":
    run()
