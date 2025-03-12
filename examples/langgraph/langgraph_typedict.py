import os
from typing import List, TypedDict, Union

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import FakeEmbeddings
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from pydantic import TypeAdapter

from agntcy_iomapper.langgraph import io_mapper_node
from examples.llm import get_azure
from examples.models import RecipeQuery, RecipeResponse


class GraphState(TypedDict):
    query: RecipeQuery
    documents: Union[List[Document], None]
    recipe: Union[RecipeResponse, None]
    formatted_output: Union[str, None]


# Small in-memory dataset of recipes stored as raw text
recipes = [
    "Pasta Primavera: Ingredients - pasta, tomato, garlic, olive oil. Instructions - Boil pasta, sauté garlic and tomatoes in olive oil, mix together.",
    "Avocado Toast: Ingredients - bread, avocado, salt, pepper. Instructions - Toast bread, mash avocado, spread on toast, add salt and pepper.",
    "Omelette: Ingredients - egg, cheese, onion, butter. Instructions - Beat eggs, cook in butter, add cheese and onions, fold omelette.",
]

embed = FakeEmbeddings(size=100)
vector_store = FAISS.from_texts(recipes, embed)
retriever = vector_store.as_retriever()


def retrieve_recipe(state: GraphState) -> GraphState:
    """Retrieve recipes that match the given ingredients."""
    query = ", ".join(state["query"]["ingredients"])
    documents = retriever.invoke(query)

    return {"documents": documents}


def format_recipe(state: GraphState) -> GraphState:
    """Formats the recipe for user display."""
    recipe: RecipeResponse = state["recipe"]
    print(recipe)
    title = recipe.get("title", "")
    ingredients = recipe.get("ingredients", [])
    instructions = recipe.get("instructions", "")
    return {
        "formatted_output": f"Recipe: {title}\n"
        f"Ingredients: {', '.join(ingredients)}\n"
        f"Instructions: {instructions}"
    }


graph = StateGraph(GraphState)
graph.add_node("retrieve", retrieve_recipe)
graph.add_node(
    "recipe_io_mapper",
    io_mapper_node,
    metadata={
        "input_fields": ["documents.0.page_content"],
        "input_schema": TypeAdapter(GraphState).json_schema(),
        "output_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "ingredients": {"type": "array", "items": {"type": "string"}},
                "instructions": {"type": "string"},
            },
            "required": ["title", "ingredients, instructions"],
        },
        "output_fields": ["recipe"],
    },
)
graph.add_node("format", format_recipe)

graph.add_edge("retrieve", "recipe_io_mapper")
graph.add_edge("recipe_io_mapper", "format")
graph.add_edge("format", END)

graph.set_entry_point("retrieve")

llm = get_azure()
config = RunnableConfig(configurable={"llm": llm})
app = graph.compile()

# Example usage
query = {
    "query": {"ingredients": ["pasta", "tomato"]},
    "documents": None,
    "response": None,
    "formatted_output": None,
}
result = app.invoke(query, config)
print(result)
