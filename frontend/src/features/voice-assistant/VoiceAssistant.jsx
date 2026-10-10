import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Link } from "react-router-dom";

import {

  FaBrain,

  FaCheck,

  FaFileAlt,

  FaMicrophone,

  FaPaperPlane,

  FaPause,

  FaPlus,

  FaRobot,

  FaSpinner,

  FaStop,

  FaTrashAlt,

  FaUser,

  FaVolumeUp,

} from "react-icons/fa";

import { chatWithDocument } from "../../services/api";
import { getSubjects, getSubjectDocuments } from "../../services/subjectApi";

import { useAuth } from "../../context/AuthContext";

import "./VoiceAssistant.css";



const MAX_STORED_MESSAGES = 30;

const MAX_REQUEST_HISTORY = 10;



const LANGUAGE_OPTIONS = [

  { code: "en-IN", label: "English" },

  { code: "ta-IN", label: "தமிழ்" },

];



const WAVE_BARS = Array.from({ length: 11 }, (_, index) => index);



function createWelcomeMessage(documentName) {

  return {

    id: `welcome-${Date.now()}`,

    role: "assistant",

    content: documentName

      ? `Hi! I am ready to help you study ${documentName}. You can ask a question by voice or type it below.`

      : "Choose a study material, then ask me a question by voice or text.",

    sources: [],

    isWelcome: true,

  };

}



function getDocumentName(document) {

  return document?.original_name || document?.name || document?.filename || "Study material";

}



function readHistory(storageKey, documentName) {

  try {

    const stored = localStorage.getItem(storageKey);

    const parsed = stored ? JSON.parse(stored) : [];



    if (Array.isArray(parsed) && parsed.length > 0) {

      return parsed.filter(

        (message) =>

          message &&

          (message.role === "assistant" || message.role === "user") &&

          typeof message.content === "string"

      );

    }

  } catch {

    // A corrupted local conversation should never prevent the assistant loading.*

  }



  return [createWelcomeMessage(documentName)];

}



function VoiceAssistant() {

  const { user } = useAuth();

  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [isLoadingSubjects, setIsLoadingSubjects] = useState(true);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [documentError, setDocumentError] = useState("");
  const [subjectError, setSubjectError] = useState("");

  const [messages, setMessages] = useState([]);

  const [input, setInput] = useState("");

  const [isSending, setIsSending] = useState(false);

  const [isListening, setIsListening] = useState(false);

  const [isSpeaking, setIsSpeaking] = useState(false);

  const [speechSupported, setSpeechSupported] = useState(true);

  const [speechError, setSpeechError] = useState("");

  const [language, setLanguage] = useState("en-IN");

  const [autoSpeak, setAutoSpeak] = useState(true);

  const [activeHistoryKey, setActiveHistoryKey] = useState(null);



  const recognitionRef = useRef(null);

  const hasSubmittedFinalRef = useRef(false);

  const spokenPrefixRef = useRef("");

  const messagesEndRef = useRef(null);



  const selectedSubject = useMemo(
    () => subjects.find((subject) => String(subject.id) === selectedSubjectId) || null,
    [subjects, selectedSubjectId]
  );

  const selectedDocument = useMemo(

    () => documents.find((document) => String(document.id) === selectedDocumentId) || null,

    [documents, selectedDocumentId]

  );



  const storageKey = user?.id && selectedDocumentId

    ? `ai-knowledge-dna:voice-history:${user.id}:${selectedDocumentId}`

    : null;



  const voiceActivity = isListening ? "listening" : isSpeaking ? "speaking" : "idle";

  const isHistoryReady = Boolean(storageKey) && activeHistoryKey === storageKey;



  const stopSpeaking = useCallback(() => {

    if ("speechSynthesis" in window) {

      window.speechSynthesis.cancel();

    }

    setIsSpeaking(false);

  }, []);



  const speak = useCallback(

    (text) => {

      if (!("speechSynthesis" in window) || !text) {

        return;

      }



      stopSpeaking();



      const utterance = new SpeechSynthesisUtterance(text.replace(/\[Page\s+\d+\]/gi, ""));

      utterance.lang = language;

      utterance.rate = language === "ta-IN" ? 0.9 : 1;



      const matchingVoice = window.speechSynthesis

        .getVoices()

        .find((voice) => voice.lang.toLowerCase().startsWith(language.slice(0, 2).toLowerCase()));



      if (matchingVoice) {

        utterance.voice = matchingVoice;

      }



      utterance.onstart = () => setIsSpeaking(true);

      utterance.onend = () => setIsSpeaking(false);

      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);

    },

    [language, stopSpeaking]

  );



  useEffect(() => {
    let isMounted = true;
    const loadSubjects = async () => {
      try {
        setIsLoadingSubjects(true); setSubjectError("");
        const result = await getSubjects();
        const availableSubjects = Array.isArray(result?.subjects) ? result.subjects : Array.isArray(result) ? result : [];
        if (!isMounted) return;
        setSubjects(availableSubjects);
        setSelectedSubjectId((currentId) => availableSubjects.some((subject) => String(subject.id) === currentId) ? currentId : (availableSubjects[0] ? String(availableSubjects[0].id) : ""));
      } catch (error) {
        if (isMounted) { setSubjectError(error?.response?.data?.message || "Your subjects could not be loaded."); setSubjects([]); setSelectedSubjectId(""); }
      } finally { if (isMounted) setIsLoadingSubjects(false); }
    };
    loadSubjects();
    return () => { isMounted = false; };
  }, []);

  useEffect(() => {
    let isMounted = true;
    const loadSubjectDocuments = async () => {
      if (!selectedSubjectId) { setDocuments([]); setSelectedDocumentId(""); setDocumentError(""); return; }
      try {
        setIsLoadingDocuments(true); setDocumentError(""); setSelectedDocumentId("");
        const result = await getSubjectDocuments(selectedSubjectId);
        const availableDocuments = Array.isArray(result?.documents) ? result.documents : Array.isArray(result) ? result : [];
        if (!isMounted) return;
        setDocuments(availableDocuments);
        setSelectedDocumentId(availableDocuments[0] ? String(availableDocuments[0].id) : "");
      } catch (error) {
        if (isMounted) { setDocuments([]); setSelectedDocumentId(""); setDocumentError(error?.response?.data?.message || "Study materials for this subject could not be loaded."); }
      } finally { if (isMounted) setIsLoadingDocuments(false); }
    };
    loadSubjectDocuments();
    return () => { isMounted = false; };
  }, [selectedSubjectId]);

  useEffect(() => {

    let isActive = true;



    const restoreConversation = () => {

      if (!isActive) {

        return;

      }



      setMessages(

        storageKey

          ? readHistory(storageKey, getDocumentName(selectedDocument))

          : []

      );

      setActiveHistoryKey(storageKey);

      setInput("");

      setSpeechError("");

      stopSpeaking();

    };



    const timer = window.setTimeout(restoreConversation, 0);



    return () => {

      isActive = false;

      window.clearTimeout(timer);

    };

  }, [selectedDocument, storageKey, stopSpeaking]);



  useEffect(() => {

    if (!storageKey || activeHistoryKey !== storageKey || messages.length === 0) {

      return;

    }



    try {

      localStorage.setItem(

        storageKey,

        JSON.stringify(messages.slice(-MAX_STORED_MESSAGES))

      );

    } catch {

      // Private browsing or full storage should not interrupt a study session.*

    }

  }, [activeHistoryKey, messages, storageKey]);



  useEffect(() => {

    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });

  }, [isSending, messages]);



  useEffect(() => {

    return () => {

      recognitionRef.current?.abort?.();

      if ("speechSynthesis" in window) {

        window.speechSynthesis.cancel();

      }

    };

  }, []);



  const stopListening = () => {
    recognitionRef.current?.stop?.();
  };

  const clearConversation = () => {
    if (!storageKey || !isHistoryReady) {
      return;
    }

    stopSpeaking();
    localStorage.removeItem(storageKey);
    setMessages([createWelcomeMessage(getDocumentName(selectedDocument))]);
    setInput("");
    setSpeechError("");
  };

  const sendQuestion = async (eventOrQuestion) => {
    if (eventOrQuestion && typeof eventOrQuestion.preventDefault === "function") {
      eventOrQuestion.preventDefault();
    }

    const question = (
      typeof eventOrQuestion === "string"
        ? eventOrQuestion
        : input
    ).trim();

    if (!question || !selectedDocumentId || !isHistoryReady || isSending) {
      return;
    }

    stopListening();
    setSpeechError("");

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      sources: [],
    };

    const requestHistory = messages
      .filter((message) => !message.isWelcome)
      .slice(-MAX_REQUEST_HISTORY)
      .map(({ role, content }) => ({ role, content }));

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setInput("");
    setIsSending(true);

    try {
      const result = await chatWithDocument(
        selectedDocumentId,
        question,
        requestHistory,
        { voiceResponse: true }
      );

      const answer =
        result?.answer ||
        result?.response ||
        result?.message ||
        "I could not generate an answer from this study material.";

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: answer,
        sources: [],
      };

      setMessages((currentMessages) => [...currentMessages, assistantMessage]);

      if (autoSpeak) {
        speak(answer);
      }
    } catch (error) {
      const message =
        error?.response?.data?.message ||
        "I could not reach the AI assistant. Please check your connection and try again.";

      setSpeechError(message);
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: message,
          sources: [],
          isError: true,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const startListening = () => {
    setSpeechError("");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSpeechSupported(false);
      setSpeechError("Speech recognition is not available in this browser. You can still type your question.");
      return;
    }

    stopSpeaking();
    recognitionRef.current?.abort?.();
    hasSubmittedFinalRef.current = false;

    const recognition = new SpeechRecognition();
    recognition.lang = language;
    recognition.continuous = false;
    recognition.interimResults = true;
    spokenPrefixRef.current = input.trim();

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event?.error, event);
      setIsListening(false);

      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        setSpeechError("Microphone permission was blocked. Allow microphone access and try again.");
      } else if (event.error === "no-speech") {
        setSpeechError("No speech detected. Please speak closer to the microphone or try again.");
      } else if (event.error === "audio-capture") {
        setSpeechError("No microphone was found or microphone is in use by another application.");
      } else if (event.error === "network") {
        setSpeechError("Network error occurred during speech recognition. Please check your connection.");
      } else if (event.error === "aborted") {
        // Recognition was aborted by user or replacement; ignore silently
      } else {
        setSpeechError("I could not hear that clearly. Please try again or type your question.");
      }
    };

    recognition.onresult = (event) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        const text = result?.[0]?.transcript || "";
        if (result.isFinal) {
          finalTranscript += text;
        } else {
          interimTranscript += text;
        }
      }

      const spokenText = (finalTranscript || interimTranscript).trim();
      const fullQuestion = [spokenPrefixRef.current, spokenText]
        .filter(Boolean)
        .join(" ")
        .trim();

      setInput(fullQuestion);

      if (finalTranscript.trim() && !hasSubmittedFinalRef.current) {
        hasSubmittedFinalRef.current = true;
        recognition.stop();
        sendQuestion(fullQuestion);
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  };



  const handleLanguageChange = (event) => {

    setLanguage(event.target.value);

    stopSpeaking();

  };



  const renderMessage = (message) => (

    <article

      className={`voice-message voice-message-${message.role}${message.isError ? " voice-message-error" : ""}`}

      key={message.id}

    >

      <div className="voice-message-avatar" aria-hidden="true">

        {message.role === "assistant" ? <FaRobot /> : <FaUser />}

      </div>

      <div className="voice-message-content">

        <div className="voice-message-meta">

          <strong>{message.role === "assistant" ? "DNA Assistant" : "You"}</strong>

          {message.role === "assistant" && !message.isWelcome && !message.isError && (

            <button

              type="button"

              className="voice-play-message"

              onClick={() => speak(message.content)}

              aria-label="Read this answer aloud"

              title="Read aloud"

            >

              <FaVolumeUp />

            </button>

          )}

        </div>

        <p>{message.content}</p>

      </div>

    </article>

  );



  return (

    <main className="voice-assistant-page">

      <section className="voice-assistant-hero" aria-labelledby="voice-assistant-title">

        <div>

          <p className="voice-eyebrow"><FaBrain /> AI STUDY COMPANION</p>

          <h1 id="voice-assistant-title">Talk through your study material.</h1>

          <p>

            Ask a question naturally and receive a clear answer that can be read back to you.

          </p>

        </div>



        <div className="voice-language-control">

          <label htmlFor="voice-language">Conversation language</label>

          <select id="voice-language" value={language} onChange={handleLanguageChange}>

            {LANGUAGE_OPTIONS.map((option) => (

              <option key={option.code} value={option.code}>{option.label}</option>

            ))}

          </select>

        </div>

      </section>



      <section className="voice-assistant-layout">

        <aside className="voice-assistant-sidebar">

          <div className="voice-sidebar-heading">

            <div className="voice-sidebar-icon"><FaFileAlt /></div>

            <div>

              <h2>Study material</h2>

              <p>Your selected material guides each answer.</p>

            </div>

          </div>



          {isLoadingSubjects ? (
            <div className="voice-sidebar-state"><FaSpinner className="voice-spinner" /> Loading subjects…</div>
          ) : subjectError ? (
            <div className="voice-sidebar-state voice-sidebar-error">{subjectError}</div>
          ) : subjects.length === 0 ? (
            <div className="voice-empty-materials">
              <p>Create a subject and upload study material before starting a voice study session.</p>
              <Link to="/dashboard" className="voice-upload-link"><FaPlus /> Go to Dashboard</Link>
            </div>
          ) : (
            <>
              <label className="voice-document-picker" htmlFor="voice-subject">
                <span>Subject</span>
                <select id="voice-subject" value={selectedSubjectId} onChange={(event) => setSelectedSubjectId(event.target.value)} disabled={isSending || isLoadingDocuments}>
                  {subjects.map((subject) => (
                    <option key={subject.id} value={String(subject.id)}>{subject.name}</option>
                  ))}
                </select>
              </label>

              <label className="voice-document-picker" htmlFor="voice-document">
                <span>Study material</span>
                {isLoadingDocuments ? (
                  <div className="voice-sidebar-state"><FaSpinner className="voice-spinner" /> Loading materials…</div>
                ) : documentError ? (
                  <div className="voice-sidebar-state voice-sidebar-error">{documentError}</div>
                ) : documents.length === 0 ? (
                  <div className="voice-empty-materials">
                    <p>No study material is available for this subject.</p>
                    <Link to="/dashboard" className="voice-upload-link"><FaPlus /> Upload material</Link>
                  </div>
                ) : (
                  <select id="voice-document" value={selectedDocumentId} onChange={(event) => setSelectedDocumentId(event.target.value)} disabled={isSending || !isHistoryReady}>
                    {documents.map((document) => (
                      <option key={document.id} value={String(document.id)}>{getDocumentName(document)}</option>
                    ))}
                  </select>
                )}
              </label>
            </>
          )}

          <div className="voice-sidebar-tips">

            <h3>Tips for a better answer</h3>

            <ul>

              <li>Ask one concept at a time.</li>

              <li>Try “Explain this simply” for a quick revision.</li>

              <li>Switch to Tamil when your browser supports it.</li>

            </ul>

          </div>

        </aside>



        <section className="voice-conversation-panel" aria-label="Voice assistant conversation">

          <header className="voice-conversation-header">

            <div>

              <span className="voice-status-dot" aria-hidden="true" />

              <strong>{selectedDocument ? getDocumentName(selectedDocument) : selectedSubject ? `${selectedSubject.name} — No material selected` : "No material selected"}</strong>

            </div>

            <div className="voice-header-actions">

              <label className="voice-auto-speak">

                <input

                  type="checkbox"

                  checked={autoSpeak}

                  onChange={(event) => setAutoSpeak(event.target.checked)}

                />

                <span>Read answers aloud</span>

              </label>

              <button

                type="button"

                className="voice-clear-button"

                onClick={clearConversation}

                disabled={!selectedDocumentId || !isHistoryReady || isSending}

              >

                <FaTrashAlt /> Clear

              </button>

            </div>

          </header>



          <div className="voice-orb-section" data-activity={voiceActivity}>

            <div className="voice-orb-shell" aria-hidden="true">

              <div className="voice-orb">

                {isSending ? <FaSpinner className="voice-spinner" /> : isListening ? <FaStop /> : isSpeaking ? <FaVolumeUp /> : <FaMicrophone />}

              </div>

            </div>

            <div className="voice-wave" aria-hidden="true">

              {WAVE_BARS.map((bar) => (

                <span

                  key={bar}

                  style={{

                    "--delay": `${bar * -0.08}s`,

                    "--height": `${10 + (bar % 5) * 4}px`,

                  }}

                />

              ))}

            </div>

            <p className="voice-activity-text" aria-live="polite">

              {isSending

                ? "Preparing a clear answer…"

                : isListening

                  ? "Listening… speak naturally"

                  : isSpeaking

                    ? "Reading the answer aloud…"

                    : selectedDocument

                      ? "Tap the microphone to ask a question"

                      : "Choose a study material to begin"}

            </p>

          </div>



          {speechError && <div className="voice-notice" role="status">{speechError}</div>}

          {!speechSupported && <div className="voice-notice">Speech input is unavailable, but text chat remains available.</div>}



          <div className="voice-messages">

            {messages.map(renderMessage)}

            {isSending && (

              <article className="voice-message voice-message-assistant voice-thinking">

                <div className="voice-message-avatar" aria-hidden="true"><FaRobot /></div>

                <div className="voice-message-content"><span>Thinking</span><i /><i /><i /></div>

              </article>

            )}

            <div ref={messagesEndRef} />

          </div>



          <div className="voice-controls">

            <button

              type="button"

              className={`voice-mic-button${isListening ? " voice-mic-button-active" : ""}`}

              onClick={isListening ? stopListening : startListening}

              disabled={!selectedDocumentId || !isHistoryReady || isSending}

              aria-pressed={isListening}

              aria-label={isListening ? "Stop listening" : "Start listening"}

            >

              {isListening ? <FaStop /> : <FaMicrophone />}

              <span>{isListening ? "Stop" : "Speak"}</span>

            </button>



            <form className="voice-text-form" onSubmit={sendQuestion}>

              <label className="visually-hidden" htmlFor="voice-question">Ask a question</label>

              <input

                id="voice-question"

                type="text"

                value={input}

                onChange={(event) => setInput(event.target.value)}

                placeholder={selectedDocument ? "Or type a question about this material…" : "Choose a study material first"}

                disabled={!selectedDocumentId || !isHistoryReady || isSending}

                autoComplete="off"

              />

              <button

                type="submit"

                disabled={!input.trim() || !selectedDocumentId || !isHistoryReady || isSending}

                aria-label="Send question"

                title="Send question"

              >

                {isSending ? <FaSpinner className="voice-spinner" /> : <FaPaperPlane />}

              </button>

            </form>



            {isSpeaking && (

              <button type="button" className="voice-stop-speaking" onClick={stopSpeaking}>

                <FaPause /> Stop audio

              </button>

            )}

          </div>

          <p className="voice-privacy-note"><FaCheck /> Your microphone audio is handled by your browser; only the recognized text is sent to the existing secured AI service.</p>

        </section>

      </section>

    </main>

  );

}



export default VoiceAssistant;
