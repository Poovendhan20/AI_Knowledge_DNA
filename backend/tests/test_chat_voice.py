import os
import sys
import unittest
from unittest.mock import patch

tests_dir = os.path.dirname(os.path.abspath(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

from test_base import BaseTestCase
import app as app_module


class TestChatVoice(BaseTestCase):
    """
    Tests for AI Chat, document-grounded RAG, source citation extraction,
    voice responses, and multi-tenant access control for AI conversations.
    """

    def setUp(self):
        super().setUp()
        self.user_a = self.create_user(name="Alice", email="alice@chat.edu")
        self.user_b = self.create_user(name="Bob", email="bob@chat.edu")
        self.headers_a = self.auth_headers(self.user_a["id"])
        self.headers_b = self.auth_headers(self.user_b["id"])

        # Create a document belonging to User A
        self.doc_a = {
            "id": "doc_alice_123",
            "name": "Neuroscience_Ch1.pdf",
            "user_id": self.user_a["id"],
            "stored_name": "doc_alice_123.pdf",
            "pages": [
                {"page": 1, "text": "Neurons transmit electrical signals using action potentials."},
                {"page": 2, "text": "Synaptic transmission involves neurotransmitters like dopamine and serotonin."}
            ],
            "topics": [{"name": "Neurons", "page": 1}, {"name": "Synapses", "page": 2}],
            "word_count": 20
        }
        all_docs = app_module.load_documents()
        all_docs.append(self.doc_a)
        app_module.save_documents(all_docs)

    def test_chat_missing_document_id(self):
        """POST /api/chat requires document_id"""
        res = self.client.post(
            "/api/chat",
            headers=self.headers_a,
            json={"question": "What are neurons?"}
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("document_id is required", data.get("message", ""))

    def test_chat_missing_question(self):
        """POST /api/chat requires question"""
        res = self.client.post(
            "/api/chat",
            headers=self.headers_a,
            json={"document_id": "doc_alice_123", "question": ""}
        )
        self.assertEqual(res.status_code, 400)

    def test_chat_cross_user_isolation(self):
        """User B cannot chat with User A's document"""
        res = self.client.post(
            "/api/chat",
            headers=self.headers_b,
            json={"document_id": "doc_alice_123", "question": "Explain neurotransmitters"}
        )
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("access denied", data.get("message", "").lower())

    @patch("app.generate_ai_response")
    def test_chat_success_with_grounding_and_citations(self, mock_ai):
        """User A can chat with their document, receiving answer with cited sources"""
        mock_ai.return_value = {
            "success": True,
            "provider": "gemini",
            "model": "gemini-3.5-flash",
            "answer": "Action potentials are electrical impulses [Page 1]. Dopamine is a neurotransmitter [Page 2].",
            "fallback_used": False
        }

        res = self.client.post(
            "/api/chat",
            headers=self.headers_a,
            json={
                "document_id": "doc_alice_123",
                "question": "How do neurons communicate?"
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("Action potentials", data["answer"])
        self.assertEqual(data["document_id"], "doc_alice_123")
        source_pages = [s.get("page") for s in data.get("sources", [])]
        self.assertIn(1, source_pages)

    @patch("app.generate_ai_response")
    def test_document_specific_chat_endpoint(self, mock_ai):
        """POST /api/documents/<document_id>/chat also routes correctly"""
        mock_ai.return_value = {
            "success": True,
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "answer": "Synapses connect neurons together [Page 2].",
            "fallback_used": False
        }

        res = self.client.post(
            f"/api/documents/{self.doc_a['id']}/chat",
            headers=self.headers_a,
            json={"question": "What is a synapse?"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("Synapses connect", data["answer"])

    @patch("app.generate_ai_response")
    def test_voice_response_cleans_citation_tags(self, mock_ai):
        """When voice_response is True, speech-friendly answer removes [Page X] tags"""
        mock_ai.return_value = {
            "success": True,
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "answer": "Neurotransmitters are chemical messengers [Page 2].",
            "fallback_used": False
        }

        res = self.client.post(
            "/api/chat",
            headers=self.headers_a,
            json={
                "document_id": "doc_alice_123",
                "question": "What are neurotransmitters?",
                "voice_response": True
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        # In voice mode, [Page 2] citation brackets should be stripped from answer
        self.assertNotIn("[Page 2]", data["answer"])


if __name__ == "__main__":
    unittest.main()
