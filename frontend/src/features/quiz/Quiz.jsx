import {
  useEffect,
  useState,
} from "react";

import {
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  FaCheck,
  FaArrowRight,
} from "react-icons/fa";

import {
  submitQuiz,
  getQuiz,
} from "../../services/subjectApi";

import { useStudyTracker } from "../../context/StudyTrackerContext";


function Quiz() {

  const {
    quizId,
  } = useParams();

  const location =
    useLocation();

  const navigate =
    useNavigate();

  const [quiz, setQuiz] = useState(() => {
    if (location.state?.quiz) return location.state.quiz;
    try {
      const cached = sessionStorage.getItem(`quiz_${quizId}`);
      return cached ? JSON.parse(cached) : null;
    } catch {
      return null;
    }
  });

  const [loading, setLoading] = useState(!quiz);
  const [error, setError] = useState("");
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState(() => {
    try {
      const cachedAnswers = sessionStorage.getItem(`quiz_answers_${quizId}`);
      return cachedAnswers ? JSON.parse(cachedAnswers) : {};
    } catch {
      return {};
    }
  });
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const { setStudyTopic } = useStudyTracker();

  useEffect(() => {
    if (quiz?.subject_name) {
      setStudyTopic(`Quiz: ${quiz.subject_name}`);
    }
    return () => {
      setStudyTopic("General");
    };
  }, [quiz?.subject_name, setStudyTopic]);

  useEffect(() => {
    if (quiz) {
      try {
        sessionStorage.setItem(`quiz_${quizId}`, JSON.stringify(quiz));
      } catch {
        // Storage full or unavailable
      }
      return;
    }

    let isMounted = true;
    const fetchQuiz = async () => {
      try {
        setLoading(true);
        setError("");
        const data = await getQuiz(quizId);
        if (isMounted && data?.success && data?.quiz) {
          setQuiz(data.quiz);
          try {
            sessionStorage.setItem(`quiz_${quizId}`, JSON.stringify(data.quiz));
          } catch {
            // Storage full or unavailable
          }
          if (data.quiz.attempted && data.quiz.score !== null) {
            setResult({
              score: data.quiz.score,
              total: data.quiz.question_count || data.quiz.questions?.length,
              accuracy: data.quiz.accuracy,
              results: data.quiz.questions,
            });
          }
        } else if (isMounted) {
          setError(data?.message || "Quiz not found.");
        }
      } catch (err) {
        if (isMounted) {
          setError(err?.response?.data?.message || "Unable to load quiz.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    if (quizId) {
      fetchQuiz();
    }

    return () => {
      isMounted = false;
    };
  }, [quizId, quiz]);

  const question = quiz?.questions ? quiz.questions[currentQuestion] : null;

  const selectAnswer = (answer) => {
    if (!question) return;
    setAnswers((current) => {
      const updated = {
        ...current,
        [question.id]: answer,
      };
      try {
        sessionStorage.setItem(`quiz_answers_${quizId}`, JSON.stringify(updated));
      } catch {
        // Storage full or unavailable
      }
      return updated;
    });
  };

  const handleNext = () => {
    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      const response = await submitQuiz(quizId, answers);
      if (response.success) {
        setResult(response);
        try {
          sessionStorage.removeItem(`quiz_answers_${quizId}`);
        } catch {
          // Ignore removal error
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <main className="quiz-page">
        <div className="quiz-missing">
          <h2>Loading Quiz...</h2>
          <p>Retrieving your questions.</p>
        </div>
      </main>
    );
  }

  if (!quiz || error || !quiz.questions || quiz.questions.length === 0) {
    return (
      <main className="quiz-page">
        <div className="quiz-missing">
          <h2>{error || "Quiz unavailable"}</h2>
          <p>Please generate the quiz again.</p>
          <button
            className="primary-button"
            onClick={() => navigate("/dashboard")}
          >
            Back to Dashboard
          </button>
        </div>
      </main>
    );
  }
  if (result) {
    return (
      <main className="quiz-page">
        <div className="quiz-result">
          <div className="quiz-result-icon">
            <FaCheck />
          </div>
          <span>
            QUIZ COMPLETE
          </span>
          <h1>
            {result.score}
            {" / "}
            {result.total}
          </h1>
          <p>
            You scored{" "}
            <strong>
              {result.accuracy}%
            </strong>
          </p>
          <div className="quiz-result-actions">
            <button
              className="primary-button"
              onClick={() =>
                navigate(
                  "/dashboard"
                )
              }
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </main>
    );
  }
  const selectedAnswer =
    answers[
      question.id
    ];
  const isLast =
    currentQuestion ===
    quiz.questions.length - 1;
  return (
    <main className="quiz-page">
      <div className="quiz-container">
        {/* HEADER */}
        <div className="quiz-top">
          <div>
            <span>
              {quiz.subject_name}
            </span>
            <h1>
              AI Quiz
            </h1>
          </div>
          <div className="quiz-progress">
            Question{" "}
            <strong>
              {currentQuestion + 1}
            </strong>
            {" / "}
            {quiz.questions.length}
          </div>
        </div>
        {/* PROGRESS BAR */}
        <div className="quiz-progress-bar">
          <div
            style={{
              width:
                `${
                  (
                    (currentQuestion + 1)
                    /
                    quiz.questions.length
                  ) * 100
                }%`,
            }}
          />
        </div>
        {/* QUESTION */}
        <div className="quiz-question-card">
          <div className="quiz-question-number">
            Question {currentQuestion + 1}
          </div>
          <h2>
            {question.question}
          </h2>
          <div className="quiz-options-list">
            {question.options.map(
              (
                option,
                index
              ) => (
                <button
                  key={index}
                  className={
                    selectedAnswer ===
                    index
                      ? "quiz-answer selected"
                      : "quiz-answer"
                  }
                  onClick={() =>
                    selectAnswer(
                      index
                    )
                  }
                >
                  <span>
                    {String.fromCharCode(
                      65 + index
                    )}
                  </span>
                  <strong>
                    {option}
                  </strong>
                </button>
              )
            )}
          </div>
          <div className="quiz-bottom">
            <span>
              {question.page
                ? `Source: Page ${question.page}`
                : ""}
            </span>
            {!isLast ? (
              <button
                className="primary-button"
                onClick={
                  handleNext
                }
                disabled={
                  selectedAnswer ===
                  undefined
                }
              >
                Next
                <FaArrowRight />
              </button>
            ) : (
              <button
                className="primary-button"
                onClick={
                  handleSubmit
                }
                disabled={
                  selectedAnswer ===
                  undefined ||
                  submitting
                }
              >
                {submitting
                  ? "Submitting..."
                  : "Submit Quiz"}
                <FaCheck />
              </button>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
export default Quiz;