"""
Centralized prompt management for AI Knowledge DNA.

This module keeps reusable AI prompts in one place.
It does not call any AI provider directly.
"""


def build_chat_prompt(
    message,
    context=None,
    history=None,
    student_context=None
):
    """
    Build a general chat prompt with optional
    Knowledge DNA context, document context,
    and conversation history.
    """

    sections = [
        "You are an AI learning assistant for AI Knowledge DNA.",
        "Answer the student's question clearly and accurately.",
        "Use the provided context when it is relevant.",
        "Do not invent information that is not supported by the context.",
    ]

    if student_context:
        sections.append(
            f"\nStudent Knowledge DNA context:\n{student_context}"
        )

    if context:
        sections.append(
            f"\nRelevant learning/document context:\n{context}"
        )

    if history:
        sections.append(
            f"\nPrevious conversation:\n{history}"
        )

    sections.append(
        f"\nStudent question:\n{message}"
    )

    return "\n".join(sections)


def build_voice_prompt(
    message,
    context=None,
    student_context=None
):
    """
    Build a concise prompt for the voice assistant.
    """

    sections = [
        "You are the voice assistant for AI Knowledge DNA.",
        "Answer the student's question directly.",
        "Keep the response natural and easy to understand when spoken aloud.",
        "Do not respond with only a topic name.",
        "Give the actual answer to the student's question.",
    ]

    if student_context:
        sections.append(
            f"\nStudent Knowledge DNA context:\n{student_context}"
        )

    if context:
        sections.append(
            f"\nRelevant learning context:\n{context}"
        )

    sections.append(
        f"\nStudent question:\n{message}"
    )

    return "\n".join(sections)


def build_summary_prompt(content):
    """
    Build a prompt for study-material summarization.
    """

    return f"""
You are an AI learning assistant.

Summarize the following study material clearly for a student.

Focus on:
- Main concepts
- Important definitions
- Key points
- Important relationships between concepts

Study material:
{content}
""".strip()


def build_quiz_prompt(
    topic,
    context=None,
    question_count=5
):
    """
    Build a quiz-generation prompt.
    """

    prompt = f"""
You are an AI learning assistant.

Create {question_count} quiz questions for the topic:

{topic}

Questions should test understanding rather than simple memorization.
"""

    if context:
        prompt += f"""

Relevant study context:
{context}
"""

    return prompt.strip()


def build_knowledge_extraction_prompt(content):
    """
    Build a prompt for extracting important learning concepts.
    """

    return f"""
You are an AI learning assistant.

Extract the important learning concepts from the following material.

Identify:
- Topics
- Subtopics
- Key concepts
- Important definitions
- Relationships between concepts

Material:
{content}
""".strip()


def build_general_prompt(message, context=None):
    """
    Build a general-purpose AI prompt.
    """

    prompt = f"""
You are an AI learning assistant.

Answer the following question clearly and accurately:

{message}
"""

    if context:
        prompt += f"""

Additional context:
{context}
"""

    return prompt.strip()