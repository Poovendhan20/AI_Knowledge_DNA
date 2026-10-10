import os
import sys
import unittest
from unittest.mock import patch, MagicMock

tests_dir = os.path.dirname(os.path.abspath(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

from test_base import BaseTestCase
from services.ai.ai_router import (
    generate_ai_response,
    is_temporary_error,
    TASK_PROVIDER_MAP,
    FALLBACK_ORDER,
    SUPPORTED_PROVIDERS,
)
import app as app_module


class TestAIRouter(BaseTestCase):
    """
    Tests for AI routing, task-to-provider mappings, temporary error detection,
    fallback chains across Gemini, OpenRouter, and Groq, and voice answer cleaning.
    """

    def test_task_provider_mapping(self):
        """Core AI tasks route to appropriate specialized providers"""
        self.assertEqual(TASK_PROVIDER_MAP["document_analysis"], "gemini")
        self.assertEqual(TASK_PROVIDER_MAP["summary"], "gemini")
        self.assertEqual(TASK_PROVIDER_MAP["chat"], "groq")
        self.assertEqual(TASK_PROVIDER_MAP["voice"], "groq")
        self.assertEqual(TASK_PROVIDER_MAP["general"], "openrouter")

    def test_fallback_order_hierarchy(self):
        """Fallback chains must cover all 3 supported providers"""
        self.assertEqual(FALLBACK_ORDER["gemini"], ["gemini", "openrouter", "groq"])
        self.assertEqual(FALLBACK_ORDER["groq"], ["groq", "openrouter", "gemini"])
        self.assertEqual(FALLBACK_ORDER["openrouter"], ["openrouter", "groq", "gemini"])

    def test_temporary_error_detection(self):
        """is_temporary_error correctly identifies transient vs permanent failures"""
        self.assertTrue(is_temporary_error(Exception("429 Too Many Requests")))
        self.assertTrue(is_temporary_error(Exception("Rate limit reached for model")))
        self.assertTrue(is_temporary_error(Exception("Quota exceeded")))
        self.assertTrue(is_temporary_error(Exception("Connection timed out")))
        self.assertTrue(is_temporary_error(Exception("503 Service Unavailable")))
        self.assertTrue(is_temporary_error(Exception("Server overloaded")))

        # Permanent errors must NOT be marked temporary
        self.assertFalse(is_temporary_error(Exception("Invalid API key provided")))
        self.assertFalse(is_temporary_error(Exception("Model not found 404")))
        self.assertFalse(is_temporary_error(Exception("Content policy violation")))

    def test_input_validation(self):
        """Invalid task or empty prompt raises ValueError"""
        with self.assertRaises(ValueError):
            generate_ai_response(task="", prompt="Hello")
        with self.assertRaises(ValueError):
            generate_ai_response(task="chat", prompt="")
        with self.assertRaises(ValueError):
            generate_ai_response(task="chat", prompt="   ")
        with self.assertRaises(ValueError):
            generate_ai_response(task="chat", prompt="Hello", provider="unsupported_vendor")

    @patch("services.ai.ai_router._generate_with_provider")
    def test_primary_provider_success(self, mock_gen):
        """When primary provider succeeds, fallback is not used"""
        mock_gen.return_value = "This is a detailed analysis of the document."
        result = generate_ai_response(task="document_analysis", prompt="Explain mitochondria")

        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "gemini")
        self.assertFalse(result["fallback_used"])
        self.assertEqual(result["answer"], "This is a detailed analysis of the document.")
        mock_gen.assert_called_once()

    @patch("services.ai.ai_router._generate_with_provider")
    def test_fallback_on_rate_limit(self, mock_gen):
        """When primary provider hits rate limit, it falls back to the next provider"""
        # First call (gemini) fails with 429 rate limit, second call (openrouter) succeeds
        mock_gen.side_effect = [
            Exception("429 Resource Exhausted / Rate limit"),
            "Fallback answer from OpenRouter."
        ]

        result = generate_ai_response(task="document_analysis", prompt="Explain ribosomes")
        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "openrouter")
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["answer"], "Fallback answer from OpenRouter.")
        self.assertEqual(mock_gen.call_count, 2)

    @patch("services.ai.ai_router._generate_with_provider")
    def test_non_temporary_error_aborts_without_fallback(self, mock_gen):
        """Non-temporary errors immediately raise without triggering fallback cascade"""
        mock_gen.side_effect = Exception("Invalid API key")

        with self.assertRaises(Exception) as ctx:
            generate_ai_response(task="document_analysis", prompt="Explain osmosis")
        self.assertIn("Invalid API key", str(ctx.exception))
        mock_gen.assert_called_once()

    @patch("services.ai.ai_router._generate_with_provider")
    def test_all_providers_failing_raises_runtime_error(self, mock_gen):
        """When all providers in fallback sequence fail with temporary errors, raises RuntimeError"""
        mock_gen.side_effect = [
            Exception("503 Service Unavailable"),
            Exception("429 Rate Limit Exceeded"),
            Exception("Timeout connecting to Groq"),
        ]

        with self.assertRaises(RuntimeError) as ctx:
            generate_ai_response(task="document_analysis", prompt="Explain genetics")
        self.assertIn("All AI providers failed", str(ctx.exception))
        self.assertEqual(mock_gen.call_count, 3)

    def test_clean_voice_answer(self):
        """clean_voice_answer strips markdown headers, citations, and URLs for speech synthesis"""
        raw_answer = (
            "### Overview of Photosynthesis\n\n"
            "Photosynthesis is the process [Page 3] by which plants convert light energy.\n"
            "For more details visit https://example.edu/biology.\n\n"
            "Sources: Chapter 4 Biology\n"
            "References: Campbell Biology 11th edition"
        )
        cleaned = app_module.clean_voice_answer(raw_answer)

        self.assertNotIn("###", cleaned)
        self.assertNotIn("[Page 3]", cleaned)
        self.assertNotIn("https://example.edu", cleaned)
        self.assertNotIn("Sources:", cleaned)
        self.assertNotIn("References:", cleaned)
        self.assertIn("Photosynthesis is the process", cleaned)


if __name__ == "__main__":
    unittest.main()
