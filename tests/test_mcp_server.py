import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add parent directory to path so amritagpt_mcp_server can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "amritagpt_mcp_server"))
from mcp_server import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "AmritaGPT Document Intelligence API" in response.json()["message"]

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "directory_accessible" in data
