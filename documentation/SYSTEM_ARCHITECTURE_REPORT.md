# AI Knowledge DNA — System Architecture & Design Specification Report

**Document Code:** MCA-PRJ-DNA-001  
**Target Project:** AI Knowledge DNA – Intelligent Personalized Learning Assistant  
**Repository Path:** `E:\DNA\AI-Knowledge-DNA`  
**Classification:** Technical Architecture & System Design Report  
**Academic Level:** Master of Computer Applications (MCA) Project Documentation  

---

## Abstract

This technical report presents the comprehensive architectural specification of the **AI Knowledge DNA** platform. The system is an intelligent, personalized educational assistant engineered to bridge academic study materials, generative artificial intelligence, and adaptive knowledge modeling. The architecture incorporates a decoupled single-page application frontend built with React 19, a RESTful micro-service backend powered by Flask and SQLAlchemy, a hybrid persistence tier utilizing distributed TiDB Cloud MySQL alongside atomic flat-file stores, and an AI routing orchestration layer that dynamically balances requests across Google Gemini, Groq Cloud, and OpenRouter with automatic failover circuits.

---

## 1. System Context & Operational Boundaries

The system context diagram delineates the operational boundaries of the AI Knowledge DNA system, detailing the interactions between the primary student persona, client user interfaces, internal core subsystems, and external specialized service providers.

```mermaid
flowchart TD
    classDef userNode fill:#2563EB,stroke:#1D4ED8,color:#FFFFFF,stroke-width:2px;
    classDef systemBoundary fill:#F8FAFC,stroke:#3B82F6,color:#0F172A,stroke-width:3px,stroke-dasharray: 5 5;
    classDef internalCore fill:#1E293B,stroke:#0F172A,color:#F8FAFC,stroke-width:2px;
    classDef externalService fill:#475569,stroke:#334155,color:#F8FAFC,stroke-width:2px;

    User["Student / Learner<br/>(Web Browser / Mobile Client)"]:::userNode

    subgraph SystemBoundary ["AI Knowledge DNA Platform (System Boundary)"]
        Platform["AI Knowledge DNA System<br/>• Personalized Learning Assistant<br/>• Document Processing & RAG Engine<br/>• Knowledge DNA & Topic Mastery<br/>• Interactive Voice & Quiz Studio"]:::internalCore
    end

    Gemini["Google Gemini API<br/>(Gemini 2.5 Flash / 1.5 Pro)<br/>Doc Analysis & Knowledge Extraction"]:::externalService
    Groq["Groq Cloud API<br/>(Llama 3 / Mixtral)<br/>Ultra-Fast Chat & Voice Synthesis"]:::externalService
    OpenRouter["OpenRouter API<br/>(Multi-Model AI Gateway)<br/>General Reasoning & Secondary Fallback"]:::externalService
    GoogleSearch["Google Search Tool<br/>(Live Web Grounding)"]:::externalService
    TiDBCloud["TiDB Cloud MySQL<br/>(Distributed Relational Database)"]:::externalService
    OSFileSystem["Server Local File System<br/>(Encrypted Uploads & JSON Stores)"]:::externalService
    TesseractOCR["Tesseract OCR Engine<br/>(Image Text Recognition)"]:::externalService

    User -->|"1. Submits study materials, chat prompts, quiz requests"| Platform
    Platform -->|"2. Streams synthesized answers, quizzes, mastery metrics"| User

    Platform -->|"3. Primary deep analysis prompts"| Gemini
    Platform -->|"4. Low-latency conversational queries"| Groq
    Platform -->|"5. Fallback requests on provider rate limits"| OpenRouter
    Gemini -.->|"6. Retrieves live citations"| GoogleSearch
    Platform -->|"7. Persists users, progress, sessions"| TiDBCloud
    Platform -->|"8. Stores uploaded files and JSON documents"| OSFileSystem
    Platform -->|"9. Passes images for text extraction"| TesseractOCR
```

### 1.1 Boundary Entities Description

1. **Student / Learner Persona:** Interacts with the platform via modern web browsers on desktop and mobile viewports. Utilizes document upload features, reads extracted texts with synchronized page navigation, queries the RAG conversational agent, engages in hands-free voice sessions, takes diagnostic quizzes, and reviews personalized study recommendations.
2. **AI Provider Ecosystem:**
   - **Google Gemini API (`gemini-3.5-flash`):** Primary engine for deep document parsing, complex prompt ingestion, structured JSON quiz synthesis, and grounded answering.
   - **Groq Cloud API (`openai/gpt-oss-20b`):** Hardware-accelerated inference engine utilized for low-latency conversational queries and real-time voice assistant speech synthesis.
   - **OpenRouter API (`openai/gpt-6-luna`):** Unified secondary fallback gateway invoked when primary providers experience transient HTTP 429 rate limits or HTTP 503 service outages.
3. **Storage & Infrastructure:**
   - **TiDB Cloud MySQL:** High-availability distributed database cluster hosting normalized user identity records, authentication credentials, and cumulative `LearningProgress` metrics.
   - **Local File System Storage:** Staged raw binary files in `backend/uploads/` and structured entity catalogs in `backend/data/`.
   - **Tesseract OCR Subprocess:** Local optical character recognition binary invoked dynamically for image-based study materials (`.png`, `.jpg`, `.jpeg`, `.webp`).

---

## 2. High-Level Multi-Tier Architectural Topology

The AI Knowledge DNA application is structured into five distinct architectural tiers following strict separation of concerns and loose coupling principles.

```mermaid
flowchart TB
    classDef clientLayer fill:#EFF6FF,stroke:#3B82F6,color:#1E3A8A,stroke-width:2px;
    classDef gatewayLayer fill:#F0FDF4,stroke:#22C55E,color:#14532D,stroke-width:2px;
    classDef serviceLayer fill:#FAF5FF,stroke:#A855F7,color:#581C87,stroke-width:2px;
    classDef aiLayer fill:#FFFBEB,stroke:#F59E0B,color:#78350F,stroke-width:2px;
    classDef dataLayer fill:#F1F5F9,stroke:#64748B,color:#0F172A,stroke-width:2px;
    classDef extLayer fill:#FEF2F2,stroke:#EF4444,color:#7F1D1D,stroke-width:2px;

    subgraph PresentationTier ["1. Presentation Tier (Client Single Page Application)"]
        direction TB
        UIApp["React 19 SPA (Vite Bundler)"]:::clientLayer
        ThemeEng["Academic Focus Theme System (Light / Dark)"]:::clientLayer
        SpeechIO["Web Speech Interface (SpeechRecognition & Synthesis)"]:::clientLayer
        Routing["React Router v7 Protected Routes"]:::clientLayer
        UIApp --- ThemeEng
        UIApp --- SpeechIO
        UIApp --- Routing
    end

    subgraph GatewayTier ["2. API Gateway & Security Tier"]
        direction TB
        FlaskCORS["Flask CORS Interceptor & Preflight"]:::gatewayLayer
        JWTAuth["JWT Security Filter (Token Validation & User Isolation)"]:::gatewayLayer
        ErrHandler["Global Error Handler (HTTPException & 500 Trapping)"]:::gatewayLayer
        FlaskCORS --> JWTAuth --> ErrHandler
    end

    subgraph ServiceTier ["3. Business Logic & Processing Tier"]
        direction TB
        AuthSvc["Authentication Service (bcrypt Hashing)"]:::serviceLayer
        DocProc["Document Parser (PDF, DOCX, PPTX, OCR)"]:::serviceLayer
        RAGChat["RAG Context Assembly & Citation Engine"]:::serviceLayer
        QuizEngine["Quiz Generator & Scoring Engine"]:::serviceLayer
        AnalyticsEngine["Learning Analytics & Knowledge DNA Calculator"]:::serviceLayer
    end

    subgraph AITier ["4. AI Routing & Orchestration Tier"]
        direction TB
        AIRouter["AI Router (Task-Based Dynamic Dispatch)"]:::aiLayer
        FallbackCircuit["Provider Fallback & Retry Handler (429/503 Detection)"]:::aiLayer
        VoiceCleaner["Speech Synthesizer Cleaner (Regex Tag Stripper)"]:::aiLayer
        AIRouter --> FallbackCircuit --> VoiceCleaner
    end

    subgraph PersistenceTier ["5. Data Persistence Tier"]
        direction TB
        SQLAlchemyORM["SQLAlchemy Relational ORM"]:::dataLayer
        TiDBCloud["TiDB Cloud MySQL (Users, Progress, Attempts)"]:::dataLayer
        JSONStores["Flat-File JSON Repositories (subjects, documents, quizzes)"]:::dataLayer
        UploadFS["Encrypted Disk Storage (backend/uploads/*.ext)"]:::dataLayer
        SQLAlchemyORM --> TiDBCloud
    end

    subgraph ExternalServices ["6. External Service Ecosystem"]
        direction TB
        GeminiAPI["Google Gemini API (Primary Document Model)"]:::extLayer
        GroqAPI["Groq Cloud API (Low-Latency Chat & Voice)"]:::extLayer
        OpenRouterAPI["OpenRouter Gateway (Secondary Fallback)"]:::extLayer
        TesseractBinary["Tesseract OCR Binary"]:::extLayer
    end

    PresentationTier -->|"REST / JSON via HTTPS / Axios"| GatewayTier
    GatewayTier -->|"Dispatches Authorized Request"| ServiceTier
    ServiceTier -->|"Requests Inferences"| AITier
    AITier -->|"Gemini Calls"| GeminiAPI
    AITier -->|"Groq Calls"| GroqAPI
    AITier -->|"OpenRouter Calls"| OpenRouterAPI
    DocProc -->|"Extracts Image Text"| TesseractBinary
    ServiceTier -->|"Relational Queries"| SQLAlchemyORM
    ServiceTier -->|"Atomic File Operations"| JSONStores
    DocProc -->|"Stores Staged Blobs"| UploadFS
```

### 2.1 Tier Breakdown and Responsibilities

| Tier | Primary Technologies | Core Responsibilities |
| :--- | :--- | :--- |
| **Presentation Tier** | React 19, Vite, React Router v7, Framer Motion, Web Speech API | Client-side routing, state management, responsive UI rendering, PDF canvas display, speech I/O, and theme synchronization. |
| **API Gateway Tier** | Flask, Flask-CORS, Flask-JWT-Extended, Werkzeug Exceptions | Endpoint routing, CORS preflight handling, JWT signature and expiration verification, client input sanitization, and HTTP error code preservation. |
| **Service Tier** | Python 3.14, pypdf, python-docx, python-pptx, PIL, pytesseract | Document text extraction, keyword extraction, context window truncation, extractive summarization, anti-cheat quiz generation, and Knowledge DNA metric computation. |
| **AI Orchestration Tier** | `ai_router.py`, `gemini_service.py`, `groq_service.py`, `openrouter_service.py` | Task-to-provider dispatching, exponential backoff retries, transient error detection (HTTP 429/503), multi-provider failover, and voice response sanitization. |
| **Persistence Tier** | SQLAlchemy, PyMySQL, TiDB Cloud, JSON storage, Local disk storage | ACID-compliant user identity storage, cumulative topic progress tracking, atomic JSON catalog persistence, and disk file stream management. |

---

## 3. Component Architecture & Subsystem Decomposition

The component architecture defines the concrete classes, controllers, contexts, and modules comprising the codebase:

```mermaid
flowchart LR
    classDef feComp fill:#DBEAFE,stroke:#2563EB,color:#1E40AF,stroke-width:1px;
    classDef beRoute fill:#DCFCE7,stroke:#16A34A,color:#14532D,stroke-width:1px;
    classDef beSvc fill:#F3E8FF,stroke:#9333EA,color:#581C87,stroke-width:1px;
    classDef dbModel fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D,stroke-width:1px;

    subgraph FrontendComponents ["Frontend Components (src/features & context)"]
        direction TB
        AuthCtx["AuthContext<br/>(JWT Token & User State)"]:::feComp
        ThemeCtx["ThemeContext<br/>(ai_knowledge_dna_theme)"]:::feComp
        DashComp["Dashboard View<br/>(Metrics & Streaks)"]:::feComp
        StudyPlanWidget["PersonalizedStudyPlan<br/>(Weak Concepts Widget)"]:::feComp
        SubjMgrComp["SubjectManager<br/>(CRUD & Upload Modal)"]:::feComp
        DocViewComp["DocumentViewer<br/>(PDF Canvas / Markdown)"]:::feComp
        DocChatComp["DocumentChat<br/>(RAG Interface & Chips)"]:::feComp
        QuizGenComp["QuizGenerator<br/>(Configurator)"]:::feComp
        QuizPlayComp["QuizPlayer<br/>(Evaluation & Review)"]:::feComp
        VoiceComp["VoiceAssistant<br/>(Speech IO Component)"]:::feComp

        DashComp --- StudyPlanWidget
        DocViewComp --- DocChatComp
    end

    subgraph BackendEndpoints ["Backend Controllers (app.py Routes)"]
        direction TB
        AuthCtrl["Auth Controller<br/>(/api/auth/register, login, me)"]:::beRoute
        SubjCtrl["Subject Controller<br/>(/api/subjects, /subjects/<id>)"]:::beRoute
        DocCtrl["Document Controller<br/>(/api/upload, /documents/<id>, /files/<f>)"]:::beRoute
        ChatCtrl["Chat Controller<br/>(/api/chat, /documents/<id>/chat)"]:::beRoute
        QuizCtrl["Quiz Controller<br/>(/api/quiz/generate, submit, /quizzes)"]:::beRoute
        LearningCtrl["Learning & Dashboard Controller<br/>(/api/learning/session, progress, insights, /dashboard/stats)"]:::beRoute
    end

    subgraph BackendServices ["Backend Services & Utility Modules"]
        direction TB
        ExtractSvc["Doc Extraction Module<br/>(PdfReader, docx, pptx, OCR)"]:::beSvc
        RAGSvc["Context & Citation Builder<br/>(build_document_context)"]:::beSvc
        AIRouterSvc["services/ai/ai_router.py<br/>(Dynamic Provider Dispatch)"]:::beSvc
        GeminiSvc["services/ai/gemini_service.py"]:::beSvc
        GroqSvc["services/ai/groq_service.py"]:::beSvc
        OpenRouterSvc["services/ai/openrouter_service.py"]:::beSvc
        AnalyticsSvc["Mastery & Streak Calc<br/>(calculate_knowledge_dna)"]:::beSvc

        AIRouterSvc --> GeminiSvc
        AIRouterSvc --> GroqSvc
        AIRouterSvc --> OpenRouterSvc
    end

    subgraph DataStorage ["Database Models & Storage (models.py & data/)"]
        direction TB
        UserModel["User Model<br/>(SQL: users)"]:::dbModel
        ProgressModel["LearningProgress Model<br/>(SQL: learning_progress)"]:::dbModel
        SubjectJSON["subjects.json Store"]:::dbModel
        DocumentJSON["documents.json Store"]:::dbModel
        QuizJSON["quizzes.json Store"]:::dbModel
        BlobStorage["backend/uploads/ Disk Store"]:::dbModel
    end

    AuthCtx -->|"Authorization: Bearer <jwt>"| AuthCtrl
    SubjMgrComp -->|"REST"| SubjCtrl
    DocViewComp -->|"Upload & Fetch"| DocCtrl
    DocChatComp -->|"Chat Q&A"| ChatCtrl
    QuizGenComp & QuizPlayComp -->|"Generate & Submit"| QuizCtrl
    DashComp & StudyPlanWidget -->|"Progress & Stats"| LearningCtrl
    VoiceComp -->|"Voice Mode Chat"| ChatCtrl

    AuthCtrl --> UserModel
    DocCtrl --> ExtractSvc
    ExtractSvc --> BlobStorage
    DocCtrl --> DocumentJSON
    SubjCtrl --> SubjectJSON
    ChatCtrl --> RAGSvc
    RAGSvc --> AIRouterSvc
    QuizCtrl --> AIRouterSvc
    QuizCtrl --> QuizJSON
    QuizCtrl --> ProgressModel
    LearningCtrl --> AnalyticsSvc
    AnalyticsSvc --> ProgressModel
    LearningCtrl --> SubjectJSON
    LearningCtrl --> DocumentJSON
```

---

## 4. Functional Boundary & Use-Case Model

The use-case model specifies all actor-to-system interactions across the platform boundary:

```mermaid
flowchart LR
    classDef actorNode fill:#1E293B,stroke:#0F172A,color:#FFFFFF,stroke-width:2px;
    classDef ucNode fill:#EFF6FF,stroke:#2563EB,color:#1E3A8A,stroke-width:1px;

    Visitor["Unauthenticated Visitor"]:::actorNode
    Student["Authenticated Student"]:::actorNode
    AIService["External AI Providers<br/>(Gemini, Groq, OpenRouter)"]:::actorNode

    subgraph SystemBoundary ["AI Knowledge DNA Platform"]
        direction TB
        UC_Reg["UC-01: Register New Account"]:::ucNode
        UC_Login["UC-02: Sign In & Acquire JWT"]:::ucNode
        UC_Theme["UC-03: Toggle Light/Dark Mode"]:::ucNode
        UC_Subj["UC-04: Manage Subjects & Folders"]:::ucNode
        UC_Upload["UC-05: Upload & Parse Study Materials"]:::ucNode
        UC_ViewDoc["UC-06: View Document with Page Nav"]:::ucNode
        UC_ChatRAG["UC-07: Query Document with Grounded Citations"]:::ucNode
        UC_Voice["UC-08: Hands-Free Voice Assistant Q&A"]:::ucNode
        UC_GenQuiz["UC-09: Generate Adaptive Topic Quiz"]:::ucNode
        UC_TakeQuiz["UC-10: Take Quiz & Review Explanations"]:::ucNode
        UC_Session["UC-11: Record Active Study Session"]:::ucNode
        UC_Progress["UC-12: Track Knowledge DNA & Weak Topics"]:::ucNode
        UC_Plan["UC-13: Access Personalized Study Plan"]:::ucNode

        UC_ChatRAG -.->|"<<includes>>"| UC_ViewDoc
        UC_TakeQuiz -.->|"<<updates>>"| UC_Progress
        UC_Session -.->|"<<updates>>"| UC_Progress
        UC_Progress -.->|"<<informs>>"| UC_Plan
    end

    Visitor --> UC_Reg
    Visitor --> UC_Login
    Visitor --> UC_Theme

    Student --> UC_Theme
    Student --> UC_Subj
    Student --> UC_Upload
    Student --> UC_ViewDoc
    Student --> UC_ChatRAG
    Student --> UC_Voice
    Student --> UC_GenQuiz
    Student --> UC_TakeQuiz
    Student --> UC_Session
    Student --> UC_Progress
    Student --> UC_Plan

    UC_Upload --> AIService
    UC_ChatRAG --> AIService
    UC_Voice --> AIService
    UC_GenQuiz --> AIService
```

---

## 5. Physical and Logical Deployment Model

```mermaid
flowchart TB
    classDef clientNode fill:#EFF6FF,stroke:#3B82F6,color:#1E3A8A,stroke-width:2px;
    classDef serverNode fill:#F0FDF4,stroke:#16A34A,color:#14532D,stroke-width:2px;
    classDef dbNode fill:#FEF3C7,stroke:#D97706,color:#78350F,stroke-width:2px;
    classDef cloudNode fill:#FAF5FF,stroke:#9333EA,color:#581C87,stroke-width:2px;

    subgraph ClientDevice ["Client Tier: Student Workstation / Mobile Device"]
        direction TB
        BrowserRuntime["Modern Web Browser (Chromium / Firefox / Safari)"]:::clientNode
        ClientArtifacts["• React 19 Single Page Application<br/>• Web Speech Recognition & Synthesis APIs<br/>• Client-Side HTML5 Canvas (PDF.js rendering)<br/>• LocalStorage (JWT token & ai_knowledge_dna_theme)"]:::clientNode
        BrowserRuntime --- ClientArtifacts
    end

    subgraph AppServerNode ["Application Server Tier: Backend Host (Port 5000)"]
        direction TB
        FlaskWSGI["Flask REST API Server (Python 3.14 Runtime)"]:::serverNode
        ServerComponents["• Flask-CORS & Flask-JWT-Extended Middleware<br/>• PyMuPDF / PyPDF Page Stream Extraction<br/>• python-docx & python-pptx Parsers<br/>• Tesseract OCR Subprocess Bridge<br/>• Multi-Provider AI Routing & Fallback Service"]:::serverNode
        LocalStoragePool["Local Server Disk Volumes:<br/>• backend/uploads/ (Encrypted Raw Documents)<br/>• backend/data/ (JSON Flat-File Stores)"]:::serverNode
        
        FlaskWSGI --- ServerComponents
        FlaskWSGI --- LocalStoragePool
    end

    subgraph DatabaseCloudNode ["Database Tier: TiDB Cloud Distributed Cluster"]
        direction TB
        TiDBInstance["TiDB Cloud MySQL Gateway<br/>Host: gateway01.ap-southeast-1.prod.aws.tidbcloud.com<br/>Port: 4000 (TLS 1.2/1.3 with CA Certificate)"]:::dbNode
        DBSchemas["Relational Schemas:<br/>• users table (Identity & bcrypt credentials)<br/>• learning_progress table (Mastery & Streaks)<br/>• quiz_attempts table (Submission histories)<br/>• subjects, documents, quizzes tables"]:::dbNode
        TiDBInstance --- DBSchemas
    end

    subgraph ExternalAICloud ["External AI Cloud Tier (HTTPS / TLS 443)"]
        direction TB
        GeminiEndpoint["Google Gemini API<br/>https://generativelanguage.googleapis.com<br/>Model: gemini-3.5-flash / gemini-1.5-pro"]:::cloudNode
        GroqEndpoint["Groq Cloud API<br/>https://api.groq.com/openai/v1<br/>Model: openai/gpt-oss-20b (Llama-3 accelerated)"]:::cloudNode
        OpenRouterEndpoint["OpenRouter AI Gateway<br/>https://openrouter.ai/api/v1<br/>Model: openai/gpt-6-luna"]:::cloudNode
    end

    ClientDevice -->|"HTTPS / REST (JSON API on :5000)<br/>Authorization: Bearer <jwt>"| AppServerNode
    AppServerNode -->|"MySQL Protocol over TLS (:4000)<br/>SQLAlchemy Connection Pool with pool_pre_ping"| DatabaseCloudNode
    AppServerNode -->|"REST over HTTPS (:443)<br/>API Key Injected via Environment"| GeminiEndpoint
    AppServerNode -->|"REST over HTTPS (:443)<br/>Low-Latency Streaming"| GroqEndpoint
    AppServerNode -->|"REST over HTTPS (:443)<br/>Resilient Fallback Gateway"| OpenRouterEndpoint
```

---

## 6. Data-Flow Modeling (Level 0 Context Diagram)

```mermaid
flowchart LR
    classDef entityNode fill:#1E293B,stroke:#0F172A,color:#FFFFFF,stroke-width:2px;
    classDef processNode fill:#2563EB,stroke:#1D4ED8,color:#FFFFFF,stroke-width:2px;
    classDef storeNode fill:#F8FAFC,stroke:#64748B,color:#0F172A,stroke-width:2px;

    Student["External Entity:<br/>Student / Learner"]:::entityNode
    AIProviders["External Entity:<br/>AI Providers (Gemini / Groq / OpenRouter)"]:::entityNode

    Platform((Process 0.0:<br/>AI Knowledge DNA<br/>Platform)):::processNode

    DBStore[("Data Store D1:<br/>TiDB Relational DB")]:::storeNode
    FileStore[("Data Store D2:<br/>File System & JSON Stores")]:::storeNode

    Student -->|"1. Credentials (Register / Login)"| Platform
    Student -->|"2. Study Materials (PDF, DOCX, PPTX, Img)"| Platform
    Student -->|"3. Natural Language & Voice Questions"| Platform
    Student -->|"4. Quiz Selections & Completed Sessions"| Platform

    Platform -->|"5. JWT Access Token & Authenticated Profile"| Student
    Platform -->|"6. Parsed Text, Topics, & Extractive Summaries"| Student
    Platform -->|"7. Grounded Answers with [Page X] Citations"| Student
    Platform -->|"8. Real-time Audio Speech & Sanitized Answers"| Student
    Platform -->|"9. Interactive Quizzes & Instant Evaluations"| Student
    Platform -->|"10. Knowledge DNA Score, Streaks, Study Plan"| Student

    Platform -->|"11. Grounded Context & System Prompt"| AIProviders
    AIProviders -->|"12. Generated Content & Structured Quiz JSON"| Platform

    Platform -->|"13. Insert/Update Users & LearningProgress"| DBStore
    DBStore -->|"14. Return User Records & Historical Mastery"| Platform

    Platform -->|"15. Write Blobs to uploads/ & Write JSON"| FileStore
    FileStore -->|"16. Read Raw Files & Load JSON Repositories"| Platform
```

---

## 7. Data-Flow Modeling (Level 1 Functional Decomposition)

```mermaid
flowchart TB
    classDef entityNode fill:#1E293B,stroke:#0F172A,color:#FFFFFF,stroke-width:2px;
    classDef procNode fill:#2563EB,stroke:#1D4ED8,color:#FFFFFF,stroke-width:2px;
    classDef storeNode fill:#F8FAFC,stroke:#64748B,color:#0F172A,stroke-width:2px;

    Student["External Entity:<br/>Student / Client"]:::entityNode
    AIProviders["External Entity:<br/>AI Model Providers"]:::entityNode

    P1(("1.0<br/>Authentication<br/>& Access Control")):::procNode
    P2(("2.0<br/>Subject<br/>Management")):::procNode
    P3(("3.0<br/>Document Ingestion<br/>& Text Extraction")):::procNode
    P4(("4.0<br/>RAG Context<br/>& Citation Chat")):::procNode
    P5(("5.0<br/>Quiz Engine<br/>& Evaluation")):::procNode
    P6(("6.0<br/>Knowledge DNA<br/>& Analytics Engine")):::procNode

    D1[("D1: users Table (TiDB)")]:::storeNode
    D2[("D2: subjects.json")]:::storeNode
    D3[("D3: documents.json & uploads/")]:::storeNode
    D4[("D4: quizzes.json")]:::storeNode
    D5[("D5: learning_progress (TiDB)")]:::storeNode

    Student -->|"Credentials"| P1
    P1 -->|"Query/Insert User"| D1
    D1 -->|"User Entity"| P1
    P1 -->|"JWT Token"| Student

    Student -->|"Subject CRUD (Name, Desc)"| P2
    P2 -->|"Write Subject"| D2
    D2 -->|"Subject Records"| P2
    P2 -->|"User's Subjects"| Student

    Student -->|"Upload File (.pdf/.docx/.pptx/img)"| P3
    P3 -->|"Save Staged File & Metadata"| D3
    P3 -->|"Extraction & Summary"| Student

    Student -->|"Question & Chat History"| P4
    D3 -->|"Read Pages Context"| P4
    P4 -->|"Grounded Prompt"| AIProviders
    AIProviders -->|"Raw Answer"| P4
    P4 -->|"Grounded Answer with [Page X]"| Student

    Student -->|"Request Quiz Config"| P5
    D3 -->|"Fetch Document Text"| P5
    P5 -->|"Quiz Prompt"| AIProviders
    AIProviders -->|"Quiz JSON"| P5
    P5 -->|"Persist Quiz"| D4
    P5 -->|"Sanitized Questions"| Student
    Student -->|"Submit Answer Choices"| P5
    D4 -->|"Verify Correct Answers"| P5
    P5 -->|"Scores, Accuracy & Explanations"| Student
    P5 -->|"Topic Attempt & Correct Counts"| P6

    Student -->|"Log Study Minutes"| P6
    P6 -->|"Update Cumulative Mastery & Minutes"| D5
    D5 -->|"Fetch User Progress Rows"| P6
    D2 & D3 -->|"Topics & Document References"| P6
    P6 -->|"Knowledge DNA, Streaks, Study Plan"| Student
```

---

## 8. Architectural Integrity and Verification Summary

1. **Multi-Tenant User Isolation:** Every data access routine (`filter_documents_for_user`, `filter_subjects_for_user`, `filter_quizzes_for_user`) inspects the authenticated JWT token identity (`get_jwt_identity()`). Users cannot query or mutate peer records.
2. **File Descriptor Resilience:** All file system read operations use context managers (`with open(...)`), eliminating `[WinError 32]` file handle locks under Windows execution environments.
3. **HTTP Contract Preservation:** The global exception handler traps `werkzeug.exceptions.HTTPException` to preserve standard 400, 401, 403, 404, 405, 409, and 413 HTTP status codes.
