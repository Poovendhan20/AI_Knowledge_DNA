import { useEffect, useRef, useState } from "react";

import {
  Link,
  useParams,
  useSearchParams,
} from "react-router-dom";
import "./DocumentViewer.css";
import {
  FaArrowLeft,
  FaExternalLinkAlt,
  FaFilePdf,
  FaChevronLeft,
  FaChevronRight,
} from "react-icons/fa";

import API, {
  getDocument,
  getFileBlob,
} from "../../services/api";

import DocumentChat from "./DocumentChat";

function DocumentViewer() {
  const { documentId } = useParams();

  const [searchParams, setSearchParams] =
    useSearchParams();

  // =====================================================
  // STATE
  // =====================================================

  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // =====================================================
  // PROTECTED PDF STATE
  // =====================================================

  const [pdfBlobUrl, setPdfBlobUrl] = useState("");
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState("");

  // =====================================================
  // CURRENT PAGE
  // =====================================================

  const currentPage = Math.max(
    1,
    Number(searchParams.get("page") || 1)
  );

  // =====================================================
  // STUDY TIME TRACKING
  // =====================================================

  const studyStartedAtRef = useRef(null);
  const studyRecordedMinutesRef = useRef(0);
  const studyTimerRef = useRef(null);
  const currentPageRef = useRef(currentPage);

  useEffect(() => {
    currentPageRef.current = currentPage;
  }, [currentPage]);

  const getStudyTopic = () => {
    const topics = Array.isArray(document?.topics)
      ? document.topics
      : [];

    const currentTopic = topics.find(
      (topic) =>
        Number(topic?.page || 0) ===
        Number(currentPageRef.current)
    );

    return (
      currentTopic?.name ||
      topics[0]?.name ||
      document?.subject ||
      document?.name ||
      "General"
    );
  };

  const recordCompletedStudyMinutes = async () => {
    if (!studyStartedAtRef.current) {
      return;
    }

    const elapsedMinutes = Math.floor(
      (Date.now() - studyStartedAtRef.current) / 60000
    );

    const minutesToRecord =
      elapsedMinutes -
      studyRecordedMinutesRef.current;

    if (minutesToRecord <= 0) {
      return;
    }

    try {
      if (!API || typeof API.post !== "function") {
        throw new Error("API client is not available.");
      }

      const response = await API.post(
        "/learning/session",
        {
          topic: getStudyTopic(),
          study_minutes: minutesToRecord,
        }
      );

      if (response?.data?.success) {
        studyRecordedMinutesRef.current =
          elapsedMinutes;
      }
    } catch (studyError) {
      console.error(
        "Study time tracking error:",
        studyError
      );
    }
  };

  // =====================================================
  // LOAD DOCUMENT
  // =====================================================

  useEffect(() => {
    let mounted = true;

    const loadDocument = async () => {
      try {
        setLoading(true);
        setError("");

        const result = await getDocument(documentId);

        if (!mounted) {
          return;
        }

        if (
          result &&
          result.success &&
          result.document
        ) {
          setDocument(result.document);
        } else {
          setError(
            result?.message ||
              "Document not found."
          );
        }
      } catch (err) {
        console.error(
          "Document loading error:",
          err
        );

        if (mounted) {
          setError(
            err?.response?.data?.message ||
              "Unable to load document."
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    if (documentId) {
      loadDocument();
    } else {
      setError("Document ID is missing.");
      setLoading(false);
    }

    return () => {
      mounted = false;
    };
  }, [documentId]);

  // =====================================================
  // LOAD PROTECTED PDF
  // =====================================================
  //
  // IMPORTANT:
  // The backend PDF endpoint requires JWT authentication.
  //
  // We DO NOT directly use:
  // /api/files/<filename>
  //
  // Instead:
  //
  // React
  //   ↓
  // Axios
  //   ↓
  // JWT Authorization header
  //   ↓
  // Backend
  //   ↓
  // PDF Blob
  //   ↓
  // Browser Blob URL
  //   ↓
  // iframe
  //
  // =====================================================

  useEffect(() => {
    let mounted = true;
    let objectUrl = null;

    const loadProtectedPdf = async () => {
      if (
        !document ||
        !document.stored_name
      ) {
        return;
      }

      try {
        setPdfLoading(true);
        setPdfError("");
        setPdfBlobUrl("");

        console.log(
          "Loading protected PDF:",
          document.stored_name
        );

        const blob = await getFileBlob(
          document.stored_name
        );

        if (!mounted) {
          return;
        }

        if (!blob) {
          throw new Error(
            "PDF file is empty."
          );
        }

        objectUrl =
          URL.createObjectURL(blob);

        console.log(
          "Protected PDF loaded successfully."
        );

        setPdfBlobUrl(objectUrl);
      } catch (err) {
        console.error(
          "Protected PDF loading error:",
          err
        );

        if (mounted) {
          let message =
            "Unable to load PDF file.";

          if (err?.response?.status === 401) {
            message =
              "Your session has expired. Please login again.";
          } else if (
            err?.response?.data?.message
          ) {
            message =
              err.response.data.message;
          }

          setPdfError(message);
        }
      } finally {
        if (mounted) {
          setPdfLoading(false);
        }
      }
    };

    loadProtectedPdf();

    return () => {
      mounted = false;

      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [document?.stored_name]);

  // =====================================================
  // ACTIVE STUDY TIMER
  // =====================================================

  useEffect(() => {
    if (
      loading ||
      error ||
      !document ||
      !documentId
    ) {
      return undefined;
    }

    studyStartedAtRef.current = Date.now();
    studyRecordedMinutesRef.current = 0;

    studyTimerRef.current =
      window.setInterval(() => {
        recordCompletedStudyMinutes();
      }, 60000);

    return () => {
      if (studyTimerRef.current) {
        window.clearInterval(
          studyTimerRef.current
        );

        studyTimerRef.current = null;
      }

      recordCompletedStudyMinutes();

      studyStartedAtRef.current = null;
      studyRecordedMinutesRef.current = 0;
    };
  }, [
    loading,
    error,
    document?.id,
    document?.stored_name,
    documentId,
  ]);

  // =====================================================
  // CHANGE PDF PAGE
  // =====================================================

  const changePage = (page) => {
    if (!document) {
      return;
    }

    const totalPages =
      Number(document.page_count) || 1;

    const requestedPage = Number(page);

    if (Number.isNaN(requestedPage)) {
      return;
    }

    const nextPage = Math.min(
      Math.max(1, requestedPage),
      totalPages
    );

    setSearchParams({
      page: String(nextPage),
    });
  };

  // =====================================================
  // LOADING SCREEN
  // =====================================================

  if (loading) {
    return (
      <main className="viewer-page">
        <div className="viewer-loading">
          <div className="viewer-loading-spinner"></div>

          <p>
            Loading document...
          </p>
        </div>
      </main>
    );
  }

  // =====================================================
  // ERROR SCREEN
  // =====================================================

  if (error || !document) {
    return (
      <main className="viewer-page">
        <div className="viewer-error">
          <div className="viewer-error-icon">
            📄
          </div>

          <h2>
            Document unavailable
          </h2>

          <p>
            {error ||
              "The requested document could not be loaded."}
          </p>

          <Link
            to="/dashboard"
            className="primary-button"
          >
            <FaArrowLeft />
            Back to Dashboard
          </Link>
        </div>
      </main>
    );
  }

  // =====================================================
  // DOCUMENT INFORMATION
  // =====================================================

  const totalPages =
    Number(document.page_count) || 1;

  const documentName =
    document.original_name ||
    document.name ||
    document.filename ||
    "Document";

  // =====================================================
  // PDF URL
  // =====================================================
  //
  // IMPORTANT:
  // This is a browser Blob URL.
  //
  // It does NOT make another request to:
  // /api/files/...
  //
  // Therefore the iframe does NOT receive a 401.
  //
  // =====================================================

  const pdfUrl = pdfBlobUrl
    ? `${pdfBlobUrl}#page=${currentPage}`
    : "";

  // =====================================================
  // RENDER
  // =====================================================

  return (
    <main className="viewer-page">

      {/* =================================================
          DOCUMENT HEADER
      ================================================= */}

      <header className="viewer-header">

        {/* BACK TO DASHBOARD */}

        <Link
          to="/dashboard"
          className="viewer-back"
        >
          <FaArrowLeft />

          <span>
            Dashboard
          </span>
        </Link>

        {/* DOCUMENT TITLE */}

        <div className="viewer-title">
          <FaFilePdf />

          <div>
            <strong>
              {documentName}
            </strong>

            <span>
              {totalPages} pages
            </span>
          </div>
        </div>

        {/* OPEN PDF */}

        {pdfBlobUrl && (
          <a
            href={pdfUrl}
            target="_blank"
            rel="noreferrer"
            className="viewer-open"
          >
            <FaExternalLinkAlt />

            Open PDF
          </a>
        )}

      </header>

      {/* =================================================
          THREE COLUMN WORKSPACE
      ================================================= */}

      <div className="viewer-workspace">

        {/* =================================================
            LEFT — SOURCES
        ================================================= */}

        <aside className="source-panel">

          {/* SOURCE HEADER */}

          <div className="source-heading">
            <div className="source-heading-icon">
              🧠
            </div>

            <div>
              <strong>
                Sources
              </strong>

              <span>
                AI extracted topics
              </span>
            </div>
          </div>

          {/* DOCUMENT SUMMARY */}

          <div className="source-summary">
            <h3>
              Document
            </h3>

            <p>
              {document.summary ||
                "AI extracted information from this document."}
            </p>
          </div>

          {/* TOPICS */}

          <div className="source-topics">
            <h3>
              Topics
            </h3>

            {Array.isArray(document.topics) &&
            document.topics.length > 0 ? (
              document.topics.map(
                (topic, index) => {
                  const topicPage =
                    Number(topic.page) || 1;

                  const active =
                    topicPage ===
                    currentPage;

                  return (
                    <button
                      key={`${topic.name || "topic"}-${index}`}
                      type="button"
                      className={
                        active
                          ? "source-item active"
                          : "source-item"
                      }
                      onClick={() =>
                        changePage(topicPage)
                      }
                    >
                      <div className="source-icon">
                        🧠
                      </div>

                      <div className="source-info">
                        <strong>
                          {topic.name ||
                            "Untitled topic"}
                        </strong>

                        <span>
                          Page {topicPage}
                        </span>
                      </div>

                      <FaExternalLinkAlt />
                    </button>
                  );
                }
              )
            ) : (
              <div className="source-empty">
                <span>
                  No extracted topics yet.
                </span>
              </div>
            )}
          </div>

        </aside>

        {/* =================================================
            CENTER — PDF VIEWER
        ================================================= */}

        <section className="pdf-area">

          {/* PDF PAGE NAVIGATION */}

          <div className="pdf-toolbar">

            {/* PREVIOUS */}

            <button
              type="button"
              onClick={() =>
                changePage(
                  currentPage - 1
                )
              }
              disabled={
                currentPage <= 1
              }
              aria-label="Previous page"
              title="Previous page"
            >
              <FaChevronLeft />
            </button>

            {/* PAGE NUMBER */}

            <span>
              Page{" "}
              <strong>
                {currentPage}
              </strong>
              {" "}of{" "}
              <strong>
                {totalPages}
              </strong>
            </span>

            {/* NEXT */}

            <button
              type="button"
              onClick={() =>
                changePage(
                  currentPage + 1
                )
              }
              disabled={
                currentPage >=
                totalPages
              }
              aria-label="Next page"
              title="Next page"
            >
              <FaChevronRight />
            </button>

          </div>

          {/* PDF */}

          <div className="pdf-container">

            {pdfLoading && (
              <div className="viewer-loading">
                <div className="viewer-loading-spinner"></div>

                <p>
                  Loading PDF...
                </p>
              </div>
            )}

            {!pdfLoading &&
              pdfError && (
                <div className="viewer-error">
                  <div className="viewer-error-icon">
                    📄
                  </div>

                  <h2>
                    PDF unavailable
                  </h2>

                  <p>
                    {pdfError}
                  </p>

                  <p>
                    Please check that the document
                    is still available.
                  </p>
                </div>
              )}

            {!pdfLoading &&
              !pdfError &&
              pdfBlobUrl && (
                <iframe
                  key={pdfUrl}
                  src={pdfUrl}
                  title={documentName}
                  className="pdf-frame"
                />
              )}

          </div>

        </section>

        {/* =================================================
            RIGHT — AI CHAT
        ================================================= */}

        <section className="document-chat-main">

          <DocumentChat
            documentId={documentId}
            documentName={documentName}
            onPageChange={changePage}
          />

        </section>

      </div>

    </main>
  );
}

export default DocumentViewer;
