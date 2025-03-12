from llama_index.core import (
    GPTVectorStoreIndex,
    StorageContext,
)
from llama_index.core.agent import FunctionCallingAgent
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.schema import TextNode
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.vector_stores.docarray import DocArrayInMemoryVectorStore

from agntcy_iomapper.llamaindex.llamaindex import IOMapperAgent
from examples.llm import Framework, get_azure
from examples.models.data import recipes
from llama_index.core.agent.workflow import AgentWorkflow

nodes = [TextNode(text=recipe) for recipe in recipes]
vector_store = DocArrayInMemoryVectorStore()
storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = GPTVectorStoreIndex(nodes, storage_context=storage_context)

llm = get_azure(framework=Framework.LLAMA_INDEX)


def search_recipe_book():
    query_engine = index.as_query_engine(similarity_top_k=3, llm=llm)
    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="reipes library",
            description="Provides recipes details based on ingridients",
        ),
    )

    return query_engine_tool


library_tool = search_recipe_book()

recipie_library_agent = FunctionCallingAgent.from_tools(
    name="RecipeAgent",
    tools=[library_tool],
    llm=llm,
    verbose=True,
    system_prompt=""" \
You are an agent designed to answer queries over a set of recipes.
Please use the tools provided to answer a question as possible. Do not rely on prior knowledge. Summarize your answer\

""",
    can_handoff_to=["IOMapperAgent"],
)

io_mapping_agent = IOMapperAgent(name="IOMapperAgent")

formatter_agent = FunctionAgent(
    name="Formatter_Agent",
    llm=llm,
    sytems_prompt="""\
    """,
)

agent_workflow = AgentWorkflow(
    agents=[recipie_library_agent, io_mapping_agent, formatter_agent],
    root_agent=recipie_library_agent.name,
    initial_state={
        "research_notes": {},
        "report_content": "Not written yet.",
        "review": "Review required.",
    },
)
