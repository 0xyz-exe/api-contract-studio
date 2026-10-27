import textwrap
import pytest
from api_contract_studio.parser import (
    SpecParseError,
    SpecRefError,
    parse_spec_content,
    resolve_local_ref,
    dereference_spec,
)

def test_parse_valid_yaml():
    yaml_text = textwrap.dedent("""
    openapi: 3.0.0
    info:
      title: Test
      version: 1.0.0
    paths: {}
    """)
    doc = parse_spec_content(yaml_text)
    assert doc["openapi"] == "3.0.0"
    assert doc["info"]["title"] == "Test"

def test_parse_valid_json():
    json_text = '{"openapi": "3.1.0", "info": {"title": "Test JSON", "version": "1.0.0"}, "paths": {}}'
    doc = parse_spec_content(json_text)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "Test JSON"

def test_parse_empty_content():
    with pytest.raises(SpecParseError):
        parse_spec_content("   ")

def test_resolve_local_ref_success():
    doc = {
        "components": {
            "schemas": {
                "User": {"type": "object", "properties": {"id": {"type": "string"}}}
            }
        }
    }
    resolved = resolve_local_ref("#/components/schemas/User", doc)
    assert resolved["type"] == "object"
    assert "id" in resolved["properties"]

def test_resolve_external_ref_rejected():
    doc = {}
    with pytest.raises(SpecRefError):
        resolve_local_ref("https://example.com/schema.json", doc)

def test_circular_ref_prevention():
    doc = {
        "components": {
            "schemas": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "parent": {"$ref": "#/components/schemas/Node"}
                    }
                }
            }
        }
    }
    derefed = dereference_spec(doc)
    # The parent property's nested parent should hit circular reference detection
    nested = derefed["components"]["schemas"]["Node"]["properties"]["parent"]["properties"]["parent"]
    assert nested.get("x-circular-ref") == "#/components/schemas/Node"
