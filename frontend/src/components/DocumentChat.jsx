import React, { useEffect, useRef, useState } from "react";
import {
  FaArrowLeft,
  FaPaperPlane,
  FaRobot,
  FaUser,
  FaSpinner,
} from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000/api",
  timeout: 120000,
});

function DocumentChat({ documentId, documentName, onPageChange }) {
  const navigate = useNavigate();

  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "assistant",
      content: documentName
        ? `I've analyzed this study material. Ask me anything about ${documentName}, and I'll answer using the uploaded document with page references.`
        : "I've analyzed this study material. Ask me anything about the uploaded document.",
      sources: [],
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  /*
   * Always keep the newest message visible.
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [messages, loading]);

  /*
   * Automatically resize textarea.
   */
  const resizeTextarea = () => {
    const textarea = textareaRef.current;

    if (!textarea) return;

    textarea.style.height = "auto";

    const newHeight = Math.min(
      Math.max(textarea.scrollHeight, 42),
      120
    );

    textarea.style.height = `${newHeight}px`;
  };

  /*
   * Ask AI.
   */
  const sendMessage = async (event) => {
    event?.preventDefault();

    const question = input.trim();

    if (!question || loading) {
      return;
    }

    setError("");

    const userMessage = {
      id: Date.now(),
      role: "user",
      content: question,
      sources: [],
    };

    setMessages((previous) => [
      ...previous,
      userMessage,
    ]);

    setInput("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "42px";
    }

    setLoading(true);

    try {
      /*
       * Backend endpoint.
       *
       * Expected backend:
       * POST /api/chat
       *
       * Body:
       * {
       *   document_id: documentId,
       *   question: question
       * }
       */

      const response = await API.post("/chat", {
        document_id: documentId,
        question: question,
      });

      const data = response.data;

      const answer =
        data.answer ||
        data.response ||
        data.message ||
        "I couldn't generate an answer.";

      const sources =
        data.sources ||
        data.references ||
        [];

      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: answer,
        sources: Array.isArray(sources)
          ? sources
          : [],
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);

    } catch (err) {
      console.error("Chat error:", err);

      let errorMessage =
        "I couldn't connect to the AI service.";

      if (err.response?.data?.error) {
        errorMessage = err.response.data.error;
      }

      setError(errorMessage);

      setMessages((previous) => [
        ...previous,
        {
          id: Date.now() + 1,
          role: "assistant",
          content:
            "Sorry, I couldn't process that question. Please check that the Flask backend and AI service are running.",
          sources: [],
          error: true,
        },
      ]);
    } finally {
      setLoading(false);

      setTimeout(() => {
        textareaRef.current?.focus();
      }, 50);
    }
  };

  /*
   * Enter = send
   * Shift + Enter = new line
   */
  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      sendMessage(event);
    }
  };

  /*
   * Click page source.
   */
  const handleSourceClick = (source) => {
    const page =
      source.page ||
      source.page_number ||
      source.pageNumber;

    if (!page) return;

    if (onPageChange) {
      onPageChange(Number(page));
    }
  };

  return (
    <section className="document-chat-panel">

      {/* ==================================================
          CHAT HEADER
      ================================================== */}

      <div className="document-chat-title">

        <div className="document-chat-title-left">

          <div className="ai-avatar">
            <FaRobot />
          </div>

          <div>
            <h2>Knowledge DNA AI</h2>

            <span>
              Ask anything about this document
            </span>
          </div>

        </div>

        <div className="ai-status">
          <span></span>
          AI Ready
        </div>

      </div>


      {/* ==================================================
          MESSAGES
      ================================================== */}

      <div className="document-chat-messages">

        {messages.map((message) => (

          <div
            key={message.id}
            className={`chat-message-row ${
              message.role === "user"
                ? "chat-message-user"
                : "chat-message-ai"
            }`}
          >

            {message.role === "assistant" && (
              <div className="message-avatar ai-message-avatar">
                <FaRobot />
              </div>
            )}

            <div
              className={`chat-message-bubble ${
                message.role === "user"
                  ? "user-message-bubble"
                  : "ai-message-bubble"
              }`}
            >

              <div
                className={
                  message.role === "user"
                    ? "user-response-content"
                    : "ai-response-content"
                }
              >
                {message.content}
              </div>


              {/* ==========================================
                  SOURCES
              ========================================== */}

              {message.role === "assistant" &&
                message.sources &&
                message.sources.length > 0 && (

                  <div className="document-chat-sources">

                    <span className="sources-label">
                      Sources
                    </span>

                    <div className="source-list">

                      {message.sources.map(
                        (source, index) => {

                          const page =
                            source.page ||
                            source.page_number ||
                            source.pageNumber;

                          const label =
                            source.title ||
                            source.name ||
                            `Page ${page || "?"}`;

                          return (
                            <button
                              key={index}
                              type="button"
                              className="source-chip"
                              onClick={() =>
                                handleSourceClick(
                                  source
                                )
                              }
                            >
                              📄 {label}

                              {page && (
                                <span>
                                  Page {page}
                                </span>
                              )}
                            </button>
                          );
                        }
                      )}

                    </div>

                  </div>
                )}

            </div>


            {message.role === "user" && (
              <div className="message-avatar user-message-avatar">
                <FaUser />
              </div>
            )}

          </div>

        ))}


        {/* ================================================
            THINKING
        ================================================= */}

        {loading && (

          <div className="chat-message-row chat-message-ai">

            <div className="message-avatar ai-message-avatar">
              <FaRobot />
            </div>

            <div className="chat-message-bubble ai-message-bubble ai-thinking-bubble">

              <div className="thinking-content">

                <span>Thinking</span>

                <div className="thinking-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>

              </div>

            </div>

          </div>

        )}

        <div ref={messagesEndRef} />

      </div>


      {/* ==================================================
          ERROR
      ================================================== */}

      {error && (
        <div className="chat-inline-error">
          {error}
        </div>
      )}


      {/* ==================================================
          INPUT AREA
          THIS MUST STAY AT THE BOTTOM
      ================================================== */}

      <div className="document-chat-input-area">

        <form
          className="document-chat-form"
          onSubmit={sendMessage}
        >

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(event) => {
              setInput(event.target.value);
              resizeTextarea();
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask something about this document..."
            disabled={loading}
            rows={1}
          />

          <button
            type="submit"
            className="document-chat-send"
            disabled={
              loading ||
              !input.trim()
            }
            title="Send message"
          >

            {loading ? (
              <FaSpinner className="send-spinner" />
            ) : (
              <FaPaperPlane />
            )}

          </button>

        </form>

        <p className="chat-input-hint">
          Press Enter to send • Shift + Enter for a new line
        </p>

      </div>

    </section>
  );
}

export default DocumentChat;