# AI Knowledge DNA — Test Evidence, Bug Fixing & Validation Report

**Document Code:** MCA-PRJ-DNA-005  
**Target Project:** AI Knowledge DNA – Intelligent Personalized Learning Assistant  
**Repository Path:** `E:\DNA\AI-Knowledge-DNA`  
**Classification:** Quality Assurance, Test Automation & Defect Remediation Report  
**Academic Level:** Master of Computer Applications (MCA) Project Documentation  

---

## 1. Test Strategy & Safety Protocols

To guarantee 100% data integrity and ensure non-destructive testing, all automated backend tests operate under an isolated in-memory test harness (`backend/tests/test_base.py`):

1. **Database Isolation:** All write, update, and delete tests dynamically swap Flask-SQLAlchemy engines to an in-memory SQLite database (`sqlite:///:memory:`). The production TiDB Cloud MySQL database (`gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test`) is completely isolated and received zero mutations.
2. **File Storage Isolation:** Staged file uploads and flat-file stores are redirected to temporary sandboxes via `tempfile.mkdtemp(prefix="dna_isolated_test_")`, preserving `backend/data/*.json` and `backend/uploads/`.
3. **Environment Secrets Protection:** The production configuration `backend/.env` was protected from modifications, replacements, or exposure.

---

## 2. Automated Test Execution Evidence

All **43 backend automated tests** were executed and validated.

### 2.1 Execution Summary
- **Total Tests Executed:** 43
- **Passed:** 43 (100%)
- **Failed:** 0 (0%)
- **Errors:** 0 (0%)
- **Overall Execution Time:** ~6.8 seconds
- **Pass Rate:** **100.0%**

### 2.2 Test Suite Breakdown

| Suite Identifier | Target Module / Subsystem | Tests Executed | Passed | Status | Key Verifications |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `test_startup_config.py` | App boot, CORS, Error Handlers | 5 | 5 | PASS | Root status, `/api/health`, CORS headers, 404 handler, DB table metadata. |
| `test_auth_security.py` | Authentication & JWT Security | 9 | 9 | PASS | Registration, duplicate email rejection (409), login validation (401), `/api/auth/me`, unauthenticated access rejection. |
| `test_subjects_documents.py` | Subjects, Uploads & Isolation | 8 | 8 | PASS | Subject CRUD, upload validation, DOCX extraction, secure file streaming (403), cross-tenant isolation. |
| `test_ai_router.py` | AI Provider Dynamic Routing | 9 | 9 | PASS | Task-to-provider mappings, fallback chains (Gemini $\to$ OpenRouter $\to$ Groq), 429/503 rate-limit recovery, voice speech cleaner. |
| `test_chat_voice.py` | Grounded RAG Chat & Voice | 6 | 6 | PASS | Document chat validation, citation grounding (`[Page X]`), voice sanitization mode, cross-tenant chat isolation (403). |
| `test_quizzes_learning.py` | Quiz Engine & Learning DB | 5 | 5 | PASS | Anti-cheat quiz generation, answer scoring, `LearningProgress` table updates, study sessions, dashboard stats. |
| `test_e2e_workflow.py` | End-to-End Student Journey | 1 | 1 | PASS | 14-step coherent student lifecycle from registration through document study, quiz evaluation, and multi-tenant security verification. |

---

## 3. Frontend Verification & Static Analysis Evidence

### 3.1 Production Bundle Compilation
- **Command:** `cmd /c npm run build` (executed in `frontend/`)
- **Outcome:** Exited with code `0` in **209ms**.
- **Generated Assets:**
  - `dist/index.html` (1.03 kB)
  - `dist/assets/index-BdiaCHpw.css` (70.03 kB)
  - `dist/assets/index-CxFe_GBs.js` (377.79 kB)
- **Result:** Zero syntax errors, zero missing imports, zero module resolution failures.

### 3.2 Static Code Analysis & Linter
- **Command:** `cmd /c npm run lint` (executed in `frontend/`)
- **Outcome:** Exited with return code `0` (**0 errors**).
- **Result:** Complete source tree adheres to ECMAScript standard and React 19 standards.

---

## 4. Defect Remediation & Retesting Traceability Matrix

| Defect ID | Severity | File & Location | Root Cause Description | Remediation Applied | Retest Verification Result |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **DEF-01** | High | `backend/app.py`<br/>Line 2116 | Global `@app.errorhandler(Exception)` trapped all `HTTPException` instances, transforming standard 404, 405, and 413 into HTTP 500 Unhandled Server Errors. | Added explicit check `if isinstance(error, HTTPException): return jsonify(...), error.code`. | `test_startup_config.py::test_404_handler` passes with 404. |
| **DEF-02** | High | `backend/app.py`<br/>Lines 408–525 | File parsing routines (`extract_pdf_pages`, `extract_docx_pages`, etc.) did not close file streams with context managers, triggering Windows `[WinError 32]` lock errors on document deletion. | Wrapped all file streams in `with open(file_path, "rb") as f:` and `with Image.open(...)`. | `test_subjects_documents.py` executes document deletion cleanly without lock error. |
| **DEF-03** | Medium | `frontend/src/services/api.js`<br/>Line 91 | Variable `baseUrl` was declared via `import.meta.env.VITE_API_URL` but never used, while the function hardcoded localhost `http://127.0.0.1:5000`. | Replaced hardcoded string with template literal `${baseUrl}/files/...`. | `npm run lint` and `npm run build` pass with zero errors. |
| **DEF-04** | Medium | `frontend/src/features/subjects/SubjectManager.jsx`<br/>Line 133 | `loadSubjects` called `showMessage` on line 133 before `const showMessage` was declared on line 205, violating JavaScript temporal dead zone rules. | Relocated `showMessage` declaration above `loadSubjects`. | ESLint temporal dead zone error completely eliminated. |
| **DEF-05** | Low | `frontend/src/features/subjects/SubjectManager.jsx`<br/>Line 541 | `openDocument` mutated `window.location.href` directly, triggering full browser reload and bypassing client SPA routing. | Replaced with React Router `navigate('/document/' + document.id)`. | Smooth client-side SPA route transition verified. |
| **DEF-06** | Low | `frontend/src/features/dashboard/Dashboard.jsx`<br/>Lines 49, 59, 103 | Unused button styles and unread state variable `learningProgress` triggered lint errors. | Removed dead style objects and prefixed unused state variable `_learningProgress`. | Linter passes with 0 errors. |

---

## 5. Security & Multi-Tenant Isolation Verification

Multi-tenant cross-user barriers were audited across all API access paths:
1. **Subject Access:** User B receives HTTP 404 when querying or attempting to delete User A's subject ID.
2. **Document Retrieval:** User B cannot view, retrieve, or list User A's uploaded documents.
3. **File Streaming:** User B receives HTTP 403 Forbidden when requesting User A's stored filename via `/api/files/<filename>`.
4. **Conversational Chat:** User B receives HTTP 403 Forbidden when requesting Q&A inferences against User A's document.
5. **Quiz Submissions:** User B receives HTTP 404 Not Found when submitting answer choices for User A's quiz ID.
6. **Dashboard Statistics:** Dashboard metrics aggregate data exclusively for the authenticated user ID.

---

## 6. Distinctions, Assumptions & Limitations

- **Verified Facts:** All 43 unit and integration tests executed in the runtime environment and passed. Frontend built in 209ms without errors. All 26 backend endpoints are present and active.
- **Historical Context:** Development database uses TiDB Cloud MySQL; tests ran against an in-memory test engine for safety.
- **Assumptions for Live Inferences:** Live AI inferences require active internet connectivity and valid provider credentials (`GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`) configured in `backend/.env`. In test suites, AI responses are mocked to verify logic deterministically.
