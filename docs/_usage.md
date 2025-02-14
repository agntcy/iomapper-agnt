# Usage

### Use Agent IO Mapper

:TODO

### Use Determenistic

The code snippet below illustrates a fully functional deterministic mapping that transforms the output of one agent into input for a second agent. The code for the agents is omitted.

```python
 #define schema for the origin agent
 input_schema = {"question": {"type": "string"}}

 #define schema to witch the input should be converted to
 output_schema = {
     "quiz": {
         "type": "object",
         "properties": {
             "prof_question": {"type": "string"},
             "due_date": {"type": "string"},
         },
     }
 }

 #the mapping object using jsonpath, note: the value of the mapping can be either a jsonpath or a function
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
 #instantiate the mapper
 imerative_mapp = ImperativeIOMapper(
     field_mapping=mapping_object,
 )
 #get the mapping result and send to the other agent
 mapping_result = imerative_mapp.invoke(input=input)



```

### Use Examples

1. To run the examples we strongly recommend that a [virtual environment is created](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
2. Install the requirements file
3. from within examples folder run:

```sh
make run_imperative_example
```

[GitHub](https://github.com/agntcy/iomapper-agnt/)
[Get Started](#getting-started)

```

```
