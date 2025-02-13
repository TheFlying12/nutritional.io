import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")