"""Tests for tolerant input handling (CoercibleModel + as_model).

These verify the server accepts both the object and the JSON-string encoding of
wrapped tool inputs, so it works regardless of how an MCP client serializes
structured arguments.
"""

import importlib
import inspect
import pkgutil
from typing import Optional

import pytest
from pydantic import BaseModel

from src.utils.inputs import CoercibleModel, as_model


class Demo(CoercibleModel):
    project_id: int
    subject: str
    type_id: int
    description: Optional[str] = None


# --- CoercibleModel: accepts object and JSON-string encodings ---


def test_coercible_accepts_dict():
    m = Demo.model_validate({"project_id": 1, "subject": "x", "type_id": 3})
    assert m.project_id == 1 and m.type_id == 3


def test_coercible_accepts_json_string():
    # This is the encoding that previously failed with a `model_type` error.
    m = Demo.model_validate('{"project_id": 1, "subject": "x", "type_id": 3}')
    assert m.project_id == 1 and m.subject == "x"


def test_coercible_as_nested_field_accepts_json_string():
    # Mirrors how FastMCP validates a wrapped `input` parameter.
    class Call(BaseModel):
        input: Demo

    c = Call.model_validate(
        {"input": '{"project_id": 2, "subject": "y", "type_id": 4}'}
    )
    assert isinstance(c.input, Demo) and c.input.project_id == 2


def test_coercible_invalid_json_raises():
    with pytest.raises(Exception):
        Demo.model_validate("{not valid json")


# --- as_model helper ---


@pytest.mark.parametrize(
    "value",
    [
        {"project_id": 1, "subject": "x", "type_id": 3},
        '{"project_id": 1, "subject": "x", "type_id": 3}',
        Demo(project_id=1, subject="x", type_id=3),
    ],
)
def test_as_model_accepts_all_encodings(value):
    m = as_model(Demo, value)
    assert m.project_id == 1 and m.type_id == 3


def test_as_model_rejects_bad_type():
    with pytest.raises(TypeError):
        as_model(Demo, 123)


def test_as_model_rejects_invalid_payload():
    with pytest.raises(Exception):
        as_model(Demo, '{"subject": "missing required fields"}')


# --- Tripwire: every wrapped *Input model must be coercible ---


def _iter_input_models():
    import src.tools as tools_pkg

    for mod in pkgutil.iter_modules(tools_pkg.__path__):
        module = importlib.import_module(f"src.tools.{mod.name}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                name.endswith("Input")
                and issubclass(obj, BaseModel)
                and obj.__module__ == module.__name__
            ):
                yield f"{mod.name}.{name}", obj


def test_every_wrapped_input_model_is_coercible():
    offenders = [
        qualname
        for qualname, model in _iter_input_models()
        if not issubclass(model, CoercibleModel)
    ]
    assert not offenders, (
        "These *Input models must subclass CoercibleModel so the server tolerates "
        f"JSON-string arguments: {offenders}"
    )


def test_flattened_work_package_tools_have_no_wrapped_input():
    # The two hot tools were flattened to explicit params; guard against a
    # regression back to a single wrapped `input` model.
    import src.tools.work_packages as wp

    assert not hasattr(wp, "CreateWorkPackageInput")
    assert not hasattr(wp, "UpdateWorkPackageInput")
