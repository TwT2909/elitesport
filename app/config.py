import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:424242@localhost:5432/fitness_club",
)

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-super-secret-key")
