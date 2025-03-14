from typing import List, Optional

from pydantic import BaseModel, Field

from agntcy_iomapper.base.utils import create_type_from_schema


class Message(BaseModel):
    messages: List[str] = Field(
        ..., description="a list of string representing the chain of messages"
    )


class IOClass(BaseModel):
    input: Optional[Message] = None
    output: Optional[Message] = None


class NestedOptional(BaseModel):
    io_messages: Optional[IOClass] = None
    status: bool = Field(
        ..., description="the status of the message true means have message to process"
    )


fake_input_messages = ["This is the message 1", "This is the message 2"]
input_messages = Message(messages=fake_input_messages)

io_instance = IOClass(input=input_messages)

data = NestedOptional(io_messages=io_instance, status=False)


def test_complex_object_mapping():
    json_schema = data.model_json_schema()

    filtered_schema = create_type_from_schema(
        json_schema, ["io_messages.output.messages"]
    )

    expected_schema = {
        "io_messages": {
            "anyOf": [
                {
                    "properties": {
                        "output": {
                            "anyOf": [
                                {
                                    "properties": {
                                        "messages": {
                                            "description": "a list of string representing the chain of messages",
                                            "items": {"type": "string"},
                                            "title": "Messages",
                                            "type": "array",
                                        }
                                    },
                                    "required": ["messages"],
                                    "title": "Message",
                                    "type": "object",
                                },
                                {"type": "null"},
                            ],
                            "default": None,
                        }
                    },
                    "title": "IOClass",
                    "type": "object",
                },
                {"type": "null"},
            ],
            "default": None,
        }
    }

    assert filtered_schema == expected_schema


def test_root_field():
    json_schema = data.model_json_schema()
    filtered_schema = create_type_from_schema(json_schema, ["status"])
    expected_output = {
        "status": {
            "description": "the status of the message true means have message to process",
            "title": "Status",
            "type": "boolean",
        }
    }
    assert expected_output == filtered_schema


def test_two_fields():
    json_schema = data.model_json_schema()
    filtered_schema = create_type_from_schema(json_schema, ["io_messages"])
    expected_output = {
        "io_messages": {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "input": {
                            "anyOf": [
                                {
                                    "properties": {
                                        "messages": {
                                            "description": "a list of string representing the chain of messages",
                                            "items": {"type": "string"},
                                            "title": "Messages",
                                            "type": "array",
                                        }
                                    },
                                    "required": ["messages"],
                                    "title": "Message",
                                    "type": "object",
                                },
                                {"type": "null"},
                            ],
                            "default": None,
                        },
                        "output": {
                            "anyOf": [
                                {
                                    "properties": {
                                        "messages": {
                                            "description": "a list of string representing the chain of messages",
                                            "items": {"type": "string"},
                                            "title": "Messages",
                                            "type": "array",
                                        }
                                    },
                                    "required": ["messages"],
                                    "title": "Message",
                                    "type": "object",
                                },
                                {"type": "null"},
                            ],
                            "default": None,
                        },
                    },
                    "title": "IOClass",
                },
                {"type": "null"},
            ],
            "default": None,
        }
    }
    assert expected_output == filtered_schema


def test_two_fields_v2():
    json_schema = data.model_json_schema()
    filtered_schema = create_type_from_schema(
        json_schema, ["io_messages.input", "io_messages.output"]
    )
    expected_output = {
        "io_messages": {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "input": {
                            "anyOf": [
                                {
                                    "properties": {
                                        "messages": {
                                            "description": "a list of string representing the chain of messages",
                                            "items": {"type": "string"},
                                            "title": "Messages",
                                            "type": "array",
                                        }
                                    },
                                    "required": ["messages"],
                                    "title": "Message",
                                    "type": "object",
                                },
                                {"type": "null"},
                            ],
                            "default": None,
                        },
                        "output": {
                            "anyOf": [
                                {
                                    "properties": {
                                        "messages": {
                                            "description": "a list of string representing the chain of messages",
                                            "items": {"type": "string"},
                                            "title": "Messages",
                                            "type": "array",
                                        }
                                    },
                                    "required": ["messages"],
                                    "title": "Message",
                                    "type": "object",
                                },
                                {"type": "null"},
                            ],
                            "default": None,
                        },
                    },
                    "title": "IOClass",
                },
                {"type": "null"},
            ],
            "default": None,
        }
    }

    assert expected_output == filtered_schema
