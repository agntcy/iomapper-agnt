# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import pytest
from langchain_core.language_models import FakeListChatModel

from agntcy_iomapper import IOMappingAgent, IOMappingAgentMetadata

predifined_responses = ["Test message", "lorem"]

llm = FakeListChatModel(responses=predifined_responses)

metadata = IOMappingAgentMetadata(input_fields=[], output_fields=[])
metadata1 = IOMappingAgentMetadata(input_fields=[""], output_fields=[])
metadata2 = IOMappingAgentMetadata(input_fields=[" "], output_fields=["", "as"])


@pytest.mark.parametrize("metadata", [metadata, metadata1, metadata2])
def test_when_invalid_io_fields_than_value_error_is_raised(metadata):
    with pytest.raises(ValueError):
        IOMappingAgent(metadata=metadata, llm=llm)


def test_when_no_llm_instance_than_value_error_is_raised():
    with pytest.raises(ValueError):
        IOMappingAgent(metadata=metadata)


def test_when_no_io_schema_than_value_error_is_raised():
    _metadata = IOMappingAgentMetadata(input_fields=["f1"], output_fields=["f2"])
    agent = IOMappingAgent(metadata=_metadata, llm=llm)
    with pytest.raises(ValueError):
        agent.langgraph_node({})
