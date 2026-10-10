import os
import sys
import json
import shutil
import tempfile
import unittest

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import app as app_module
from models import db, User, LearningProgress
from sqlalchemy import create_engine
from flask_jwt_extended import create_access_token


class BaseTestCase(unittest.TestCase):
    """
    Isolated test case that completely isolates both the SQL database
    and the file-based JSON data stores.
    
    Guarantees:
    - Never mutates TiDB/MySQL production database.
    - Never mutates backend/data/*.json production stores.
    - Never mutates backend/uploads/ storage.
    - Never modifies backend/.env.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = app_module.app
        cls.app.config["TESTING"] = True
        cls.sa = cls.app.extensions["sqlalchemy"]
        cls.original_engine_map = dict(cls.sa._app_engines.get(cls.app, {}))
        
        # Save original file paths
        cls.orig_DATA_FOLDER = app_module.DATA_FOLDER
        cls.orig_DOCUMENTS_FILE = app_module.DOCUMENTS_FILE
        cls.orig_SUBJECTS_FILE = app_module.SUBJECTS_FILE
        cls.orig_QUIZZES_FILE = app_module.QUIZZES_FILE
        cls.orig_UPLOAD_FOLDER = app_module.UPLOAD_FOLDER

    def setUp(self):
        # Create isolated temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="dna_isolated_test_")
        self.data_dir = os.path.join(self.temp_dir, "data")
        self.upload_dir = os.path.join(self.temp_dir, "uploads")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.upload_dir, exist_ok=True)

        self.documents_file = os.path.join(self.data_dir, "documents.json")
        self.subjects_file = os.path.join(self.data_dir, "subjects.json")
        self.quizzes_file = os.path.join(self.data_dir, "quizzes.json")

        for fpath in [self.documents_file, self.subjects_file, self.quizzes_file]:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump([], f)

        # Redirect app file paths to isolated test storage
        app_module.DATA_FOLDER = self.data_dir
        app_module.DOCUMENTS_FILE = self.documents_file
        app_module.SUBJECTS_FILE = self.subjects_file
        app_module.QUIZZES_FILE = self.quizzes_file
        app_module.UPLOAD_FOLDER = self.upload_dir

        # Setup isolated SQLite in-memory engine
        self.test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False}
        )
        self.sa._app_engines[self.app] = {None: self.test_engine}

        # Create tables in isolated test database
        with self.app.app_context():
            db.create_all()

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

        # Restore original engine map
        self.sa._app_engines[self.app] = dict(self.original_engine_map)

        # Restore original paths
        app_module.DATA_FOLDER = self.orig_DATA_FOLDER
        app_module.DOCUMENTS_FILE = self.orig_DOCUMENTS_FILE
        app_module.SUBJECTS_FILE = self.orig_SUBJECTS_FILE
        app_module.QUIZZES_FILE = self.orig_QUIZZES_FILE
        app_module.UPLOAD_FOLDER = self.orig_UPLOAD_FOLDER

        # Clean up temp folder
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # Helper utilities for tests
    # -------------------------------------------------------------
    def create_user(self, name="Test Student", email="test@student.edu", password="password123"):
        with self.app.app_context():
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return {"id": user.id, "name": user.name, "email": user.email}

    def get_token(self, user_id):
        with self.app.app_context():
            return create_access_token(identity=str(user_id))

    def auth_headers(self, user_id):
        return {
            "Authorization": f"Bearer {self.get_token(user_id)}",
            "Content-Type": "application/json"
        }
