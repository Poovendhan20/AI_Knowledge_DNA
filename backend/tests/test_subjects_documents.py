import os
import sys
import io
import unittest
import docx

tests_dir = os.path.dirname(os.path.abspath(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

from test_base import BaseTestCase


class TestSubjectsDocuments(BaseTestCase):
    """
    Tests for Subjects and Documents management, upload processing,
    document retrieval, file serving security, and cross-user isolation.
    """

    def setUp(self):
        super().setUp()
        self.user_a = self.create_user(name="User A", email="usera@test.edu", password="password123")
        self.user_b = self.create_user(name="User B", email="userb@test.edu", password="password123")
        self.headers_a = self.auth_headers(self.user_a["id"])
        self.headers_b = self.auth_headers(self.user_b["id"])

    def _create_sample_docx(self, text="Cellular biology is the study of cell structure and function."):
        doc = docx.Document()
        doc.add_paragraph(text)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf

    def test_create_subject_success(self):
        """User can create a new subject"""
        res = self.client.post(
            "/api/subjects",
            headers=self.headers_a,
            json={"name": "Molecular Biology", "description": "Study of macromolecules"}
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["subject"]["name"], "Molecular Biology")
        self.assertEqual(data["subject"]["description"], "Study of macromolecules")

    def test_create_subject_missing_name(self):
        """Creating subject without name returns 400"""
        res = self.client.post(
            "/api/subjects",
            headers=self.headers_a,
            json={"description": "Missing name"}
        )
        self.assertEqual(res.status_code, 400)

    def test_create_subject_duplicate_same_user(self):
        """Same user cannot create subject with duplicate name"""
        self.client.post("/api/subjects", headers=self.headers_a, json={"name": "Physics"})
        res = self.client.post("/api/subjects", headers=self.headers_a, json={"name": "Physics"})
        self.assertEqual(res.status_code, 409)

    def test_subject_multi_tenant_isolation(self):
        """Different users can have subjects with identical names without conflict"""
        res_a = self.client.post("/api/subjects", headers=self.headers_a, json={"name": "Chemistry"})
        self.assertEqual(res_a.status_code, 201)

        res_b = self.client.post("/api/subjects", headers=self.headers_b, json={"name": "Chemistry"})
        self.assertEqual(res_b.status_code, 201)

        # User A's list should only contain User A's subject
        list_a = self.client.get("/api/subjects", headers=self.headers_a).get_json()["subjects"]
        self.assertEqual(len(list_a), 1)
        self.assertEqual(list_a[0]["id"], res_a.get_json()["subject"]["id"])

    def test_get_subject_by_id_and_forbidden_access(self):
        """User can get own subject; another user gets 404"""
        res_a = self.client.post("/api/subjects", headers=self.headers_a, json={"name": "Calculus"})
        subj_id = res_a.get_json()["subject"]["id"]

        # User A retrieves
        res = self.client.get(f"/api/subjects/{subj_id}", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["subject"]["name"], "Calculus")

        # User B attempts to retrieve
        res_b = self.client.get(f"/api/subjects/{subj_id}", headers=self.headers_b)
        self.assertEqual(res_b.status_code, 404)

    def test_delete_subject(self):
        """User can delete own subject; User B cannot delete it"""
        res_a = self.client.post("/api/subjects", headers=self.headers_a, json={"name": "History"})
        subj_id = res_a.get_json()["subject"]["id"]

        # User B attempts to delete
        res_del_b = self.client.delete(f"/api/subjects/{subj_id}", headers=self.headers_b)
        self.assertEqual(res_del_b.status_code, 404)

        # User A deletes
        res_del_a = self.client.delete(f"/api/subjects/{subj_id}", headers=self.headers_a)
        self.assertEqual(res_del_a.status_code, 200)

        # Verify deletion
        res_check = self.client.get(f"/api/subjects/{subj_id}", headers=self.headers_a)
        self.assertEqual(res_check.status_code, 404)

    def test_upload_missing_file_or_invalid_extension(self):
        """Upload requires a valid file and allowed extension"""
        # No file in request
        res1 = self.client.post(
            "/api/upload",
            headers={"Authorization": f"Bearer {self.get_token(self.user_a['id'])}"}
        )
        self.assertEqual(res1.status_code, 400)

        # Invalid file type (.exe)
        data = {"file": (io.BytesIO(b"binary"), "malicious.exe")}
        res2 = self.client.post(
            "/api/upload",
            headers={"Authorization": f"Bearer {self.get_token(self.user_a['id'])}"},
            content_type="multipart/form-data",
            data=data
        )
        self.assertEqual(res2.status_code, 400)
        self.assertIn("Unsupported file type", res2.get_json().get("message", ""))

    def test_upload_valid_docx_and_cross_user_isolation(self):
        """Upload valid DOCX, extract text, and verify cross-user isolation"""
        file_buf = self._create_sample_docx("Photosynthesis occurs in chloroplasts and produces ATP.")
        data = {"file": (file_buf, "biology_chapter1.docx")}

        res_upload = self.client.post(
            "/api/upload",
            headers={"Authorization": f"Bearer {self.get_token(self.user_a['id'])}"},
            content_type="multipart/form-data",
            data=data
        )
        self.assertEqual(res_upload.status_code, 201)
        doc_data = res_upload.get_json()["document"]
        doc_id = doc_data["id"]
        stored_name = doc_data["stored_name"]

        self.assertEqual(doc_data["original_name"], "biology_chapter1.docx")
        self.assertGreaterEqual(doc_data["word_count"], 5)

        # User A retrieves document list
        res_list_a = self.client.get("/api/documents", headers=self.headers_a)
        self.assertEqual(res_list_a.status_code, 200)
        self.assertEqual(len(res_list_a.get_json()["documents"]), 1)

        # User B retrieves document list -> must be empty
        res_list_b = self.client.get("/api/documents", headers=self.headers_b)
        self.assertEqual(res_list_b.status_code, 200)
        self.assertEqual(len(res_list_b.get_json()["documents"]), 0)

        # User B attempts to access document details -> 404
        res_get_b = self.client.get(f"/api/documents/{doc_id}", headers=self.headers_b)
        self.assertEqual(res_get_b.status_code, 404)

        # User A downloads file -> 200
        res_file_a = self.client.get(f"/api/files/{stored_name}", headers=self.headers_a)
        self.assertEqual(res_file_a.status_code, 200)
        res_file_a.close()

        # User B attempts to download file -> 403 Forbidden
        res_file_b = self.client.get(f"/api/files/{stored_name}", headers=self.headers_b)
        self.assertEqual(res_file_b.status_code, 403)
        res_file_b.close()

        # User B attempts to delete document -> 404
        res_del_b = self.client.delete(f"/api/documents/{doc_id}", headers=self.headers_b)
        self.assertEqual(res_del_b.status_code, 404)

        # User A deletes document -> 200
        res_del_a = self.client.delete(f"/api/documents/{doc_id}", headers=self.headers_a)
        self.assertEqual(res_del_a.status_code, 200)


if __name__ == "__main__":
    unittest.main()
