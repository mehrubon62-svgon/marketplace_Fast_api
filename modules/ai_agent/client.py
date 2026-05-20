from openai import OpenAI
from config import CEREBRAS_API_KEY, CEREBRAS_BASE_URL


def get_ai_client() -> OpenAI:
    if not CEREBRAS_API_KEY:
        raise RuntimeError(
            "CEREBRAS_API_KEY is not set. Add it to .env file."
        )
    return OpenAI(
        base_url=CEREBRAS_BASE_URL,
        api_key=CEREBRAS_API_KEY,
    )
