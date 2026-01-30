"""
API Tests for ChatMode

Tests for authentication and agent CRUD endpoints.
Run with: pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from chatmode.main import app
from chatmode.database import Base, get_db
from chatmode.models import User
from chatmode.auth import hash_password
import uuid


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(setup_database):
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def test_user(setup_database):
    """Create a test admin user."""
    db = TestingSessionLocal()
    user = User(
        id=str(uuid.uuid4()),
        username="testadmin",
        email="admin@test.com",
        password_hash=hash_password("testpass123"),
        role="admin",
        enabled=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture(scope="module")
def auth_token(client, test_user):
    """Get authentication token for testing."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "testpass123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


# ============================================================================
# Authentication Tests
# ============================================================================

class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testadmin", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testadmin", "password": "wrongpass"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "anypass"}
        )
        assert response.status_code == 401
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/agents/")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/api/v1/agents/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


# ============================================================================
# Agent CRUD Tests
# ============================================================================

class TestAgentCRUD:
    """Test agent CRUD endpoints."""
    
    def test_list_agents_empty(self, client, auth_token):
        """Test listing agents when none exist."""
        response = client.get(
            "/api/v1/agents/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 0
    
    def test_create_agent(self, client, auth_token):
        """Test creating a new agent."""
        import uuid
        unique_name = f"test_agent_{uuid.uuid4().hex[:8]}"
        
        agent_data = {
            "name": unique_name,
            "display_name": "Test Agent",
            "model": "gpt-4o-mini",
            "provider": "openai",
            "system_prompt": "You are a helpful test agent.",
            "temperature": 0.7,
            "max_tokens": 512,
            "enabled": True
        }
        
        response = client.post(
            "/api/v1/agents/",
            json=agent_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == unique_name
        assert data["display_name"] == "Test Agent"
        assert "id" in data
        return data["id"]
    
    def test_create_duplicate_agent(self, client, auth_token):
        """Test creating agent with duplicate name."""
        agent_data = {
            "name": "test_agent",
            "display_name": "Duplicate",
            "model": "gpt-4o-mini",
            "provider": "openai",
            "system_prompt": "Test",
            "temperature": 0.7,
            "max_tokens": 512,
            "enabled": True
        }
        
        response = client.post(
            "/api/v1/agents/",
            json=agent_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 409  # Conflict
    
    def test_get_agent(self, client, auth_token):
        """Test getting a specific agent."""
        # First create an agent
        agent_id = self.test_create_agent(client, auth_token)
        
        response = client.get(
            f"/api/v1/agents/{agent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent_id
    
    def test_get_nonexistent_agent(self, client, auth_token):
        """Test getting a nonexistent agent."""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/agents/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404
    
    def test_update_agent(self, client, auth_token):
        """Test updating an agent."""
        # First create an agent
        agent_id = self.test_create_agent(client, auth_token)
        
        update_data = {
            "display_name": "Updated Test Agent",
            "temperature": 0.9
        }
        
        response = client.put(
            f"/api/v1/agents/{agent_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Test Agent"
        assert data["temperature"] == 0.9
    
    def test_delete_agent(self, client, auth_token):
        """Test deleting an agent."""
        # First create an agent
        agent_id = self.test_create_agent(client, auth_token)
        
        response = client.delete(
            f"/api/v1/agents/{agent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        
        # Verify agent is deleted
        response = client.get(
            f"/api/v1/agents/{agent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404


# ============================================================================
# Role-Based Access Control Tests
# ============================================================================

class TestRoleEnforcement:
    """Test role-based access control."""
    
    @pytest.fixture(scope="class")
    def viewer_user(self, setup_database):
        """Create a test viewer user."""
        db = TestingSessionLocal()
        user = User(
            id=str(uuid.uuid4()),
            username="testviewer",
            email="viewer@test.com",
            password_hash=hash_password("viewerpass"),
            role="viewer",
            enabled=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        return user
    
    @pytest.fixture(scope="class")
    def viewer_token(self, client, viewer_user):
        """Get authentication token for viewer."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testviewer", "password": "viewerpass"}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_viewer_can_list_agents(self, client, viewer_token):
        """Test that viewer can list agents."""
        response = client.get(
            "/api/v1/agents/",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        assert response.status_code == 200
    
    def test_viewer_cannot_create_agent(self, client, viewer_token):
        """Test that viewer cannot create agents."""
        agent_data = {
            "name": "forbidden_agent",
            "display_name": "Forbidden",
            "model": "gpt-4o-mini",
            "provider": "openai",
            "system_prompt": "Test",
            "temperature": 0.7,
            "max_tokens": 512,
            "enabled": True
        }
        
        response = client.post(
            "/api/v1/agents/",
            json=agent_data,
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        assert response.status_code == 403  # Forbidden


# ============================================================================
# Validation Tests
# ============================================================================

class TestValidation:
    """Test input validation."""
    
    def test_invalid_temperature(self, client, auth_token):
        """Test that invalid temperature is rejected."""
        agent_data = {
            "name": "invalid_temp",
            "display_name": "Invalid",
            "model": "gpt-4o-mini",
            "provider": "openai",
            "system_prompt": "Test",
            "temperature": 3.0,  # Invalid: > 2.0
            "max_tokens": 512,
            "enabled": True
        }
        
        response = client.post(
            "/api/v1/agents/",
            json=agent_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client, auth_token):
        """Test that missing required fields are rejected."""
        agent_data = {
            "name": "incomplete",
            # Missing required fields
        }
        
        response = client.post(
            "/api/v1/agents/",
            json=agent_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
