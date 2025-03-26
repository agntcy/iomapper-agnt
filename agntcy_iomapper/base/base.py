# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import ClassVar, Optional

import jsonschema
from jinja2 import Environment
from jinja2.sandbox import SandboxedEnvironment

from agntcy_iomapper.base.models import (
    AgentIOMapperInput,
    AgentIOMapperOutput,
    BaseIOMapperConfig,
)

logger = logging.getLogger(__name__)


class BaseIOMapper(ABC):
    """Abstract base class for interfacing with io mapper.
    All io mappers wrappers inherited from BaseIOMapper.
    """

    _json_search_pattern: ClassVar[re.Pattern] = re.compile(
        r"```json\n(.*?)\n```", re.DOTALL
    )

    def __init__(
        self,
        config: Optional[BaseIOMapperConfig] = None,
        jinja_env: Optional[Environment] = None,
        jinja_env_async: Optional[Environment] = None,
    ):
        if config is None:
            config = BaseIOMapperConfig()

        if jinja_env is not None and jinja_env.is_async:
            raise ValueError("Async Jinja env passed to jinja_env argument")
        elif jinja_env_async is not None and not jinja_env_async.is_async:
            raise ValueError("Sync Jinja env passed to jinja_env_async argument")

        self.jinja_env = jinja_env
        self.prompt_template = None
        self.user_template = None

        self.jinja_env_async = jinja_env_async
        self.prompt_template_async = None
        self.user_template_async = None
        self.config = config

    # Delay init until sync or async functions called.
    def _check_jinja_env(self, enable_async: bool):
        if enable_async:
            # Delay load of env until needed
            if self.jinja_env_async is None:
                # Default is sandboxed, no loader
                self.jinja_env_async = SandboxedEnvironment(
                    loader=None,
                    enable_async=True,
                    autoescape=False,
                )
            if self.prompt_template_async is None:
                self.prompt_template_async = self.jinja_env_async.from_string(
                    self.config.system_prompt_template
                )
            if self.user_template_async is None:
                self.user_template_async = self.jinja_env_async.from_string(
                    self.config.message_template
                )
        else:
            if self.jinja_env is None:
                self.jinja_env = SandboxedEnvironment(
                    loader=None,
                    enable_async=False,
                    autoescape=False,
                )
            if self.prompt_template is None:
                self.prompt_template = self.jinja_env.from_string(
                    self.config.system_prompt_template
                )
            if self.user_template is None:
                self.user_template = self.jinja_env.from_string(
                    self.config.message_template
                )

    def _get_render_env(self, input: AgentIOMapperInput) -> dict[str, str]:
        return {
            "input": input.input,
            "output": input.output,
            "data": input.data,
        }

    def _get_output(
        self, input: AgentIOMapperInput, outputs: str
    ) -> AgentIOMapperOutput:

        if input.output.json_schema is None:
            # If there is no schema, quote the chars for JSON.
            return AgentIOMapperOutput.model_validate_json(
                f'{{"data": {json.dumps(outputs)} }}'
            )

        logger.debug(f"{outputs}")

        # Check if data is returned in JSON markdown text
        matches = self._json_search_pattern.findall(outputs)
        if matches:
            outputs = matches[-1]

        return AgentIOMapperOutput.model_validate_json(f'{{"data": {outputs} }}')

    def _validate_input(self, input: AgentIOMapperInput) -> None:
        if self.config.validate_json_input and input.input.json_schema is not None:
            jsonschema.validate(
                instance=input.data,
                schema=input.input.json_schema.model_dump(
                    exclude_none=True, mode="json"
                ),
            )

    def _validate_output(
        self, input: AgentIOMapperInput, output: AgentIOMapperOutput
    ) -> None:
        if self.config.validate_json_output and input.output.json_schema is not None:
            output_schema = input.output.json_schema.model_dump(
                exclude_none=True, mode="json"
            )
            logging.debug(f"Checking output schema: {output_schema}")
            jsonschema.validate(
                instance=output.data,
                schema=output_schema,
            )

    def _invoke(self, input: AgentIOMapperInput, **kwargs) -> AgentIOMapperOutput:
        self._validate_input(input)
        self._check_jinja_env(False)
        render_env = self._get_render_env(input)
        system_prompt = self.prompt_template.render(render_env)

        if input.message_template is not None:
            logging.info(f"User template supplied on input: {input.message_template}")
            user_template = self.jinja_env.from_string(input.message_template)
        else:
            user_template = self.user_template
        user_prompt = user_template.render(render_env)

        outputs = self.invoke(
            input,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **kwargs,
        )
        logging.debug(f"The LLM returned: {outputs}")
        output = self._get_output(input, outputs)

        self._validate_output(input, output)
        return output

    async def _ainvoke(
        self, input: AgentIOMapperInput, **kwargs
    ) -> AgentIOMapperOutput:
        self._validate_input(input)
        self._check_jinja_env(True)
        render_env = self._get_render_env(input)
        system_prompt = await self.prompt_template_async.render_async(render_env)

        if input.message_template is not None:
            logging.info(f"User template supplied on input: {input.message_template}")
            user_template_async = self.jinja_env_async.from_string(
                input.message_template
            )
        else:
            user_template_async = self.user_template_async
        user_prompt = await user_template_async.render_async(render_env)

        outputs = await self.ainvoke(
            input,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **kwargs,
        )
        logging.debug(f"The LLM returned: {outputs}")
        output = self._get_output(input, outputs)
        self._validate_output(input, output)
        return output

    @abstractmethod
    def invoke(
        self, input: AgentIOMapperInput, messages: list[dict[str, str]], **kwargs
    ) -> str:
        """Invoke internal model to process messages.
        Args:
            messages: the messages to send to the LLM
        """

    @abstractmethod
    async def ainvoke(
        self, input: AgentIOMapperInput, messages: list[dict[str, str]], **kwargs
    ) -> str:
        """Async invoke internal model to process messages.
        Args:
            messages: the messages to send to the LLM
        """
