from typing import List, TypedDict, Union

from llama_index.core import (
    GPTVectorStoreIndex,
    StorageContext,
)
from llama_index.core.agent.workflow import (
    AgentOutput,
    AgentWorkflow,
    FunctionAgent,
    ToolCall,
    ToolCallResult,
)
from llama_index.core.schema import TextNode
from llama_index.core.workflow import Context
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.docarray import DocArrayInMemoryVectorStore
from pydantic import TypeAdapter

from agntcy_iomapper import FieldMetadata, IOMappingAgent, IOMappingAgentMetadata
from examples.llm import Framework, get_azure
from examples.models import RecipeQuery, RecipeResponse
from examples.models.data import recipes


class GraphState(TypedDict):
    query: RecipeQuery
    documents: Union[List[TextNode], None]
    recipe: Union[RecipeResponse, None]
    formatted_output: Union[str, None]


nodes = [TextNode(text=recipe) for recipe in recipes]
vector_store = DocArrayInMemoryVectorStore()
storage_context = StorageContext.from_defaults(vector_store=vector_store)

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

index = GPTVectorStoreIndex(
    nodes, storage_context=storage_context, embed_model=embed_model
)

llm = get_azure(framework=Framework.LLAMA_INDEX)


async def get_recipe(ctx: Context) -> str:
    """Useful for getting recipe from vector store."""
    current_state = await ctx.get("state")
    query = current_state["query"]["ingredients"]

    query_engine = index.as_retriever(similarity_top_k=3, llm=llm)

    response = query_engine.retrieve(",".join(query))
    current_state["documents"] = [response[0].node]
    await ctx.set("state", current_state)
    return "Found recipe document needs mapping"


async def format_recipe(ctx: Context) -> str:
    """Formats the recipe for user display."""
    current_state = await ctx.get("state")

    recipe: RecipeResponse = current_state["recipe"]
    title = recipe.get("title", "")
    ingredients = recipe.get("ingredients", [])
    instructions = recipe.get("instructions", "")
    return {
        "formatted_output": f"Recipe: {title}\n"
        f"Ingredients: {', '.join(ingredients)}\n"
        f"Instructions: {instructions}"
    }


async def got_to_format(ctx: Context) -> str:
    return "Got to format recipe"


recipie_library_agent = FunctionAgent(
    name="RecipeAgent",
    description="Expert in finding recipe in a in memory database",
    tools=[get_recipe],
    llm=llm,
    verbose=True,
    can_handoff_to=["IOMapperAgent"],
    system_prompt=""" \
You are an agent designed to answer queries over a set of recipes.
Please use the tools provided to answer a question as possible.
""",
)

mapping_metadata = IOMappingAgentMetadata(
    input_fields=["documents.0.text"],
    output_fields=[
        FieldMetadata(
            json_path="recipe",
            description="this is a recipe for the ingredients you've provided",
        )
    ],
    input_schema=TypeAdapter(GraphState).json_schema(),
    output_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "ingredients": {"type": "array", "items": {"type": "string"}},
            "instructions": {"type": "string"},
        },
        "required": ["title", "ingredients, instructions"],
    },
)

io_mapping_agent = IOMappingAgent.as_workflow_agent(
    mapping_metadata=mapping_metadata,
    llm=llm,
    name="IOMapperAgent",
    description="Useful for mapping a recipe document into recipe object",
    can_handoff_to=["Formatter_Agent"],
    tools=[got_to_format],
)

formatter_agent = FunctionAgent(
    name="Formatter_Agent",
    llm=llm,
    description="Useful for formatting a recipe object and return it as a string",
    sytems_prompt="""\
    """,
    tools=[format_recipe],
)

agent_workflow = AgentWorkflow(
    agents=[recipie_library_agent, io_mapping_agent, formatter_agent],
    root_agent=recipie_library_agent.name,
    initial_state={"query": {"ingredients": ["pasta", "tomato"]}},
)


async def main():
    handler = agent_workflow.run(user_msg="pasta, tomato output in a readable format")

    current_agent = None

    async for event in handler.stream_events():
        if (
            hasattr(event, "current_agent_name")
            and event.current_agent_name != current_agent
        ):
            current_agent = event.current_agent_name
            print(f"\n{'='*50}")
            print(f"🤖 Agent: {current_agent}")
            print(f"{'='*50}\n")
        elif isinstance(event, AgentOutput):
            if event.response.content:
                print("📤 Output:", event.response.content)
            if event.tool_calls:
                print(
                    "🛠️  Planning to use tools:",
                    [call.tool_name for call in event.tool_calls],
                )
        elif isinstance(event, ToolCallResult):
            print(f"🔧 Tool Result ({event.tool_name}):")
            print(f"  Arguments: {event.tool_kwargs}")
            print(f"  Output: {event.tool_output}")
        elif isinstance(event, ToolCall):
            print(f"🔨 Calling Tool: {event.tool_name}")
            print(f"  With arguments: {event.tool_kwargs}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
