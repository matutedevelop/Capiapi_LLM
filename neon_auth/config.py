import os
from dotenv import load_dotenv

load_dotenv()

NEON_AUTH_URL = os.getenv("NEON_AUTH_URL")
NEON_DATA_API_URL = os.getenv("NEON_DATA_API_URL")
NEON_API_KEY = os.getenv("NEON_API_KEY")
TEST_EMAIL = os.getenv("TEST_EMAIL")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")