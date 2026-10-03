import os
from openai import OpenAI
from dotenv import load_dotenv


# Load backend/.env
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

load_dotenv(os.path.join(BASE_DIR, ".env"))


OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-6-luna"
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_openrouter_api_key():
    """Return the configured OpenRouter API key."""
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return None

    api_key = api_key.strip()

    return api_key if api_key else None


def get_client():
    """Create and return an OpenRouter client."""
    api_key = get_openrouter_api_key()

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    return OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL
    )


def generate(prompt, model=None):
    """
    Generate a response using OpenRouter.

    Existing app.py functionality remains unchanged.
    """

    if not prompt or not str(prompt).strip():
        raise ValueError("Prompt cannot be empty.")

    client = get_client()

    response = client.chat.completions.create(
        model=model or OPENROUTER_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    if not response or not response.choices:
        raise RuntimeError(
            "OpenRouter returned an empty response."
        )

    text = response.choices[0].message.content

    if not text or not text.strip():
        raise RuntimeError(
            "OpenRouter returned an empty response."
        )

    return text.strip()