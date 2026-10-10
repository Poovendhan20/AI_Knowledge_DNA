import os
import sys
import io
import json
import unittest
from unittest.mock import patch, MagicMock
import docx

tests_dir = os.path.dirname(os.path.abspath(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

from test_base import BaseTestCase
import app as app_module


class TestE2EWorkflow(BaseTestCase):
    """
    Complete end-to-end integration workflow test:
    Simulates the entire student lifecycle from registration through document study,
    AI Q&A, quiz generation, submission, learning progress tracking, dashboard stats,
    and multi-tenant isolation.
    """

    def _create_sample_docx(self, text):
        doc = docx.Document()
        doc.add_paragraph(text)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf

    @patch("app.get_gemini_client")
    @patch("app.generate_ai_response")
    def test_complete_student_learning_journey(self, mock_ai_router, mock_gemini_getter):
        # ---------------------------------------------------------
        # Mock AI responses
        # ---------------------------------------------------------
        mock_ai_router.return_value = {
            "success": True,
            "provider": "gemini",
            "model": "gemini-3.5-flash",
            "answer": "The OSI model consists of 7 layers including Physical and Data Link [Page 1].",
            "fallback_used": False
        }

        mock_gemini = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "questions": [
                {
                    "question": "How many layers are in the OSI model?",
                    "options": ["4 layers", "5 layers", "7 layers", "9 layers"],
                    "correct_answer": 2,
                    "explanation": "The OSI model has 7 distinct layers.",
                    "topic": "OSI Architecture",
                    "difficulty": "medium",
                    "page": 1
                }
            ]
        })
        mock_gemini.models.generate_content.return_value = mock_response
        mock_gemini_getter.return_value = mock_gemini

        # ---------------------------------------------------------
        # Step 1: Student Registration
        # ---------------------------------------------------------
        reg_res = self.client.post(
            "/api/auth/register",
            json={
                "name": "Sarah Connor",
                "email": "sarah@cyberdyne.edu",
                "password": "resistance2026"
            }
        )
        self.assertEqual(reg_res.status_code, 201)
        token = reg_res.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # ---------------------------------------------------------
        # Step 2: Student Login
        # ---------------------------------------------------------
        login_res = self.client.post(
            "/api/auth/login",
            json={"email": "sarah@cyberdyne.edu", "password": "resistance2026"}
        )
        self.assertEqual(login_res.status_code, 200)

        # ---------------------------------------------------------
        # Step 3: Identity Verification (/api/auth/me)
        # ---------------------------------------------------------
        me_res = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.get_json()["user"]["name"], "Sarah Connor")

        # ---------------------------------------------------------
        # Step 4: Create Subject
        # ---------------------------------------------------------
        subj_res = self.client.post(
            "/api/subjects",
            headers=headers,
            json={"name": "Computer Networks", "description": "OSI model, TCP/IP, routing"}
        )
        self.assertEqual(subj_res.status_code, 201)
        subject_id = subj_res.get_json()["subject"]["id"]

        # ---------------------------------------------------------
        # Step 5: Upload Document
        # ---------------------------------------------------------
        docx_file = self._create_sample_docx(
            "The OSI Model defines 7 layers of telecommunication protocols: Physical, Data Link, Network, Transport, Session, Presentation, Application."
        )
        data = {"file": (docx_file, "OSI_Reference_Model.docx")}
        upload_res = self.client.post(
            "/api/upload",
            headers={"Authorization": f"Bearer {token}"},
            content_type="multipart/form-data",
            data=data
        )
        self.assertEqual(upload_res.status_code, 201)
        doc_data = upload_res.get_json()["document"]
        document_id = doc_data["id"]

        # Link document to subject in storage
        docs = app_module.load_documents()
        for d in docs:
            if d.get("id") == document_id:
                d["subject_id"] = subject_id
        app_module.save_documents(docs)

        # ---------------------------------------------------------
        # Step 6: Verify Subject has Document Count == 1
        # ---------------------------------------------------------
        subjects_res = self.client.get("/api/subjects", headers=headers)
        self.assertEqual(subjects_res.status_code, 200)
        subjs = subjects_res.get_json()["subjects"]
        self.assertEqual(len(subjs), 1)
        self.assertEqual(subjs[0]["document_count"], 1)

        # ---------------------------------------------------------
        # Step 7: Document Chat (RAG)
        # ---------------------------------------------------------
        chat_res = self.client.post(
            "/api/chat",
            headers=headers,
            json={"document_id": document_id, "question": "What are the OSI layers?"}
        )
        self.assertEqual(chat_res.status_code, 200)
        self.assertTrue(chat_res.get_json()["success"])
        self.assertIn("OSI model consists of 7 layers", chat_res.get_json()["answer"])

        # ---------------------------------------------------------
        # Step 8: Voice Chat
        # ---------------------------------------------------------
        voice_res = self.client.post(
            "/api/chat",
            headers=headers,
            json={"document_id": document_id, "question": "Summarize OSI", "voice_response": True}
        )
        self.assertEqual(voice_res.status_code, 200)
        self.assertNotIn("[Page 1]", voice_res.get_json()["answer"])

        # ---------------------------------------------------------
        # Step 9: Quiz Generation
        # ---------------------------------------------------------
        quiz_gen_res = self.client.post(
            "/api/quiz/generate",
            headers=headers,
            json={"subject_id": subject_id, "question_count": 5}
        )
        self.assertEqual(quiz_gen_res.status_code, 200)
        quiz_data = quiz_gen_res.get_json()["quiz"]
        quiz_id = quiz_data["id"]
        q_id = quiz_data["questions"][0]["id"]

        # ---------------------------------------------------------
        # Step 10: Quiz Submission
        # ---------------------------------------------------------
        submit_res = self.client.post(
            f"/api/quiz/{quiz_id}/submit",
            headers=headers,
            json={"answers": {q_id: 2}} # option 2 is correct
        )
        self.assertEqual(submit_res.status_code, 200)
        submit_data = submit_res.get_json()
        self.assertEqual(submit_data["score"], 1)
        self.assertEqual(submit_data["accuracy"], 100.0)

        # ---------------------------------------------------------
        # Step 11: Record Study Session
        # ---------------------------------------------------------
        session_res = self.client.post(
            "/api/learning/session",
            headers=headers,
            json={"topic": "OSI Architecture", "study_minutes": 60}
        )
        self.assertEqual(session_res.status_code, 201)
        self.assertEqual(session_res.get_json()["study_hours"], 1.0)

        # ---------------------------------------------------------
        # Step 12: Learning Progress & Insights
        # ---------------------------------------------------------
        prog_res = self.client.get("/api/learning/progress", headers=headers)
        self.assertEqual(prog_res.status_code, 200)
        self.assertGreaterEqual(len(prog_res.get_json()["progress"]), 1)

        insights_res = self.client.get("/api/learning/insights", headers=headers)
        self.assertEqual(insights_res.status_code, 200)
        self.assertTrue(insights_res.get_json()["success"])

        # ---------------------------------------------------------
        # Step 13: Dashboard Statistics
        # ---------------------------------------------------------
        dash_res = self.client.get("/api/dashboard/stats", headers=headers)
        self.assertEqual(dash_res.status_code, 200)
        stats = dash_res.get_json()["stats"]
        self.assertEqual(stats["quiz_accuracy"], 100.0)
        self.assertEqual(stats["study_hours"], 1.0)
        self.assertGreaterEqual(stats["knowledge_dna"], 1)

        # ---------------------------------------------------------
        # Step 14: Multi-Tenant Isolation Protection
        # ---------------------------------------------------------
        # Register a second student
        reg_b = self.client.post(
            "/api/auth/register",
            json={"name": "Attacker / Observer", "email": "other@student.edu", "password": "password123"}
        )
        headers_b = {"Authorization": f"Bearer {reg_b.get_json()['token']}", "Content-Type": "application/json"}

        # Observer cannot see Sarah's subjects
        subj_b = self.client.get("/api/subjects", headers=headers_b)
        self.assertEqual(len(subj_b.get_json()["subjects"]), 0)

        # Observer cannot access Sarah's document
        doc_b = self.client.get(f"/api/documents/{document_id}", headers=headers_b)
        self.assertEqual(doc_b.status_code, 404)

        # Observer cannot chat with Sarah's document
        chat_b = self.client.post(
            "/api/chat",
            headers=headers_b,
            json={"document_id": document_id, "question": "Leak data"}
        )
        self.assertEqual(chat_b.status_code, 403)

        # Observer has 0 study hours and 0 quiz stats
        dash_b = self.client.get("/api/dashboard/stats", headers=headers_b)
        stats_b = dash_b.get_json()["stats"]
        self.assertEqual(stats_b["study_hours"], 0.0)
        self.assertEqual(stats_b["quiz_accuracy"], 0.0)


if __name__ == "__main__":
    unittest.main()
