"""
Root-level conftest: set DATABASE_URL to SQLite *before* any app module is imported.
This ensures tests never try to connect to a real PostgreSQL instance.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_buy_service.db")
