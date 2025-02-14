# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
from agntcy_iomapper import IOMapper
from agntcy_iomapper.supported_agents import get_supported_agent
import re

__COMPARE_SYSTEM_PROMPT="""You are comparing two texts for similarity. 
First, write out in a step by step manner your reasoning to be sure that your conclusion is correct. Avoid simply stating the correct answer at the outset. Then print only a single choice from [true, false] (without quotes or punctuation) on its own line corresponding to the correct answer. At the end, repeat just the answer by itself on a new line.
"""
__COMPARE_USER_PROMPT="""Here is the data:
[BEGIN DATA]
************
[First text]: {text1}
************
[Second text]: {text2}
************
[END DATA]

Compare the factual content of the texts. Ignore any differences in style, grammar, or punctuation.
Answer the question by selecting one of the following options:
(true) The first text is largely the same as the second and fully consistent with it.
(false) There is a disagreement between the first text and the second.

Reasoning
"""

async def compare_outputs_async(iomapper: IOMapper, text1: str, text2: str) -> bool:
    model_name = iomapper.config.default_model
    agent = get_supported_agent(
        True, 
        model_name, 
        system_prompt=__COMPARE_SYSTEM_PROMPT, 
        model_args=iomapper.config.models[model_name],
    )
    user_prompt = __COMPARE_USER_PROMPT.format(**locals())
    response = await agent.run(user_prompt=user_prompt, model_settings=iomapper.config.default_model_settings[model_name])
    matches = re.search("(true|false)\\s*$", response.data, re.IGNORECASE)
    match = matches.group(1)
    return match is not None and match.startswith("t")

def compare_outputs(iomapper: IOMapper, text1: str, text2: str) -> bool:
    model_name = iomapper.config.default_model
    agent = get_supported_agent(
        False, 
        model_name, 
        system_prompt=__COMPARE_SYSTEM_PROMPT, 
        model_args=iomapper.config.models[model_name],
    )
    user_prompt = __COMPARE_USER_PROMPT.format(**locals())
    response = agent.run_sync(user_prompt=user_prompt, model_settings=iomapper.config.default_model_settings[model_name])
    matches = re.search("(true|false)\\s*$", response.data, re.IGNORECASE)
    match = matches.group(1)
    return match is not None and match.startswith("t")
