"""Tests for src.utils.custom_fields.extract_custom_fields."""

import pytest

from src.utils.custom_fields import extract_custom_fields


@pytest.fixture
def fields(load_fixture):
    result = extract_custom_fields(load_fixture("wp_basic"), load_fixture("wp_schema"))
    return {item["key"]: item for item in result}


@pytest.mark.parametrize(
    "key, name, field_type, value",
    [
        ("customField40", "Kategoria (rozwój)", "CustomOption", "06. Ulepszenie UI i UX"),
        ("customField60", "Moduły", "[]CustomOption", "Nieruchomości, Księgowość"),
        ("customField61", "Analityk", "User", "Jan Testowy"),
        ("customField53", "Planowana wersja (tylko PO)", "Version", "3.00.001. (planowana)"),
        ("customField48", "Opis biznesowy zmian (tylko PO)", "Formattable", "Użytkownicy szybciej znajdą blokadę."),
        ("customField10", "Tag 2", "String", "DevEx"),
        ("customField36", "Szacowany czas analizy", "Integer", "3"),
        ("customField63", "Współczynnik ryzyka", "Float", "0.5"),
        ("customField33", "Termin przekazania do testów", "Date", "2026-07-01"),
        ("customField26", "ASAP (tylko PO)", "Boolean", "Nie"),
        ("customField47", "Do publikacji (tylko PO)", "Boolean", "Tak"),
    ],
)
def test_field_values(fields, key, name, field_type, value):
    assert fields[key] == {"key": key, "name": name, "type": field_type, "value": value}


@pytest.mark.parametrize(
    "key",
    [
        "customField45",  # link z href None
        "customField54",  # wersja pusta
        "customField62",  # pusta lista User
        "customField20",  # Formattable z pustym raw
        "customField9",  # String None
        "customField55",  # pusty string
        "customField64",  # Boolean None
    ],
)
def test_empty_fields_are_skipped(fields, key):
    assert key not in fields


def test_order_follows_schema(load_fixture):
    schema = load_fixture("wp_schema")
    result = extract_custom_fields(load_fixture("wp_basic"), schema)

    schema_order = [key for key in schema if key.startswith("customField")]
    keys = [item["key"] for item in result]
    assert keys == [key for key in schema_order if key in keys]


def test_non_custom_schema_entries_are_ignored(fields):
    assert all(key.startswith("customField") for key in fields)


def test_field_missing_in_work_package_is_skipped(load_fixture):
    schema = {"customField99": {"type": "String", "name": "Brak"}}

    assert extract_custom_fields(load_fixture("wp_basic"), schema) == []


def test_empty_inputs():
    assert extract_custom_fields({}, {}) == []
