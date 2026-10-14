# AI Knowledge DNA — Workflows, Algorithms & AI Orchestration Report

**Document Code:** MCA-PRJ-DNA-002  
**Target Project:** AI Knowledge DNA – Intelligent Personalized Learning Assistant  
**Repository Path:** `E:\DNA\AI-Knowledge-DNA`  
**Classification:** Engineering Workflows, Mathematical Formulations & Algorithm Specifications  
**Academic Level:** Master of Computer Applications (MCA) Project Documentation  

---

## 1. Document Upload & Multi-Format Ingestion Pipeline

The document ingestion pipeline processes diverse file formats (PDF, DOCX, PPTX, Images), extracts textual contents, runs extractive text analysis, and indexes topics.

```mermaid
flowchart TD
    classDef startNode fill:#10B981,stroke:#059669,color:#FFFFFF,stroke-width:2px;
    classDef actionNode fill:#EFF6FF,stroke:#3B82F6,color:#1E3A8A,stroke-width:1px;
    classDef decisionNode fill:#FEF3C7,stroke:#D97706,color:#78350F,stroke-width:2px;
    classDef errorNode fill:#FEE2E2,stroke:#DC2626,color:#991B1B,stroke-width:1px;
    classDef endNode fill:#1E293B,stroke:#0F172A,color:#FFFFFF,stroke-width:2px;

    Start([Student Selects Document in UI]):::startNode --> ValidateClient[Client Validates Format & Previews]:::actionNode
    ValidateClient --> SendRequest[POST /api/upload multipart/form-data with JWT]:::actionNode

    SendRequest --> CheckJWT{JWT Valid & Identity Present?}:::decisionNode
    CheckJWT -- No --> Reject401[Return 401 Unauthorized]:::errorNode --> EndFailure([Upload Aborted]):::endNode
    CheckJWT -- Yes --> CheckFile{File Part Present & Not Empty?}:::decisionNode

    CheckFile -- No --> Reject400[Return 400 'No file provided']:::errorNode --> EndFailure
    CheckFile -- Yes --> CheckExt{Extension in ALLOWED_EXTENSIONS?<br/>pdf, docx, pptx, png, jpg, jpeg, webp}:::decisionNode

    CheckExt -- No --> RejectType[Return 400 'Unsupported file type']:::errorNode --> EndFailure
    CheckExt -- Yes --> CheckSize{File Size <= 25 MB?}:::decisionNode

    CheckSize -- No --> RejectSize[Return 413 'File is too large']:::errorNode --> EndFailure
    CheckSize -- Yes --> SaveDisk[Generate UUID & Save to backend/uploads/<uuid>.<ext>]:::actionNode

    SaveDisk --> BranchExt{Detect File Extension}:::decisionNode

    BranchExt -- pdf --> ExtractPDF[extract_pdf_pages: Stream PdfReader page-by-page]:::actionNode
    BranchExt -- docx --> ExtractDOCX[extract_docx_pages: Stream Document paragraphs]:::actionNode
    BranchExt -- pptx --> ExtractPPTX[extract_pptx_pages: Stream Presentation slide shapes]:::actionNode
    BranchExt -- image --> ExtractOCR[extract_image_pages: PIL Image + Tesseract OCR]:::actionNode

    ExtractPDF --> JoinAnalysis[Consolidate Pages Array]:::actionNode
    ExtractDOCX --> JoinAnalysis
    ExtractPPTX --> JoinAnalysis
    ExtractOCR --> JoinAnalysis

    CheckParseSuccess{Text Extracted Successfully?}:::decisionNode
    JoinAnalysis --> CheckParseSuccess
    CheckParseSuccess -- Exception --> CleanupDisk[Unlink / Delete Staged File from Disk]:::errorNode
    CleanupDisk --> Return500[Return 500 'Extraction Error']:::errorNode --> EndFailure

    CheckParseSuccess -- Success --> RunAnalysis[analyze_document: Keyword Extraction & Sentence Scoring]:::actionNode
    RunAnalysis --> GenTopics[generate_topics: Top Keywords & Source Pages]:::actionNode
    RunAnalysis --> GenSummary[generate_summary: Top Scored Sentences]:::actionNode

    GenTopics & GenSummary --> AssembleDoc[Construct Document Object with user_id, word_count, topics]:::actionNode
    AssembleDoc --> SaveJSON[Append to backend/data/documents.json with Lock]:::actionNode
    SaveJSON --> Return201[Return 201 Created with Document Metadata]:::actionNode
    Return201 --> UpdateUI[UI Updates Subject Materials List & Renders Viewer]:::actionNode
    UpdateUI --> EndSuccess([Processing Complete]):::endNode
```

### 1.1 Text Extraction and Sentence Scoring Algorithm

Extractive summarization operates deterministically without relying on high-latency AI calls, ensuring offline capability:

1. **Keyword Extraction:** Identifies significant terms ($W$) exceeding length 3 while filtering standard stop words:
   $$\text{Frequency}(w) = \sum_{p \in P} \text{count}(w, p.text)$$
2. **Sentence Relevance Scoring:** For each sentence $s \in S$, its informational weight $R(s)$ is the sum of keyword occurrences normalized by sentence length:
   $$R(s) = \sum_{w \in W_{\text{top}}} \text{count}(w, s)$$
3. **Summary Generation:** The top 3 ranked sentences meeting minimal length requirements ($> 30$ characters) are combined chronologically to form the document executive summary.

---

## 2. Grounded Document RAG Q&A & Citation Extraction

The Retrieval-Augmented Generation (RAG) subsystem enables students to ask questions against their uploaded materials, receiving answers grounded with verifiable page citations.

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (UI)
    participant DocChat as DocumentChat Component
    participant DocViewer as DocumentViewer (PDF Canvas)
    participant ChatAPI as Backend (/api/chat or /documents/:id/chat)
    participant Store as documents.json Repository
    participant RAGEngine as RAG Context Builder (app.py)
    participant AIRouter as AI Router (ai_router.py)
    participant LLM as External AI Model (Gemini / Groq)

    Student->>DocChat: Enters question ("Explain active transport in cell biology")
    DocChat->>ChatAPI: POST /api/chat {document_id, question, history, voice_response: false}
    
    ChatAPI->>ChatAPI: Validate JWT Identity & Request Payload
    ChatAPI->>Store: load_documents() & filter_documents_for_user(user_id)
    Store-->>ChatAPI: Return user-owned documents
    
    alt Document not found or owned by another user
        ChatAPI-->>DocChat: 403 Forbidden / 404 Not Found
        DocChat-->>Student: Display "Document not found or access denied"
    else Document ownership confirmed
        ChatAPI->>RAGEngine: build_document_context(pages, question)
        note over RAGEngine: Keyword matching scores pages against question.<br/>Sorts and selects top-k relevant pages.<br/>Attaches [Page X] boundary markers.
        RAGEngine-->>ChatAPI: Returns {context_string, relevant_pages}
        
        ChatAPI->>RAGEngine: build_chat_history(history)
        RAGEngine-->>ChatAPI: Formatted prior turns
        
        ChatAPI->>RAGEngine: Assemble Grounded Prompt with Citation Rules
        note over RAGEngine: Injects rule: "When info comes from a page, add [Page X].<br/>Never invent page numbers."

        ChatAPI->>AIRouter: generate_ai_response(task="document_analysis", prompt)
        AIRouter->>LLM: Ingest Context + Instructions + Prompt
        LLM-->>AIRouter: "Active transport requires ATP [Page 3] to move against gradient [Page 4]."
        AIRouter-->>ChatAPI: Return {success: true, answer, model}

        ChatAPI->>ChatAPI: clean_ai_answer(answer)
        ChatAPI->>ChatAPI: extract_page_references(answer, available_pages)
        note over ChatAPI: Parses regex r"\[Page\s+(\d+)\]"<br/>Maps to structured sources: [{page: 3}, {page: 4}]

        ChatAPI-->>DocChat: 200 OK {success: true, answer, sources: [{page: 3}, {page: 4}], model}
        DocChat-->>Student: Renders AI message bubble with clickable [Page 3] and [Page 4] chips
        
        opt Student clicks [Page 3] chip
            Student->>DocChat: Click Page 3 citation chip
            DocChat->>DocViewer: onPageChange(3)
            DocViewer-->>Student: Scrolls & renders Page 3 in PDF canvas
        end
    end
```

### 2.1 Context Assembly and Citation Rules

- **Relevance Ranking:** Page chunks are scored against student question tokens:
  $$\text{PageScore}(P_i, Q) = \sum_{q \in Q} \text{TermFrequency}(q, P_i)$$
- **Strict Citation Policy:** The system prompt enforces:
  1. Primary source restriction: Information must be extracted from the supplied context.
  2. Grounding references: Information derived from a specific page must be annotated with `[Page X]`.
  3. Anti-hallucination guard: If an answer is not present in the study materials, the model explicitly notifies the student rather than extrapolating.

---

## 3. AI Provider Routing & Resilient Fallback Circuits

The AI orchestration engine in `backend/services/ai/ai_router.py` provides resilient multi-provider dispatch:

```mermaid
flowchart TD
    classDef startNode fill:#10B981,stroke:#059669,color:#FFFFFF,stroke-width:2px;
    classDef actionNode fill:#EFF6FF,stroke:#3B82F6,color:#1E3A8A,stroke-width:1px;
    classDef decisionNode fill:#FEF3C7,stroke:#D97706,color:#78350F,stroke-width:2px;
    classDef errorNode fill:#FEE2E2,stroke:#DC2626,color:#991B1B,stroke-width:1px;
    classDef endNode fill:#1E293B,stroke:#0F172A,color:#FFFFFF,stroke-width:2px;

    Start([Call generate_ai_response]):::startNode --> ValidateInput{Validate Task & Prompt?}:::decisionNode

    ValidateInput -- Empty / Invalid --> RaiseValueError[Raise ValueError 'Task/Prompt Required']:::errorNode --> Abort([Execution Terminated]):::endNode
    ValidateInput -- Valid --> CheckExplicitProvider{Explicit Provider Specified?}:::decisionNode

    CheckExplicitProvider -- Yes --> UseExplicit[Selected = Explicit Provider]:::actionNode
    CheckExplicitProvider -- No --> TaskLookup[Lookup TASK_PROVIDER_MAP by Task]:::actionNode

    TaskLookup --> BranchTask{Classify Task}:::decisionNode
    BranchTask -- document_analysis / summary / embedding --> MapGemini[Primary = Gemini]:::actionNode
    BranchTask -- chat / voice / fast_response / quick_quiz --> MapGroq[Primary = Groq]:::actionNode
    BranchTask -- general / model_testing --> MapOpenRouter[Primary = OpenRouter]:::actionNode

    UseExplicit & MapGemini & MapGroq & MapOpenRouter --> ResolveSequence[Resolve Sequence from FALLBACK_ORDER]:::actionNode

    ResolveSequence --> SeqNote["Gemini: [Gemini -> OpenRouter -> Groq]<br/>Groq: [Groq -> OpenRouter -> Gemini]<br/>OpenRouter: [OpenRouter -> Groq -> Gemini]"]:::actionNode

    SeqNote --> InitLoop[Index = 0; FallbackUsed = False]:::actionNode
    InitLoop --> ExecProvider[Execute _generate_with_provider for Current Provider]:::actionNode

    ExecProvider --> CheckCallSuccess{API Call Successful?}:::decisionNode

    CheckCallSuccess -- Yes --> LogSuccess[Log Response Time & Model Metadata]:::actionNode
    LogSuccess --> ReturnPayload[Return {success: True, provider, model, answer, fallback_used}]:::actionNode
    ReturnPayload --> EndSuccess([Return Response]):::endNode

    CheckCallSuccess -- Caught Exception --> CheckTempErr{is_temporary_error?<br/>429, rate limit, quota, timeout, 500, 502, 503, overloaded}:::decisionNode

    CheckTempErr -- No Permanent Error<br/>e.g. Auth/Invalid Key --> RaisePermanent[Raise Exception Immediately<br/>Do Not Cascade Fallback]:::errorNode --> Abort

    CheckTempErr -- Yes Transient Error --> CheckHasNext{Next Provider Available in Sequence?}:::decisionNode

    CheckHasNext -- Yes --> TriggerFallback[Set FallbackUsed = True<br/>Index = Index + 1<br/>Log Fallback Warning]:::actionNode
    TriggerFallback --> ExecProvider

    CheckHasNext -- No Exhausted --> RaiseAllFailed[Raise RuntimeError 'All AI providers failed']:::errorNode --> Abort
```

### 3.1 Task Mapping & Fallback Table

| Task Category | Primary Provider | Fallback Sequence | Target Model | Optimization Goal |
| :--- | :--- | :--- | :--- | :--- |
| `document_analysis` | **Gemini** | Gemini $\to$ OpenRouter $\to$ Groq | `gemini-3.5-flash` | Large token context, dense reasoning |
| `summary` | **Gemini** | Gemini $\to$ OpenRouter $\to$ Groq | `gemini-3.5-flash` | Comprehensive document compression |
| `chat` | **Groq** | Groq $\to$ OpenRouter $\to$ Gemini | `openai/gpt-oss-20b` | High throughput, conversational fluency |
| `voice` | **Groq** | Groq $\to$ OpenRouter $\to$ Gemini | `openai/gpt-oss-20b` | Minimal latency ($< 800\text{ms}$ time-to-first-token) |
| `quick_quiz` | **Groq** | Groq $\to$ OpenRouter $\to$ Gemini | `openai/gpt-oss-20b` | Rapid multi-choice extraction |
| `general` | **OpenRouter** | OpenRouter $\to$ Groq $\to$ Gemini | `openai/gpt-6-luna` | Broad pedagogical explanations |

---

## 4. Adaptive Quiz Generation & Anti-Cheat Evaluation

The quiz subsystem generates customized assessments and evaluates attempts:

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (Quiz UI)
    participant QuizGen as QuizGenerator Component
    participant QuizPlay as QuizPlayer Component
    participant QuizAPI as Backend (/api/quiz/*)
    participant Store as quizzes.json & documents.json
    participant AIRouter as AI Router / Gemini Client
    participant ProgressDB as LearningProgress Table (TiDB)

    rect rgb(240, 249, 255)
        note over Student, ProgressDB: Phase 1: Quiz Generation Workflow
        Student->>QuizGen: Configure Quiz (Subject, Count: 5-20, Difficulty: Medium)
        QuizGen->>QuizAPI: POST /api/quiz/generate {subject_id, question_count, difficulty}
        QuizAPI->>Store: Validate Subject Ownership & Fetch Subject Documents
        Store-->>QuizAPI: Documents Found (Extract text context)

        QuizAPI->>AIRouter: Request Structured JSON Quiz (Strict 4-option schema)
        AIRouter-->>QuizAPI: Raw AI JSON with questions, options, correct_answer, explanations
        QuizAPI->>QuizAPI: Validate JSON & Enforce 4 options per question

        QuizAPI->>Store: Save Full Quiz to backend/data/quizzes.json (with answers & attempted=false)
        note over QuizAPI: Anti-Cheat Sanitization:<br/>Omit correct_answer and explanation<br/>from client-facing response payload.
        QuizAPI-->>QuizGen: 200 OK {success: true, quiz: {id, questions: [id, question, options, page, topic]}}
        QuizGen->>QuizPlay: Mount Quiz with Sanitized Questions
    end

    rect rgb(240, 253, 244)
        note over Student, ProgressDB: Phase 2: Quiz Attempt & Submission Workflow
        Student->>QuizPlay: Completes all questions, clicks "Submit Quiz"
        QuizPlay->>QuizAPI: POST /api/quiz/<quiz_id>/submit {answers: {q1: 1, q2: 0}}
        QuizAPI->>Store: Load Stored Quiz & Verify User Ownership

        loop For Each Question in Quiz
            QuizAPI->>QuizAPI: Compare student selection with question["correct_answer"]
            note over QuizAPI: Track topic_totals[topic] += [attempted, correct]
        end

        QuizAPI->>QuizAPI: Compute score, total, accuracy = (score / total) * 100
        QuizAPI->>Store: Update Quiz (attempted=true, score, accuracy, completed_at)

        loop For Each Topic in topic_totals
            QuizAPI->>ProgressDB: update_learning_progress(user_id, topic, attempted, correct)
            note over ProgressDB: Calculate new mastery_score = (correct / attempted) * 100<br/>Update last_studied timestamp
        end
        QuizAPI->>ProgressDB: db.session.commit()

        QuizAPI-->>QuizPlay: 200 OK {success: true, score, total, accuracy, results: [with explanations & pages]}
        QuizPlay-->>Student: Displays Score Banner, Topic Breakdown, and Question Explanations
    end
```

---

## 5. Learning Progress Accumulation & Streak Algorithms

```mermaid
flowchart TD
    classDef startNode fill:#10B981,stroke:#059669,color:#FFFFFF,stroke-width:2px;
    classDef actionNode fill:#EFF6FF,stroke:#3B82F6,color:#1E3A8A,stroke-width:1px;
    classDef decisionNode fill:#FEF3C7,stroke:#D97706,color:#78350F,stroke-width:2px;
    classDef errorNode fill:#FEE2E2,stroke:#DC2626,color:#991B1B,stroke-width:1px;
    classDef endNode fill:#1E293B,stroke:#0F172A,color:#FFFFFF,stroke-width:2px;

    StartA([Event A: Study Session Completed]):::startNode --> InputMinutes[Payload: topic, study_minutes]:::actionNode
    StartB([Event B: Quiz Attempt Submitted]):::startNode --> InputQuiz[Payload: topic_totals with questions attempted & correct]:::actionNode

    InputMinutes --> CheckMinutes{Minutes between 1 and 720?}:::decisionNode
    CheckMinutes -- No --> RejectMinutes[Return 400 'Invalid study_minutes']:::errorNode --> EndFailure([Aborted]):::endNode
    CheckMinutes -- Yes --> FetchUser[Extract Authenticated user_id from JWT]:::actionNode

    InputQuiz --> FetchUser

    FetchUser --> QueryDB[Query LearningProgress for user_id and topic in TiDB]:::actionNode
    QueryDB --> CheckRowExists{Record Exists for Topic?}:::decisionNode

    CheckRowExists -- No --> CreateRow[Instantiate new LearningProgress record<br/>defaults: attempted=0, correct=0, minutes=0]:::actionNode
    CheckRowExists -- Yes --> LoadRow[Load existing LearningProgress entity]:::actionNode

    CreateRow & LoadRow --> AccumulateStats[Accumulate Metrics:<br/>study_minutes += new_minutes<br/>questions_attempted += new_attempted<br/>questions_correct += new_correct]:::actionNode

    AccumulateStats --> CalcMastery{questions_attempted > 0?}:::decisionNode
    CalcMastery -- Yes --> ComputeMastery[mastery_score = round((correct / attempted) * 100, 2)]:::actionNode
    CalcMastery -- No --> KeepMastery[Preserve existing mastery_score]:::actionNode

    ComputeMastery & KeepMastery --> UpdateTimestamp[Update last_studied = current UTC timestamp]:::actionNode
    UpdateTimestamp --> CommitDB[Execute db.session.commit() to TiDB Cloud]:::actionNode

    CommitDB --> LoadAllUserRows[Fetch all progress rows for user_id]:::actionNode
    LoadAllUserRows --> CalcStreak[calculate_learning_streak: Count consecutive active study dates]:::actionNode
    LoadAllUserRows --> CalcHours[Total Study Hours = sum(study_minutes) / 60]:::actionNode
    LoadAllUserRows --> CalcDNA["calculate_knowledge_dna:<br/>Score = 0.6 * avg(mastery) + 0.4 * quiz_accuracy"]:::actionNode

    CalcStreak & CalcHours & CalcDNA --> ReturnResponse[Return 200/201 JSON with progress, study_hours, streak, DNA score]:::actionNode
    ReturnResponse --> UpdateUI[Dashboard & Personalized Study Plan Refresh UI]:::actionNode
    UpdateUI --> EndSuccess([Learning Progress Synchronized]):::endNode
```

### 5.1 Mastery and Streak Formulations

1. **Topic Mastery Score:**
   $$\text{Mastery}(T) = \begin{cases} \text{round}\left(\frac{\sum \text{QuestionsCorrect}(T)}{\sum \text{QuestionsAttempted}(T)} \times 100, 2\right), & \text{if } \text{Attempted} > 0 \\ 0.00, & \text{otherwise} \end{cases}$$
2. **Learning Streak Algorithm:**
   Let $D = \{ \text{date}(\text{last\_studied}_i) \mid \text{last\_studied}_i \neq \text{NULL} \}$ sorted in descending order.
   Starting from current date $d_0 = \text{today}$:
   $$\text{Streak} = \max \{ k \mid \forall j \in [0, k-1], \, (d_0 - j \text{ days}) \in D \}$$

---

## 6. Voice Assistant Speech Processing Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (Voice Assistant)
    participant UI as VoiceAssistant Component
    participant WebSpeechIn as Web Speech API (SpeechRecognition)
    participant ChatAPI as Backend (/api/chat)
    participant AIRouter as AI Router (services/ai/ai_router.py)
    participant GroqAPI as Groq Cloud API (Low-Latency LLM)
    participant Cleaner as clean_voice_answer (app.py)
    participant WebSpeechOut as Web Speech API (SpeechSynthesis)

    Student->>UI: Clicks Microphone Button ("Start Listening")
    UI->>WebSpeechIn: recognition.start()
    WebSpeechIn-->>Student: Prompts for mic access / listens to audio
    Student->>WebSpeechIn: Speaks query ("What is mitosis and how does it work?")
    WebSpeechIn-->>UI: Event onresult (Transcribed Text: "What is mitosis and how does it work?")

    UI->>UI: Display user prompt & set listening = false, processing = true
    UI->>ChatAPI: POST /api/chat {document_id, question, history, voice_response: true}

    ChatAPI->>ChatAPI: Validate JWT & Verify Document Ownership
    ChatAPI->>AIRouter: generate_ai_response(task="voice", prompt)
    note over AIRouter: Task "voice" routes primarily to Groq<br/>for sub-second generation latency.
    AIRouter->>GroqAPI: Low-latency inference query
    GroqAPI-->>AIRouter: Raw answer containing markdown & citation tags
    AIRouter-->>ChatAPI: Return raw answer text

    ChatAPI->>Cleaner: clean_voice_answer(raw_answer)
    note over Cleaner: Regex sanitization:<br/>1. Strip markdown headers (#, ##, ###)<br/>2. Strip citation tags [Page X]<br/>3. Strip hyperlinks https://...<br/>4. Strip Source: and References: blocks<br/>5. Normalize whitespace for natural cadence.
    Cleaner-->>ChatAPI: Clean, natural speakable text

    ChatAPI-->>UI: 200 OK {success: true, answer: clean_text, sources: []}
    UI->>UI: Append answer to conversation log

    UI->>WebSpeechOut: new SpeechSynthesisUtterance(clean_text)
    WebSpeechOut-->>Student: Speaks natural synthesized voice response
    Student->>UI: Toggles mic again or continues learning session
```

---

## 7. Knowledge DNA Processing & Study Plan Synthesis

```mermaid
flowchart TD
    classDef startNode fill:#10B981,stroke:#059669,color:#FFFFFF,stroke-width:2px;
    classDef inputNode fill:#EFF6FF,stroke:#3B82F6,color:#1E3A8A,stroke-width:1px;
    classDef calcNode fill:#FEF3C7,stroke:#D97706,color:#78350F,stroke-width:2px;
    classDef outputNode fill:#F3E8FF,stroke:#9333EA,color:#581C87,stroke-width:1px;
    classDef endNode fill:#1E293B,stroke:#0F172A,color:#FFFFFF,stroke-width:2px;

    Start([Trigger: GET /api/dashboard/stats & /api/learning/insights]):::startNode --> CollectInputs[Collect Student Artifacts for Authenticated user_id]:::inputNode

    subgraph InputSignals ["Multi-Dimensional Learning Signals"]
        DocTopics["Signal 1: Discovered Topics<br/>(Extracted from user documents)"]:::inputNode
        QuizAttempts["Signal 2: Quiz Accuracy<br/>(Total Correct / Total Attempted)"]:::inputNode
        TopicMastery["Signal 3: Topic Mastery<br/>(learning_progress.mastery_score)"]:::inputNode
        StudyTime["Signal 4: Study Time<br/>(learning_progress.study_minutes)"]:::inputNode
        Timestamps["Signal 5: Recency Timestamps<br/>(learning_progress.last_studied)"]:::inputNode
    end

    CollectInputs --> DocTopics & QuizAttempts & TopicMastery & StudyTime & Timestamps

    subgraph AnalyticalEngines ["Analytics & Synthesis Engines"]
        CalcDNA{"Has Active Progress Records?"}:::calcNode
        
        FormulaActive["Standard Knowledge DNA Formula:<br/>DNA = round(0.6 * Average(Mastery) + 0.4 * QuizAccuracy, 1)"]:::calcNode
        FormulaBoot["Bootstrap Topic DNA Formula:<br/>DNA = min(100, DiscoveredTopicCount * 5)"]:::calcNode

        StreakEngine["Streak Algorithm:<br/>Group last_studied by unique date (YYYY-MM-DD).<br/>Check consecutive daily calendar steps from today."]:::calcNode
        
        HoursEngine["Study Hours Aggregator:<br/>Total Hours = round(sum(study_minutes) / 60, 1)"]:::calcNode

        WeakConceptEngine["Weak Concept Detector:<br/>Filter topics where mastery < 70% or unattempted.<br/>Map each weak topic to source document & page."]:::calcNode
    end

    TopicMastery & QuizAttempts --> CalcDNA
    CalcDNA -- Yes --> FormulaActive
    CalcDNA -- No --> FormulaBoot

    Timestamps --> StreakEngine
    StudyTime --> HoursEngine
    DocTopics & TopicMastery --> WeakConceptEngine

    subgraph OutputRepresentations ["Personalized UI Artifacts"]
        DNAScoreMetric["Knowledge DNA Index (0 - 100%)"]:::outputNode
        StreakMetric["Learning Streak Counter (Days)"]:::outputNode
        StudyHoursMetric["Total Study Hours Metric"]:::outputNode
        StudyPlan["Personalized Study Plan Widget<br/>• Prioritized Weak Topics<br/>• Target Study Duration<br/>• Recommended Document Reference"]:::outputNode
    end

    FormulaActive & FormulaBoot --> DNAScoreMetric
    StreakEngine --> StreakMetric
    HoursEngine --> StudyHoursMetric
    WeakConceptEngine --> StudyPlan

    DNAScoreMetric & StreakMetric & StudyHoursMetric & StudyPlan --> RenderDashboard[Dashboard State Rendered in Academic Focus UI]:::outputNode
    RenderDashboard --> End([Workflow Completed]):::endNode
```

### 7.1 Mathematical Knowledge DNA Formulation

The Knowledge DNA index ($K_{\text{DNA}} \in [0, 100]$) serves as the student's unified mastery score:

$$K_{\text{DNA}} = \begin{cases} 
\text{round}\left(0.6 \cdot \bar{M} + 0.4 \cdot A_Q, \, 1\right), & \text{if } |\mathcal{T}_{\text{evaluated}}| > 0 \\ 
\min\left(100, \, |\mathcal{T}_{\text{discovered}}| \cdot 5\right), & \text{if } |\mathcal{T}_{\text{evaluated}}| = 0 \text{ and } |\mathcal{T}_{\text{discovered}}| > 0 \\ 
0.0, & \text{otherwise} 
\end{cases}$$

Where:
- $\bar{M} = \frac{1}{|\mathcal{T}_{\text{evaluated}}|} \sum_{t \in \mathcal{T}} \text{Mastery}(t)$ is the mean topic mastery score.
- $A_Q = \frac{\sum \text{Correct}}{\sum \text{TotalQuestions}} \times 100$ is the cumulative quiz accuracy across all attempts.
- $|\mathcal{T}_{\text{discovered}}|$ represents unique topics extracted across the student's study materials.
