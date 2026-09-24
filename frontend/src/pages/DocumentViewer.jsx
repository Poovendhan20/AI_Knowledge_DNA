import { useEffect, useState } from "react";

import {
  Link,
  useParams,
  useSearchParams,
} from "react-router-dom";

import {
  FaArrowLeft,
  FaExternalLinkAlt,
  FaFilePdf,
  FaChevronLeft,
  FaChevronRight,
} from "react-icons/fa";

import {
  getDocument,
  getFileUrl,
} from "../services/api";

import DocumentChat from "../components/DocumentChat";


function DocumentViewer() {

  const { documentId } = useParams();

  const [
    searchParams,
    setSearchParams,
  ] = useSearchParams();


  // =====================================================
  // STATE
  // =====================================================

  const [
    document,
    setDocument,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");


  // =====================================================
  // CURRENT PAGE
  // =====================================================

  const currentPage = Math.max(
    1,
    Number(
      searchParams.get("page") || 1
    )
  );


  // =====================================================
  // LOAD DOCUMENT
  // =====================================================

  useEffect(() => {

    let mounted = true;


    const loadDocument = async () => {

      try {

        setLoading(true);
        setError("");


        const result =
          await getDocument(documentId);


        if (!mounted) {
          return;
        }


        if (
          result &&
          result.success &&
          result.document
        ) {

          setDocument(
            result.document
          );

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

      setError(
        "Document ID is missing."
      );

      setLoading(false);

    }


    return () => {
      mounted = false;
    };

  }, [documentId]);


  // =====================================================
  // CHANGE PDF PAGE
  // =====================================================

  const changePage = (page) => {

    if (!document) {
      return;
    }


    const totalPages =
      Number(document.page_count) || 1;


    const requestedPage =
      Number(page);


    if (
      Number.isNaN(requestedPage)
    ) {
      return;
    }


    const nextPage = Math.min(
      Math.max(
        1,
        requestedPage
      ),
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

  if (
    error ||
    !document
  ) {

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

  const fileUrl =
    getFileUrl(
      document.stored_name
    );


  const totalPages =
    Number(
      document.page_count
    ) || 1;


  const documentName =
    document.original_name ||
    document.name ||
    document.filename ||
    "Document";


  // =====================================================
  // PDF URL
  // =====================================================

  const pdfUrl =
    `${fileUrl}#page=${currentPage}`;


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

        <a
          href={fileUrl}
          target="_blank"
          rel="noreferrer"
          className="viewer-open"
        >

          <FaExternalLinkAlt />

          Open PDF

        </a>

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


            {Array.isArray(
              document.topics
            ) &&
            document.topics.length > 0 ? (

              document.topics.map(
                (
                  topic,
                  index
                ) => {

                  const topicPage =
                    Number(
                      topic.page
                    ) || 1;


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
                        changePage(
                          topicPage
                        )
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

            <iframe
              key={pdfUrl}
              src={pdfUrl}
              title={documentName}
              className="pdf-frame"
            />

          </div>

        </section>


        {/* =================================================
            RIGHT — AI CHAT
        ================================================= */}

        <section className="document-chat-main">

          <DocumentChat
            documentId={documentId}
            documentName={documentName}

            /*
             * IMPORTANT:
             *
             * DocumentChat can now tell DocumentViewer
             * which PDF page to display.
             */
            onPageChange={changePage}
          />

        </section>


      </div>

    </main>

  );

}


export default DocumentViewer;