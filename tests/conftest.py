"""Configuration for pytest."""


def pytest_configure(config):
    """Register custom marks for pytest."""
    config.addinivalue_line("markers", "asyncio: mark a test as an asyncio coroutine")
