# Usage

The Agntcy IO Mapper functions provided an easy to use package for mapping output from 
one agent to another. The data can be described in JSON or with natural language. The 
(incomplete) [pydantic](https://docs.pydantic.dev/latest/) models follow:

```python
class ArgumentsDescription(BaseModel):
    json_schema: Schema | None = Field(description="Data format JSON schema")
    description: str | None = Field(description="Data (semantic) natural language description")

class BaseIOMapperInput(BaseModel):
    input: ArgumentsDescription = Field(description="Input data descriptions")
    output: ArgumentsDescription = Field(description="Output data descriptions")
    data: Any = Field(description="Data to translate")

class BaseIOMapperOutput(BaseModel):
    data: Any = Field(description="Data after translation")
    error: str | None = Field(description="Description of error on failure.")

class BaseIOMapperConfig(BaseModel):
    validate_json_input: bool = Field(description="Validate input against JSON schema.")
    validate_json_output: bool = Field(description="Validate output against JSON schema.")
```

There are several different ways to leverage the IO Mapper functions in Python. There 
is an [agentic interface](#use-agent-io-mapper) using models that can be invoked on 
different AI platforms and a [imperative interface](#use-imperative--deterministic-io-mapper) 
that does deterministic JSON remapping without using any AI models.

## Use Agent IO Mapper

The Agent IO Mapper uses an LLM/model to transform the inputs (typically output of the 
first agent) to match the desired output (typically the input of a second agent). As such,
it additionally supports specifying the model prompts for the translation. The configuration 
object provides a specification for the system and default user prompts:

```python
class AgentIOMapperConfig(BaseIOMapperConfig):
    system_prompt_template: str = Field(
        description="System prompt Jinja2 template used with LLM service for translation."
    )
    message_template: str = Field(
        description="Default user message template. This can be overridden by the message request."
    )
```

and the input object supports overriding the user prompt for the requested translation:

```python
class AgentIOMapperInput(BaseIOMapperInput):
    message_template: str | None = Field(
        description="Message (user) to send to LLM to effect translation.",
    )
```

Further specification of models and their arguments is left to the underlying supported 
packages:
  * [Pydantic-AI](#pydantic-ai)
  * [LangGraph](#langgraph)


### Pydantic-AI

One of the supported platforms for managing the model interactions is [Pydantic-AI](https://ai.pydantic.dev/).

### LangGraph

This project supports specifying model interations using [LangGraph](https://langchain-ai.github.io/langgraph/).

## Use Imperative / Deterministic IO Mapper

The code snippet below illustrates a fully functional deterministic mapping that 
transforms the output of one agent into input for a second agent. The code for the 
agents is omitted.

```python
 # define schema for the origin agent
 input_schema = {"question": {"type": "string"}}

 # define schema to witch the input should be converted to
 output_schema = {
     "quiz": {
         "type": "object",
         "properties": {
             "prof_question": {"type": "string"},
             "due_date": {"type": "string"},
         },
     }
 }

 # the mapping object using jsonpath, note: the value of the mapping 
 # can be either a jsonpath or a function
 mapping_object = {
     "prof_question": "$.question",
     "due_date": lambda _: datetime.now().strftime("%x"),
 }

 input = IOMapperInput(
     input=ArgumentsDescription(
         json_schema=Schema.model_validate(input_schema)
     ),
     output=ArgumentsDescription(
         json_schema=Schema.model_validate(output_schema)
     ),
     data={"question": output_prof},
 )
 # instantiate the mapper
 imerative_mapp = ImperativeIOMapper(
     field_mapping=mapping_object,
 )
 # get the mapping result and send to the other agent
 mapping_result = imerative_mapp.invoke(input=input)
```

### Use Examples

1. To run the examples we strongly recommend that a 
  [virtual environment is created](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
2. Install the requirements file
3. From within examples folder run:

```shell
make run_imperative_example
```
