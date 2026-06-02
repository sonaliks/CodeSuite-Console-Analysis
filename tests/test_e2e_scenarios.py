"""End-to-end integration tests for all three demo scenarios.

These tests require:
- Deployed CDK infrastructure (all 3 scenario stacks)
- AWS credentials with access to CodePipeline, CodeCommit, IAM, CloudWatch
- Amazon Bedrock access (Claude 3.5 Sonnet)

Run with: pytest tests/test_e2e_scenarios.py -v --run-e2e
"""

import sys
import os
import pytest
import httpx

# Skip all E2E tests unless --run-e2e flag is provided
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_E2E_TESTS"),
    reason="E2E tests require deployed infrastructure. Set RUN_E2E_TESTS=1 to run.",
)

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# Pipeline names from CDK stacks
SCENARIO1_PIPELINE = "codesuite-diag-scenario1-pipeline"
SCENARIO2_PIPELINE = "codesuite-diag-scenario2-pipeline"
SCENARIO3_PIPELINE = "codesuite-diag-scenario3-pipeline"


@pytest.fixture
def api_client():
    """Create an HTTP client for the backend API."""
    return httpx.Client(base_url=BACKEND_URL, timeout=120.0)


class TestAgentOrchestration:
    """Task 4.8: Test agent orchestration end-to-end against each seeded scenario."""

    def test_backend_health_check(self, api_client):
        """Backend should be running and healthy."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_list_pipelines(self, api_client):
        """Should list all three demo pipelines."""
        response = api_client.get("/api/pipelines")
        assert response.status_code == 200
        pipelines = response.json()
        assert len(pipelines) == 3

        names = [p["name"] for p in pipelines]
        assert SCENARIO1_PIPELINE in names
        assert SCENARIO2_PIPELINE in names
        assert SCENARIO3_PIPELINE in names

    def test_get_pipeline_detail(self, api_client):
        """Should return pipeline details for each scenario."""
        for pipeline_name in [SCENARIO1_PIPELINE, SCENARIO2_PIPELINE, SCENARIO3_PIPELINE]:
            response = api_client.get(f"/api/pipelines/{pipeline_name}")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == pipeline_name
            assert data["status"] == "Failed"


class TestScenario1Diagnosis:
    """Task 6.1: Trigger Scenario 1 diagnosis and verify Analysis Panel output.

    Scenario: Missing appspec.yml in CodeCommit repository.
    Expected: Agent identifies missing appspec.yml and recommends adding it.
    """

    def test_scenario1_diagnosis_returns_200(self, api_client):
        """Diagnosis endpoint should return successfully."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO1_PIPELINE}/executions/latest/diagnose"
        )
        assert response.status_code == 200

    def test_scenario1_root_cause_category(self, api_client):
        """Should classify as Configuration Issue."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO1_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        assert data["root_cause_category"] == "Configuration Issue"

    def test_scenario1_identifies_missing_appspec(self, api_client):
        """Should identify appspec.yml as the missing file."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO1_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        description = data["root_cause_description"].lower()
        assert "appspec" in description

    def test_scenario1_provides_fix_recommendation(self, api_client):
        """Should provide a recommended fix."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO1_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        assert len(data["recommended_fix"]) > 0
        # Should mention adding appspec.yml
        fix_lower = data["recommended_fix"].lower()
        assert "appspec" in fix_lower

    def test_scenario1_has_evidence(self, api_client):
        """Should include evidence from MCP tool calls."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO1_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        assert len(data["evidence"]) > 0


class TestScenario2Diagnosis:
    """Task 6.2: Trigger Scenario 2 diagnosis and verify Analysis Panel output.

    Scenario: Pipeline role missing codecommit:GitPull permission.
    Expected: Agent identifies the missing IAM permission and recommends the policy fix.
    """

    def test_scenario2_diagnosis_returns_200(self, api_client):
        """Diagnosis endpoint should return successfully."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO2_PIPELINE}/executions/latest/diagnose"
        )
        assert response.status_code == 200

    def test_scenario2_root_cause_category(self, api_client):
        """Should classify as Permission Issue."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO2_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        assert data["root_cause_category"] == "Permission Issue"

    def test_scenario2_identifies_missing_permission(self, api_client):
        """Should identify codecommit:GitPull as the missing permission."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO2_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        combined_text = (
            data["root_cause_description"] + data["recommended_fix"]
        ).lower()
        assert "gitpull" in combined_text or "git pull" in combined_text

    def test_scenario2_identifies_role(self, api_client):
        """Should identify the affected IAM role."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO2_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        # Should reference the pipeline role
        assert "role" in data["affected_resource"].lower() or "iam" in data["affected_resource"].lower()

    def test_scenario2_has_evidence(self, api_client):
        """Should include evidence from MCP tool calls."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO2_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        assert len(data["evidence"]) > 0


class TestScenario3Diagnosis:
    """Task 6.3: Trigger Scenario 3 diagnosis and verify Analysis Panel output.

    Scenario: LZA accounts-config.yaml references non-existent OU "Workloads-Production".
    Expected: Agent identifies the OU mismatch and suggests the correct name "Workloads-Prod".
    """

    def test_scenario3_diagnosis_returns_200(self, api_client):
        """Diagnosis endpoint should return successfully."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO3_PIPELINE}/executions/latest/diagnose"
        )
        assert response.status_code == 200

    def test_scenario3_root_cause_category(self, api_client):
        """Should classify as Infrastructure Issue."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO3_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        assert data["root_cause_category"] == "Infrastructure Issue"

    def test_scenario3_identifies_ou_mismatch(self, api_client):
        """Should identify the invalid OU name."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO3_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        combined_text = (
            data["root_cause_description"] + data["recommended_fix"]
        ).lower()
        # Should mention the invalid OU name or the correct one
        assert (
            "workloads-production" in combined_text
            or "workloads-prod" in combined_text
            or "organizational unit" in combined_text
            or "ou" in combined_text
        )

    def test_scenario3_references_config_file(self, api_client):
        """Should reference accounts-config.yaml."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO3_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        combined_text = (
            data["root_cause_description"] + data["recommended_fix"]
        ).lower()
        assert "accounts-config" in combined_text

    def test_scenario3_has_evidence(self, api_client):
        """Should include evidence from MCP tool calls."""
        response = api_client.post(
            f"/api/pipelines/{SCENARIO3_PIPELINE}/executions/latest/diagnose"
        )
        data = response.json()
        assert len(data["evidence"]) > 0
