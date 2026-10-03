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


  // =========================================================

  // ==========================================================
  // LEARNING PROGRESS
  // ==========================================================

  const loadLearningProgress = async () => {
    try {
      const response = await API.get(
        "/learning/progress"
      );

      if (response?.data?.success) {
        const progressRows = Array.isArray(response.data.progress)
          ? response.data.progress
          : [];
        const subjects = Array.isArray(response.data.subjects)
          ? response.data.subjects
          : [];

        setLearningProgress(progressRows);
        setSubjectProgress(subjects);

        // Automatically select the first available subject so the
        // learned/weak topics are visible immediately after refresh.
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
      }
    } catch (error) {
      console.error(
        "Learning progress error:",
        error
      );
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

      <section style={{ marginBottom: "24px", padding: "22px", borderRadius: "18px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
        <div style={{ marginBottom: "16px" }}>
          <h2 style={{ margin: 0 }}>Learned Topics</h2>
          <p style={{ margin: "6px 0 0", opacity: 0.7 }}>Select a subject to see the topics you have studied in that subject.</p>
        </div>
        {subjectProgress.length === 0 ? (
          <p style={{ opacity: 0.7 }}>Add subjects and study materials to build your learned topics.</p>
        ) : (
          <>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginBottom: "18px" }}>
              {subjectProgress.map((subject) => (
                <button key={subject.id} type="button" onClick={() => setSelectedLearnedSubject(subject.id)} style={SUBJECT_BUTTON_STYLE}>{subject.name}</button>
              ))}
            </div>
            {(() => {
              const activeSubject = subjectProgress.find((subject) => subject.id === selectedLearnedSubject) || subjectProgress[0];
              if (!activeSubject || !activeSubject.learned_topics?.length) return <p style={{ opacity: 0.7 }}>No learned topics yet for this subject.</p>;
              return <div><h3 style={{ margin: "0 0 12px" }}>{activeSubject.name}</h3><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>{activeSubject.learned_topics.map((item) => <button key={item.id || item.topic} type="button" onClick={() => setSelectedTopic({ ...item, subject_id: activeSubject.id, subject_name: activeSubject.name })} style={{ textAlign: "left", padding: "16px", borderRadius: "14px", border: "1px solid rgba(255,255,255,0.09)", background: "rgba(255,255,255,0.035)", color: "inherit", cursor: "pointer" }}><strong style={{ display: "block", marginBottom: "8px" }}>{item.topic || "Unknown Topic"}</strong><span style={{ opacity: 0.7, fontSize: "13px" }}>{Number(item.study_minutes || 0)} minutes studied</span></button>)}</div></div>;
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

                  ".subject-manager"

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
          <div className="weak-concepts-header"><h2>Weak Concepts</h2><p>Select a subject to see the weak topics for that subject.</p></div>
          {subjectProgress.length === 0 ? (
            <div className="weak-concept"><strong>No subjects available</strong><span>Add a subject and complete a quiz to identify weak concepts.</span></div>
          ) : (
            <>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "16px" }}>{subjectProgress.map((subject) => <button key={subject.id} type="button" onClick={() => setSelectedWeakSubject(subject.id)} style={{ ...SUBJECT_BUTTON_STYLE, padding: "8px 13px", fontSize: "12px" }}>{subject.name}</button>)}</div>
              {(() => {
                const activeSubject = subjectProgress.find((subject) => subject.id === selectedWeakSubject) || subjectProgress[0];
                if (!activeSubject || !activeSubject.weak_topics?.length) return <div className="weak-concept"><strong>{activeSubject?.name || "Subject"}</strong><span>No weak concepts yet. Complete a quiz for this subject.</span></div>;
                return activeSubject.weak_topics.map((item) => { const mastery = Math.max(0, Math.min(100, Number(item?.mastery_score || 0))); return <div className="weak-concept" key={item.id || item.topic}><div className="weak-concept-top"><div><strong>{item.topic || "Unknown Topic"}</strong><span>Mastery based on your quiz performance</span></div><b>{Math.round(mastery)}%</b></div><div className="weak-progress"><div style={{ width: `${mastery}%` }} /></div><button type="button" onClick={() => openPracticeQuiz(item.topic, activeSubject.id, activeSubject.name)} style={{ ...BLUE_ACTION_BUTTON_STYLE, marginTop: "12px", padding: "8px 12px", fontSize: "12px" }}>📝 Practice Quiz</button></div>; });
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
        <div onClick={() => setSelectedTopic(null)} style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(0,0,0,0.65)", display: "flex", alignItems: "center", justifyContent: "center", padding: "20px" }}>
          <div onClick={(event) => event.stopPropagation()} style={{ width: "min(520px, 100%)", padding: "24px", borderRadius: "20px", background: "#101a36", border: "1px solid rgba(255,255,255,0.12)" }}>
            <h2 style={{ marginTop: 0 }}>{selectedTopic.topic}</h2><div style={{ opacity: 0.7, marginBottom: "14px" }}>{selectedTopic.subject_name || "Subject"}</div>
            <div style={{ display: "grid", gap: "10px" }}>
              <div>Study time: <strong>{Number(selectedTopic.study_minutes || 0)} minutes</strong></div>
              <div>Mastery: <strong>{Math.round(Number(selectedTopic.mastery_score || 0))}%</strong></div>
              <div>Questions attempted: <strong>{Number(selectedTopic.questions_attempted || 0)}</strong></div>
              <div>Questions correct: <strong>{Number(selectedTopic.questions_correct || 0)}</strong></div>
              <div>Last studied: <strong>{selectedTopic.last_studied ? new Date(selectedTopic.last_studied).toLocaleString() : "Not yet"}</strong></div>
            </div>
            <div style={{ marginTop: "20px", display: "flex", gap: "10px" }}>
              <button type="button" onClick={() => { const topic = selectedTopic.topic; const subjectId = selectedTopic.subject_id; const subjectName = selectedTopic.subject_name; setSelectedTopic(null); openPracticeQuiz(topic, subjectId, subjectName); }} style={BLUE_ACTION_BUTTON_STYLE}>📝 Practice Quiz</button>
              <button type="button" onClick={() => setSelectedTopic(null)} style={{ padding: "10px 14px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "inherit", cursor: "pointer" }}>Close</button>
            </div>
          </div>
        </div>
      )}

      {(practiceQuiz || practiceLoading || practiceError) && (
        <div style={{ position: "fixed", inset: 0, zIndex: 1100, background: "rgba(0,0,0,0.72)", overflowY: "auto", padding: "30px 20px" }}>
          <div style={{ width: "min(760px, 100%)", margin: "0 auto", padding: "24px", borderRadius: "20px", background: "#101a36", border: "1px solid rgba(255,255,255,0.12)" }}>
            {practiceLoading && !practiceQuiz && <p>Generating practice quiz...</p>}
            {practiceError && <div style={{ marginBottom: "16px", color: "#fca5a5" }}>{practiceError}</div>}
            {practiceQuiz && !practiceResult && <>
              <h2 style={{ marginTop: 0 }}>Practice Quiz: {practiceQuiz.target_topic || practiceQuiz.questions?.[0]?.topic || "Weak Concept"}</h2><div style={{ opacity: 0.7, marginBottom: "16px" }}>{practiceQuiz.subject_name || "Subject"}</div>
              {practiceQuiz.questions?.map((question, index) => <div key={question.id} style={{ marginBottom: "18px", padding: "16px", borderRadius: "14px", background: "rgba(255,255,255,0.04)" }}>
                <strong>{index + 1}. {question.question}</strong>
                <div style={{ marginTop: "10px", display: "grid", gap: "7px" }}>
                  {question.options?.map((option, optionIndex) => <label key={optionIndex} style={{ cursor: "pointer" }}><input type="radio" name={`practice-${question.id}`} checked={Number(practiceAnswers[question.id]) === optionIndex} onChange={() => setPracticeAnswers((current) => ({ ...current, [question.id]: optionIndex }))} /> {option}</label>)}
                </div>
              </div>)}
              <button type="button" onClick={submitPracticeQuiz} disabled={practiceLoading} style={{ ...BLUE_ACTION_BUTTON_STYLE, marginRight: "10px" }}>{practiceLoading ? "Submitting..." : "Submit Quiz"}</button>
              <button type="button" onClick={closePracticeQuiz} style={BLUE_ACTION_BUTTON_STYLE}>Close</button>
            </>}
            {practiceQuiz && practiceResult && <>
              <h2 style={{ marginTop: 0 }}>Quiz Completed 🎉</h2>
              <div style={{ display: "grid", gap: "8px", marginBottom: "20px" }}>
                <div>Score: <strong>{practiceResult.score} / {practiceResult.total}</strong></div>
                <div>Correct: <strong>{practiceResult.score}</strong></div>
                <div>Wrong: <strong>{practiceResult.total - practiceResult.score}</strong></div>
                <div>Accuracy: <strong>{practiceResult.accuracy}%</strong></div>
              </div>
              <button type="button" onClick={() => setShowPracticeAnswers((value) => !value)} style={BLUE_ACTION_BUTTON_STYLE}>{showPracticeAnswers ? "Hide Answers" : "View Answers"}</button>
              {showPracticeAnswers && <div style={{ display: "grid", gap: "12px", marginTop: "16px" }}>
                {practiceResult.results?.map((result, index) => {
                  const question = practiceQuiz.questions?.find((item) => item.id === result.question_id);
                  const selected = result.selected_answer;
                  const correct = result.correct_answer;
                  return <div key={result.question_id} style={{ padding: "15px", borderRadius: "13px", background: "rgba(255,255,255,0.04)" }}>
                    <strong>{index + 1}. {question?.question}</strong>
                    <p>Your answer: {selected >= 0 ? question?.options?.[selected] : "Not answered"}</p>
                    {!result.correct && <p>Correct answer: {question?.options?.[correct]}</p>}
                    {result.explanation && <p style={{ opacity: 0.7 }}>{result.explanation}</p>}
                  </div>;
                })}
              </div>}
              <button type="button" onClick={closePracticeQuiz} style={{ marginTop: "18px", padding: "10px 15px", borderRadius: "10px", cursor: "pointer" }}>Close</button>
            </>}
          </div>
        </div>
      )}
    </main>



  );



}





export default Dashboard;
