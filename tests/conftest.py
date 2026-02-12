import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "unit: fast tests with mocks")
    config.addinivalue_line("markers", "integration: tests requiring Redis/API/ChromaDB")
