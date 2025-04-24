from dotenv import load_dotenv
import os

load_dotenv()
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")