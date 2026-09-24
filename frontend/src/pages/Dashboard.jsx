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
} from "../services/subjectApi";

import SubjectManager from "../components/SubjectManager";
import QuizGenerator from "../components/QuizGenerator";
import "./Dashboard.css";


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
  // INITIAL LOAD
  // =========================================================

  useEffect(() => {

    loadDashboardStats();

  }, []);


  // =========================================================
  // REFRESH WHEN PAGE BECOMES VISIBLE
  // =========================================================

  useEffect(() => {

    const handleVisibilityChange = () => {

      if (
        document.visibilityState ===
        "visible"
      ) {

        loadDashboardStats();

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
          MAIN DASHBOARD GRID
      ===================================================== */}

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

          <div className="weak-concepts-header">

            <h2>
              Weak Concepts
            </h2>

            <p>
              Topics that need more attention
            </p>

          </div>


          {/* These will become AI-generated
              after the mastery engine is added. */}

          <div className="weak-concept">

            <div className="weak-concept-top">

              <div>

                <strong>
                  Knowledge analysis
                </strong>

                <span>
                  Complete quizzes to identify
                  weak concepts
                </span>

              </div>

              <b>
                --
              </b>

            </div>

            <div className="weak-progress">

              <div
                style={{
                  width: "0%",
                }}
              />

            </div>

          </div>


          <div className="weak-concept">

            <div className="weak-concept-top">

              <div>

                <strong>
                  Topic mastery
                </strong>

                <span>
                  AI will calculate mastery
                  from quiz performance
                </span>

              </div>

              <b>
                --
              </b>

            </div>

            <div className="weak-progress">

              <div
                style={{
                  width: "0%",
                }}
              />

            </div>

          </div>


          <div className="weak-concept">

            <div className="weak-concept-top">

              <div>

                <strong>
                  Learning gaps
                </strong>

                <span>
                  Complete more assessments
                  to discover gaps
                </span>

              </div>

              <b>
                --
              </b>

            </div>

            <div className="weak-progress">

              <div
                style={{
                  width: "0%",
                }}
              />

            </div>

          </div>

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


    </main>

  );

}


export default Dashboard;