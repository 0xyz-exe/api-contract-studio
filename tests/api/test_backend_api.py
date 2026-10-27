import pytest
from starlette.testclient import TestClient
from apps.api.app.main import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_auth_and_project_lifecycle():
    # 1. Register User A
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "password123", "full_name": "Alice Dev"},
    )
    assert reg_res.status_code in (201, 400)  # 400 if already exists in local db

    # 2. Login User A
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert login_res.status_code == 200
    token_a = login_res.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 3. Create Project
    proj_res = client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={"name": "Alice Core API", "description": "Core services"},
    )
    assert proj_res.status_code == 201
    proj_data = proj_res.json()
    project_id = proj_data["id"]
    assert proj_data["name"] == "Alice Core API"

    # 4. Create Contract with initial revision
    yaml_content = """openapi: 3.0.0
info:
  title: Core Service
  version: 1.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: OK
"""
    contract_res = client.post(
        f"/api/v1/projects/{project_id}/contracts",
        headers=headers_a,
        json={
            "name": "Users Contract",
            "description": "User management API",
            "initial_content": yaml_content,
            "version": "1.0.0",
        },
    )
    assert contract_res.status_code == 201
    contract_data = contract_res.json()
    contract_id = contract_data["id"]
    assert contract_data["revisions_count"] == 1

    # 5. Add second revision
    rev2_content = yaml_content.replace("1.0.0", "1.1.0")
    rev_res = client.post(
        f"/api/v1/contracts/{contract_id}/revisions",
        headers=headers_a,
        json={"version": "1.1.0", "content": rev2_content, "summary": "Minor upgrade"},
    )
    assert rev_res.status_code == 201
    rev2_id = rev_res.json()["id"]

    # 6. Verify list revisions
    revs_res = client.get(f"/api/v1/contracts/{contract_id}/revisions", headers=headers_a)
    assert revs_res.status_code == 200
    revs = revs_res.json()
    assert len(revs) == 2

    # 7. Restore initial revision -> creates 3rd revision (immutable history preserved)
    init_rev_id = revs[-1]["id"]
    restore_res = client.post(
        f"/api/v1/contracts/{contract_id}/revisions/{init_rev_id}/restore",
        headers=headers_a,
    )
    assert restore_res.status_code == 200
    assert "restored" in restore_res.json()["version"]

    revs_after = client.get(f"/api/v1/contracts/{contract_id}/revisions", headers=headers_a).json()
    assert len(revs_after) == 3


def test_tenant_isolation():
    # Register user Bob
    client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "password": "password456", "full_name": "Bob Dev"},
    )
    token_bob = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "password456"},
    ).json()["access_token"]
    headers_bob = {"Authorization": f"Bearer {token_bob}"}

    # Bob tries to create project
    bob_proj = client.post(
        "/api/v1/projects",
        headers=headers_bob,
        json={"name": "Bob Project"},
    ).json()

    # Alice logs in
    token_alice = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    ).json()["access_token"]
    headers_alice = {"Authorization": f"Bearer {token_alice}"}

    # Alice tries to read Bob's project -> must be 404
    forbidden_res = client.get(f"/api/v1/projects/{bob_proj['id']}", headers=headers_alice)
    assert forbidden_res.status_code == 404


def test_api_spec_validation_and_comparison():
    valid_spec = """openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /ping:
    get:
      responses:
        '200':
          description: Pong
"""
    # 1. Validate spec
    val_res = client.post("/api/v1/contracts/validate", json={"content": valid_spec})
    assert val_res.status_code == 200
    assert val_res.json()["is_valid"] is True

    # 2. Compare baseline with breaking candidate
    broken_spec = valid_spec.replace("/ping:", "/pong:")
    comp_res = client.post(
        "/api/v1/contracts/compare",
        json={"baseline_content": valid_spec, "candidate_content": broken_spec},
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["summary"]["breaking_count"] > 0
    assert comp_data["summary"]["passed_policy"] is False
    assert comp_data["id"] is not None

    # 3. Read back comparison by ID
    comp_id = comp_data["id"]
    get_comp_res = client.get(f"/api/v1/comparisons/{comp_id}")
    assert get_comp_res.status_code == 200
    assert get_comp_res.json()["id"] == comp_id
