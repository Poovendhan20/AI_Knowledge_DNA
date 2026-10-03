import os
from google import genai
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


GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash"
)


def get_gemini_api_key():
    """Return the configured Gemini API key."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    api_key = api_key.strip()

    return api_key if api_key else None


def get_client():
    """Create and return a Gemini client."""
    api_key = get_gemini_api_key()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(api_key=api_key)


def generate(prompt, model=None):
    """
    Generate a response using Gemini.

    This is a simple provider wrapper.
    Existing Gemini/RAG logic in app.py remains unchanged.
    """

    if not prompt or not str(prompt).strip():
        raise ValueError("Prompt cannot be empty.")

    client = get_client()

    response = client.models.generate_content(
        model=model or GEMINI_MODEL,
        contents=prompt
    )

    text = response.text if response else ""

    if not text or not text.strip():
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return text.strip()