import {
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
  FaBrain,
} from "react-icons/fa";

import {
  submitQuiz,
} from "../services/subjectApi";


function Quiz() {

  const {
    quizId,
  } = useParams();

  const location =
    useLocation();

  const navigate =
    useNavigate();

  const quiz =
    location.state?.quiz;


  const [
    currentQuestion,
    setCurrentQuestion,
  ] = useState(0);

  const [
    answers,
    setAnswers,
  ] = useState({});

  const [
    result,
    setResult,
  ] = useState(null);

  const [
    submitting,
    setSubmitting,
  ] = useState(false);


  if (!quiz) {

    return (

      <main className="quiz-page">

        <div className="quiz-missing">

          <h2>
            Quiz unavailable
          </h2>

          <p>
            Please generate the quiz again.
          </p>

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

      </main>

    );

  }


  const question =
    quiz.questions[
      currentQuestion
    ];


  const selectAnswer =
    (answer) => {

      setAnswers(
        (current) => ({

          ...current,

          [question.id]:
            answer,

        })
      );

    };


  const handleNext =
    () => {

      if (
        currentQuestion <
        quiz.questions.length - 1
      ) {

        setCurrentQuestion(
          currentQuestion + 1
        );

      }

    };


  const handleSubmit =
    async () => {

      try {

        setSubmitting(true);

        const response =
          await submitQuiz(
            quizId,
            answers
          );

        if (
          response.success
        ) {

          setResult(
            response
          );

        }

      } catch (error) {

        console.error(error);

      } finally {

        setSubmitting(false);

      }

    };


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