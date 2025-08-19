import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Settings:
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 4096
    DEBUG: bool = False