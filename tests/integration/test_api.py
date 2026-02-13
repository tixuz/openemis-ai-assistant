"""
Integration Tests for API Endpoints

NOTE: These tests require the LLM server to be running.
Start it with: ./start_ai.sh
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


class TestAuthenticationAPI:
    """Test authentication endpoints"""

    def test_login_success(self):
        """Should login with correct credentials"""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        """Should reject invalid credentials"""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrong"}
        )
        assert response.status_code == 401

    def test_get_current_user_with_token(self):
        """Should get user info with valid token"""
        # First login
        login_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        # Then get user info
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    def test_get_current_user_without_token(self):
        """Should reject request without token"""
        response = client.get("/auth/me")
        assert response.status_code == 403  # No auth header


class TestAutomationAPI:
    """Test automation endpoints"""

    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        return response.json()["access_token"]

    def test_execute_automation_without_auth(self):
        """Should reject automation without auth"""
        response = client.post(
            "/automation/execute",
            json={
                "task_description": "test task",
                "auto_execute": False
            }
        )
        assert response.status_code == 403

    @pytest.mark.skip(reason="Requires LLM server running")
    def test_execute_automation_with_auth(self, auth_token):
        """Should execute automation with valid auth"""
        response = client.post(
            "/automation/execute",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "task_description": "Navigate to OpenEMIS homepage",
                "auto_execute": False
            }
        )
        # May fail if LLM not running, but should not be auth error
        assert response.status_code != 403


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_endpoint(self):
        """Should return health status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "llm_available" in data


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_endpoint(self):
        """Should return API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "features" in data
