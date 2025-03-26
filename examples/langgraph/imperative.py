# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
import logging
from datetime import datetime
from typing import Optional

from langchain_core.language_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from agntcy_iomapper import IOMappingAgent, IOMappingAgentMetadata

logger = logging.getLogger(__name__)


class InputQuiz(BaseModel):
    prof_question: str
    due_date: str


class OverallState(BaseModel):
    question: Optional[str] = Field(None)
    quiz: Optional[InputQuiz] = Field(None)
    student_answer: Optional[str] = Field(None)


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

    def ask_question(self, state: OverallState) -> OverallState:
        response = self.model.invoke([HumanMessage(content="Generate a question")])
        return {"question": str(response.content)}


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

    def answer(self, state: OverallState) -> str:
        response = self.model.invoke(
            [HumanMessage(content=state.quiz["prof_question"])]
        )
        return {"student_answer": str(response.content)}


class MultiAgentApp:
    @staticmethod
    def run_app():
        agent_prof = ProfessorAgent()
        agent_student = StudentAgent()

        mapping_object = {
            "quiz.prof_question": "$.question",
            "quiz.due_date": lambda _: datetime.now().strftime("%x"),
        }

        metadata = IOMappingAgentMetadata(
            field_mapping=mapping_object,
            input_fields=["question"],
            output_fields=["quiz"],
        )

        iomap = IOMappingAgent(metadata=metadata)

        graph = StateGraph(OverallState)
        graph.add_node("student_node", agent_student.answer)
        graph.add_node("professor_node", agent_prof.ask_question)
        graph.add_node("mapping_node", iomap.langgraph_imperative)

        graph.add_edge("professor_node", "mapping_node")
        graph.add_edge("mapping_node", "student_node")
        graph.add_edge("student_node", END)

        graph.set_entry_point("professor_node")

        app = graph.compile()

        result = app.invoke({"question": ""})
        print(result)


def run():
    MultiAgentApp.run_app()


if __name__ == "__main__":
    run()
