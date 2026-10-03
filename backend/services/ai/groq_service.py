import os
from groq import Groq
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


GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)


def get_groq_api_key():
    """Return the configured Groq API key."""
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None

    api_key = api_key.strip()

    return api_key if api_key else None


def get_client():
    """Create and return a Groq client."""
    api_key = get_groq_api_key()

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    return Groq(api_key=api_key)


def generate(prompt, model=None):
    """
    Generate a response using Groq.

    Existing app.py functionality remains unchanged.
    """

    if not prompt or not str(prompt).strip():
        raise ValueError("Prompt cannot be empty.")

    client = get_client()

    response = client.chat.completions.create(
        model=model or GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    if not response or not response.choices:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    text = response.choices[0].message.content

    if not text or not text.strip():
        raise RuntimeError(
            "Groq returned an empty response."
        )

    return text.strip()