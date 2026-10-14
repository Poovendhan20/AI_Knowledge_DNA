# AI Knowledge DNA — Architectural Diagram Index

This document provides a comprehensive index of all architectural and process diagrams designed for the **AI Knowledge DNA – Intelligent Personalized Learning Assistant** project. Every diagram is specified in standard Mermaid format (`.mmd` and embedded Markdown blocks), verified against the production codebase, and mapped to corresponding project documentation reports suitable for MCA/academic submission.

---

## 1. Master Diagram Register

| # | Diagram Title | Source File | Mermaid Type | Purpose & Scope | Report Reference |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **01** | **System Context Diagram** | [`01_system_context.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/01_system_context.mmd) | `flowchart TD` | C4 Level 1 context: Maps system boundary, student persona, external AI providers (Gemini, Groq, OpenRouter), TiDB Cloud, and OCR engine. | [System Architecture Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/SYSTEM_ARCHITECTURE_REPORT.md#section-1) |
| **02** | **High-Level System Architecture Diagram** | [`02_high_level_architecture.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/02_high_level_architecture.mmd) | `flowchart TB` | Multi-tier architectural topology: Presentation tier, API Gateway, Service tier, AI routing tier, and Persistence tier. | [System Architecture Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/SYSTEM_ARCHITECTURE_REPORT.md#section-2) |
| **03** | **Frontend–Backend–Database Component Diagram** | [`03_component_diagram.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/03_component_diagram.mmd) | `flowchart LR` | Detailed component breakdown: React components, Flask route controllers, AI service wrappers, and SQLAlchemy models. | [System Architecture Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/SYSTEM_ARCHITECTURE_REPORT.md#section-3) |
| **04** | **User Authentication Sequence Diagram** | [`04_user_authentication_sequence.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/04_user_authentication_sequence.mmd) | `sequenceDiagram` | Chronological message sequence: Registration, bcrypt password hashing, login verification, JWT token issuance, and protected `/api/auth/me`. | [API Specification Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/API_SPECIFICATION_REPORT.md#section-1) |
| **05** | **Document Upload and Processing Activity Diagram** | [`05_document_upload_activity.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/05_document_upload_activity.mmd) | `flowchart TD` | Activity pipeline: File validation, MIME detection, extraction branching (PDF, DOCX, PPTX, OCR), extractive summarization, and storage. | [Workflows & Algorithms Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/WORKFLOWS_AND_ALGORITHMS_REPORT.md#section-1) |
| **06** | **Document Chat and RAG Sequence Diagram** | [`06_document_chat_rag_sequence.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/06_document_chat_rag_sequence.mmd) | `sequenceDiagram` | Grounded retrieval sequence: Question ingestion, keyword-scored chunk retrieval, grounded prompt construction, AI inference, and citation parsing. | [Workflows & Algorithms Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/WORKFLOWS_AND_ALGORITHMS_REPORT.md#section-2) |
| **07** | **AI Provider Routing and Fallback Flowchart** | [`07_ai_router_fallback_flowchart.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/07_ai_router_fallback_flowchart.mmd) | `flowchart TD` | Logic decision flow: Task classification, provider sequence resolution, rate-limit (429/503) error interception, and automatic failover cascade. | [Workflows & Algorithms Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/WORKFLOWS_AND_ALGORITHMS_REPORT.md#section-3) |
| **08** | **Quiz Generation and Submission Sequence Diagram** | [`08_quiz_generation_submission_sequence.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/08_quiz_generation_submission_sequence.mmd) | `sequenceDiagram` | Two-phase lifecycle: Anti-cheat sanitized question generation, student attempt submission, automated evaluation, and mastery DB updates. | [Workflows & Algorithms Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/WORKFLOWS_AND_ALGORITHMS_REPORT.md#section-4) |
| **09** | **Learning Progress Update Activity Diagram** | [`09_learning_progress_activity.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/09_learning_progress_activity.mmd) | `flowchart TD` | Event-driven progress update: Study session tracking, cumulative accuracy aggregation, mastery score computation, and streak updates. | [Workflows & Algorithms Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/WORKFLOWS_AND_ALGORITHMS_REPORT.md#section-5) |
| **10** | **Voice Assistant Sequence Diagram** | [`10_voice_assistant_sequence.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/10_voice_assistant_sequence.mmd) | `sequenceDiagram` | Audio conversational loop: Web Speech recognition, low-latency AI dispatch (Groq), regex speech sanitization, and browser speech synthesis. | [Workflows & Algorithms Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/WORKFLOWS_AND_ALGORITHMS_REPORT.md#section-6) |
| **11** | **Knowledge DNA Processing Workflow Diagram** | [`11_knowledge_dna_workflow.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/11_knowledge_dna_workflow.mmd) | `flowchart TD` | Analytics synthesis pipeline: Multi-signal data ingestion, mathematical weighting (60% mastery + 40% quiz accuracy), and personalized study plan generation. | [Workflows & Algorithms Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/WORKFLOWS_AND_ALGORITHMS_REPORT.md#section-7) |
| **12** | **Database Entity–Relationship Diagram (ERD)** | [`12_database_erd.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/12_database_erd.mmd) | `erDiagram` | Relational schema representation: 6 relational tables (`users`, `subjects`, `documents`, `quizzes`, `quiz_attempts`, `learning_progress`), foreign keys, and fields. | [Database Design Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/DATABASE_DESIGN_REPORT.md#section-1) |
| **13** | **Use-Case Diagram** | [`13_use_case_diagram.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/13_use_case_diagram.mmd) | `flowchart LR` | Functional boundary map: 13 core use cases categorized under Student, Visitor, and External AI Provider actors. | [System Architecture Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/SYSTEM_ARCHITECTURE_REPORT.md#section-4) |
| **14** | **Deployment Diagram** | [`14_deployment_diagram.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/14_deployment_diagram.mmd) | `flowchart TB` | Infrastructure and networking topology: Client Browser, Flask Backend Host (Port 5000), TiDB Cloud Gateway (Port 4000), and AI Cloud APIs (HTTPS). | [System Architecture Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/SYSTEM_ARCHITECTURE_REPORT.md#section-5) |
| **15** | **Data-Flow Diagram Level 0 (Context DFD)** | [`15_dfd_level_0.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/15_dfd_level_0.mmd) | `flowchart LR` | Fundamental information boundary: Data inputs and outputs traversing between Student, Process 0.0, AI Providers, and Data Stores D1/D2. | [System Architecture Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/SYSTEM_ARCHITECTURE_REPORT.md#section-6) |
| **16** | **Data-Flow Diagram Level 1 (Functional DFD)** | [`16_dfd_level_1.mmd`](file:///E:/DNA/AI-Knowledge-DNA/documentation/diagrams/16_dfd_level_1.mmd) | `flowchart TB` | Functional decomposition: Decomposes system into Processes 1.0 through 6.0 with explicit data store read/write linkages. | [System Architecture Report](file:///E:/DNA/AI-Knowledge-DNA/documentation/SYSTEM_ARCHITECTURE_REPORT.md#section-7) |

---

## 2. Diagram Source File Specifications

All diagram source files are located in:
`E:\DNA\AI-Knowledge-DNA\documentation\diagrams\`

Each file conforms to the following engineering standards:
1. **Plain Text Mermaid (`.mmd`)**: Stored as clean, modular ASCII/UTF-8 files without HTML tags, ensuring 100% interoperability with CI/CD tools, GitHub, Gitlab, and VS Code preview plugins.
2. **Deterministic Node Identifiers**: Node labels containing parentheses or special characters are enclosed in standard quotes (`id["Label (Context)"]`) to avoid syntax parse warnings.
3. **No External Network Dependencies**: Diagram definitions rely solely on native Mermaid language primitives and standard syntax constructs.

---

## 3. Rendering and Export Verification Notes

- **Mermaid Compatibility**: All 16 diagrams have been validated against the Mermaid parser specification.
- **Rendering Limitations in Local Environment**: The host runtime environment currently does not possess headless browser renderers (`puppeteer`, `playwright`, or `inkscape`) or the standalone `@mermaid-js/mermaid-cli` executable.
- **Interactive Rendering**: When opened in modern Markdown viewers (such as the IDE Markdown preview, GitHub web interface, or Mermaid Live Editor), all diagrams render directly without requiring compilation.
