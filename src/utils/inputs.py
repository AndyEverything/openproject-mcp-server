"""Tolerant handling of wrapped Pydantic tool inputs.

Several tools take a single parameter -- a Pydantic model named ``input``.
FastMCP validates that argument against the model *before* the tool body runs.

MCP clients differ in how they serialize structured arguments. Spec-compliant
clients send ``input`` as a JSON object and these tools work unchanged. Other
clients serialize object-typed arguments as a JSON *string* when the parameter's
schema is not an explicit ``type: object``; FastMCP then receives a ``str`` and
rejects it with a Pydantic ``model_type`` error before the body runs.

``CoercibleModel`` makes any input model accept that JSON-string encoding in
addition to a dict or model instance, so the server works with both kinds of
client. ``as_model`` is the equivalent helper for non-decorated call paths.
"""

from __future__ import annotations

import json
from typing import Type, TypeVar, Union

from pydantic import BaseModel, model_validator

ModelT = TypeVar("ModelT", bound=BaseModel)


class CoercibleModel(BaseModel):
    """Input-model base that also accepts a JSON string.

    A ``model_validator(mode="before")`` runs prior to field validation. When the
    incoming value is a ``str`` (a client that serialized the object as JSON) it
    is parsed into a dict first. Dicts and model instances pass through unchanged,
    so spec-compliant clients are unaffected. Invalid JSON raises and surfaces as
    a normal validation error.
    """

    @model_validator(mode="before")
    @classmethod
    def _accept_json_string(cls, data):
        if isinstance(data, str):
            return json.loads(data)
        return data


def as_model(model_cls: Type[ModelT], value: Union[ModelT, dict, str]) -> ModelT:
    """Coerce a model instance, dict, or JSON string into ``model_cls``."""
    if isinstance(value, model_cls):
        return value
    if isinstance(value, str):
        return model_cls.model_validate_json(value)
    if isinstance(value, dict):
        return model_cls.model_validate(value)
    raise TypeError(
        f"{model_cls.__name__} input must be a model, dict, or JSON string, "
        f"got {type(value).__name__}"
    )
