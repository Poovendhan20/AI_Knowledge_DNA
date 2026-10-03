import os
import logging
import time

from dotenv import load_dotenv

from . import gemini_service
from . import groq_service
from . import openrouter_service


# Load backend/.env
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

load_dotenv(os.path.join(BASE_DIR, ".env"))


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Default provider
# ---------------------------------------------------------

DEFAULT_PROVIDER = os.getenv(
    "AI_DEFAULT_PROVIDER",
    "gemini"
).strip().lower()


# ---------------------------------------------------------
# Task-based routing
# ---------------------------------------------------------

TASK_PROVIDER_MAP = {
    "document_analysis": "gemini",
    "knowledge_extraction": "gemini",
    "summary": "gemini",
    "embedding": "gemini",

    "chat": "groq",
    "voice": "groq",
    "fast_response": "groq",
    "quick_quiz": "groq",

    "general": "openrouter",
    "model_testing": "openrouter",
}


# ---------------------------------------------------------
# Fallback order
# ---------------------------------------------------------

FALLBACK_ORDER = {
    "gemini": ["gemini", "openrouter", "groq"],
    "groq": ["groq", "openrouter", "gemini"],
    "openrouter": ["openrouter", "groq", "gemini"],
}


# ---------------------------------------------------------
# Supported providers
# ---------------------------------------------------------

SUPPORTED_PROVIDERS = {
    "gemini",
    "groq",
    "openrouter",
}


# ---------------------------------------------------------
# Temporary error detection
# ---------------------------------------------------------

def is_temporary_error(error):
    """
    Determine whether an error is temporary and should
    allow fallback to another AI provider.
    """

    message = str(error).lower()

    temporary_keywords = [
        "429",
        "rate limit",
        "rate_limit",
        "quota",
        "resource exhausted",
        "timeout",
        "timed out",
        "temporarily unavailable",
        "service unavailable",
        "connection reset",
        "connection error",
        "503",
        "502",
        "500",
        "overloaded",
    ]

    return any(
        keyword in message
        for keyword in temporary_keywords
    )


# ---------------------------------------------------------
# Provider generator
# ---------------------------------------------------------

def _generate_with_provider(
    provider,
    prompt,
    model=None
):
    """
    Send the prompt to the selected provider.
    """

    if provider == "gemini":
        answer = gemini_service.generate(
            prompt,
            model=model
        )

    elif provider == "groq":
        answer = groq_service.generate(
            prompt,
            model=model
        )

    elif provider == "openrouter":
        answer = openrouter_service.generate(
            prompt,
            model=model
        )

    else:
        raise ValueError(
            f"Unsupported AI provider: {provider}"
        )

    return answer


# ---------------------------------------------------------
# Main AI Router
# ---------------------------------------------------------

def generate_ai_response(
    task,
    prompt,
    context=None,
    provider=None,
    model=None
):
    """
    Central AI generation function.

    Parameters:
        task:
            Type of AI task.

        prompt:
            User/system prompt.

        context:
            Optional additional context.

        provider:
            Optional explicit provider override.

        model:
            Optional model override.

    Returns:
        {
            "success": True,
            "provider": "...",
            "model": "...",
            "answer": "...",
            "fallback_used": False
        }
    """

    if not task:
        raise ValueError("AI task is required.")

    if not prompt or not str(prompt).strip():
        raise ValueError("AI prompt cannot be empty.")

    task = str(task).strip().lower()

    # -----------------------------------------------------
    # Determine provider
    # -----------------------------------------------------

    if provider:
        selected_provider = str(
            provider
        ).strip().lower()

    else:
        selected_provider = TASK_PROVIDER_MAP.get(
            task,
            DEFAULT_PROVIDER
        )

    if selected_provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported AI provider: {selected_provider}"
        )

    # -----------------------------------------------------
    # Build final prompt
    # -----------------------------------------------------

    final_prompt = str(prompt)

    if context:
        final_prompt = (
            f"{prompt}\n\n"
            f"Additional context:\n"
            f"{context}"
        )

    # -----------------------------------------------------
    # Provider sequence
    # -----------------------------------------------------

    provider_sequence = FALLBACK_ORDER[
        selected_provider
    ]

    last_error = None
    fallback_used = False

    # -----------------------------------------------------
    # Try providers
    # -----------------------------------------------------

    for index, current_provider in enumerate(
        provider_sequence
    ):

        # Never retry a provider more than once
        try:
            start_time = time.time()

            answer = _generate_with_provider(
                current_provider,
                final_prompt,
                model=model
            )

            response_time = round(
                time.time() - start_time,
                3
            )

            actual_model = model or {
                "gemini": os.getenv(
                    "GEMINI_MODEL",
                    "gemini-3.5-flash"
                ),
                "groq": os.getenv(
                    "GROQ_MODEL",
                    "openai/gpt-oss-20b"
                ),
                "openrouter": os.getenv(
                    "OPENROUTER_MODEL",
                    "openai/gpt-6-luna"
                ),
            }[current_provider]

            logger.info(
                "AI request successful | "
                "task=%s provider=%s model=%s "
                "response_time=%ss fallback=%s",
                task,
                current_provider,
                actual_model,
                response_time,
                fallback_used
            )

            return {
                "success": True,
                "provider": current_provider,
                "model": actual_model,
                "answer": answer,
                "fallback_used": fallback_used,
                "response_time": response_time,
            }

        except Exception as error:

            last_error = error

            logger.warning(
                "AI provider failed | "
                "task=%s provider=%s error_type=%s",
                task,
                current_provider,
                type(error).__name__
            )

            # -------------------------------------------------
            # Only temporary errors allow fallback
            # -------------------------------------------------

            if not is_temporary_error(error):

                raise error

            # If another provider exists, continue
            if index < len(provider_sequence) - 1:

                fallback_used = True

                logger.warning(
                    "Falling back | "
                    "from=%s to=%s task=%s",
                    current_provider,
                    provider_sequence[index + 1],
                    task
                )

                continue

    # -----------------------------------------------------
    # All providers failed
    # -----------------------------------------------------

    raise RuntimeError(
        f"All AI providers failed. Last error: {last_error}"
    ) from last_error