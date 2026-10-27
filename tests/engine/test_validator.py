from api_contract_studio.validator import validate_openapi_spec
from api_contract_studio.models import Severity

def test_validator_valid_spec():
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "Valid API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "OK"}
                    }
                }
            }
        }
    }
    res = validate_openapi_spec(doc)
    assert res.is_valid is True
    assert res.title == "Valid API"
    assert len(res.issues) == 0

def test_validator_missing_version_and_info():
    doc = {"paths": {}}
    res = validate_openapi_spec(doc)
    assert res.is_valid is False
    assert any("openapi" in i.location for i in res.issues)
    assert any("info" in i.location for i in res.issues)

def test_validator_path_slash_validation():
    doc = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "invalid-path": {
                "get": {
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    }
    res = validate_openapi_spec(doc)
    assert any("must begin with a forward slash" in i.message for i in res.issues)

def test_validator_broken_reference():
    doc = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/NonExistent"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    res = validate_openapi_spec(doc)
    assert any("Broken reference" in i.message for i in res.issues)
