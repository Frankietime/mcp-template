"""Shared pytest fixtures and configuration."""

import pytest


@pytest.fixture
def sample_resource_data() -> dict:
    """A minimal resource data dict for testing response builders."""
    return {
        "id": 1928,
        "name": "Test Resource",
        "status": "active",
        "tags": ["tag1", "tag2"],
        "metadata": {},
    }
