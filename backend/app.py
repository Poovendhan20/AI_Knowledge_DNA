import os
import re
import json
import time
import random
from uuid import uuid4
from collections import Counter
from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory,
)
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document
from pptx import Presentation
from PIL import Image
import pytesseract
from google import genai
from models import db, User
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)
ENV_FILE = os.path.join(
    BASE_DIR,
    ".env"
)
load_dotenv(
    ENV_FILE
)
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash"
)
def get_gemini_api_key():
    """
    Gets the Gemini API key from .env.
    The API key is never hard-coded
    inside the Python source code.
    """
    api_key = os.getenv(
        "GEMINI_API_KEY"
    )
    if not api_key:
        return None
    api_key = api_key.strip()
    if not api_key:
        return None
    return api_key
def get_gemini_client():
    """
    Creates a Gemini client using
    the API key from .env.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Please create backend/.env and add "
            "GEMINI_API_KEY=your_api_key"
        )
    return genai.Client(
        api_key=api_key
    )
def is_gemini_configured():
    """
    Returns True when Gemini API key
    is available.
    """
    return bool(
        get_gemini_api_key()
    )
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSL_CA = os.getenv("DB_SSL_CA")
if DB_SSL_CA and not os.path.isabs(DB_SSL_CA):
    DB_SSL_CA = os.path.join(BASE_DIR, DB_SSL_CA)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/"
    f"{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "connect_args": {
        "ssl": {
            "ca": DB_SSL_CA
        }
    }
}
db.init_app(app)
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY",
    os.getenv("SECRET_KEY")
)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 60 * 60 * 24
jwt = JWTManager(app)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*"
        }
    }
)
UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)
DATA_FOLDER = os.path.join(
    BASE_DIR,
    "data"
)
DOCUMENTS_FILE = os.path.join(
    DATA_FOLDER,
    "documents.json"
)
os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)
os.makedirs(
    DATA_FOLDER,
    exist_ok=True
)
MAX_FILE_SIZE = (
    25 * 1024 * 1024
)
app.config[
    "MAX_CONTENT_LENGTH"
] = MAX_FILE_SIZE
ALLOWED_EXTENSIONS = {
    "pdf",
    "pptx",
    "docx",
    "png",
    "jpg",
    "jpeg",
    "webp",
}
STOP_WORDS = {
    "about",
    "after",
    "again",
    "against",
    "also",
    "because",
    "before",
    "being",
    "between",
    "could",
    "does",
    "during",
    "each",
    "from",
    "have",
    "having",
    "into",
    "more",
    "most",
    "other",
    "over",
    "same",
    "should",
    "some",
    "such",
    "than",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "under",
    "using",
    "very",
    "were",
    "which",
    "while",
    "with",
    "would",
    "your",
    "you",
    "then",
    "when",
    "where",
    "what",
    "will",
    "shall",
    "been",
    "only",
    "many",
    "much",
    "here",
    "like",
    "just",
    "page",
    "unit",
    "chapter",
    "lecture",
    "notes",
    "figure",
    "table",
    "explain",
    "explanation",
    "give",
    "tell",
    "please",
    "document",
    "topic",
}
def load_documents():
    if not os.path.exists(
        DOCUMENTS_FILE
    ):
        return []
    try:
        with open(
            DOCUMENTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(
                file
            )
            if isinstance(
                data,
                list
            ):
                return data
            return []
    except Exception as error:
        print(
            "DOCUMENT LOAD ERROR:",
            error
        )
        return []
def save_documents(
    documents
):
    with open(
        DOCUMENTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            documents,
            file,
            indent=2,
            ensure_ascii=False
        )
def allowed_file(
    filename
):
    if not filename:
        return False
    if "." not in filename:
        return False
    extension = (
        filename
        .rsplit(
            ".",
            1
        )[1]
        .lower()
    )
    return (
        extension
        in ALLOWED_EXTENSIONS
    )
def extract_pdf_pages(
    file_path
):
    pages = []
    reader = PdfReader(
        file_path
    )
    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):
        try:
            text = (
                page.extract_text()
                or ""
            )
            pages.append({
                "page":
                    page_number,
                "text":
                    text.strip()
            })
        except Exception as error:
            print(
                f"PDF PAGE "
                f"{page_number} ERROR:",
                error
            )
            pages.append({
                "page":
                    page_number,
                "text":
                    ""
            })
    return pages
def extract_docx_pages(
    file_path
):
    document = Document(
        file_path
    )
    text = []
    for paragraph in (
        document.paragraphs
    ):
        value = (
            paragraph.text.strip()
        )
        if value:
            text.append(
                value
            )
    return [
        {
            "page": 1,
            "text": "\n".join(text)
        }
    ]
def extract_pptx_pages(
    file_path
):
    presentation = Presentation(
        file_path
    )
    pages = []
    for slide_number, slide in enumerate(
        presentation.slides,
        start=1
    ):
        texts = []
        for shape in slide.shapes:
            if hasattr(
                shape,
                "text"
            ):
                value = (
                    shape.text.strip()
                )
                if value:
                    texts.append(
                        value
                    )
        pages.append({
            "page":
                slide_number,
            "text":
                "\n".join(texts)
        })
    return pages
def extract_image_pages(
    file_path
):
    try:
        image = Image.open(
            file_path
        )
        text = (
            pytesseract.image_to_string(
                image
            )
        )
        return [
            {
                "page": 1,
                "text": text.strip()
            }
        ]
    except Exception as error:
        print(
            "OCR ERROR:",
            error
        )
        return [
            {
                "page": 1,
                "text": ""
            }
        ]
def extract_pages(
    file_path,
    extension
):
    if extension == "pdf":
        return extract_pdf_pages(
            file_path
        )
    if extension == "docx":
        return extract_docx_pages(
            file_path
        )
    if extension == "pptx":
        return extract_pptx_pages(
            file_path
        )
    if extension in {
        "png",
        "jpg",
        "jpeg",
        "webp"
    }:
        return extract_image_pages(
            file_path
        )
    return []
def extract_keywords(
    text,
    limit=12
):
    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z0-9-]{3,}\b",
        text.lower()
    )
    words = [
        word
        for word in words
        if word not in STOP_WORDS
    ]
    counts = Counter(
        words
    )
    return [
        word
        for word, count
        in counts.most_common(limit)
    ]
def find_source_page(
    keyword,
    pages
):
    keyword = keyword.lower()
    best_page = 1
    best_count = 0
    for page in pages:
        text = page.get(
            "text",
            ""
        ).lower()
        count = text.count(
            keyword
        )
        if count > best_count:
            best_count = count
            best_page = page[
                "page"
            ]
    return best_page
def generate_topics(
    pages
):
    full_text = "\n".join(
        page.get(
            "text",
            ""
        )
        for page in pages
    )
    keywords = extract_keywords(
        full_text,
        10
    )
    topics = []
    for keyword in keywords:
        page_number = (
            find_source_page(
                keyword,
                pages
            )
        )
        topics.append({
            "name":
                keyword.title(),
            "confidence":
                70,
            "page":
                page_number
        })
    return topics
def generate_summary(
    text
):
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )
    sentences = [
        sentence.strip()
        for sentence in sentences
        if len(
            sentence.strip()
        ) > 30
    ]
    if not sentences:
        return (
            "No readable text was found "
            "in this document."
        )
    keywords = extract_keywords(
        text,
        8
    )
    scored = []
    for sentence in sentences:
        lower = (
            sentence.lower()
        )
        score = sum(
            lower.count(
                keyword
            )
            for keyword in keywords
        )
        scored.append(
            (
                score,
                sentence
            )
        )
    scored.sort(
        reverse=True
    )
    return " ".join(
        sentence
        for score, sentence
        in scored[:5]
    )
def analyze_document(
    pages
):
    full_text = "\n".join(
        page.get(
            "text",
            ""
        )
        for page in pages
    ).strip()
    if not full_text:
        return {
            "summary":
                "No readable text was found.",
            "topics":
                [],
            "word_count":
                0,
            "character_count":
                0
        }
    words = re.findall(
        r"\b\w+\b",
        full_text
    )
    return {
        "summary":
            generate_summary(
                full_text
            ),
        "topics":
            generate_topics(
                pages
            ),
        "word_count":
            len(words),
        "character_count":
            len(full_text)
    }
def normalize_text(
    text
):
    text = text or ""
    text = re.sub(
        r"\s+",
        " ",
        text
    )
    return text.strip()
def find_relevant_pages(
    question,
    pages,
    max_pages=12
):
    question_words = re.findall(
        r"\b[a-zA-Z][a-zA-Z0-9-]{2,}\b",
        question.lower()
    )
    question_words = [
        word
        for word in question_words
        if word not in STOP_WORDS
    ]
    if not question_words:
        return pages[:max_pages]
    scored_pages = []
    for page in pages:
        page_text = normalize_text(
            page.get(
                "text",
                ""
            )
        )
        if not page_text:
            continue
        lower_text = (
            page_text.lower()
        )
        score = 0
        for word in question_words:
            score += (
                lower_text.count(
                    word
                )
            )
        if score > 0:
            scored_pages.append({
                "score":
                    score,
                "page":
                    page["page"],
                "text":
                    page_text
            })
    scored_pages.sort(
        key=lambda item:
            item["score"],
        reverse=True
    )
    if not scored_pages:
        return pages[:max_pages]
    return [
        {
            "page":
                item["page"],
            "text":
                item["text"]
        }
        for item
        in scored_pages[:max_pages]
    ]
def build_document_context(
    pages,
    question
):
    relevant_pages = (
        find_relevant_pages(
            question,
            pages,
            max_pages=12
        )
    )
    context_parts = []
    for page in relevant_pages:
        page_number = (
            page["page"]
        )
        page_text = (
            page["text"]
        )
        if not page_text:
            continue
        page_text = page_text[
            :12000
        ]
        context_parts.append(
            f"\n--- PAGE {page_number} ---\n"
            f"{page_text}\n"
            f"--- END PAGE {page_number} ---\n"
        )
    return (
        "\n".join(
            context_parts
        ),
        relevant_pages
    )
def build_chat_history(
    history
):
    if not isinstance(
        history,
        list
    ):
        return ""
    history_parts = []
    for item in history[-10:]:
        if not isinstance(
            item,
            dict
        ):
            continue
        role = item.get(
            "role",
            ""
        )
        content = item.get(
            "content",
            ""
        )
        if not content:
            continue
        label = (
            "Student"
            if role == "user"
            else "AI Assistant"
        )
        history_parts.append(
            f"{label}: "
            f"{str(content)[:4000]}"
        )
    return "\n".join(
        history_parts
    )
def extract_page_references(
    answer,
    available_pages
):
    if not answer:
        return []
    matches = re.findall(
        r"\[Page\s+(\d+)\]",
        answer,
        flags=re.IGNORECASE
    )
    references = []
    seen = set()
    for value in matches:
        try:
            page_number = int(
                value
            )
        except ValueError:
            continue
        if page_number in seen:
            continue
        if (
            page_number
            not in available_pages
        ):
            continue
        seen.add(
            page_number
        )
        references.append({
            "page":
                page_number
        })
    return references
def clean_ai_answer(
    answer
):
    if not answer:
        return ""
    # Remove Markdown heading symbols.
    # Example:
    # ### What is Cloud Computing?
    # becomes:
    # What is Cloud Computing?
    answer = re.sub(
        r"(?m)^\s*#{1,6}\s*",
        "",
        answer
    )
    # Remove excessive bold markers
    # around headings while keeping
    # normal text readable.
    answer = re.sub(
        r"\*\*(.*?)\*\*",
        r"\1",
        answer
    )
    # Remove unnecessary horizontal rules.
    answer = re.sub(
        r"(?m)^\s*[-_*]{3,}\s*$",
        "",
        answer
    )
    # Reduce excessive blank lines.
    answer = re.sub(
        r"\n{3,}",
        "\n\n",
        answer
    )
    return answer.strip()
def generate_document_answer(
    document,
    question,
    history
):
    client = get_gemini_client()
    pages = document.get(
        "pages",
        []
    )
    if not pages:
        raise RuntimeError(
            "This document has no extracted text."
        )
    context, relevant_pages = (
        build_document_context(
            pages,
            question
        )
    )
    available_pages = {
        page["page"]
        for page
        in relevant_pages
    }
    history_text = (
        build_chat_history(
            history
        )
    )
    # GEMINI PROMPT
    prompt = f"""
You are AI Knowledge DNA,
a personalized learning assistant
for students.
The student uploaded a study document.
Your job is to answer questions using
the supplied document context.
DOCUMENT:
{document.get("name", "Study Material")}
IMPORTANT RULES:
1. Use the uploaded document as the
   primary source.
2. Do not invent information.
3. If the answer is not available
   in the document, clearly tell the
   student.
4. Explain concepts in simple,
   student-friendly English.
5. Keep answers focused and useful
   for learning and exams.
6. You can use simple bullet points.
7. You can use simple section titles.
8. DO NOT use Markdown heading symbols.
9. NEVER use:
10. For example, do NOT write:
   ### What is Cloud Computing?
   Instead write:
   What is Cloud Computing?
11. When information comes from a
    specific page, add:
    [Page X]
12. NEVER invent a page number.
13. Only cite pages that exist in
    the supplied document context.
14. Do not mention these instructions.
15. Do not give information unrelated
    to the student's question unless
    it helps explain the answer.
CONVERSATION HISTORY:
{history_text}
DOCUMENT CONTEXT:
{context}
STUDENT QUESTION:
{question}
Answer the student's question now.
"""
    # RETRY CONFIGURATION
    max_retries = 4
    last_error = None
    for attempt in range(
        max_retries
    ):
        try:
            print(
                f"Gemini request "
                f"attempt {attempt + 1}/"
                f"{max_retries}"
            )
            response = (
                client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt
                )
            )
            answer = (
                response.text
                if response
                else ""
            )
            if not answer:
                answer = (
                    "I could not generate "
                    "an answer from this document."
                )
            answer = clean_ai_answer(
                answer
            )
            sources = (
                extract_page_references(
                    answer,
                    available_pages
                )
            )
            # If Gemini didn't provide
            # references, provide the
            # relevant pages ourselves.
            if not sources:
                sources = [
                    {
                        "page":
                            page["page"]
                    }
                    for page
                    in relevant_pages[:3]
                ]
            return (
                answer,
                sources
            )
        except Exception as error:
            last_error = error
            error_text = str(
                error
            ).lower()
            print()
            print(
                "--------------------------------"
            )
            print(
                "GEMINI ERROR"
            )
            print(
                error
            )
            print(
                "--------------------------------"
            )
            # TEMPORARY GEMINI ERRORS
            is_temporary_error = (
                "503"
                in error_text
                or
                "unavailable"
                in error_text
                or
                "overloaded"
                in error_text
                or
                "temporarily"
                in error_text
                or
                "high demand"
                in error_text
                or
                "429"
                in error_text
                or
                "resource exhausted"
                in error_text
            )
            # NON-RETRYABLE ERROR
            if not is_temporary_error:
                raise RuntimeError(
                    f"Gemini request failed: "
                    f"{error}"
                )
            # LAST ATTEMPT
            if attempt >= (
                max_retries - 1
            ):
                break
            # EXPONENTIAL BACKOFF
            delay = (
                2 ** attempt
            )
            jitter = random.uniform(
                0,
                1
            )
            total_delay = (
                delay + jitter
            )
            print(
                "Gemini is temporarily "
                "unavailable."
            )
            print(
                f"Retrying in "
                f"{total_delay:.1f} seconds..."
            )
            time.sleep(
                total_delay
            )
    # FINAL ERROR
    raise RuntimeError(
        "Gemini is temporarily unavailable "
        "because the AI service is experiencing "
        "high demand. Please try again in a "
        "few moments."
    )
@app.route(
    "/",
    methods=["GET"]
)
def home():
    return jsonify({
        "success":
            True,
        "message":
            "AI Knowledge DNA Backend is running!"
    })
@app.route("/api/health",
    methods=["GET"]
)
def health():
    return jsonify({
        "success":
            True,
        "status":
            "healthy",
        "gemini_configured":
            is_gemini_configured(),
        "gemini_model":
            GEMINI_MODEL
    })
@app.route(
    "/api/auth/register",
    methods=["POST"]
)
def register():
    try:
        data = (
            request.get_json(
                silent=True
            )
            or {}
        )
        name = (
            data.get(
                "name",
                ""
            )
            .strip()
        )
        email = (
            data.get(
                "email",
                ""
            )
            .strip()
            .lower()
        )
        password = data.get(
            "password",
            ""
        )
        if not name:
            return jsonify({
                "success": False,
                "message": "Name is required."
            }), 400
        if not email:
            return jsonify({
                "success": False,
                "message": "Email is required."
            }), 400
        if not password:
            return jsonify({
                "success": False,
                "message": "Password is required."
            }), 400
        if len(password) < 6:
            return jsonify({
                "success": False,
                "message": "Password must be at least 6 characters long."
            }), 400
        existing_user = (
            User.query
            .filter_by(email=email)
            .first()
        )
        if existing_user:
            return jsonify({
                "success": False,
                "message": "An account with this email already exists."
            }), 409
        user = User(
            name=name,
            email=email
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        access_token = create_access_token(
            identity=str(user.id)
        )
        return jsonify({
            "success": True,
            "message": "Registration successful.",
            "token": access_token,
            "user": user.to_dict()
        }), 201
    except Exception as error:
        db.session.rollback()
        print()
        print(
            "REGISTRATION ERROR:",
            repr(error)
        )
        print()
        return jsonify({
            "success": False,
            "message": "Unable to create account.",
            "error": str(error)
        }), 500
@app.route(
    "/api/auth/login",
    methods=["POST"]
)
def login():
    try:
        data = (
            request.get_json(
                silent=True
            )
            or {}
        )
        email = (
            data.get(
                "email",
                ""
            )
            .strip()
            .lower()
        )
        password = data.get(
            "password",
            ""
        )
        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email and password are required."
            }), 400
        user = (
            User.query
            .filter_by(email=email)
            .first()
        )
        if (
            not user
            or not user.check_password(password)
        ):
            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401
        access_token = create_access_token(
            identity=str(user.id)
        )
        return jsonify({
            "success": True,
            "message": "Login successful.",
            "token": access_token,
            "user": user.to_dict()
        }), 200
    except Exception as error:
        print()
        print(
            "LOGIN ERROR:",
            repr(error)
        )
        print()
        return jsonify({
            "success": False,
            "message": "Unable to login.",
            "error": str(error)
        }), 500
@app.route(
    "/api/auth/me",
    methods=["GET"]
)
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = db.session.get(
            User,
            int(user_id)
        )
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404
        return jsonify({
            "success": True,
            "user": user.to_dict()
        }), 200
    except Exception as error:
        print()
        print(
            "CURRENT USER ERROR:",
            repr(error)
        )
        print()
        return jsonify({
            "success": False,
            "message": "Unable to get current user.",
            "error": str(error)
        }), 500
@app.route(
    "/api/upload",
    methods=["POST"]
)
def upload_file():
    if "file" not in request.files:
        return jsonify({
            "success":
                False,
            "message":
                "No file was provided."
        }), 400
    file = request.files[
        "file"
    ]
    if not file.filename:
        return jsonify({
            "success":
                False,
            "message":
                "No file was selected."
        }), 400
    if not allowed_file(
        file.filename
    ):
        return jsonify({
            "success":
                False,
            "message":
                "Unsupported file type. "
                "Use PDF, PPTX, DOCX, PNG, "
                "JPG, JPEG or WEBP."
        }), 400
    original_name = secure_filename(
        file.filename
    )
    extension = (
        original_name
        .rsplit(
            ".",
            1
        )[1]
        .lower()
    )
    document_id = uuid4().hex
    stored_name = (
        f"{document_id}.{extension}"
    )
    file_path = os.path.join(
        UPLOAD_FOLDER,
        stored_name
    )
    try:
        file.save(
            file_path
        )
        print(
            f"Uploaded file: "
            f"{original_name}"
        )
        pages = extract_pages(
            file_path,
            extension
        )
        analysis = analyze_document(
            pages
        )
    except Exception as error:
        print(
            "DOCUMENT EXTRACTION ERROR:"
        )
        print(
            repr(error)
        )
        if os.path.exists(
            file_path
        ):
            try:
                os.remove(
                    file_path
                )
            except Exception:
                pass
        return jsonify({
            "success":
                False,
            "message":
                "The file was uploaded, "
                "but its contents could "
                "not be extracted.",
            "error":
                str(error)
        }), 500
    document = {
        "id":
            document_id,
        "name":
            original_name,
        "original_name":
            original_name,
        "stored_name":
            stored_name,
        "type":
            extension,
        "page_count":
            len(pages),
        "pages":
            pages,
        "summary":
            analysis[
                "summary"
            ],
        "topics":
            analysis[
                "topics"
            ],
        "word_count":
            analysis[
                "word_count"
            ],
        "character_count":
            analysis[
                "character_count"
            ]
    }
    documents = load_documents()
    documents.append(
        document
    )
    save_documents(
        documents
    )
    return jsonify({
        "success":
            True,
        "message":
            "Document uploaded successfully.",
        "document":
            document
    }), 201
@app.route(
    "/api/documents",
    methods=["GET"]
)
def get_documents():
    documents = load_documents()
    result = []
    for document in documents:
        result.append({
            "id":
                document[
                    "id"
                ],
            "name":
                document[
                    "name"
                ],
            "original_name":
                document.get(
                    "original_name",
                    document[
                        "name"
                    ]
                ),
            "stored_name":
                document.get(
                    "stored_name"
                ),
            "type":
                document[
                    "type"
                ],
            "page_count":
                document[
                    "page_count"
                ],
            "topics":
                document.get(
                    "topics",
                    []
                ),
            "summary":
                document.get(
                    "summary",
                    ""
                ),
            "word_count":
                document.get(
                    "word_count",
                    0
                )
        })
    return jsonify({
        "success":
            True,
        "documents":
            result
    })
@app.route(
    "/api/documents/<document_id>",
    methods=["GET"]
)
def get_document(
    document_id
):
    documents = load_documents()
    document = next(
        (
            item
            for item
            in documents
            if item.get(
                "id"
            ) == document_id
        ),
        None
    )
    if not document:
        return jsonify({
            "success":
                False,
            "message":
                "Document not found."
        }), 404
    return jsonify({
        "success":
            True,
        "document":
            document
    })
def process_document_chat(
    document_id,
    data
):
    if not is_gemini_configured():
        raise RuntimeError(
            "Gemini AI is not configured. "
            "Please check backend/.env."
        )
    question = (
        data.get(
            "question",
            ""
        )
        .strip()
    )
    history = data.get(
        "history",
        []
    )
    if not question:
        raise ValueError(
            "Question is required."
        )
    documents = load_documents()
    document = next(
        (
            item
            for item
            in documents
            if item.get(
                "id"
            ) == document_id
        ),
        None
    )
    if not document:
        raise FileNotFoundError(
            "Document not found."
        )
    answer, sources = (
        generate_document_answer(
            document,
            question,
            history
        )
    )
    return {
        "success":
            True,
        "answer":
            answer,
        "sources":
            sources,
        "document_id":
            document_id,
        "model":
            GEMINI_MODEL
    }
@app.route(
    "/api/chat",
    methods=["POST"]
)
def chat():
    try:
        data = (
            request.get_json(
                silent=True
            )
            or {}
        )
        document_id = data.get(
            "document_id"
        )
        if not document_id:
            return jsonify({
                "success":
                    False,
                "message":
                    "document_id is required."
            }), 400
        result = (
            process_document_chat(
                document_id,
                data
            )
        )
        return jsonify(
            result
        )
    except FileNotFoundError as error:
        return jsonify({
            "success":
                False,
            "message":
                str(error)
        }), 404
    except ValueError as error:
        return jsonify({
            "success":
                False,
            "message":
                str(error)
        }), 400
    except RuntimeError as error:
        print()
        print(
            "CHAT RUNTIME ERROR:"
        )
        print(
            repr(error)
        )
        return jsonify({
            "success":
                False,
            "message":
                str(error)
        }), 503
    except Exception as error:
        print()
        print(
            "======================================"
        )
        print(
            "CHAT ERROR"
        )
        print(
            repr(error)
        )
        print(
            "======================================"
        )
        print()
        return jsonify({
            "success":
                False,
            "message":
                "The AI service could not "
                "process your question.",
            "error":
                str(error)
        }), 500
@app.route(
    "/api/documents/<document_id>/chat",
    methods=["POST"]
)
def chat_with_document(
    document_id
):
    try:
        data = (
            request.get_json(
                silent=True
            )
            or {}
        )
        result = (
            process_document_chat(
                document_id,
                data
            )
        )
        return jsonify(
            result
        )
    except FileNotFoundError as error:
        return jsonify({
            "success":
                False,
            "message":
                str(error)
        }), 404
    except ValueError as error:
        return jsonify({
            "success":
                False,
            "message":
                str(error)
        }), 400
    except RuntimeError as error:
        print()
        print(
            "DOCUMENT CHAT RUNTIME ERROR:"
        )
        print(
            repr(error)
        )
        return jsonify({
            "success":
                False,
            "message":
                str(error)
        }), 503
    except Exception as error:
        print()
        print(
            "======================================"
        )
        print(
            "DOCUMENT CHAT ERROR"
        )
        print(
            repr(error)
        )
        print(
            "======================================"
        )
        print()
        return jsonify({
            "success":
                False,
            "message":
                "The AI service could not "
                "process your question.",
            "error":
                str(error)
        }), 500
@app.route(
    "/api/files/<filename>",
    methods=["GET"]
)
def serve_file(
    filename
):
    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )
@app.route(
    "/api/documents/<document_id>",
    methods=["DELETE"]
)
def delete_document(
    document_id
):
    documents = load_documents()
    document = next(
        (
            item
            for item
            in documents
            if item.get(
                "id"
            ) == document_id
        ),
        None
    )
    if not document:
        return jsonify({
            "success":
                False,
            "message":
                "Document not found."
        }), 404
    stored_name = document.get(
        "stored_name"
    )
    if stored_name:
        file_path = os.path.join(
            UPLOAD_FOLDER,
            stored_name
        )
        if os.path.exists(
            file_path
        ):
            try:
                os.remove(
                    file_path
                )
            except Exception as error:
                print(
                    "FILE DELETE ERROR:",
                    error
                )
    documents = [
        item
        for item
        in documents
        if item.get(
            "id"
        ) != document_id
    ]
    save_documents(
        documents
    )
    return jsonify({
        "success":
            True,
        "message":
            "Document deleted successfully."
    })
@app.errorhandler(413)
def file_too_large(
    error
):
    return jsonify({
        "success":
            False,
        "message":
            "File is too large. "
            "Maximum size is 25 MB."
    }), 413
@app.errorhandler(Exception)
def handle_general_error(
    error
):
    print()
    print(
        "======================================"
    )
    print(
        "UNHANDLED SERVER ERROR"
    )
    print(
        repr(error)
    )
    print(
        "======================================"
    )
    print()
    return jsonify({
        "success":
            False,
        "message":
            "An unexpected server error occurred.",
        "error":
            str(error)
    }), 500
SUBJECTS_FILE = os.path.join(
    DATA_FOLDER,
    "subjects.json"
)
QUIZZES_FILE = os.path.join(
    DATA_FOLDER,
    "quizzes.json"
)
def load_subjects():
    if not os.path.exists(
        SUBJECTS_FILE
    ):
        return []
    try:
        with open(
            SUBJECTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)
            return (
                data
                if isinstance(data, list)
                else []
            )
    except Exception as error:
        print(
            "SUBJECT LOAD ERROR:",
            error
        )
        return []
def save_subjects(
    subjects
):
    with open(
        SUBJECTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            subjects,
            file,
            indent=2,
            ensure_ascii=False
        )
def load_quizzes():
    if not os.path.exists(
        QUIZZES_FILE
    ):
        return []
    try:
        with open(
            QUIZZES_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)
            return (
                data
                if isinstance(data, list)
                else []
            )
    except Exception as error:
        print(
            "QUIZ LOAD ERROR:",
            error
        )
        return []
def save_quizzes(
    quizzes
):
    with open(
        QUIZZES_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            quizzes,
            file,
            indent=2,
            ensure_ascii=False
        )
@app.route(
    "/api/subjects",
    methods=["POST"]
)
def create_subject():
    try:
        data = (
            request.get_json(
                silent=True
            )
            or {}
        )
        name = (
            data.get(
                "name",
                ""
            )
            .strip()
        )
        description = (
            data.get(
                "description",
                ""
            )
            .strip()
        )
        if not name:
            return jsonify({
                "success":
                    False,
                "message":
                    "Subject name is required."
            }), 400
        subjects = load_subjects()
        existing = next(
            (
                subject
                for subject
                in subjects
                if subject[
                    "name"
                ].lower()
                == name.lower()
            ),
            None
        )
        if existing:
            return jsonify({
                "success":
                    False,
                "message":
                    "This subject already exists."
            }), 409
        subject = {
            "id":
                uuid4().hex,
            "name":
                name,
            "description":
                description,
            "created_at":
                time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        }
        subjects.append(
            subject
        )
        save_subjects(
            subjects
        )
        return jsonify({
            "success":
                True,
            "message":
                "Subject created successfully.",
            "subject":
                subject
        }), 201
    except Exception as error:
        print(
            "CREATE SUBJECT ERROR:",
            repr(error)
        )
        return jsonify({
            "success":
                False,
            "message":
                "Unable to create subject.",
            "error":
                str(error)
        }), 500
@app.route(
    "/api/subjects",
    methods=["GET"]
)
def get_subjects():
    subjects = load_subjects()
    documents = load_documents()
    result = []
    for subject in subjects:
        subject_id = subject[
            "id"
        ]
        subject_documents = [
            document
            for document
            in documents
            if document.get(
                "subject_id"
            ) == subject_id
        ]
        topic_names = set()
        for document in subject_documents:
            for topic in document.get(
                "topics",
                []
            ):
                topic_name = topic.get(
                    "name"
                )
                if topic_name:
                    topic_names.add(
                        topic_name
                    )
        result.append({
            **subject,
            "document_count":
                len(
                    subject_documents
                ),
            "topic_count":
                len(
                    topic_names
                )
        })
    return jsonify({
        "success":
            True,
        "subjects":
            result
    })
@app.route(
    "/api/subjects/<subject_id>",
    methods=["GET"]
)
def get_subject(
    subject_id
):
    subjects = load_subjects()
    subject = next(
        (
            item
            for item
            in subjects
            if item.get(
                "id"
            ) == subject_id
        ),
        None
    )
    if not subject:
        return jsonify({
            "success":
                False,
            "message":
                "Subject not found."
        }), 404
    documents = load_documents()
    subject_documents = [
        document
        for document
        in documents
        if document.get(
            "subject_id"
        ) == subject_id
    ]
    return jsonify({
        "success":
            True,
        "subject":
            subject,
        "documents":
            subject_documents
    })
@app.route(
    "/api/subjects/<subject_id>",
    methods=["DELETE"]
)
def delete_subject(
    subject_id
):
    subjects = load_subjects()
    subject = next(
        (
            item
            for item
            in subjects
            if item.get(
                "id"
            ) == subject_id
        ),
        None
    )
    if not subject:
        return jsonify({
            "success":
                False,
            "message":
                "Subject not found."
        }), 404
    subjects = [
        item
        for item
        in subjects
        if item.get(
            "id"
        ) != subject_id
    ]
    save_subjects(
        subjects
    )
    # Remove subject association
    # from existing documents.
    documents = load_documents()
    for document in documents:
        if document.get(
            "subject_id"
        ) == subject_id:
            document[
                "subject_id"
            ] = None
    save_documents(
        documents
    )
    return jsonify({
        "success":
            True,
        "message":
            "Subject deleted successfully."
    })
@app.route(
    "/api/upload-multiple",
    methods=["POST"]
)
def upload_multiple():
    subject_id = (
        request.form.get(
            "subject_id"
        )
    )
    if not subject_id:
        return jsonify({
            "success":
                False,
            "message":
                "subject_id is required."
        }), 400
    subjects = load_subjects()
    subject = next(
        (
            item
            for item
            in subjects
            if item.get(
                "id"
            ) == subject_id
        ),
        None
    )
    if not subject:
        return jsonify({
            "success":
                False,
            "message":
                "Subject not found."
        }), 404
    files = request.files.getlist(
        "files"
    )
    if not files:
        return jsonify({
            "success":
                False,
            "message":
                "No files were selected."
        }), 400
    documents = load_documents()
    uploaded_documents = []
    errors = []
    for file in files:
        if not file or not file.filename:
            continue
        if not allowed_file(
            file.filename
        ):
            errors.append({
                "filename":
                    file.filename,
                "message":
                    "Unsupported file type."
            })
            continue
        original_name = secure_filename(
            file.filename
        )
        extension = (
            original_name
            .rsplit(
                ".",
                1
            )[1]
            .lower()
        )
        document_id = uuid4().hex
        stored_name = (
            f"{document_id}.{extension}"
        )
        file_path = os.path.join(
            UPLOAD_FOLDER,
            stored_name
        )
        try:
            file.save(
                file_path
            )
            pages = extract_pages(
                file_path,
                extension
            )
            analysis = analyze_document(
                pages
            )
            document = {
                "id":
                    document_id,
                "name":
                    original_name,
                "original_name":
                    original_name,
                "stored_name":
                    stored_name,
                "type":
                    extension,
                "subject_id":
                    subject_id,
                "subject_name":
                    subject[
                        "name"
                    ],
                "page_count":
                    len(pages),
                "pages":
                    pages,
                "summary":
                    analysis[
                        "summary"
                    ],
                "topics":
                    analysis[
                        "topics"
                    ],
                "word_count":
                    analysis[
                        "word_count"
                    ],
                "character_count":
                    analysis[
                        "character_count"
                    ]
            }
            documents.append(
                document
            )
            uploaded_documents.append(
                document
            )
        except Exception as error:
            print(
                "MULTIPLE UPLOAD ERROR:",
                repr(error)
            )
            if os.path.exists(
                file_path
            ):
                try:
                    os.remove(
                        file_path
                    )
                except Exception:
                    pass
            errors.append({
                "filename":
                    original_name,
                "message":
                    str(error)
            })
    save_documents(
        documents
    )
    return jsonify({
        "success":
            len(
                uploaded_documents
            ) > 0,
        "message":
            (
                f"{len(uploaded_documents)} "
                f"document(s) uploaded."
            ),
        "documents":
            uploaded_documents,
        "errors":
            errors
    })
@app.route(
    "/api/subjects/<subject_id>/documents",
    methods=["GET"]
)
def get_subject_documents(
    subject_id
):
    subjects = load_subjects()
    subject = next(
        (
            item
            for item
            in subjects
            if item.get(
                "id"
            ) == subject_id
        ),
        None
    )
    if not subject:
        return jsonify({
            "success":
                False,
            "message":
                "Subject not found."
        }), 404
    documents = load_documents()
    subject_documents = [
        document
        for document
        in documents
        if document.get(
            "subject_id"
        ) == subject_id
    ]
    return jsonify({
        "success":
            True,
        "subject":
            subject,
        "documents":
            subject_documents
    })
@app.route(
    "/api/quiz/generate",
    methods=["POST"]
)
def generate_quiz():
    try:
        if not is_gemini_configured():
            return jsonify({
                "success":
                    False,
                "message":
                    "Gemini AI is not configured."
            }), 503
        data = (
            request.get_json(
                silent=True
            )
            or {}
        )
        subject_id = data.get(
            "subject_id"
        )
        document_ids = data.get(
            "document_ids",
            []
        )
        question_count = int(
            data.get(
                "question_count",
                10
            )
        )
        difficulty = (
            data.get(
                "difficulty",
                "medium"
            )
            .lower()
        )
        if not subject_id:
            return jsonify({
                "success":
                    False,
                "message":
                    "subject_id is required."
            }), 400
        question_count = max(
            5,
            min(
                question_count,
                20
            )
        )
        subjects = load_subjects()
        subject = next(
            (
                item
                for item
                in subjects
                if item.get(
                    "id"
                ) == subject_id
            ),
            None
        )
        if not subject:
            return jsonify({
                "success":
                    False,
                "message":
                    "Subject not found."
            }), 404
        documents = load_documents()
        subject_documents = [
            document
            for document
            in documents
            if document.get(
                "subject_id"
            ) == subject_id
        ]
        if document_ids:
            subject_documents = [
                document
                for document
                in subject_documents
                if document.get(
                    "id"
                ) in document_ids
            ]
        if not subject_documents:
            return jsonify({
                "success":
                    False,
                "message":
                    "No study materials are "
                    "available for this subject."
            }), 400
        context_parts = []
        for document in subject_documents:
            for page in document.get(
                "pages",
                []
            ):
                text = page.get(
                    "text",
                    ""
                )
                if not text:
                    continue
                context_parts.append(
                    f"""
DOCUMENT:
{document.get("name")}
PAGE:
{page.get("page")}
CONTENT:
{text[:8000]}
"""
                )
        context = "\n".join(
            context_parts
        )
        context = context[
            :60000
        ]
        prompt = f"""
You are an AI quiz generator
for AI Knowledge DNA.
Create a multiple-choice quiz
from the student's uploaded
study material.
Subject:
{subject["name"]}
Difficulty:
{difficulty}
Number of questions:
{question_count}
STRICT RULES:
1. Questions must be based ONLY
   on the supplied study material.
2. Do not invent facts.
3. Each question must have exactly
   four options.
4. Exactly one option must be correct.
5. Include a page number.
6. Questions should test understanding,
   not just memorization.
7. Use simple student-friendly English.
8. Return ONLY valid JSON.
9. Do NOT use Markdown.
Use exactly this JSON structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "correct_answer": 0,
      "explanation": "Short explanation",
      "page": 3,
      "topic": "Cloud Computing"
    }}
  ]
}}
IMPORTANT:
correct_answer must be:
0 = first option
1 = second option
2 = third option
3 = fourth option
STUDY MATERIAL:
{context}
"""
        client = get_gemini_client()
        response = None
        last_error = None
        for attempt in range(4):
            try:
                response = (
                    client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=prompt
                    )
                )
                break
            except Exception as error:
                last_error = error
                error_text = str(
                    error
                ).lower()
                temporary = (
                    "503"
                    in error_text
                    or
                    "unavailable"
                    in error_text
                    or
                    "overloaded"
                    in error_text
                    or
                    "429"
                    in error_text
                    or
                    "resource exhausted"
                    in error_text
                )
                if not temporary:
                    raise
                if attempt >= 3:
                    raise RuntimeError(
                        "Gemini is temporarily "
                        "unavailable. Please try "
                        "again shortly."
                    )
                time.sleep(
                    (2 ** attempt)
                    + random.uniform(
                        0,
                        1
                    )
                )
        if not response:
            raise RuntimeError(
                str(last_error)
            )
        raw = (
            response.text
            or ""
        ).strip()
        # Remove accidental code fences.
        raw = re.sub(
            r"^```json\s*",
            "",
            raw,
            flags=re.IGNORECASE
        )
        raw = re.sub(
            r"^```\s*",
            "",
            raw
        )
        raw = re.sub(
            r"\s*```$",
            "",
            raw
        )
        try:
            quiz_data = json.loads(
                raw
            )
        except json.JSONDecodeError:
            match = re.search(
                r"\{.*\}",
                raw,
                flags=re.DOTALL
            )
            if not match:
                raise RuntimeError(
                    "Gemini returned an "
                    "invalid quiz response."
                )
            quiz_data = json.loads(
                match.group(0)
            )
        questions = (
            quiz_data.get(
                "questions",
                []
            )
        )
        if not questions:
            raise RuntimeError(
                "No quiz questions were generated."
            )
        cleaned_questions = []
        for index, question in enumerate(
            questions[:question_count]
        ):
            options = question.get(
                "options",
                []
            )
            if len(options) != 4:
                continue
            correct_answer = int(
                question.get(
                    "correct_answer",
                    0
                )
            )
            if correct_answer < 0:
                correct_answer = 0
            if correct_answer > 3:
                correct_answer = 3
            cleaned_questions.append({
                "id":
                    uuid4().hex,
                "question":
                    question.get(
                        "question",
                        ""
                    ),
                "options":
                    options,
                "correct_answer":
                    correct_answer,
                "explanation":
                    question.get(
                        "explanation",
                        ""
                    ),
                "page":
                    question.get(
                        "page",
                        1
                    ),
                "topic":
                    question.get(
                        "topic",
                        "General"
                    )
            })
        if not cleaned_questions:
            raise RuntimeError(
                "The AI did not generate "
                "valid quiz questions."
            )
        quiz = {
            "id":
                uuid4().hex,
            "subject_id":
                subject_id,
            "subject_name":
                subject[
                    "name"
                ],
            "document_ids":
                [
                    document["id"]
                    for document
                    in subject_documents
                ],
            "question_count":
                len(
                    cleaned_questions
                ),
            "difficulty":
                difficulty,
            "questions":
                cleaned_questions,
            "created_at":
                time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            "attempted":
                False,
            "score":
                None,
            "accuracy":
                None
        }
        quizzes = load_quizzes()
        quizzes.append(
            quiz
        )
        save_quizzes(
            quizzes
        )
        # Do not expose correct answers
        # to the frontend before submission.
        client_quiz = {
            **quiz,
            "questions": [
                {
                    "id":
                        question["id"],
                    "question":
                        question["question"],
                    "options":
                        question["options"],
                    "page":
                        question["page"],
                    "topic":
                        question["topic"]
                }
                for question
                in cleaned_questions
            ]
        }
        return jsonify({
            "success":
                True,
            "quiz":
                client_quiz
        })
    except Exception as error:
        print()
        print(
            "QUIZ GENERATION ERROR:"
        )
        print(
            repr(error)
        )
        print()
        return jsonify({
            "success":
                False,
            "message":
                "Unable to generate quiz.",
            "error":
                str(error)
        }), 500
@app.route(
    "/api/quiz/<quiz_id>/submit",
    methods=["POST"]
)
def submit_quiz(
    quiz_id
):
    try:
        data = (
            request.get_json(
                silent=True
            )
            or {}
        )
        answers = data.get(
            "answers",
            {}
        )
        quizzes = load_quizzes()
        quiz = next(
            (
                item
                for item
                in quizzes
                if item.get(
                    "id"
                ) == quiz_id
            ),
            None
        )
        if not quiz:
            return jsonify({
                "success":
                    False,
                "message":
                    "Quiz not found."
            }), 404
        score = 0
        results = []
        for question in quiz.get(
            "questions",
            []
        ):
            question_id = question[
                "id"
            ]
            selected = answers.get(
                question_id
            )
            try:
                selected = int(
                    selected
                )
            except (
                TypeError,
                ValueError
            ):
                selected = -1
            correct = (
                selected
                == question[
                    "correct_answer"
                ]
            )
            if correct:
                score += 1
            results.append({
                "question_id":
                    question_id,
                "selected_answer":
                    selected,
                "correct_answer":
                    question[
                        "correct_answer"
                    ],
                "correct":
                    correct,
                "explanation":
                    question.get(
                        "explanation",
                        ""
                    ),
                "page":
                    question.get(
                        "page"
                    ),
                "topic":
                    question.get(
                        "topic"
                    )
            })
        total = len(
            quiz[
                "questions"
            ]
        )
        accuracy = round(
            (
                score / total
            ) * 100,
            2
        ) if total else 0
        quiz[
            "attempted"
        ] = True
        quiz[
            "score"
        ] = score
        quiz[
            "accuracy"
        ] = accuracy
        quiz[
            "completed_at"
        ] = time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        save_quizzes(
            quizzes
        )
        return jsonify({
            "success":
                True,
            "score":
                score,
            "total":
                total,
            "accuracy":
                accuracy,
            "results":
                results
        })
    except Exception as error:
        print(
            "QUIZ SUBMIT ERROR:",
            repr(error)
        )
        return jsonify({
            "success":
                False,
            "message":
                "Unable to submit quiz.",
            "error":
                str(error)
        }), 500
@app.route(
    "/api/quizzes",
    methods=["GET"]
)
def get_quizzes():
    quizzes = load_quizzes()
    result = []
    for quiz in quizzes:
        result.append({
            "id":
                quiz.get(
                    "id"
                ),
            "subject_id":
                quiz.get(
                    "subject_id"
                ),
            "subject_name":
                quiz.get(
                    "subject_name"
                ),
            "question_count":
                quiz.get(
                    "question_count"
                ),
            "difficulty":
                quiz.get(
                    "difficulty"
                ),
            "attempted":
                quiz.get(
                    "attempted",
                    False
                ),
            "score":
                quiz.get(
                    "score"
                ),
            "accuracy":
                quiz.get(
                    "accuracy"
                ),
            "created_at":
                quiz.get(
                    "created_at"
                )
        })
    return jsonify({
        "success":
            True,
        "quizzes":
            result
    })
@app.route(
    "/api/dashboard/stats",
    methods=["GET"]
)
def dashboard_stats():
    documents = load_documents()
    quizzes = load_quizzes()
    topic_names = set()
    for document in documents:
        for topic in document.get(
            "topics",
            []
        ):
            name = topic.get(
                "name"
            )
            if name:
                topic_names.add(
                    name.lower()
                )
    attempted_quizzes = [
        quiz
        for quiz
        in quizzes
        if quiz.get(
            "attempted"
        )
    ]
    if attempted_quizzes:
        total_questions = sum(
            quiz.get(
                "question_count",
                0
            )
            for quiz
            in attempted_quizzes
        )
        total_correct = sum(
            quiz.get(
                "score",
                0
            )
            for quiz
            in attempted_quizzes
        )
        quiz_accuracy = round(
            (
                total_correct
                /
                total_questions
            )
            * 100,
            1
        ) if total_questions else 0
    else:
        quiz_accuracy = 0
    # Basic Knowledge DNA score.
    # As the project grows, this will be
    # replaced by the complete mastery model.
    if topic_names:
        knowledge_dna = round(
            min(
                100,
                (
                    len(topic_names)
                    * 5
                )
            ),
            1
        )
    else:
        knowledge_dna = 0
    # Current document-based
    # topic count.
    topics_learned = len(
        topic_names
    )
    # Learning streak will be
    # connected to activity tracking
    # in the next phase.
    learning_streak = 0
    # Study hours will be connected
    # to study-session tracking.
    study_hours = 0
    return jsonify({
        "success":
            True,
        "stats": {
            "knowledge_dna":
                knowledge_dna,
            "topics_learned":
                topics_learned,
            "quiz_accuracy":
                quiz_accuracy,
            "learning_streak":
                learning_streak,
            "study_hours":
                study_hours
        }
    })
if __name__ == "__main__":
    print()
    print(
        "=========================================="
    )
    print(
        "       AI KNOWLEDGE DNA BACKEND"
    )
    print(
        "=========================================="
    )
    print(
        f"Server: "
        f"http://127.0.0.1:5000"
    )
    print()
    print(
        f"Gemini configured: "
        f"{is_gemini_configured()}"
    )
    print()
    print(
        f"Gemini model: "
        f"{GEMINI_MODEL}"
    )
    print()
    print(
        f"Upload folder: "
        f"{UPLOAD_FOLDER}"
    )
    print(
        f"Documents database: "
        f"{DOCUMENTS_FILE}"
    )
    print(
        "=========================================="
    )
    print()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
