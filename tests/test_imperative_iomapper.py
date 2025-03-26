# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json

import pytest
from openapi_pydantic import Schema

from agntcy_iomapper.base import ArgumentsDescription
from agntcy_iomapper.imperative import ImperativeIOMapper, ImperativeIOMapperInput


@pytest.mark.parametrize(
    "input_schema, output_schema,field_mapping,input_value, expected",
    [
        (
            {
                "type": "object",
                "properties": {"fullName": {"type": "string"}},
                "required": ["fullName"],
            },
            {
                "type": "object",
                "properties": {
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                },
                "required": ["firstName", "lastName"],
            },
            {
                "$.firstName": "$.fullName.`split(' ', 0, 1)`",
                "$.lastName": "$.fullName.`split(' ', -1, -1)`",
            },
            {"fullName": "John Doe"},
            {"firstName": "John", "lastName": "Doe"},
        ),
        (
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "address": {
                        "type": "object",
                        "properties": {
                            "street": {"type": "string"},
                            "city": {"type": "string"},
                        },
                    },
                },
            },
            {
                "type": "object",
                "properties": {
                    "fullName": {"type": "string"},
                    "location": {
                        "type": "object",
                        "properties": {
                            "streetAddress": {"type": "string"},
                            "cityName": {"type": "string"},
                        },
                    },
                },
            },
            {
                "fullName": "$.name",
                "location.streetAddress": "$.address.street",
                "location.cityName": "$.address.city",
            },
            {
                "name": "John Doe",
                "age": 30,
                "address": {"street": "123 Elm St", "city": "Springfield"},
            },
            {
                "fullName": "John Doe",
                "location": {"streetAddress": "123 Elm St", "cityName": "Springfield"},
            },
        ),
        (
            {
                "type": "object",
                "properties": {
                    "employeeId": {"type": "number"},
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                    "email": {"type": "string"},
                    "position": {"type": "string"},
                    "department": {"type": "string"},
                },
                "required": ["firstName", "email", "position", "department"],
            },
            {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["recipient", "subject", "body"],
            },
            {"recipient": "$.email", "subject": "$.position", "body": "$.firstName"},
            {
                "employeeId": 123,
                "firstName": "Jane",
                "lastName": "Doe",
                "email": "jane.doe@example.com",
                "position": "Marketing Manager",
                "department": "Marketing",
            },
            {
                "recipient": "jane.doe@example.com",
                "subject": "Marketing Manager",
                "body": "Jane",
            },
        ),
        (
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "details": {
                        "type": "object",
                        "properties": {
                            "brand": {"type": "string"},
                            "specifications": {
                                "type": "object",
                                "properties": {
                                    "memory": {"type": "string"},
                                    "storage": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
            {
                "product_name": {"type": "string"},
                "product_category": {"type": "string"},
                "brand": {"type": "string"},
                "storage": {"type": "string"},
                "full_product_info": {"type": "string"},
            },
            {
                "product_name": "$.product.name",
                "product_category": "$.category",
                "brand": "$.product.details.brand",
                "storage": "$.product.details.specifications.storage",
                "full_product_info": lambda d: d.get("product", {}),
            },
            {
                "product": {
                    "name": "Laptop",
                    "details": {
                        "brand": "Dell",
                        "specifications": {"memory": "16GB", "storage": "1TB"},
                    },
                },
                "category": "Electronics",
            },
            {
                "product_name": "Laptop",
                "product_category": "Electronics",
                "brand": "Dell",
                "storage": "1TB",
                "full_product_info": {
                    "details": {
                        "brand": "Dell",
                        "specifications": {"memory": "16GB", "storage": "1TB"},
                    },
                    "name": "Laptop",
                },
            },
        ),
    ],
)
def test_imperative_iomapp(
    input_schema, output_schema, field_mapping, input_value, expected
) -> None:
    """Test imperative io mapping"""
    input = ImperativeIOMapperInput(
        input=ArgumentsDescription(json_schema=Schema.model_validate(input_schema)),
        output=ArgumentsDescription(json_schema=Schema.model_validate(output_schema)),
        data=input_value,
    )

    io_mapp = ImperativeIOMapper(field_mapping=field_mapping, input=input)

    actual = io_mapp.invoke(data=json.dumps(input_value))

    # When test returns none fail the test
    if actual is None:
        assert True is False
        return

    assert expected == actual
