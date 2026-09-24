import os

from dotenv import load_dotenv
from google import genai


# Load variables from backend/.env
load_dotenv()


GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash"
)


def get_gemini_api_key():
    """
    Get the Gemini API key from the environment.

    Returns:
        str: Gemini API key

    Raises:
        RuntimeError: If the API key is not configured.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Please add GEMINI_API_KEY to the backend .env file."
        )

    return api_key.strip()


def get_gemini_client():
    """
    Create and return a Gemini client using the
    API key stored in the environment.
    """

    api_key = get_gemini_api_key()

    return genai.Client(
        api_key=api_key
    )


def get_gemini_model():
    """
    Return the configured Gemini model name.
    """

    return GEMINI_MODEL


def is_gemini_configured():
    """
    Check whether the Gemini API key exists.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    return bool(
        api_key and api_key.strip()
    )


def generate_text(prompt):
    """
    Send a prompt to Gemini and return the response text.
    """

    client = get_gemini_client()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return response.text or ""