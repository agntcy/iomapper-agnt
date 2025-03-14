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

- [Pydantic-AI](#pydantic-ai)
- [LangGraph](#langgraph)

### Pydantic-AI

One of the supported platforms for managing the model interactions is [Pydantic-AI](https://ai.pydantic.dev/).

### LangGraph

This project supports specifying model interations using [LangGraph](https://langchain-ai.github.io/langgraph/).

## Use with Langgraph graph [Pydantic state]
<table>
    <tr>
        <th>Field</th>
        <th>Description</th>
        <th>Required</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>input_fields</td>
        <td>an array of json paths </td>
        <td>:white_check_mark:</td>
<td>

```["state.fiedl1", "state.field2", "state"]```            
</td>
    </tr>
    <tr>
        <td>output_fields</td>
        <td>an array of json paths </td>
        <td>:white_check_mark:</td>
<td>

```["state.output_fiedl1"]```
</td>
    </tr>
    <tr>
        <td>input_schema</td>
        <td>defines the schema of the input data</td>
        <td> :heavy_minus_sign: </td>
        <td>
            
```json
{ 
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "ingredients": {"type": "array", "items": {"type": "string"}},
        "instructions": {"type": "string"},
    },
    "required": ["title", "ingredients, instructions"],
}
```
<hr />
OR

```python
from pydantic import TypeAdapter
TypeAdapter(GraphState).json_schema()
```
</td>
    </tr>
    <tr>
        <td>output_schema</td>
        <td>defines the schema for the output data</td>
        <td>:heavy_minus_sign:</td>
        <td>same as input_schema</td>
    </tr>
    <tr>
        <td>output_template</td>
        <td>a prompt follwoing jinja template</td>
        <td>:heavy_minus_sign:</td>
        <td>
    
```python
"""Return the output as a JSON object with the following structure:
{{
"name": "Campaign Name",
"content": "Campaign Content",
"is_urgent": yes/no
}}
"""
```
</td>
</tr>
</table>

In langgraph you can used with states typed as ```python TypedDict``` or our recommended way with ```python Pydantic```.
We will show two examples of how to add the io mapper in a langgraph graph. We assume you have a langgraph graph created therefore the steps of how the graph is created is ommited.
```python
from agntcy_iomapper.langgraph import (
    io_mapper_node,
)
```
Users can easily specify the input fields that needs to be translated and the expected output fields 
```python
workflow.add_node(
    "io_mapping",
    io_mapper_node,
    metadata={
        "input_fields": ["selected_users", "campaign_details.name"],
        "output_fields": ["stats.status"],
    },
)
```
:warning: The configurations needed by the io mapper node must be passed in the metadata dictionary when adding the node

This instruction tells the io mapper agent to use ```selected_users ``` and ```name``` from ```campaign_details``` field the langgraph stat
```python
workflow.add_edge("create_communication", "io_mapping")
workflow.add_edge("io_mapping", "send_communication")
```
Here is a flow chart of io mapper in a langgraph graph of the discussed application
```mermaid
flowchart TD
    A[create_communication] -->|input in specific format| B(IO Mapper Agent)
    B -->|output expected format| D[send_communication]
```
:warning: Very important to set the llm instance to be used by the iomapper agent, in the runnable config with the key llm before you invoke the graph
```python
config = RunnableConfig(configurable={"llm": llm})
app.invoke(inputs, config)
```


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
