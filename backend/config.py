from dotenv import load_dotenv
import os

load_dotenv()

# Use SQLite by default for development
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./nutritional.db"  # This creates a file named nutritional.db in your project
) 