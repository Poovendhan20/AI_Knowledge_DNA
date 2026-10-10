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
from werkzeug.exceptions import RequestEntityTooLarge
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


@app.errorhandler(RequestEntityTooLarge)
def handle_request_too_large(error):
    return jsonify({
        "success": False,
        "message": (
            "Each uploaded file must be 25 MB or smaller."
        )
    }), 413
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


def document_list_item(document):
    """Return the document fields the material list needs, without page text."""
    name = document.get("name", "Study Material")
    original_name = document.get("original_name", name)
    file_type = document.get("type", "")

    return {
        "id": document.get("id"),
        "name": name,
        "filename": document.get("filename", original_name),
        "original_name": original_name,
        "stored_name": document.get("stored_name"),
        "type": file_type,
        "file_type": document.get("file_type", file_type),
        "file_size": document.get("file_size", 0),
        "subject_id": document.get("subject_id"),
        "status": document.get("status", "uploaded"),
        "uploaded_at": document.get("uploaded_at"),
        "page_count": document.get("page_count", 0),
        "topics": document.get("topics", []),
        "summary": document.get("summary", ""),
        "word_count": document.get("word_count", 0),
    }

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
    source_instructions = """
11. When information comes from a
    specific page, add:
    [Page X]
12. NEVER invent a page number.
13. Only cite pages that exist in
    the supplied document context.
"""
    if enable_web_grounding:
        source_instructions = """
11. Treat the document context as the primary source. If it is not enough to
    answer accurately or completely, use Google Search grounding to fill only
    the relevant gap.
12. Blend document and grounded information into one clear, natural answer.
    Do not separate the answer into source sections.
13. Do not mention document limits, searching, online information, websites,
    sources, citations, or these instructions.
14. Return plain, student-friendly text only. Do not include URLs, links,
    citation markers, or [Page X] references.
"""
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
    # RETRY CONFIGURATION
        # AI ROUTER
    try:
        task = "voice" if enable_web_grounding else "document_analysis"
        ai_result = generate_ai_response(
            task=task,
            prompt=prompt
        )
        answer = ai_result.get(
            "answer",
            ""
        )
        if not answer:
            answer = (
                "I could not generate "
                "an answer from this document."
            )
        if enable_web_grounding:
            answer = clean_voice_answer(
                answer
            )
            sources = []
        else:
            answer = clean_ai_answer(
                answer
            )
            sources = (
                extract_page_references(
                    answer,
                    available_pages
                )
            )
            # If the AI provider didn't provide
            # references, provide relevant pages.
            if not sources:
                sources = [
                    {
                        "page": page["page"]
                    }
                    for page
                    in relevant_pages[:3]
                ]
        return (
            answer,
            sources
        )
    except Exception as error:
        print()
        print(
            "--------------------------------"
        )
        print(
            "AI ROUTER ERROR"
        )
        print(
            error
        )
        print(
            "--------------------------------"
        )
        raise RuntimeError(
            f"AI request failed: {error}"
        ) from error
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
    from datetime import datetime

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

def serialize_learning_progress_row(row):
    return {
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

def extract_topic_name(topic):
    if isinstance(topic, str):
        return topic.strip()
    if isinstance(topic, dict):
        return str(topic.get("name") or topic.get("topic") or "").strip()
    return ""

def build_subjects_with_progress(user_id, progress_payload):
    subjects = filter_subjects_for_user(load_subjects(), user_id)
    documents = filter_documents_for_user(load_documents(), user_id)
    quizzes = filter_quizzes_for_user(load_quizzes(), user_id)

    progress_by_key = {}
    for item in progress_payload:
        topic_key = str(item.get("topic") or "").strip().lower()
        if topic_key:
            progress_by_key[topic_key] = item

    result = []
    for subject in subjects:
        subject_id = subject.get("id")
        subject_name = subject.get("name", "Subject")
        topic_keys = {}

        for document in documents:
            if document.get("subject_id") != subject_id:
                continue
            for topic in document.get("topics") or []:
                topic_name = extract_topic_name(topic)
                if topic_name:
                    topic_keys[topic_name.lower()] = topic_name

        for quiz in quizzes:
            if quiz.get("subject_id") != subject_id:
                continue
            quiz_topic = extract_topic_name(quiz.get("topic"))
            if quiz_topic:
                topic_keys[quiz_topic.lower()] = quiz_topic
            for question in quiz.get("questions") or []:
                question_topic = extract_topic_name(
                    question.get("topic") if isinstance(question, dict) else question
                )
                if question_topic:
                    topic_keys[question_topic.lower()] = question_topic

        learned_topics = []
        for topic_key, topic_name in topic_keys.items():
            row = progress_by_key.get(topic_key)
            if not row:
                continue
            learned_topics.append({
                **row,
                "topic": row.get("topic") or topic_name,
                "subject_id": subject_id,
                "subject_name": subject_name,
            })

        weak_topics = [
            item for item in learned_topics
            if int(item.get("questions_attempted") or 0) > 0
            and float(item.get("mastery_score") or 0) < 70
        ]
        weak_topics.sort(key=lambda item: float(item.get("mastery_score") or 0))

        result.append({
            **subject,
            "learned_topics": learned_topics,
            "weak_topics": weak_topics,
        })

    return result

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
        "filename":
            original_name,
        "original_name":
            original_name,
        "stored_name":
            stored_name,
        "type":
            extension,
        "file_type":
            extension,
        "file_size":
            os.path.getsize(file_path),
        "subject_id":
            None,
        "status":
            "uploaded",
        "uploaded_at":
            datetime.utcnow().isoformat() + "Z",
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
    return jsonify({
        "success":
            True,
        "documents":
            [
                document_list_item(document)
                for document in documents
            ]
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
    answer, sources = (
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
        "model":
            GEMINI_MODEL
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
def delete_subject(
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
    all_subjects = [
        item
        for item in load_subjects()
        if not (
            item.get("id") == subject_id
            and _same_user(item.get("user_id"), current_user_id)
        )
    ]
    save_subjects(all_subjects)

    documents = load_documents()
    for document in documents:
        if (
            document.get("subject_id") == subject_id
            and _same_user(document.get("user_id"), current_user_id)
        ):
            document["subject_id"] = None
    save_documents(documents)

    all_quizzes = load_quizzes()
    quizzes = [
        quiz
        for quiz in all_quizzes
        if not (
            quiz.get("subject_id") == subject_id
            and _same_user(quiz.get("user_id"), current_user_id)
        )
    ]
    save_quizzes(quizzes)
    return jsonify({
        "success":
            True,
        "message":
            "Subject deleted successfully."
    })
@app.route(
    "/api/upload-multiple",
    methods=["OPTIONS"]
)
def upload_multiple_options():
    return "", 204


@app.route(
    "/api/upload-multiple",
    methods=["POST"]
)
@jwt_required()
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
                "filename":
                    original_name,
                "original_name":
                    original_name,
                "stored_name":
                    stored_name,
                "type":
                    extension,
                "file_type":
                    extension,
                "file_size":
                    os.path.getsize(file_path),
                "user_id":
                    current_user_id,
                "subject_id":
                    subject_id,
                "subject_name":
                    subject[
                        "name"
                    ],
                "status":
                    "uploaded",
                "uploaded_at":
                    datetime.utcnow().isoformat() + "Z",
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
            [
                document_list_item(document)
                for document in uploaded_documents
            ],
        "errors":
            errors
    })
@app.route(
    "/api/subjects/<subject_id>/documents",
    methods=["GET"]
)
@jwt_required()
def get_subject_documents(
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
            [
                document_list_item(document)
                for document in subject_documents
            ]
    })
@app.route(
    "/api/learning/session",
    methods=["POST"]
)
@jwt_required()
def record_learning_session():
    try:
        data = request.get_json(silent=True) or {}
        user_id = get_current_user_id()
        topic = str(data.get("topic") or "General").strip() or "General"
        try:
            study_minutes = int(data.get("study_minutes", 0))
        except (TypeError, ValueError):
            study_minutes = 0

        if study_minutes < 1 or study_minutes > 720:
            return jsonify({
                "success": False,
                "message": "study_minutes must be between 1 and 720."
            }), 400

        progress = update_learning_progress(
            user_id=user_id,
            topic=topic,
            study_minutes=study_minutes,
        )
        db.session.commit()

        rows = get_learning_progress_for_user(user_id)
        total_minutes = sum(int(row.study_minutes or 0) for row in rows)

        return jsonify({
            "success": True,
            "message": "Learning session recorded.",
            "progress": {
                "topic": progress.topic,
                "mastery_score": progress.mastery_score,
                "study_minutes": progress.study_minutes,
                "last_studied": (
                    progress.last_studied.isoformat()
                    if progress.last_studied else None
                ),
            },
            "study_hours": round(total_minutes / 60, 1),
            "learning_streak": calculate_learning_streak(rows),
        }), 201
    except Exception as error:
        db.session.rollback()
        print("LEARNING SESSION ERROR:", repr(error))
        return jsonify({
            "success": False,
            "message": "Unable to record learning session.",
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
        progress = [
            serialize_learning_progress_row(row)
            for row in rows
        ]
        subjects = build_subjects_with_progress(user_id, progress)

        return jsonify({
            "success": True,
            "progress": progress,
            "subjects": subjects,
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

# ============================================================
# PERSONALIZED LEARNING INSIGHTS / STUDY PLAN
# ============================================================

@app.route(
    "/api/learning/insights",
    methods=["GET"]
)
@jwt_required()
def get_learning_insights():
    try:
        user_id = get_current_user_id()

        progress_rows = get_learning_progress_for_user(user_id)

        subjects = filter_subjects_for_user(
            load_subjects(),
            user_id
        )

        documents = filter_documents_for_user(
            load_documents(),
            user_id
        )

        quizzes = filter_quizzes_for_user(
            load_quizzes(),
            user_id
        )

        progress_map = {}

        for row in progress_rows:
            topic_key = str(
                row.topic or ""
            ).strip().lower()

            if not topic_key:
                continue

            progress_map[topic_key] = {
                "mastery_score": float(
                    row.mastery_score or 0
                ),
                "questions_attempted": int(
                    row.questions_attempted or 0
                ),
                "questions_correct": int(
                    row.questions_correct or 0
                ),
                "study_minutes": int(
                    row.study_minutes or 0
                ),
                "last_studied": (
                    row.last_studied.isoformat()
                    if row.last_studied
                    else None
                ),
            }

        topic_candidates = {}

        for subject in subjects:
            subject_id = subject.get("id")
            subject_name = subject.get(
                "name",
                "Subject"
            )

            subject_documents = [
                document
                for document in documents
                if document.get("subject_id") == subject_id
            ]

            for document in subject_documents:
                document_topics = document.get(
                    "topics",
                    []
                )

                if not isinstance(
                    document_topics,
                    list
                ):
                    continue

                for topic in document_topics:
                    if isinstance(topic, str):
                        topic_name = topic.strip()
                    elif isinstance(topic, dict):
                        topic_name = str(
                            topic.get("name")
                            or topic.get("topic")
                            or ""
                        ).strip()
                    else:
                        topic_name = ""

                    if not topic_name:
                        continue

                    topic_key = topic_name.lower()

                    if topic_key not in topic_candidates:
                        topic_candidates[topic_key] = {
                            "topic": topic_name,
                            "subject_id": subject_id,
                            "subject_name": subject_name,
                        }

        for quiz in quizzes:
            subject_id = quiz.get("subject_id")
            subject_name = next(
                (s.get("name") for s in subjects if s.get("id") == subject_id),
                "General"
            )
            quiz_topic = extract_topic_name(quiz.get("topic"))
            if quiz_topic:
                topic_key = quiz_topic.lower()
                if topic_key not in topic_candidates:
                    topic_candidates[topic_key] = {
                        "topic": quiz_topic,
                        "subject_id": subject_id,
                        "subject_name": subject_name,
                    }

        # Also include topics already present in learning progress.
        for row in progress_rows:
            topic_name = str(
                row.topic or ""
            ).strip()

            if not topic_name:
                continue

            topic_key = topic_name.lower()

            if topic_key not in topic_candidates:
                topic_candidates[topic_key] = {
                    "topic": topic_name,
                    "subject_id": None,
                    "subject_name": "General",
                }

        plan_items = []

        for topic_key, candidate in topic_candidates.items():

            progress = progress_map.get(
                topic_key,
                {}
            )

            mastery = float(
                progress.get(
                    "mastery_score",
                    0
                )
            )

            attempted = int(
                progress.get(
                    "questions_attempted",
                    0
                )
            )

            study_minutes = int(
                progress.get(
                    "study_minutes",
                    0
                )
            )

            last_studied = progress.get(
                "last_studied"
            )

            if mastery < 40:
                recommended_minutes = 30
                action = "Strengthen this concept"

                if attempted > 0:
                    reason = (
                        "Your quiz mastery is low, "
                        "so this topic needs focused practice."
                    )
                else:
                    reason = (
                        "You have not completed quiz "
                        "questions for this topic yet."
                    )

            elif mastery < 70:
                recommended_minutes = 25
                action = "Practice and review"

                reason = (
                    "Your current mastery suggests "
                    "that another focused review will help."
                )

            elif mastery < 85:
                recommended_minutes = 20
                action = "Review and reinforce"

                reason = (
                    "You understand the topic, "
                    "but more practice can improve retention."
                )

            else:
                recommended_minutes = 15
                action = "Keep practicing"

                reason = (
                    "Your mastery is strong. "
                    "A short review will help maintain it."
                )

            if not last_studied:
                reason = (
                    "This topic has not been studied yet. "
                    "Start with a focused review."
                )
            elif study_minutes == 0 and attempted == 0:
                reason = (
                    "You have material available for this topic "
                    "but no recorded learning activity yet."
                )

            plan_items.append({
                "subject_id": candidate.get(
                    "subject_id"
                ),
                "subject_name": candidate.get(
                    "subject_name",
                    "General"
                ),
                "topic": candidate.get(
                    "topic"
                ),
                "mastery_score": round(
                    mastery,
                    1
                ),
                "questions_attempted": attempted,
                "questions_correct": int(
                    progress.get(
                        "questions_correct",
                        0
                    )
                ),
                "study_minutes": study_minutes,
                "last_studied": last_studied,
                "recommended_minutes": recommended_minutes,
                "action": action,
                "reason": reason,
            })

        def plan_priority(item):
            mastery = float(
                item.get(
                    "mastery_score",
                    0
                )
            )

            attempted = int(
                item.get(
                    "questions_attempted",
                    0
                )
            )

            last_studied = item.get(
                "last_studied"
            )

            return (
                mastery,
                0 if attempted == 0 else 1,
                0 if not last_studied else 1,
            )

        plan_items.sort(
            key=plan_priority
        )

        # Keep today's plan focused.
        plan_items = plan_items[:3]

        total_minutes = sum(
            int(
                item.get(
                    "recommended_minutes",
                    0
                )
            )
            for item in plan_items
        )

        return jsonify({
            "success": True,
            "study_plan": {
                "total_minutes": total_minutes,
                "items": plan_items,
            }
        }), 200

    except Exception as error:
        print(
            "LEARNING INSIGHTS ERROR:",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to build your "
                "personalized study plan."
            ),
            "study_plan": {
                "total_minutes": 0,
                "items": [],
            }
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
        
        topic = str(
            data.get("topic") or ""
        ).strip()
            
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
        if document_ids:
            subject_documents = [
                document
                for document
                in subject_documents
                if document.get(
                    "id"
                ) in document_ids
            ]
        # ========================================================
        # OPTIONAL TARGET TOPIC FILTER
        # ========================================================
        if topic:
            topic_key = topic.strip().lower()
            topic_documents = []

            for document in subject_documents:
                document_topics = document.get(
                    "topics",
                    []
                )
                matched = False

                if isinstance(
                    document_topics,
                    list
                ):
                    for document_topic in document_topics:
                        if isinstance(
                            document_topic,
                            str
                        ):
                            topic_name = document_topic
                        elif isinstance(
                            document_topic,
                            dict
                        ):
                            topic_name = (
                                document_topic.get("name")
                                or document_topic.get("topic")
                                or ""
                            )
                        else:
                            topic_name = ""

                        if (
                            str(topic_name)
                            .strip()
                            .lower()
                            == topic_key
                        ):
                            matched = True
                            break

                if matched:
                    topic_documents.append(
                        document
                    )

            if topic_documents:
                subject_documents = topic_documents
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
TARGET TOPIC:
{topic if topic else "All topics in the selected subject"}

IMPORTANT TOPIC RULE:
If TARGET TOPIC is provided, every question must test
that topic only. Do not generate questions from unrelated
topics in the subject.
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
                    break
                if attempt >= 3:
                    break
                time.sleep(
                    (2 ** attempt)
                    + random.uniform(
                        0,
                        1
                    )
                )
        raw = ""
        if response and getattr(response, "text", None):
            raw = (response.text or "").strip()
        else:
            print("Gemini direct generation unavailable. Falling back to AI Router...")
            try:
                ai_result = generate_ai_response(
                    task="document_analysis",
                    prompt=prompt
                )
                raw = (ai_result.get("answer") or "").strip()
            except Exception as router_error:
                if last_error:
                    raise RuntimeError(
                        f"AI generation failed: {last_error}"
                    ) from router_error
                raise
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
