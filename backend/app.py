import os
import re
import json
import time
import random
from datetime import datetime
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
from google.genai import types
from services.ai.ai_router import generate_ai_response
from models import db, User, LearningProgress
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
def get_current_user_id():
    return int(get_jwt_identity())

# All JSON-backed learning data must carry user_id and must be filtered
# through the authenticated JWT identity before it is returned or changed.
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
def get_legacy_owner_user_id():
    try:
        with app.app_context():
            user = User.query.order_by(User.id.asc()).first()
            if not user:
                return None
            return int(user.id)
    except Exception:
        return None
def migrate_legacy_json_records(file_path, collection_name):
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            return False
    except Exception:
        return False
    legacy_user_id = get_legacy_owner_user_id()
    if legacy_user_id is None:
        return False
    changed = False
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("user_id") is None:
            item["user_id"] = legacy_user_id
            changed = True
    if not changed:
        return False
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
    print(f"Migrated legacy {collection_name} records to user_id={legacy_user_id}.")
    return True
def load_documents():
    migrate_legacy_json_records(DOCUMENTS_FILE, "documents")
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
def _same_user(record_user_id, user_id):
    try:
        return int(record_user_id) == int(user_id)
    except (TypeError, ValueError):
        return False

def filter_documents_for_user(documents, user_id):
    if user_id is None:
        return []
    return [
        document
        for document in documents
        if isinstance(document, dict)
        and _same_user(document.get("user_id"), user_id)
    ]

def filter_subjects_for_user(subjects, user_id):
    if user_id is None:
        return []
    return [
        subject
        for subject in subjects
        if isinstance(subject, dict)
        and _same_user(subject.get("user_id"), user_id)
    ]

def filter_quizzes_for_user(quizzes, user_id):
    if user_id is None:
        return []
    return [
        quiz
        for quiz in quizzes
        if isinstance(quiz, dict)
        and _same_user(quiz.get("user_id"), user_id)
    ]
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

def clean_voice_answer(
    answer
):
    """
    Produces a natural, speakable response for the voice assistant.
    Gemini Search grounding can return citations in metadata; they are not
    exposed in the voice UI.
    """
    answer = clean_ai_answer(
        answer
    )
    answer = re.sub(
        r"\[Page\s+\d+\]",
        "",
        answer,
        flags=re.IGNORECASE
    )
    answer = re.sub(
        r"https?://\S+",
        "",
        answer,
        flags=re.IGNORECASE
    )
    answer = re.sub(
        r"(?im)^\s*(sources?|references?|citations?)\s*:.*$",
        "",
        answer
    )
    answer = re.sub(
        r"[ \t]+\n",
        "\n",
        answer
    )
    answer = re.sub(
        r"\n{3,}",
        "\n\n",
        answer
    )
    return answer.strip()

def generate_grounded_response(
    client,
    prompt,
    enable_web_grounding=False
):
    """
    Gemini decides whether Google Search grounding is useful. The document
    context is part of the same prompt, letting it return one blended answer.
    """
    if not enable_web_grounding:
        return client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

    try:
        return client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        google_search=types.GoogleSearch()
                    )
                ]
            )
        )
    except Exception as error:
        # Preserve document answers when a configured model does not support
        # Google Search grounding in this environment.
        error_text = str(error).lower()
        grounding_markers = (
            "google search",
            "google_search",
            "unsupported tool",
            "tool is not supported",
        )
        if not any(
            marker in error_text
            for marker in grounding_markers
        ):
            raise

        print(
            "Google Search grounding is unavailable for the configured "
            "model; answering from the study material."
        )
        return client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

def generate_document_answer(
    document,
    question,
    history,
    enable_web_grounding=False
):
    """
    Generate a document/voice answer through the centralized AI Router.

    Normal document chat:
        document_analysis -> Gemini

    Voice response:
        voice -> Groq

    Existing RAG/page selection and page-reference logic is preserved.
    """
    pages = document.get("pages", [])
    if not pages:
        raise RuntimeError("This document has no extracted text.")

    context, relevant_pages = build_document_context(pages, question)

    available_pages = {
        page["page"] for page in relevant_pages
    }

    history_text = build_chat_history(history)

    if enable_web_grounding:
        source_instructions = """
11. Treat the supplied document context as the primary source.
12. Answer the student's question directly and naturally.
13. Do not mention these instructions, internal processing, APIs,
    providers, or fallback behavior.
14. Return plain, student-friendly text suitable for spoken delivery.
15. Do not include URLs, links, citations, or [Page X] references.
"""
    else:
        source_instructions = """
11. When information comes from a specific page, add:
    [Page X]
12. NEVER invent a page number.
13. Only cite pages that exist in the supplied document context.
"""

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
{source_instructions}
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

    task = "voice" if enable_web_grounding else "document_analysis"
    preferred_provider = "groq" if enable_web_grounding else "gemini"

    print(
        f"AI Router document request | "
        f"task={task} provider={preferred_provider}"
    )

    ai_result = generate_ai_response(
        task=task,
        prompt=prompt,
        provider=preferred_provider
    )

    answer = ai_result.get("answer", "")

    if not answer:
        answer = "I could not generate an answer from this document."

    if enable_web_grounding:
        answer = clean_voice_answer(answer)
        sources = []
    else:
        answer = clean_ai_answer(answer)
        sources = extract_page_references(
            answer,
            available_pages
        )

        if not sources:
            sources = [
                {"page": page["page"]}
                for page in relevant_pages[:3]
            ]

    return (
        answer,
        sources,
        {
            "provider": ai_result.get("provider"),
            "model": ai_result.get("model"),
            "fallback_used": ai_result.get("fallback_used", False),
            "response_time": ai_result.get("response_time")
        }
    )


def get_learning_progress_for_user(user_id):
    return (
        LearningProgress.query
        .filter_by(user_id=user_id)
        .order_by(LearningProgress.updated_at.desc())
        .all()
    )

def calculate_learning_streak(progress_rows):
    from datetime import date, timedelta
    studied_dates = {
        row.last_studied.date()
        for row in progress_rows
        if row.last_studied
    }
    if not studied_dates:
        return 0
    current = date.today()
    if current not in studied_dates:
        return 0
    streak = 0
    while current in studied_dates:
        streak += 1
        current -= timedelta(days=1)
    return streak

def calculate_knowledge_dna(progress_rows, quiz_accuracy=0):
    scores = [
        float(row.mastery_score or 0)
        for row in progress_rows
        if row.questions_attempted or row.study_minutes or row.last_studied
    ]
    mastery = sum(scores) / len(scores) if scores else 0
    return round((mastery * 0.7) + (float(quiz_accuracy) * 0.3), 1) if scores else 0

def update_learning_progress(
    user_id,
    topic,
    study_minutes=0,
    questions_attempted=0,
    questions_correct=0,
):
    topic = str(topic or "General").strip()[:255] or "General"
    progress = (
        LearningProgress.query
        .filter_by(user_id=user_id, topic=topic)
        .first()
    )

    if not progress:
        progress = LearningProgress(
            user_id=user_id,
            topic=topic,
            mastery_score=0,
            questions_attempted=0,
            questions_correct=0,
            study_minutes=0,
        )
        db.session.add(progress)

    progress.study_minutes = (
        int(progress.study_minutes or 0) + max(0, int(study_minutes or 0))
    )
    progress.questions_attempted = (
        int(progress.questions_attempted or 0)
        + max(0, int(questions_attempted or 0))
    )
    progress.questions_correct = (
        int(progress.questions_correct or 0)
        + max(0, int(questions_correct or 0))
    )

    quiz_mastery = (
        progress.questions_correct / progress.questions_attempted * 100
        if progress.questions_attempted
        else 0
    )
    study_mastery = min(100, float(progress.study_minutes or 0) * 2)

    if progress.questions_attempted:
        progress.mastery_score = round(
            (study_mastery * 0.4) + (quiz_mastery * 0.6),
            1,
        )
    else:
        progress.mastery_score = round(study_mastery, 1)

    progress.last_studied = datetime.utcnow()
    return progress

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
@jwt_required()
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
        "user_id":
            get_current_user_id(),
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
@jwt_required()
def get_documents():
    current_user_id = get_current_user_id()
    documents = filter_documents_for_user(load_documents(), current_user_id)
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
@jwt_required()
def get_document(
    document_id
):
    documents = filter_documents_for_user(load_documents(), get_current_user_id())
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
                "Document not found or access denied."
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
    enable_web_grounding = bool(
        data.get(
            "voice_response",
            False
        )
    )
    if not question:
        raise ValueError(
            "Question is required."
        )
    current_user_id = get_current_user_id()
    documents = filter_documents_for_user(load_documents(), current_user_id)
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
        raise PermissionError(
            "Document not found or access denied."
        )
    answer, sources, ai_info = (
        generate_document_answer(
            document,
            question,
            history,
            enable_web_grounding=enable_web_grounding
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
        "provider":
            ai_info.get("provider"),
        "model":
            ai_info.get("model"),
        "fallback_used":
            ai_info.get("fallback_used", False),
        "response_time":
            ai_info.get("response_time")
    }
@app.route(
    "/api/chat",
    methods=["POST"]
)
@jwt_required()
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
    except PermissionError as error:
        return jsonify({
            "success":
                False,
            "message":
                str(error)
        }), 403
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
@jwt_required()
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
    except PermissionError as error:
        return jsonify({
            "success":
                False,
            "message":
                str(error)
        }), 403
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
@jwt_required()
def serve_file(
    filename
):
    current_user_id = get_current_user_id()
    documents = load_documents()
    owned_document = next(
        (
            item
            for item in documents
            if item.get("stored_name") == filename
            and int(item.get("user_id") or -1) == current_user_id
        ),
        None
    )
    if not owned_document:
        return jsonify({
            "success": False,
            "message": "File not found or access denied."
        }), 403
    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )
@app.route(
    "/api/documents/<document_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_document(
    document_id
):
    current_user_id = get_current_user_id()
    documents = filter_documents_for_user(load_documents(), current_user_id)
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
                "Document not found or access denied."
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
    all_documents = load_documents()
    documents = [
        item
        for item in all_documents
        if not (
            item.get("id") == document_id
            and _same_user(item.get("user_id"), current_user_id)
        )
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
STUDY_SESSIONS_FILE = os.path.join(
    DATA_FOLDER,
    "study_sessions.json"
)
def load_subjects():
    migrate_legacy_json_records(SUBJECTS_FILE, "subjects")
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
def load_study_session_counts():
    if not os.path.exists(STUDY_SESSIONS_FILE):
        return {}
    try:
        with open(STUDY_SESSIONS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except Exception as error:
        print("STUDY SESSION COUNT LOAD ERROR:", error)
        return {}

def save_study_session_counts(data):
    with open(STUDY_SESSIONS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def increment_study_session_count(user_id, topic):
    data = load_study_session_counts()
    user_data = data.setdefault(str(user_id), {})
    user_data[topic] = int(user_data.get(topic, 0)) + 1
    save_study_session_counts(data)
    return user_data[topic]

def get_study_session_count(user_id, topic):
    data = load_study_session_counts()
    return int(data.get(str(user_id), {}).get(topic, 0))

def load_quizzes():
    migrate_legacy_json_records(QUIZZES_FILE, "quizzes")
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
@jwt_required()
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
        current_user_id = get_current_user_id()
        subjects = filter_subjects_for_user(load_subjects(), current_user_id)
        existing = next(
            (
                subject
                for subject
                in subjects
                if subject.get("name", "").lower() == name.lower()
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
            "user_id":
                current_user_id,
            "created_at":
                time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        }
        all_subjects = load_subjects()
        all_subjects.append(subject)
        save_subjects(all_subjects)
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
@jwt_required()
def get_subjects():
    current_user_id = get_current_user_id()
    subjects = filter_subjects_for_user(load_subjects(), current_user_id)
    documents = filter_documents_for_user(load_documents(), current_user_id)
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
@jwt_required()
def get_subject(
    subject_id
):
    current_user_id = get_current_user_id()
    subjects = filter_subjects_for_user(load_subjects(), current_user_id)
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
                "Subject not found or access denied."
        }), 404
    documents = filter_documents_for_user(load_documents(), current_user_id)
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
@jwt_required()
def delete_subject(subject_id):
    try:
        current_user_id = get_current_user_id()

        subjects = filter_subjects_for_user(
            load_subjects(),
            current_user_id
        )

        subject = next(
            (
                item
                for item in subjects
                if item.get("id") == subject_id
            ),
            None
        )

        if not subject:
            return jsonify({
                "success": False,
                "message": "Subject not found or access denied."
            }), 404

        documents = load_documents()

        subject_documents = [
            document
            for document in documents
            if (
                document.get("subject_id") == subject_id
                and _same_user(
                    document.get("user_id"),
                    current_user_id
                )
            )
        ]

        subject_topics = set()

        for document in subject_documents:
            for topic in document.get("topics", []):
                if isinstance(topic, dict):
                    topic_name = str(
                        topic.get("name") or ""
                    ).strip()
                else:
                    topic_name = str(topic or "").strip()

                if topic_name:
                    subject_topics.add(
                        _normalized_learning_topic(topic_name)
                    )

        all_quizzes = load_quizzes()

        subject_quizzes = [
            quiz
            for quiz in all_quizzes
            if (
                quiz.get("subject_id") == subject_id
                and _same_user(
                    quiz.get("user_id"),
                    current_user_id
                )
            )
        ]

        for quiz in subject_quizzes:
            for question in quiz.get("questions", []):
                if not isinstance(question, dict):
                    continue

                topic_name = str(
                    question.get("topic") or ""
                ).strip()

                if topic_name:
                    subject_topics.add(
                        _normalized_learning_topic(topic_name)
                    )

        remaining_documents = []

        for document in documents:
            is_subject_document = (
                document.get("subject_id") == subject_id
                and _same_user(
                    document.get("user_id"),
                    current_user_id
                )
            )

            if is_subject_document:
                stored_name = document.get("stored_name")

                if stored_name:
                    file_path = os.path.join(
                        UPLOAD_FOLDER,
                        stored_name
                    )

                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as error:
                            print(
                                "SUBJECT FILE DELETE ERROR:",
                                error
                            )

                continue

            remaining_documents.append(document)

        save_documents(remaining_documents)

        remaining_quizzes = [
            quiz
            for quiz in all_quizzes
            if not (
                quiz.get("subject_id") == subject_id
                and _same_user(
                    quiz.get("user_id"),
                    current_user_id
                )
            )
        ]

        save_quizzes(remaining_quizzes)

        remaining_subject_topics = set()

        for document in remaining_documents:
            if not _same_user(
                document.get("user_id"),
                current_user_id
            ):
                continue

            for topic in document.get("topics", []):
                if isinstance(topic, dict):
                    topic_name = str(
                        topic.get("name") or ""
                    ).strip()
                else:
                    topic_name = str(topic or "").strip()

                if topic_name:
                    remaining_subject_topics.add(
                        _normalized_learning_topic(topic_name)
                    )

        for quiz in remaining_quizzes:
            if not _same_user(
                quiz.get("user_id"),
                current_user_id
            ):
                continue

            for question in quiz.get("questions", []):
                if not isinstance(question, dict):
                    continue

                topic_name = str(
                    question.get("topic") or ""
                ).strip()

                if topic_name:
                    remaining_subject_topics.add(
                        _normalized_learning_topic(topic_name)
                    )

        topics_to_delete = (
            subject_topics - remaining_subject_topics
        )

        if topics_to_delete:
            progress_rows = get_learning_progress_for_user(
                current_user_id
            )

            for row in progress_rows:
                row_topic = _normalized_learning_topic(
                    row.topic
                )

                if row_topic in topics_to_delete:
                    db.session.delete(row)

            db.session.commit()

        try:
            study_sessions = load_study_session_counts()

            user_sessions = study_sessions.get(
                str(current_user_id),
                {}
            )

            if isinstance(user_sessions, dict):
                for topic in list(user_sessions.keys()):
                    normalized_topic = _normalized_learning_topic(
                        topic
                    )

                    if normalized_topic in topics_to_delete:
                        del user_sessions[topic]

                study_sessions[str(current_user_id)] = user_sessions
                save_study_session_counts(study_sessions)

        except Exception as error:
            print(
                "SUBJECT STUDY SESSION DELETE ERROR:",
                repr(error)
            )

        all_subjects = load_subjects()

        remaining_subjects = [
            item
            for item in all_subjects
            if not (
                item.get("id") == subject_id
                and _same_user(
                    item.get("user_id"),
                    current_user_id
                )
            )
        ]

        save_subjects(remaining_subjects)

        return jsonify({
            "success": True,
            "message": "Subject and all related learning data deleted successfully."
        }), 200

    except Exception as error:
        db.session.rollback()

        print(
            "SUBJECT DELETE ERROR:",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete subject.",
            "error": str(error)
        }), 500
@app.route(
    "/api/learning/progress",
    methods=["GET"]
)
@jwt_required()
def get_learning_progress():
    try:
        user_id = get_current_user_id()
        rows = get_learning_progress_for_user(user_id)
        progress = [{
            "id": row.id,
            "topic": row.topic,
            "mastery_score": round(float(row.mastery_score or 0), 1),
            "questions_attempted": int(row.questions_attempted or 0),
            "questions_correct": int(row.questions_correct or 0),
            "study_minutes": int(row.study_minutes or 0),
            "study_sessions": get_study_session_count(user_id, row.topic),
            "last_studied": (
                row.last_studied.isoformat()
                if row.last_studied else None
            ),
        } for row in rows]

        # Build subject-wise learning data without changing the existing
        # LearningProgress table. Topics are mapped to subjects using the
        # user's uploaded document topics first, then quiz question topics.
        subjects = filter_subjects_for_user(
            load_subjects(),
            user_id,
        )
        documents = filter_documents_for_user(
            load_documents(),
            user_id,
        )
        quizzes = filter_quizzes_for_user(
            load_quizzes(),
            user_id,
        )

        subject_topic_map = {}
        topic_subject_candidates = {}

        for subject in subjects:
            subject_id = subject.get("id")
            subject_topic_map[subject_id] = set()

        for document in documents:
            subject_id = document.get("subject_id")
            if subject_id not in subject_topic_map:
                continue
            for topic in document.get("topics", []):
                if isinstance(topic, dict):
                    topic_name = str(topic.get("name") or "").strip()
                else:
                    topic_name = str(topic or "").strip()
                if topic_name:
                    key = topic_name.lower()
                    subject_topic_map[subject_id].add(key)
                    topic_subject_candidates.setdefault(key, []).append(subject_id)

        for quiz in quizzes:
            subject_id = quiz.get("subject_id")
            if subject_id not in subject_topic_map:
                continue
            for question in quiz.get("questions", []):
                topic_name = str(question.get("topic") or "").strip()
                if topic_name:
                    key = topic_name.lower()
                    subject_topic_map[subject_id].add(key)
                    topic_subject_candidates.setdefault(key, []).append(subject_id)

        subject_progress = []
        for subject in subjects:
            subject_id = subject.get("id")
            learned = []
            weak = []

            for row in rows:
                topic_key = str(row.topic or "General").strip().lower()
                candidates = topic_subject_candidates.get(topic_key, [])
                belongs = subject_id in candidates

                if not belongs and topic_key in subject_topic_map.get(subject_id, set()):
                    belongs = True

                if not belongs:
                    continue

                item = {
                    "id": row.id,
                    "topic": row.topic,
                    "mastery_score": round(float(row.mastery_score or 0), 1),
                    "questions_attempted": int(row.questions_attempted or 0),
                    "questions_correct": int(row.questions_correct or 0),
                    "study_minutes": int(row.study_minutes or 0),
                    "last_studied": (
                        row.last_studied.isoformat()
                        if row.last_studied else None
                    ),
                }
                learned.append(item)
                if int(row.questions_attempted or 0) > 0:
                    weak.append(item)

            subject_progress.append({
                "id": subject_id,
                "name": subject.get("name", "Unnamed Subject"),
                "description": subject.get("description", ""),
                "learned_topics": learned,
                "weak_topics": sorted(
                    weak,
                    key=lambda item: float(item.get("mastery_score") or 0),
                )[:3],
            })

        return jsonify({
            "success": True,
            "progress": progress,
            "subjects": subject_progress,
            "learning_streak": calculate_learning_streak(rows),
            "study_hours": round(
                sum(int(row.study_minutes or 0) for row in rows) / 60,
                1,
            ),
        }), 200
    except Exception as error:
        print("LEARNING PROGRESS ERROR:", repr(error))
        return jsonify({
            "success": False,
            "message": "Unable to get learning progress.",
            "error": str(error)
        }), 500


def _normalized_learning_topic(value):
    return str(value or "").strip().casefold()


def _document_topic_name(topic):
    if isinstance(topic, dict):
        return str(topic.get("name") or "").strip()
    return str(topic or "").strip()


def build_learning_insights(user_id):
    """Build user-scoped graph and plan data from existing learning records."""
    subjects = filter_subjects_for_user(load_subjects(), user_id)
    documents = filter_documents_for_user(load_documents(), user_id)
    quizzes = filter_quizzes_for_user(load_quizzes(), user_id)
    progress_rows = get_learning_progress_for_user(user_id)

    subjects_by_id = {
        subject.get("id"): subject
        for subject in subjects
        if subject.get("id") is not None
    }
    topic_entries = {}
    topic_subject_candidates = {}
    document_details = {}

    def add_topic(topic_name, subject_id=None, document=None):
        name = str(topic_name or "").strip()[:255]
        normalized = _normalized_learning_topic(name)
        if not normalized:
            return None

        if subject_id not in subjects_by_id:
            subject_id = None
            subject_name = "Independent learning"
            subject_key = "independent"
        else:
            subject_name = str(subjects_by_id[subject_id].get("name") or "Subject")
            subject_key = str(subject_id)

        key = f"{subject_key}:{normalized}"
        entry = topic_entries.setdefault(key, {
            "key": key,
            "topic": name,
            "subject_id": subject_id,
            "subject_name": subject_name,
            "document_ids": set(),
            "document_names": set(),
            "progress": None,
        })

        if subject_id is not None:
            candidates = topic_subject_candidates.setdefault(normalized, [])
            if subject_id not in candidates:
                candidates.append(subject_id)

        if document:
            document_id = str(document.get("id") or "")
            document_name = str(
                document.get("name")
                or document.get("original_name")
                or "Study material"
            ).strip()
            if document_id:
                entry["document_ids"].add(document_id)
                document_details.setdefault(document_id, {
                    "id": document_id,
                    "name": document_name or "Study material",
                    "subject_id": subject_id,
                })
            if document_name:
                entry["document_names"].add(document_name)
        return entry

    for document in documents:
        subject_id = document.get("subject_id")
        document_has_topic = False
        for topic in document.get("topics", []):
            if add_topic(_document_topic_name(topic), subject_id, document):
                document_has_topic = True

        if not document_has_topic and subject_id in subjects_by_id:
            document_id = str(document.get("id") or "")
            if document_id:
                document_details.setdefault(document_id, {
                    "id": document_id,
                    "name": str(
                        document.get("name")
                        or document.get("original_name")
                        or "Study material"
                    ).strip() or "Study material",
                    "subject_id": subject_id,
                })

    for quiz in quizzes:
        subject_id = quiz.get("subject_id")
        for question in quiz.get("questions", []):
            add_topic(question.get("topic"), subject_id)

    for row in progress_rows:
        topic_name = str(row.topic or "General").strip()[:255] or "General"
        normalized = _normalized_learning_topic(topic_name)
        candidates = topic_subject_candidates.get(normalized, [])
        entry = add_topic(topic_name, candidates[0] if candidates else None)
        if entry is None:
            continue
        entry["progress"] = {
            "mastery_score": round(float(row.mastery_score or 0), 1),
            "questions_attempted": int(row.questions_attempted or 0),
            "questions_correct": int(row.questions_correct or 0),
            "study_minutes": int(row.study_minutes or 0),
            "last_studied": row.last_studied,
        }

    plan_candidates = []
    for entry in topic_entries.values():
        progress = entry["progress"] or {}
        mastery = max(0, min(100, float(progress.get("mastery_score") or 0)))
        attempted = int(progress.get("questions_attempted") or 0)
        correct = int(progress.get("questions_correct") or 0)
        study_minutes = int(progress.get("study_minutes") or 0)
        last_studied = progress.get("last_studied")
        days_since_studied = None
        if last_studied:
            try:
                days_since_studied = max(0, (datetime.utcnow() - last_studied).days)
            except TypeError:
                days_since_studied = None

        no_activity = attempted == 0 and study_minutes == 0
        if attempted and mastery < 60:
            action = "Strengthen weak area"
            recommended_minutes = 30
            reason = (
                f"Your mastery is {round(mastery)}% across {attempted} quiz question"
                f"{'s' if attempted != 1 else ''}."
            )
            priority = 145 - mastery
        elif no_activity:
            action = "Start this topic"
            recommended_minutes = 25
            source_text = next(iter(entry["document_names"]), "your uploaded material")
            reason = f"{source_text} includes this topic, with no recorded study session yet."
            priority = 120
        elif days_since_studied is not None and days_since_studied >= 7:
            action = "Refresh and retain"
            recommended_minutes = 20
            reason = f"You last studied this {days_since_studied} days ago."
            priority = 100 + min(days_since_studied, 30)
        elif mastery < 75:
            action = "Build confidence"
            recommended_minutes = 25
            reason = f"Current mastery is {round(mastery)}%; a short review can move it forward."
            priority = 90 - mastery
        else:
            action = "Consolidate"
            recommended_minutes = 15
            reason = "A quick retrieval practice session will help preserve this strength."
            priority = 10

        plan_candidates.append({
            "topic": entry["topic"],
            "subject_id": entry["subject_id"],
            "subject_name": entry["subject_name"],
            "action": action,
            "recommended_minutes": recommended_minutes,
            "reason": reason,
            "mastery_score": round(mastery, 1),
            "questions_attempted": attempted,
            "questions_correct": correct,
            "study_minutes": study_minutes,
            "last_studied": last_studied.isoformat() if last_studied else None,
            "document_names": sorted(entry["document_names"])[:3],
            "priority": priority,
        })

    plan_candidates.sort(
        key=lambda item: (-item["priority"], item["subject_name"].casefold(), item["topic"].casefold())
    )
    plan_items = plan_candidates[:4]
    for item in plan_items:
        item.pop("priority", None)

    graph_nodes = []
    graph_edges = []
    for subject in subjects:
        subject_id = subject.get("id")
        graph_nodes.append({
            "id": f"subject:{subject_id}",
            "type": "subject",
            "label": str(subject.get("name") or "Subject"),
            "subject_id": subject_id,
        })

    graph_topics_by_subject = {}
    for entry in topic_entries.values():
        subject_key = entry["subject_id"] if entry["subject_id"] is not None else "independent"
        graph_topics_by_subject.setdefault(subject_key, []).append(entry)

    if graph_topics_by_subject.get("independent"):
        graph_nodes.append({
            "id": "subject:independent",
            "type": "subject",
            "label": "Independent learning",
            "subject_id": None,
        })

    connected_document_ids = set()
    for subject_key, entries in graph_topics_by_subject.items():
        subject_node_id = f"subject:{subject_key}"
        for entry in sorted(entries, key=lambda item: item["topic"].casefold())[:10]:
            topic_node_id = f"topic:{entry['key']}"
            progress = entry["progress"] or {}
            graph_nodes.append({
                "id": topic_node_id,
                "type": "topic",
                "label": entry["topic"],
                "subject_id": entry["subject_id"],
                "subject_name": entry["subject_name"],
                "mastery_score": round(float(progress.get("mastery_score") or 0), 1),
                "study_minutes": int(progress.get("study_minutes") or 0),
                "questions_attempted": int(progress.get("questions_attempted") or 0),
            })
            graph_edges.append({"source": subject_node_id, "target": topic_node_id})
            for document_id in sorted(entry["document_ids"])[:3]:
                connected_document_ids.add(document_id)
                graph_edges.append({"source": topic_node_id, "target": f"document:{document_id}"})

    for document_id in connected_document_ids:
        document = document_details.get(document_id)
        if not document:
            continue
        graph_nodes.append({
            "id": f"document:{document_id}",
            "type": "document",
            "label": document["name"],
            "subject_id": document["subject_id"],
        })

    for document in document_details.values():
        if document["id"] in connected_document_ids:
            continue
        graph_nodes.append({
            "id": f"document:{document['id']}",
            "type": "document",
            "label": document["name"],
            "subject_id": document["subject_id"],
        })
        graph_edges.append({
            "source": f"subject:{document['subject_id']}",
            "target": f"document:{document['id']}",
        })

    return {
        "graph": {
            "nodes": graph_nodes,
            "edges": graph_edges,
        },
        "study_plan": {
            "items": plan_items,
            "total_minutes": sum(item["recommended_minutes"] for item in plan_items),
            "based_on": {
                "subjects": len(subjects),
                "documents": len(documents),
                "tracked_topics": len(progress_rows),
            },
        },
    }


@app.route(
    "/api/learning/insights",
    methods=["GET"]
)
@jwt_required()
def get_learning_insights():
    try:
        return jsonify({
            "success": True,
            **build_learning_insights(get_current_user_id()),
        }), 200
    except Exception as error:
        print("LEARNING INSIGHTS ERROR:", repr(error))
        return jsonify({
            "success": False,
            "message": "Unable to build learning insights.",
            "error": str(error),
        }), 500

@app.route(
    "/api/quiz/generate",
    methods=["POST"]
)
@jwt_required()
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
        current_user_id = get_current_user_id()
        subject_id = data.get(
            "subject_id"
        )
        target_topic = str(data.get("topic") or "").strip()
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
        if not subject_id and not target_topic:
            return jsonify({
                "success":
                    False,
                "message":
                    "subject_id or topic is required."
            }), 400
        question_count = max(
            5,
            min(
                question_count,
                20
            )
        )
        subjects = filter_subjects_for_user(load_subjects(), current_user_id)

        if not subject_id and target_topic:
            user_documents = filter_documents_for_user(load_documents(), current_user_id)
            topic_lower = target_topic.lower()
            matching_document = None
            for candidate in user_documents:
                topic_names = [
                    str(item.get("name", "")).lower()
                    for item in candidate.get("topics", [])
                    if isinstance(item, dict)
                ]
                page_text = " ".join(
                    str(page.get("text", ""))
                    for page in candidate.get("pages", [])
                ).lower()
                if any(topic_lower in name for name in topic_names) or topic_lower in page_text:
                    matching_document = candidate
                    break
            if matching_document:
                subject_id = matching_document.get("subject_id")

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
                    "Subject not found or access denied."
            }), 404
        documents = filter_documents_for_user(load_documents(), current_user_id)
        subject_documents = [
            document
            for document
            in documents
            if document.get(
                "subject_id"
            ) == subject_id
        ]
        if target_topic:
            topic_lower = target_topic.lower()
            filtered_documents = []
            for document in subject_documents:
                matching_pages = []
                for page in document.get("pages", []):
                    page_text = str(page.get("text", ""))
                    if topic_lower in page_text.lower():
                        matching_pages.append(page)
                topic_names = [
                    str(item.get("name", ""))
                    for item in document.get("topics", [])
                    if isinstance(item, dict)
                ]
                if matching_pages or any(topic_lower in name.lower() for name in topic_names):
                    document_copy = dict(document)
                    if matching_pages:
                        document_copy["pages"] = matching_pages
                    filtered_documents.append(document_copy)
            if filtered_documents:
                subject_documents = filtered_documents
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
Target topic:
{target_topic or "General"}
STRICT RULES:
1. Questions must be based ONLY
   on the supplied study material.
2. When a Target topic is provided, keep the questions focused on that topic.
3. Do not invent facts.
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
            "user_id":
                current_user_id,
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
@jwt_required()
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
        current_user_id = get_current_user_id()
        answers = data.get(
            "answers",
            {}
        )
        quizzes = filter_quizzes_for_user(load_quizzes(), current_user_id)
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
                    "Quiz not found or access denied."
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
        all_quizzes = load_quizzes()
        for index, item in enumerate(all_quizzes):
            if item.get("id") == quiz_id:
                all_quizzes[index] = quiz
                break
        save_quizzes(
            all_quizzes
        )

        # Update the authenticated user's topic mastery from this quiz.
        topic_totals = {}
        for result in results:
            topic = str(
                result.get("topic") or "General"
            ).strip()[:255] or "General"
            if topic not in topic_totals:
                topic_totals[topic] = [0, 0]
            topic_totals[topic][0] += 1
            if result.get("correct"):
                topic_totals[topic][1] += 1

        for topic, values in topic_totals.items():
            update_learning_progress(
                user_id=current_user_id,
                topic=topic,
                questions_attempted=values[0],
                questions_correct=values[1],
            )

        db.session.commit()
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
@jwt_required()
def get_quizzes():
    current_user_id = get_current_user_id()
    quizzes = filter_quizzes_for_user(load_quizzes(), current_user_id)
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
@jwt_required()
def dashboard_stats():
    try:
        current_user_id = get_current_user_id()
        documents = filter_documents_for_user(
            load_documents(),
            current_user_id,
        )
        quizzes = filter_quizzes_for_user(
            load_quizzes(),
            current_user_id,
        )
        progress_rows = get_learning_progress_for_user(current_user_id)

        topic_names = set()
        for document in documents:
            for topic in document.get("topics", []):
                name = topic.get("name")
                if name:
                    topic_names.add(name.lower())
        for row in progress_rows:
            if row.topic:
                topic_names.add(row.topic.lower())

        attempted_quizzes = [
            quiz for quiz in quizzes if quiz.get("attempted")
        ]
        if attempted_quizzes:
            total_questions = sum(
                quiz.get("question_count", 0)
                for quiz in attempted_quizzes
            )
            total_correct = sum(
                quiz.get("score", 0)
                for quiz in attempted_quizzes
            )
            quiz_accuracy = round(
                (total_correct / total_questions) * 100,
                1,
            ) if total_questions else 0
        else:
            quiz_accuracy = 0

        study_minutes = sum(
            int(row.study_minutes or 0)
            for row in progress_rows
        )
        study_hours = round(study_minutes / 60, 1)
        learning_streak = calculate_learning_streak(progress_rows)
        knowledge_dna = calculate_knowledge_dna(
            progress_rows,
            quiz_accuracy,
        )

        if not progress_rows and topic_names:
            knowledge_dna = round(
                min(100, len(topic_names) * 5),
                1,
            )

        return jsonify({
            "success": True,
            "stats": {
                "knowledge_dna": knowledge_dna,
                "topics_learned": len(topic_names),
                "quiz_accuracy": quiz_accuracy,
                "learning_streak": learning_streak,
                "study_hours": study_hours,
                "study_minutes": study_minutes,
            }
        })
    except Exception as error:
        print("DASHBOARD STATS ERROR:", repr(error))
        return jsonify({
            "success": False,
            "message": "Unable to get dashboard statistics.",
            "error": str(error)
        }), 500

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
