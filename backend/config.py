from dotenv import load_dotenv
import os

load_dotenv()

# Use environment variable for DATABASE_URL, with fallback to SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./nutritional.db"
)

# Heroku provides DATABASE_URL starting with 'postgres://' but SQLAlchemy needs 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1) 