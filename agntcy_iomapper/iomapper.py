# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
import argparse
import asyncio
import aiofiles
import logging
import jsonschema
import json
import re

from dotenv import load_dotenv, find_dotenv
from pydantic import Field, model_validator, BaseModel
from typing import TypedDict, ClassVar
from typing_extensions import Self
from jinja2 import Environment
from jinja2.sandbox import SandboxedEnvironment
from pydantic_ai import Agent

from .base import BaseIOMapper, IOModelSettings, IOMapperOutput, IOMapperInput
from .supported_agents import get_supported_agent

logger = logging.getLogger(__name__)


class IOModelArgs(TypedDict, total=False):
    base_url: str
    api_version: str
    azure_endpoint: str
    azure_ad_token: str
    project: str
    organization: str


class IOMapperConfig(BaseModel):
    models: dict[str, IOModelArgs] = Field(
        default={"azure:gpt-4o-mini": IOModelArgs()},
        description="LLM configuration to use for translation",
    )
    default_model: str | None = Field(
        default="azure:gpt-4o-mini",
        description="Default arguments to LLM completion function by configured model.",
    )
    default_model_settings: dict[str, IOModelSettings] = Field(
        default={"azure:gpt-4o-mini": IOModelSettings(seed=42, temperature=0.8)},
        description="LLM configuration to use for translation",
    )
    validate_json_input: bool = Field(
        default=False, description="Validate input against JSON schema."
    )
    validate_json_output: bool = Field(
        default=False, description="Validate output against JSON schema."
    )
    system_prompt_template: str = Field(
        max_length=4096,
        default="You are a translation machine. You translate both natural language and object formats for computers.",
        description="System prompt Jinja2 template used with LLM service for translation.",
    )
    message_template: str = Field(
        max_length=4096,
        default="The input is described {% if input.json_schema %}by the following JSON schema: {{ input.json_schema.model_dump(exclude_none=True) }}{% else %}as {{ input.description }}{% endif %}, and the output is described {% if output.json_schema %}by the following JSON schema: {{ output.json_schema.model_dump(exclude_none=True) }}{% else %}as {{ output.description }}{% endif %}. The data to translate is: {{ data }}",
        description="Default user message template. This can be overridden by the message request.",
    )

    @model_validator(mode="after")
    def _validate_obj(self) -> Self:
        if self.models and self.default_model not in self.models:
            raise ValueError(
                f"default model {self.default_model} not present in configured models"
            )
        # Fill out defaults to eliminate need for checking.
        for model_name in self.models.keys():
            if model_name not in self.default_model_settings:
                self.default_model_settings[model_name] = IOModelSettings()

        return self


class IOMapper(BaseIOMapper):
    _json_search_pattern: ClassVar[re.Pattern] = re.compile(r"```json\n(.*?)\n```", re.DOTALL)

    def __init__(
        self,
        config: IOMapperConfig,
        jinja_env: Environment | None = None,
        jinja_env_async: Environment | None = None,
    ):
        self.config = config

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

    def _get_render_env(self, input: IOMapperInput) -> dict[str, str]:
        return {
            "input": input.input,
            "output": input.output,
            "data": input.data,
        }

    def _get_model_settings(self, input: IOMapperInput):
        model_name = input.model or self.config.default_model
        if model_name not in self.config.models:
            raise ValueError(f"requested model {model_name} not found")
        elif input.model_settings is None:
            return self.config.default_model_settings[model_name]
        else:
            model_settings = self.config.default_model_settings[model_name].copy()
            model_settings.update(input.model_settings)
            return model_settings

    def _get_agent(
        self, is_async: bool, input: IOMapperInput, system_prompt: str
    ) -> Agent:
        model_name = input.model or self.config.default_model
        if model_name not in self.config.models:
            raise ValueError(f"requested model {model_name} not found")

        return get_supported_agent(
            is_async,
            model_name,
            model_args=self.config.models[model_name],
            system_prompt=system_prompt,
        )

    def _get_output(self, input: IOMapperInput, outputs: str) -> IOMapperOutput:
        if input.output.json_schema is None:
            # If there is no schema, quote the chars for JSON.
            return IOMapperOutput.model_validate_json(
                f'{{"data": {json.dumps(outputs)} }}'
            )

        # Check if data is returned in JSON markdown text
        matches = self._json_search_pattern.findall(outputs)
        if matches:
            outputs = matches[-1]

        return IOMapperOutput.model_validate_json(f'{{"data": {outputs} }}')

    def _validate_input(self, input: IOMapperInput) -> None:
        if self.config.validate_json_input and input.input.json_schema is not None:
            jsonschema.validate(
                instance=input.data,
                schema=input.input.json_schema.model_dump(
                    exclude_none=True, mode="json"
                ),
            )

    def _validate_output(self, input: IOMapperInput, output: IOMapperOutput) -> None:
        if self.config.validate_json_output and input.output.json_schema is not None:
            output_schema = input.output.json_schema.model_dump(
                exclude_none=True, mode="json"
            )
            logging.debug(f"Checking output schema: {output_schema}")
            jsonschema.validate(
                instance=output.data,
                schema=output_schema,
            )

    def invoke(self, input: IOMapperInput) -> IOMapperOutput:
        self._validate_input(input)
        self._check_jinja_env(False)
        render_env = self._get_render_env(input)
        system_prompt = self.prompt_template.render(render_env)
        agent = self._get_agent(False, input, system_prompt)

        if input.message_template is not None:
            logging.info(f"User template supplied on input: {input.message_template}")
            user_template = self.jinja_env.from_string(input.message_template)
        else:
            user_template = self.user_template
        response = agent.run_sync(
            user_prompt=user_template.render(render_env),
            model_settings=self._get_model_settings(input),
        )
        outputs = response.data
        logging.debug(f"The LLM returned: {outputs}")
        output = self._get_output(input, outputs)
        self._validate_output(input, output)
        return output

    async def ainvoke(self, input: IOMapperInput) -> IOMapperOutput:
        self._validate_input(input)
        self._check_jinja_env(True)
        render_env = self._get_render_env(input)
        system_prompt = await self.prompt_template_async.render_async(render_env)
        agent = self._get_agent(True, input, system_prompt)

        if input.message_template is not None:
            logging.info(f"User template supplied on input: {input.message_template}")
            user_template_async = self.jinja_env_async.from_string(
                input.message_template
            )
        else:
            user_template_async = self.user_template_async
        response = await agent.run(
            user_prompt=await user_template_async.render_async(render_env),
            model_settings=self._get_model_settings(input),
        )
        outputs = response.data
        logging.debug(f"The LLM returned: {outputs}")
        output = self._get_output(input, outputs)
        self._validate_output(input, output)
        return output


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputfile", help="Inputfile", required=True)
    parser.add_argument("--configfile", help="Configuration file", required=True)
    parser.add_argument("--outputfile", help="Output file", required=True)
    args = parser.parse_args()
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

    jinja_env = SandboxedEnvironment(
        loader=None,
        enable_async=True,
        autoescape=False,
    )

    async with aiofiles.open(args.configfile, "r") as fp:
        configs = await fp.read()

    config = IOMapperConfig.model_validate_json(configs)
    logging.info(f"Loaded config from {args.configfile}: {config.model_dump_json()}")

    async with aiofiles.open(args.inputfile, "r") as fp:
        inputs = await fp.read()

    input = IOMapperInput.model_validate_json(inputs)
    logging.info(f"Loaded input from {args.inputfile}: {input.model_dump_json()}")

    p = IOMapper(config, jinja_env)
    output = await p.ainvoke(input)
    outputs = output.model_dump_json()

    async with aiofiles.open(args.outputfile, "w") as fp:
        await fp.write(outputs)

    logging.info(f"Dumped output to {args.outputfile}: {outputs}")


if __name__ == "__main__":
    load_dotenv(dotenv_path=find_dotenv(usecwd=True))
    asyncio.run(main())
