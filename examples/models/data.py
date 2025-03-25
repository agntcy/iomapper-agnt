from typing import List

from examples.models import User

users: List[User] = [
    User(name="Alice", email="alice@example.com", phone="123-456-7890"),
    User(name="Bob", email="bob@example.com", phone="987-654-3210"),
]

# Small in-memory dataset of recipes stored as raw text
recipes = [
    "Pasta Primavera: Ingredients - pasta, tomato, garlic, olive oil. Instructions - Boil pasta, sauté garlic and tomatoes in olive oil, mix together.",
    "Avocado Toast: Ingredients - bread, avocado, salt, pepper. Instructions - Toast bread, mash avocado, spread on toast, add salt and pepper.",
    "Omelette: Ingredients - egg, cheese, onion, butter. Instructions - Beat eggs, cook in butter, add cheese and onions, fold omelette.",
]
