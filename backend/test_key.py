from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()

print(os.getenv("OPENAI_KEY"))

try:
    response = client.chat.completions.create(model="gpt-4o-mini",
    messages=[{"role": "system", "content": "Say hello"}])
    print(response)
except Exception as e:
    print("Error:", e)
