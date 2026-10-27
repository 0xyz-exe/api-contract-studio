from api_contract_studio.comparator import compare_specs
from api_contract_studio.models import Compatibility, PolicyConfig, Severity
from api_contract_studio.parser import load_spec_file

def test_identical_contracts():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0"},
        "paths": {
            "/items": {
                "get": {
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    }
    report = compare_specs(spec, spec)
    assert report.summary.total_changes == 0
    assert report.summary.breaking_count == 0
    assert report.summary.passed_policy is True

def test_endpoint_and_method_removed():
    base = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "OK"}}},
                "delete": {"responses": {"204": {"description": "Deleted"}}},
            },
            "/orders": {
                "get": {"responses": {"200": {"description": "OK"}}}
            }
        }
    }
    cand = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "2.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "OK"}}},
            }
        }
    }
    report = compare_specs(base, cand)
    rule_ids = {f.rule_id for f in report.findings}
    assert "ACS-PATH-REMOVED" in rule_ids
    assert "ACS-METHOD-REMOVED" in rule_ids
    assert report.summary.breaking_count >= 2
    assert report.summary.passed_policy is False

def test_request_parameters_rules():
    base = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0"},
        "paths": {
            "/users": {
                "get": {
                    "parameters": [
                        {"name": "filter", "in": "query", "required": False, "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    }
    cand = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.1"},
        "paths": {
            "/users": {
                "get": {
                    "parameters": [
                        {"name": "filter", "in": "query", "required": False, "schema": {"type": "string"}},
                        {"name": "api_key", "in": "header", "required": True, "schema": {"type": "string"}},
                        {"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}},
                    ],
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    }
    report = compare_specs(base, cand)
    findings = {f.rule_id: f for f in report.findings}
    assert "ACS-REQ-PARAM-ADDED-REQUIRED" in findings
    assert findings["ACS-REQ-PARAM-ADDED-REQUIRED"].compatibility == Compatibility.BREAKING
    assert "ACS-REQ-PARAM-ADDED-OPTIONAL" in findings
    assert findings["ACS-REQ-PARAM-ADDED-OPTIONAL"].compatibility == Compatibility.NON_BREAKING

def test_response_property_removed_and_type_changed():
    base = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0"},
        "paths": {
            "/profile": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "email": {"type": "string"},
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    cand = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.1"},
        "paths": {
            "/profile": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},  # integer -> string (type changed)
                                            # email removed!
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    report = compare_specs(base, cand)
    findings = {f.rule_id: f for f in report.findings}
    assert "ACS-RESP-PROP-REMOVED" in findings
    assert findings["ACS-RESP-PROP-REMOVED"].compatibility == Compatibility.BREAKING
    assert "ACS-SCHEMA-TYPE-CHANGED" in findings
    assert findings["ACS-SCHEMA-TYPE-CHANGED"].compatibility == Compatibility.BREAKING

def test_enum_narrowing_rule():
    base = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0"},
        "paths": {
            "/status": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "string",
                                        "enum": ["active", "pending", "archived"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    cand = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.1"},
        "paths": {
            "/status": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "string",
                                        "enum": ["active", "pending"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    report = compare_specs(base, cand)
    findings = {f.rule_id: f for f in report.findings}
    assert "ACS-SCHEMA-ENUM-REMOVED" in findings

def test_petstore_examples_comparison():
    base = load_spec_file("contracts/examples/baseline_petstore.yaml")
    cand_breaking = load_spec_file("contracts/examples/candidate_breaking.yaml")
    cand_non_breaking = load_spec_file("contracts/examples/candidate_non_breaking.yaml")

    # Breaking candidate
    report_breaking = compare_specs(base, cand_breaking)
    assert report_breaking.summary.breaking_count > 0
    assert report_breaking.summary.passed_policy is False

    # Non-breaking candidate
    report_non_breaking = compare_specs(base, cand_non_breaking)
    assert report_non_breaking.summary.breaking_count == 0
    assert report_non_breaking.summary.passed_policy is True
