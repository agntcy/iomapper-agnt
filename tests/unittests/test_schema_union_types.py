# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from agntcy_iomapper.base.models import FieldMetadata
from agntcy_iomapper.base.utils import create_type_from_schema


class Type(Enum):
    human = "human"
    assistant = "assistant"
    ai = "ai"


class Message(BaseModel):
    type: Type = Field(
        ...,
        description="indicates the originator of the message, a human or an assistant",
    )
    content: str = Field(..., description="the content of the message")


class InputSchema(BaseModel):
    query: str = Field(..., description="just a query")


class OverallState(BaseModel):
    messages: List[Message] = Field([], description="Chat messages")
    state_query: Optional[InputSchema] = Field(None, description="email query")


data = OverallState(messages=[{"type": "human", "content": "question"}])


def test_when_union_fields_proper_types_are_returned():
    json_schema = data.model_json_schema()
    new_description = "A list of chat messages"
    filtered_schema = create_type_from_schema(
        json_schema,
        [FieldMetadata(json_path="messages", description=new_description)],
    )
    expected_schema = {
        "messages": {
            "default": [],
            "description": new_description,
            "items": {
                "properties": {
                    "type": {
                        "enum": ["human", "assistant", "ai"],
                        "title": "Type",
                        "type": "string",
                    },
                    "content": {
                        "description": "the content of the message",
                        "title": "Content",
                        "type": "string",
                    },
                },
                "required": ["type", "content"],
                "title": "Message",
                "type": "object",
            },
            "title": "Messages",
            "type": "array",
        }
    }
    print(filtered_schema)
    assert filtered_schema == expected_schema


def test_when_union_fields_all_proper_types_are_returned():
    json_schema = data.model_json_schema()
    new_description = "a valid query with valid content"
    filtered_schema = create_type_from_schema(
        json_schema,
        [
            FieldMetadata(json_path="state_query.query", description=new_description),
            "messages",
        ],
    )
    expected_schema = {
        "state_query": {
            "anyOf": [
                {
                    "properties": {
                        "query": {
                            "description": new_description,
                            "title": "Query",
                            "type": "string",
                        }
                    },
                    "required": ["query"],
                    "title": "InputSchema",
                    "type": "object",
                },
                {"type": "null"},
            ],
            "default": None,
            "description": "email query",
        },
        "messages": {
            "default": [],
            "description": "Chat messages",
            "items": {
                "properties": {
                    "type": {
                        "enum": ["human", "assistant", "ai"],
                        "title": "Type",
                        "type": "string",
                    },
                    "content": {
                        "description": "the content of the message",
                        "title": "Content",
                        "type": "string",
                    },
                },
                "required": ["type", "content"],
                "title": "Message",
                "type": "object",
            },
            "title": "Messages",
            "type": "array",
        },
    }
    assert filtered_schema == expected_schema


def test_when_union_fields_description_is_set_at_correct_level():
    json_schema = data.model_json_schema()
    new_description = (
        "an object with a field called query that represents a query for an api"
    )
    filtered_schema = create_type_from_schema(
        json_schema,
        [
            FieldMetadata(json_path="state_query", description=new_description),
            "messages",
        ],
    )
    expected_schema = {
        "state_query": {
            "anyOf": [
                {
                    "properties": {
                        "query": {
                            "description": "just a query",
                            "title": "Query",
                            "type": "string",
                        }
                    },
                    "required": ["query"],
                    "title": "InputSchema",
                    "type": "object",
                },
                {"type": "null"},
            ],
            "default": None,
            "description": new_description,
        },
        "messages": {
            "default": [],
            "description": "Chat messages",
            "items": {
                "properties": {
                    "type": {
                        "enum": ["human", "assistant", "ai"],
                        "title": "Type",
                        "type": "string",
                    },
                    "content": {
                        "description": "the content of the message",
                        "title": "Content",
                        "type": "string",
                    },
                },
                "required": ["type", "content"],
                "title": "Message",
                "type": "object",
            },
            "title": "Messages",
            "type": "array",
        },
    }
    assert filtered_schema == expected_schema
