import {

  useEffect,

  useState,

} from "react";



import {

  FaBook,

  FaBullseye,

  FaFire,

  FaClock,

  FaBrain,

  FaUpload,

  FaArrowRight,

} from "react-icons/fa";



import {

  getDashboardStats,

} from "../../services/subjectApi";

import API from "../../services/api";



import SubjectManager from "../subjects/SubjectManager";

import QuizGenerator from "../quiz/QuizGenerator";

import PersonalizedStudyPlan from "./PersonalizedStudyPlan";

import "./Dashboard.css";

const SUBJECT_BUTTON_STYLE = {
  padding: "10px 16px",
  borderRadius: "999px",
  border: "1px solid rgba(120,180,255,0.8)",
  background: "rgba(80,140,255,0.18)",
  color: "inherit",
  cursor: "pointer",
  fontWeight: 700,
};

const BLUE_ACTION_BUTTON_STYLE = {
  padding: "9px 14px",
  borderRadius: "10px",
  border: "1px solid rgba(120,180,255,0.8)",
  background: "rgba(80,140,255,0.18)",
  color: "inherit",
  cursor: "pointer",
  fontWeight: 700,
};





function Dashboard() {



  const [stats, setStats] = useState({

    knowledge_dna: 0,

    topics_learned: 0,

    quiz_accuracy: 0,

    learning_streak: 0,

    study_hours: 0,

  });



  const [loadingStats, setLoadingStats] =

    useState(true);



  const [statsError, setStatsError] =

    useState("");

  const [learningProgress, setLearningProgress] =
    useState([]);
  const [subjectProgress, setSubjectProgress] = useState([]);
  const [studyPlan, setStudyPlan] = useState({
    items: [],
    total_minutes: 0,
  });
  const [studyPlanLoading, setStudyPlanLoading] = useState(true);
  const [studyPlanError, setStudyPlanError] = useState("");
  const [selectedLearnedSubject, setSelectedLearnedSubject] = useState(null);
  const [selectedWeakSubject, setSelectedWeakSubject] = useState(null);

  const [selectedTopic, setSelectedTopic] = useState(null);
  const [practiceQuiz, setPracticeQuiz] = useState(null);
  const [practiceAnswers, setPracticeAnswers] = useState({});
  const [practiceResult, setPracticeResult] = useState(null);
  const [practiceLoading, setPracticeLoading] = useState(false);
  const [practiceError, setPracticeError] = useState("");
  const [showPracticeAnswers, setShowPracticeAnswers] = useState(false);





  // =========================================================

  // LOAD DASHBOARD STATISTICS

  // =========================================================



  const loadDashboardStats = async () => {



    try {



      setLoadingStats(true);

      setStatsError("");



      const result =

        await getDashboardStats();



      if (result?.success) {



        setStats({

          knowledge_dna:

            Number(

              result.stats?.knowledge_dna || 0

            ),



          topics_learned:

            Number(

              result.stats?.topics_learned || 0

            ),



          quiz_accuracy:

            Number(

              result.stats?.quiz_accuracy || 0

            ),



          learning_streak:

            Number(

              result.stats?.learning_streak || 0

            ),



          study_hours:

            Number(

              result.stats?.study_hours || 0

            ),

        });



      } else {



        setStatsError(

          result?.message ||

          "Unable to load dashboard statistics."

        );



      }



    } catch (error) {



      console.error(

        "Dashboard statistics error:",

        error

      );



      setStatsError(

        error?.response?.data?.message ||

        "Unable to connect to the backend."

      );



    } finally {



      setLoadingStats(false);



    }



  };

  // ==========================================================
  // LEARNING PROGRESS
  // ==========================================================

  const loadLearningProgress = async () => {
    try {
      const response = await API.get("/learning/progress");

      if (response?.data?.success) {
        const progressRows = Array.isArray(response.data.progress)
          ? response.data.progress
          : [];
        const subjects = Array.isArray(response.data.subjects)
          ? response.data.subjects
          : [];

        setLearningProgress(progressRows);
        setSubjectProgress(subjects);

        setSelectedLearnedSubject((current) =>
          current && subjects.some((subject) => subject.id === current)
            ? current
            : (subjects[0]?.id || null)
        );

        setSelectedWeakSubject((current) =>
          current && subjects.some((subject) => subject.id === current)
            ? current
            : (subjects[0]?.id || null)
        );
      } else {
        setLearningProgress([]);
        setSubjectProgress([]);
      }
    } catch (error) {
      console.error(
        "Learning progress error:",
        error
      );
      setLearningProgress([]);
      setSubjectProgress([]);
    }
  };

  const loadPersonalizedStudyPlan = async () => {
    try {
      setStudyPlanLoading(true);
      setStudyPlanError("");
      const response = await API.get("/learning/insights");

      if (response?.data?.success) {
        setStudyPlan(response.data.study_plan || { items: [], total_minutes: 0 });
      } else {
        setStudyPlanError(response?.data?.message || "Unable to build your personalized study plan.");
      }
    } catch (error) {
      console.error("Personalized study plan error:", error);
      setStudyPlanError(error?.response?.data?.message || "Unable to load your personalized study plan.");
    } finally {
      setStudyPlanLoading(false);
    }
  };

  const recordStudySession = async (
    topic,
    studyMinutes
  ) => {
    if (
      !topic ||
      !Number.isFinite(Number(studyMinutes)) ||
      Number(studyMinutes) <= 0
    ) {
      return;
    }

    try {
      const response = await API.post(
        "/learning/session",
        {
          topic,
          study_minutes: Number(studyMinutes),
        }
      );

      if (response?.data?.success) {
        await loadDashboardStats();
        await loadLearningProgress();
        await loadPersonalizedStudyPlan();
      }
    } catch (error) {
      console.error(
        "Study session error:",
        error
      );
    }
  };

  // INITIAL LOAD

  // =========================================================



  useEffect(() => {
    loadDashboardStats();
    loadLearningProgress();
    loadPersonalizedStudyPlan();

    const handleStudySessionRecorded = (event) => {
      const detail = event?.detail || {};

      recordStudySession(
        detail.topic,
        detail.study_minutes
      );
    };

    window.addEventListener(
      "ai-knowledge-dna:study-session",
      handleStudySessionRecorded
    );

    return () => {
      window.removeEventListener(
        "ai-knowledge-dna:study-session",
        handleStudySessionRecorded
      );
    };
  }, []);



  // REFRESH WHEN PAGE BECOMES VISIBLE

  // =========================================================



  useEffect(() => {



    const handleVisibilityChange = () => {



      if (

        document.visibilityState ===

        "visible"

      ) {



        loadDashboardStats();
        loadLearningProgress();
        loadPersonalizedStudyPlan();



      }



    };



    document.addEventListener(

      "visibilitychange",

      handleVisibilityChange

    );



    return () => {



      document.removeEventListener(

        "visibilitychange",

        handleVisibilityChange

      );



    };



  }, []);





  // =========================================================

  // STAT DISPLAY HELPERS

  // =========================================================



  const displayNumber = (

    value

  ) => {



    if (loadingStats) {

      return "...";

    }



    return value;



  };





  const displayPercentage = (

    value

  ) => {



    if (loadingStats) {

      return "...";

    }



    return `${value}%`;



  };





  // =========================================================

  // ==========================================================
  // WEAK CONCEPTS
  // ==========================================================

  const openPracticeQuiz = async (topic, subjectId, subjectName) => {
    if (!topic || !subjectId) return;
    setPracticeLoading(true);
    setPracticeError("");
    setPracticeQuiz(null);
    setPracticeResult(null);
    setPracticeAnswers({});
    setShowPracticeAnswers(false);
    try {
      const response = await API.post("/quiz/generate", {
        subject_id: subjectId,
        topic,
        question_count: 5,
        difficulty: "medium",
      });
      if (response?.data?.success && response.data.quiz) {
        setPracticeQuiz({
          ...response.data.quiz,
          subject_name: subjectName || response.data.quiz.subject_name,
          target_topic: topic,
        });
      } else {
        setPracticeError(response?.data?.message || "Unable to generate the practice quiz.");
      }
    } catch (error) {
      console.error("Practice quiz error:", error);
      setPracticeError(error?.response?.data?.message || "Unable to generate the practice quiz.");
    } finally {
      setPracticeLoading(false);
    }
  };

  const submitPracticeQuiz = async () => {
    if (!practiceQuiz?.id) return;
    setPracticeLoading(true);
    setPracticeError("");
    try {
      const response = await API.post(`/quiz/${practiceQuiz.id}/submit`, { answers: practiceAnswers });
      if (response?.data?.success) {
        setPracticeResult(response.data);
        setShowPracticeAnswers(false);
        await loadLearningProgress();
        await loadDashboardStats();
        await loadPersonalizedStudyPlan();
      } else {
        setPracticeError(response?.data?.message || "Unable to submit the practice quiz.");
      }
    } catch (error) {
      console.error("Practice quiz submission error:", error);
      setPracticeError(error?.response?.data?.message || "Unable to submit the practice quiz.");
    } finally {
      setPracticeLoading(false);
    }
  };

  const closePracticeQuiz = () => {
    setPracticeQuiz(null);
    setPracticeResult(null);
    setPracticeAnswers({});
    setPracticeError("");
    setShowPracticeAnswers(false);
  };

  // RENDER

  // =========================================================



  return (



    <main className="dashboard-page">





      {/* =====================================================

          DASHBOARD HERO

      ===================================================== */}



      <section className="dashboard-header">



        <div className="dashboard-welcome">



          <p className="dashboard-label">

            YOUR LEARNING SPACE

          </p>



          <h1>

            Welcome back 👋

          </h1>



          <p className="dashboard-subtitle">

            Let's continue building your

            Knowledge DNA.

          </p>



        </div>





        {/* ===================================================

            KNOWLEDGE DNA SCORE

        =================================================== */}



        <div className="dna-score">



          <span>

            🧠

          </span>



          <small>

            Knowledge DNA

          </small>



          <strong>

            {displayPercentage(

              stats.knowledge_dna

            )}

          </strong>



        </div>



      </section>





      {/* =====================================================

          API ERROR

      ===================================================== */}



      {statsError && (



        <div

          style={{

            marginBottom: "18px",

            padding: "12px 15px",

            borderRadius: "10px",

            border:

              "1px solid rgba(239,68,68,0.35)",

            background:

              "rgba(239,68,68,0.08)",

            color: "#fca5a5",

            fontSize: "13px",

          }}

       >



          {statsError}



        </div>



      )}





      {/* =====================================================

          STATISTICS

      ===================================================== */}



      <section className="stats-grid">





        {/* TOPICS */}



        <div className="stat-card">



          <div className="stat-icon">

            <FaBook />

          </div>



          <p>

            Topics Learned

          </p>



          <strong>

            {displayNumber(

              stats.topics_learned

            )}

          </strong>



        </div>





        {/* QUIZ ACCURACY */}



        <div className="stat-card">



          <div className="stat-icon">

            <FaBullseye />

          </div>



          <p>

            Quiz Accuracy

          </p>



          <strong>

            {displayPercentage(

              stats.quiz_accuracy

            )}

          </strong>



        </div>





        {/* LEARNING STREAK */}



        <div className="stat-card">



          <div className="stat-icon">

            <FaFire />

          </div>



          <p>

            Learning Streak

          </p>



          <strong>

            {displayNumber(

              stats.learning_streak

            )}

            {" "}

            {stats.learning_streak === 1

              ? "Day"

              : "Days"}

          </strong>



        </div>





        {/* STUDY HOURS */}



        <div className="stat-card">



          <div className="stat-icon">

            <FaClock />

          </div>



          <p>

            Study Hours

          </p>



          <strong>

            {displayNumber(

              stats.study_hours

            )}

          </strong>



        </div>



      </section>





      {/* =====================================================
          LEARNED TOPICS
      ===================================================== */}

      <section className="learned-topics-card">
        <div className="learned-topics-header">
          <h2>Learned Topics</h2>
          <p>Select a subject to see the topics you have studied in that subject.</p>
        </div>
        {subjectProgress.length === 0 ? (
          <p style={{ color: "var(--text-muted)" }}>Add subjects and study materials to build your learned topics.</p>
        ) : (
          <>
            <div className="subject-filter-chips">
              {subjectProgress.map((subject) => (
                <button
                  key={subject.id}
                  type="button"
                  onClick={() => setSelectedLearnedSubject(subject.id)}
                  className={selectedLearnedSubject === subject.id ? "subject-chip-btn active" : "subject-chip-btn"}
                >
                  {subject.name}
                </button>
              ))}
            </div>
            {(() => {
              const activeSubject = subjectProgress.find((subject) => subject.id === selectedLearnedSubject) || subjectProgress[0];
              if (!activeSubject || !activeSubject.learned_topics?.length) return <p style={{ color: "var(--text-muted)" }}>No learned topics yet for this subject.</p>;
              return (
                <div>
                  <h3 style={{ margin: "0 0 12px", color: "var(--text-primary)", fontSize: "16px" }}>{activeSubject.name}</h3>
                  <div className="learned-topics-grid">
                    {activeSubject.learned_topics.map((item) => (
                      <button
                        key={item.id || item.topic}
                        type="button"
                        onClick={() => setSelectedTopic({ ...item, subject_id: activeSubject.id, subject_name: activeSubject.name })}
                        className="learned-topic-item"
                      >
                        <strong>{item.topic || "Unknown Topic"}</strong>
                        <span>{Number(item.study_minutes || 0)} minutes studied</span>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })()}
          </>
        )}
      </section>

      <PersonalizedStudyPlan
        studyPlan={studyPlan}
        loading={studyPlanLoading}
        error={studyPlanError}
        onPracticeTopic={openPracticeQuiz}
      />

      <section className="dashboard-main-grid">





        {/* ===================================================

            UPLOAD CARD

        =================================================== */}



        <div className="dashboard-upload-card">



          <div className="dashboard-upload-icon">



            <FaUpload />



          </div>





          <h2>

            Upload Study Material

          </h2>





          <p>



            Upload your PDFs, PowerPoint

            presentations, lecture notes or

            handwritten notes. AI will understand

            your material and connect every topic

            to its original source.



          </p>





          <div className="upload-types">



            <span>

              PDF

            </span>



            <span>

              PPTX

            </span>



            <span>

              DOCX

            </span>



            <span>

              Images

            </span>



          </div>





          <button

            className="primary-button"

            onClick={() => {



              const subjectSection =

                document.querySelector(

                  ".sdna-subject-manager"

                );



              if (

                subjectSection

              ) {



                subjectSection.scrollIntoView({

                  behavior: "smooth",

                  block: "start",

                });



              }



            }}

         >



            <FaUpload />



            Upload Material



            <FaArrowRight />



          </button>



        </div>





        {/* ===================================================

            WEAK CONCEPTS

        =================================================== */}



        <div className="weak-concepts-card">
          <div className="weak-concepts-header">
            <h2>Weak Concepts</h2>
            <p>Select a subject to see the weak topics for that subject.</p>
          </div>
          {subjectProgress.length === 0 ? (
            <div className="weak-concept">
              <strong>No subjects available</strong>
              <span>Add a subject and complete a quiz to identify weak concepts.</span>
            </div>
          ) : (
            <>
              <div className="subject-filter-chips">
                {subjectProgress.map((subject) => (
                  <button
                    key={subject.id}
                    type="button"
                    onClick={() => setSelectedWeakSubject(subject.id)}
                    className={selectedWeakSubject === subject.id ? "subject-chip-btn active" : "subject-chip-btn"}
                  >
                    {subject.name}
                  </button>
                ))}
              </div>
              {(() => {
                const activeSubject = subjectProgress.find((subject) => subject.id === selectedWeakSubject) || subjectProgress[0];
                if (!activeSubject || !activeSubject.weak_topics?.length) return (
                  <div className="weak-concept">
                    <strong>{activeSubject?.name || "Subject"}</strong>
                    <span>No weak concepts yet. Complete a quiz for this subject.</span>
                  </div>
                );
                return activeSubject.weak_topics.map((item) => {
                  const mastery = Math.max(0, Math.min(100, Number(item?.mastery_score || 0)));
                  return (
                    <div className="weak-concept" key={item.id || item.topic}>
                      <div className="weak-concept-top">
                        <div>
                          <strong>{item.topic || "Unknown Topic"}</strong>
                          <span>Mastery based on your quiz performance</span>
                        </div>
                        <b>{Math.round(mastery)}%</b>
                      </div>
                      <div className="weak-progress">
                        <div style={{ width: `${mastery}%` }} />
                      </div>
                      <button
                        type="button"
                        onClick={() => openPracticeQuiz(item.topic, activeSubject.id, activeSubject.name)}
                        className="weak-practice-btn"
                      >
                        📝 Practice Quiz
                      </button>
                    </div>
                  );
                });
              })()}
            </>
          )}
        </div>



      </section>





      {/* =====================================================

          SUBJECT MANAGEMENT

      ===================================================== */}



      <SubjectManager />





      {/* =====================================================

          AI QUIZ GENERATOR

      ===================================================== */}



      <QuizGenerator />





      {/* =====================================================

          KNOWLEDGE DNA SECTION

      ===================================================== */}



      <section className="knowledge-dna-preview">



        <div className="knowledge-dna-icon">



          <FaBrain />



        </div>





        <div className="knowledge-dna-content">



          <span>

            YOUR KNOWLEDGE DNA

          </span>



          <h2>

            Your learning profile grows

            as you study.

          </h2>



          <p>



            Upload study materials, study

            different topics and complete

            AI-generated quizzes. Your

            Knowledge DNA will gradually

            represent your understanding,

            strengths and learning gaps.



          </p>



        </div>





        <div className="knowledge-dna-value">



          <strong>

            {displayPercentage(

              stats.knowledge_dna

            )}

          </strong>



          <span>

            Current Score

          </span>



        </div>



      </section>






      {selectedTopic && (
        <div onClick={() => setSelectedTopic(null)} className="dashboard-modal-overlay">
          <div onClick={(event) => event.stopPropagation()} className="dashboard-modal-card">
            <h2 style={{ marginTop: 0, marginBottom: "4px" }}>{selectedTopic.topic}</h2>
            <div style={{ color: "var(--accent)", fontSize: "13px", fontWeight: 600, marginBottom: "16px" }}>
              {selectedTopic.subject_name || "Subject"}
            </div>
            <div style={{ display: "grid", gap: "10px" }}>
              <div className="modal-stat-row"><span>Study time</span><strong>{Number(selectedTopic.study_minutes || 0)} minutes</strong></div>
              <div className="modal-stat-row"><span>Mastery</span><strong>{Math.round(Number(selectedTopic.mastery_score || 0))}%</strong></div>
              <div className="modal-stat-row"><span>Questions attempted</span><strong>{Number(selectedTopic.questions_attempted || 0)}</strong></div>
              <div className="modal-stat-row"><span>Questions correct</span><strong>{Number(selectedTopic.questions_correct || 0)}</strong></div>
              <div className="modal-stat-row"><span>Last studied</span><strong>{selectedTopic.last_studied ? new Date(selectedTopic.last_studied).toLocaleString() : "Not yet"}</strong></div>
            </div>
            <div className="modal-action-row">
              <button
                type="button"
                onClick={() => {
                  const topic = selectedTopic.topic;
                  const subjectId = selectedTopic.subject_id;
                  const subjectName = selectedTopic.subject_name;
                  setSelectedTopic(null);
                  openPracticeQuiz(topic, subjectId, subjectName);
                }}
                className="primary-button"
              >
                📝 Practice Quiz
              </button>
              <button type="button" onClick={() => setSelectedTopic(null)} className="secondary-button">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {(practiceQuiz || practiceLoading || practiceError) && (
        <div className="dashboard-modal-overlay">
          <div className="dashboard-modal-card wide-modal" onClick={(event) => event.stopPropagation()}>
            {practiceLoading && !practiceQuiz && <p style={{ color: "var(--text-muted)" }}>Generating practice quiz...</p>}
            {practiceError && <div className="auth-error">{practiceError}</div>}
            {practiceQuiz && !practiceResult && (
              <>
                <h2 style={{ marginTop: 0, marginBottom: "4px" }}>Practice Quiz: {practiceQuiz.target_topic || practiceQuiz.questions?.[0]?.topic || "Weak Concept"}</h2>
                <div style={{ color: "var(--accent)", fontSize: "13px", fontWeight: 600, marginBottom: "18px" }}>
                  {practiceQuiz.subject_name || "Subject"}
                </div>
                {practiceQuiz.questions?.map((question, index) => (
                  <div key={question.id} style={{ marginBottom: "16px", padding: "16px", borderRadius: "var(--radius-lg)", background: "var(--bg-surface-secondary)", border: "1px solid var(--border-subtle)" }}>
                    <strong style={{ display: "block", marginBottom: "12px", fontSize: "15px" }}>{index + 1}. {question.question}</strong>
                    <div style={{ display: "grid", gap: "8px" }}>
                      {question.options?.map((option, optionIndex) => (
                        <label key={optionIndex} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "8px 12px", borderRadius: "var(--radius-sm)", cursor: "pointer", background: Number(practiceAnswers[question.id]) === optionIndex ? "var(--primary-subtle)" : "transparent", border: Number(practiceAnswers[question.id]) === optionIndex ? "1px solid var(--primary-border)" : "1px solid transparent" }}>
                          <input type="radio" name={`practice-${question.id}`} checked={Number(practiceAnswers[question.id]) === optionIndex} onChange={() => setPracticeAnswers((current) => ({ ...current, [question.id]: optionIndex }))} />
                          <span>{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
                <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
                  <button type="button" onClick={submitPracticeQuiz} disabled={practiceLoading} className="primary-button">
                    {practiceLoading ? "Submitting..." : "Submit Quiz"}
                  </button>
                  <button type="button" onClick={closePracticeQuiz} className="secondary-button">
                    Close
                  </button>
                </div>
              </>
            )}
            {practiceQuiz && practiceResult && (
              <>
                <h2 style={{ marginTop: 0, marginBottom: "12px" }}>Quiz Completed 🎉</h2>
                <div style={{ display: "grid", gap: "8px", margin: "16px 0 20px" }}>
                  <div className="modal-stat-row"><span>Score</span><strong>{practiceResult.score} / {practiceResult.total}</strong></div>
                  <div className="modal-stat-row"><span>Correct</span><strong style={{ color: "var(--success)" }}>{practiceResult.score}</strong></div>
                  <div className="modal-stat-row"><span>Wrong</span><strong style={{ color: "var(--error)" }}>{practiceResult.total - practiceResult.score}</strong></div>
                  <div className="modal-stat-row"><span>Accuracy</span><strong>{practiceResult.accuracy}%</strong></div>
                </div>
                <div style={{ display: "flex", gap: "10px", marginBottom: "16px" }}>
                  <button type="button" onClick={() => setShowPracticeAnswers((value) => !value)} className="primary-button">
                    {showPracticeAnswers ? "Hide Answers" : "View Answers"}
                  </button>
                  <button type="button" onClick={closePracticeQuiz} className="secondary-button">
                    Close
                  </button>
                </div>
                {showPracticeAnswers && (
                  <div style={{ display: "grid", gap: "12px", marginTop: "16px" }}>
                    {practiceResult.results?.map((result, index) => {
                      const question = practiceQuiz.questions?.find((item) => item.id === result.question_id);
                      const selected = result.selected_answer;
                      const correct = result.correct_answer;
                      return (
                        <div key={result.question_id} style={{ padding: "14px 16px", borderRadius: "var(--radius-md)", background: "var(--bg-surface-secondary)", border: "1px solid var(--border-subtle)" }}>
                          <strong style={{ display: "block", marginBottom: "6px" }}>{index + 1}. {question?.question}</strong>
                          <p style={{ margin: "4px 0", color: result.correct ? "var(--success)" : "var(--error)" }}>
                            Your answer: {selected >= 0 ? question?.options?.[selected] : "Not answered"}
                          </p>
                          {!result.correct && (
                            <p style={{ margin: "4px 0", color: "var(--primary)" }}>
                              Correct answer: {question?.options?.[correct]}
                            </p>
                          )}
                          {result.explanation && <p style={{ margin: "4px 0", color: "var(--text-muted)", fontSize: "13px" }}>{result.explanation}</p>}
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </main>



  );



}





export default Dashboard;
