import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

tests_dir = os.path.dirname(os.path.abspath(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

from test_base import BaseTestCase
from models import db, LearningProgress
import app as app_module


class TestQuizzesLearning(BaseTestCase):
    """
    Tests for Quiz generation, answer submission, scoring accuracy,
    LearningProgress database tracking, study session recording,
    personalized learning insights, and dashboard statistics.
    """

    def setUp(self):
        super().setUp()
        self.user_a = self.create_user(name="Alice", email="alice@learning.edu")
        self.user_b = self.create_user(name="Bob", email="bob@learning.edu")
        self.headers_a = self.auth_headers(self.user_a["id"])
        self.headers_b = self.auth_headers(self.user_b["id"])

        # Create Subject for User A
        self.subject_a = {
            "id": "subj_alice_1",
            "name": "Biochemistry",
            "description": "Chemical processes within living organisms",
            "user_id": self.user_a["id"],
            "created_at": "2026-01-01 12:00:00"
        }
        all_subjects = app_module.load_subjects()
        all_subjects.append(self.subject_a)
        app_module.save_subjects(all_subjects)

        # Create Document for User A attached to Subject A
        self.doc_a = {
            "id": "doc_alice_1",
            "name": "Enzymes.pdf",
            "user_id": self.user_a["id"],
            "subject_id": self.subject_a["id"],
            "stored_name": "doc_alice_1.pdf",
            "pages": [
                {"page": 1, "text": "Enzymes act as biological catalysts to accelerate metabolic reactions."},
                {"page": 2, "text": "Substrates bind to the enzyme active site forming an enzyme-substrate complex."}
            ],
            "topics": [{"name": "Enzymes", "page": 1}, {"name": "Catalysis", "page": 2}],
            "word_count": 25
        }
        all_docs = app_module.load_documents()
        all_docs.append(self.doc_a)
        app_module.save_documents(all_docs)

    def test_generate_quiz_missing_or_unowned_subject(self):
        """Quiz generation requires a valid subject owned by the authenticated user"""
        # Missing subject_id
        res1 = self.client.post("/api/quiz/generate", headers=self.headers_a, json={})
        self.assertEqual(res1.status_code, 400)

        # User B cannot generate quiz for User A's subject
        res2 = self.client.post("/api/quiz/generate", headers=self.headers_b, json={"subject_id": "subj_alice_1"})
        self.assertEqual(res2.status_code, 404)

    @patch("app.get_gemini_client")
    def test_generate_quiz_success(self, mock_client_getter):
        """Quiz generation creates questions, hides answers in client response, and persists quiz"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "questions": [
                {
                    "question": "What is the primary function of an enzyme?",
                    "options": ["Slow reactions", "Catalyze reactions", "Store fat", "Form DNA"],
                    "correct_answer": 1,
                    "explanation": "Enzymes act as biological catalysts.",
                    "topic": "Enzymes",
                    "difficulty": "medium",
                    "page": 1
                },
                {
                    "question": "Where does a substrate bind on an enzyme?",
                    "options": ["Ribosome", "Active site", "Mitochondria", "Lipid bilayer"],
                    "correct_answer": 1,
                    "explanation": "Substrates bind to the active site.",
                    "topic": "Enzymes",
                    "difficulty": "medium",
                    "page": 2
                }
            ]
        })
        mock_client.models.generate_content.return_value = mock_response
        mock_client_getter.return_value = mock_client

        res = self.client.post(
            "/api/quiz/generate",
            headers=self.headers_a,
            json={"subject_id": "subj_alice_1", "question_count": 5}
        )
        self.assertIn(res.status_code, [200, 201])
        data = res.get_json()
        self.assertTrue(data.get("success"))
        quiz = data.get("quiz")
        self.assertIsNotNone(quiz)
        self.assertEqual(len(quiz["questions"]), 2)
        # Client questions MUST NOT expose correct_answer
        for q in quiz["questions"]:
            self.assertNotIn("correct_answer", q)

    def test_submit_quiz_and_progress_tracking(self):
        """Submitting a quiz updates score, explanations, and User's LearningProgress table"""
        quiz_id = "test_quiz_alice_999"
        q1_id = "q1"
        q2_id = "q2"
        stored_quiz = {
            "id": quiz_id,
            "user_id": self.user_a["id"],
            "subject_id": self.subject_a["id"],
            "subject_name": "Biochemistry",
            "document_ids": [self.doc_a["id"]],
            "question_count": 2,
            "difficulty": "medium",
            "questions": [
                {
                    "id": q1_id,
                    "question": "What is an enzyme?",
                    "options": ["Catalyst", "Inhibitor", "Lipid", "Sugar"],
                    "correct_answer": 0,
                    "explanation": "Enzymes catalyze reactions.",
                    "page": 1,
                    "topic": "Enzymes"
                },
                {
                    "id": q2_id,
                    "question": "Where do substrates bind?",
                    "options": ["Active site", "Nucleus", "Cytoplasm", "Vacuole"],
                    "correct_answer": 0,
                    "explanation": "Substrates bind to active sites.",
                    "page": 2,
                    "topic": "Enzymes"
                }
            ],
            "created_at": "2026-01-01 12:00:00",
            "attempted": False,
            "score": None,
            "accuracy": None
        }
        all_quizzes = app_module.load_quizzes()
        all_quizzes.append(stored_quiz)
        app_module.save_quizzes(all_quizzes)

        # User B cannot submit User A's quiz
        res_b = self.client.post(
            f"/api/quiz/{quiz_id}/submit",
            headers=self.headers_b,
            json={"answers": {q1_id: 0, q2_id: 0}}
        )
        self.assertEqual(res_b.status_code, 404)

        # User A submits answers (q1 correct, q2 incorrect)
        res_a = self.client.post(
            f"/api/quiz/{quiz_id}/submit",
            headers=self.headers_a,
            json={"answers": {q1_id: 0, q2_id: 1}}
        )
        self.assertEqual(res_a.status_code, 200)
        data = res_a.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["score"], 1)
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["accuracy"], 50.0)

        # Verify database record updated in LearningProgress
        with self.app.app_context():
            progress_rec = LearningProgress.query.filter_by(
                user_id=self.user_a["id"],
                topic="Enzymes"
            ).first()
            self.assertIsNotNone(progress_rec)
            self.assertEqual(progress_rec.questions_attempted, 2)
            self.assertEqual(progress_rec.questions_correct, 1)

    def test_record_learning_session(self):
        """User can record a study session and accumulate study minutes"""
        # Invalid minutes
        res1 = self.client.post(
            "/api/learning/session",
            headers=self.headers_a,
            json={"topic": "Catalysis", "study_minutes": 0}
        )
        self.assertEqual(res1.status_code, 400)

        # Valid session (60 minutes)
        res2 = self.client.post(
            "/api/learning/session",
            headers=self.headers_a,
            json={"topic": "Catalysis", "study_minutes": 60}
        )
        self.assertEqual(res2.status_code, 201)
        data = res2.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["study_hours"], 1.0)
        self.assertGreaterEqual(data["learning_streak"], 1)

    def test_learning_progress_and_dashboard_stats(self):
        """User A has recorded stats; User B remains empty and isolated"""
        # User A records 120 minutes of study
        self.client.post(
            "/api/learning/session",
            headers=self.headers_a,
            json={"topic": "Biochemistry", "study_minutes": 120}
        )

        # User A gets progress
        res_prog_a = self.client.get("/api/learning/progress", headers=self.headers_a)
        self.assertEqual(res_prog_a.status_code, 200)
        data_a = res_prog_a.get_json()
        self.assertEqual(data_a["study_hours"], 2.0)
        self.assertGreaterEqual(len(data_a["progress"]), 1)

        # User B gets progress -> empty
        res_prog_b = self.client.get("/api/learning/progress", headers=self.headers_b)
        self.assertEqual(res_prog_b.status_code, 200)
        data_b = res_prog_b.get_json()
        self.assertEqual(data_b["study_hours"], 0.0)
        self.assertEqual(len(data_b["progress"]), 0)

        # User A gets dashboard stats
        res_dash_a = self.client.get("/api/dashboard/stats", headers=self.headers_a)
        self.assertEqual(res_dash_a.status_code, 200)
        stats_a = res_dash_a.get_json()["stats"]
        self.assertEqual(stats_a["study_hours"], 2.0)
        self.assertGreaterEqual(stats_a["knowledge_dna"], 0)

        # User A gets learning insights
        res_insights = self.client.get("/api/learning/insights", headers=self.headers_a)
        self.assertEqual(res_insights.status_code, 200)
        self.assertTrue(res_insights.get_json().get("success"))

    def test_get_single_quiz_and_anti_cheat_masking(self):
        """GET /api/quiz/<quiz_id> provides user isolation and anti-cheat masking"""
        quiz_id = "test_quiz_masking_1"
        stored_quiz = {
            "id": quiz_id,
            "user_id": self.user_a["id"],
            "subject_id": self.subject_a["id"],
            "subject_name": "Biochemistry",
            "document_ids": [self.doc_a["id"]],
            "question_count": 1,
            "difficulty": "easy",
            "questions": [
                {
                    "id": "qm1",
                    "question": "What is an enzyme?",
                    "options": ["Catalyst", "Inhibitor", "Lipid", "Sugar"],
                    "correct_answer": 0,
                    "explanation": "Enzymes catalyze reactions.",
                    "page": 1,
                    "topic": "Enzymes"
                }
            ],
            "created_at": "2026-01-01 12:00:00",
            "attempted": False,
            "score": None,
            "accuracy": None
        }
        all_quizzes = app_module.load_quizzes()
        all_quizzes.append(stored_quiz)
        app_module.save_quizzes(all_quizzes)

        # Unauthenticated request -> 401
        res_no_auth = self.client.get(f"/api/quiz/{quiz_id}")
        self.assertEqual(res_no_auth.status_code, 401)

        # Cross-user access denied -> 404
        res_user_b = self.client.get(f"/api/quiz/{quiz_id}", headers=self.headers_b)
        self.assertEqual(res_user_b.status_code, 404)

        # Non-existent quiz -> 404
        res_404 = self.client.get("/api/quiz/non_existent_id", headers=self.headers_a)
        self.assertEqual(res_404.status_code, 404)

        # Unattempted quiz -> 200, correct_answer & explanation masked
        res_unattempted = self.client.get(f"/api/quiz/{quiz_id}", headers=self.headers_a)
        self.assertEqual(res_unattempted.status_code, 200)
        quiz_data = res_unattempted.get_json()["quiz"]
        self.assertEqual(quiz_data["difficulty"], "easy")
        self.assertFalse(quiz_data["attempted"])
        for q in quiz_data["questions"]:
            self.assertNotIn("correct_answer", q)
            self.assertNotIn("explanation", q)
            self.assertIn("options", q)
            self.assertEqual(len(q["options"]), 4)

        # Mark attempted and verify answers become visible for review
        stored_quiz["attempted"] = True
        stored_quiz["score"] = 1
        stored_quiz["accuracy"] = 100.0
        app_module.save_quizzes([stored_quiz])

        res_attempted = self.client.get(f"/api/quiz/{quiz_id}", headers=self.headers_a)
        self.assertEqual(res_attempted.status_code, 200)
        attempted_quiz = res_attempted.get_json()["quiz"]
        self.assertTrue(attempted_quiz["attempted"])
        self.assertIn("correct_answer", attempted_quiz["questions"][0])
        self.assertIn("explanation", attempted_quiz["questions"][0])

    @patch("app.get_gemini_client")
    def test_quiz_difficulty_easy_medium_hard(self, mock_client_getter):
        """Quiz generation verifies easy, medium, and hard modes and validates prompt guidance"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "questions": [
                {
                    "question": "What is an enzyme?",
                    "options": ["Catalyst", "Inhibitor", "Lipid", "Sugar"],
                    "correct_answer": 0,
                    "explanation": "Enzymes catalyze reactions.",
                    "page": 1,
                    "topic": "Enzymes"
                }
            ]
        })
        mock_client.models.generate_content.return_value = mock_response
        mock_client_getter.return_value = mock_client

        # 1. Easy mode
        res_easy = self.client.post(
            "/api/quiz/generate",
            headers=self.headers_a,
            json={"subject_id": "subj_alice_1", "difficulty": "easy", "question_count": 5}
        )
        self.assertEqual(res_easy.status_code, 200)
        quiz_easy = res_easy.get_json()["quiz"]
        self.assertEqual(quiz_easy["difficulty"], "easy")
        prompt_call = mock_client.models.generate_content.call_args[1]["contents"]
        self.assertIn("DIFFICULTY LEVEL: EASY", prompt_call)

        # 2. Hard mode
        res_hard = self.client.post(
            "/api/quiz/generate",
            headers=self.headers_a,
            json={"subject_id": "subj_alice_1", "difficulty": "hard", "question_count": 5}
        )
        self.assertEqual(res_hard.status_code, 200)
        quiz_hard = res_hard.get_json()["quiz"]
        self.assertEqual(quiz_hard["difficulty"], "hard")
        prompt_call_hard = mock_client.models.generate_content.call_args[1]["contents"]
        self.assertIn("DIFFICULTY LEVEL: HARD", prompt_call_hard)

        # 3. Invalid mode defaults to medium
        res_invalid = self.client.post(
            "/api/quiz/generate",
            headers=self.headers_a,
            json={"subject_id": "subj_alice_1", "difficulty": "expert_extreme", "question_count": 5}
        )
        self.assertEqual(res_invalid.status_code, 200)
        quiz_invalid = res_invalid.get_json()["quiz"]
        self.assertEqual(quiz_invalid["difficulty"], "medium")



if __name__ == "__main__":
    unittest.main()
