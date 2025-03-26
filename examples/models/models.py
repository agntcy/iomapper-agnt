# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import List, TypedDict

from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., description="The name of the user.")
    email: str = Field(..., description="The email address of the user.")
    phone: str = Field(..., description="The phone number of the user.")


class Campaign(BaseModel):
    name: str = Field(..., description="The name of the campaign")
    content: str = Field(..., description="The name of the campaign")
    is_urgent: str = Field(False, description="Indicates if the campaign is urgent.")


class Communication(BaseModel):
    subject: str = Field(..., description="The subject of the email.")
    body: str = Field(..., description="The body of the email.")
    recipients: List[str] = Field(
        ..., description="A list of recipient email addresses."
    )


class Statistics(BaseModel):
    status: str = Field(
        False, description="Indicates if the campaign is was successfully sent"
    )
    message: str = Field(..., description="Indicates how many users were targeted")


# Define data structure using TypedDict
class Recipe(TypedDict):
    title: str
    ingredients: List[str]
    instructions: str


class RecipeQuery(TypedDict):
    ingredients: List[str]


class RecipeResponse(TypedDict):
    recipe: Recipe
