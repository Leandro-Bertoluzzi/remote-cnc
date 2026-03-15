"""Shared DB setup for API tests.

Extracted from conftest.py to avoid name collision with the core test conftest
when both 'tests/' and 'api/tests/' are on pythonpath.
"""

from core.database.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Authorized users
test_user = User(
    "User", "user@test.com", "$2b$12$4kHVTQCMgWieAvSHUTWFVu11gAY0wXb1SDWtuAbiV2L9hITuxBQxy", "user"
)
test_admin = User(
    "Admin",
    "admin@test.com",
    "$2b$12$4kHVTQCMgWieAvSHUTWFVu11gAY0wXb1SDWtuAbiV2L9hITuxBQxy",
    "admin",
)


# Fake DB session, with a containerized test DB
# In local development: TEST_DB_URL = "postgresql+psycopg2://test:test@localhost:5000/cnc_db"
# In Docker: TEST_DB_URL = "postgresql+psycopg2://test:test@testdb:5432/cnc_db"
TEST_DB_URL = "postgresql+psycopg2://test:test@testdb:5432/cnc_db"
engine = create_engine(TEST_DB_URL)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
