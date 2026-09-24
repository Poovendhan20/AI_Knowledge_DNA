import {
  useEffect,
  useState,
} from "react";

import {
  FaBrain,
  FaRocket,
  FaFileAlt,
} from "react-icons/fa";

import {
  getSubjects,
  getSubjectDocuments,
  generateQuiz,
} from "../services/subjectApi";

import { useNavigate } from "react-router-dom";


function QuizGenerator() {

  const navigate =
    useNavigate();

  const [
    subjects,
    setSubjects,
  ] = useState([]);

  const [
    documents,
    setDocuments,
  ] = useState([]);

  const [
    subjectId,
    setSubjectId,
  ] = useState("");

  const [
    selectedDocuments,
    setSelectedDocuments,
  ] = useState([]);

  const [
    questionCount,
    setQuestionCount,
  ] = useState(10);

  const [
    difficulty,
    setDifficulty,
  ] = useState("medium");

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");


  useEffect(() => {

    const load =
      async () => {

        try {

          const result =
            await getSubjects();

          if (
            result.success
          ) {

            setSubjects(
              result.subjects
            );

          }

        } catch (err) {

          console.error(err);

        }

      };

    load();

  }, []);


  useEffect(() => {

    if (!subjectId) {

      setDocuments([]);

      setSelectedDocuments([]);

      return;

    }

    const loadDocuments =
      async () => {

        try {

          const result =
            await getSubjectDocuments(
              subjectId
            );

          if (
            result.success
          ) {

            setDocuments(
              result.documents
            );

          }

        } catch (err) {

          console.error(err);

        }

      };

    loadDocuments();

  }, [subjectId]);


  const toggleDocument =
    (documentId) => {

      setSelectedDocuments(
        (current) => {

          if (
            current.includes(
              documentId
            )
          ) {

            return current.filter(
              (id) =>
                id !== documentId
            );

          }

          return [
            ...current,
            documentId,
          ];

        }
      );

    };


  const handleGenerate =
    async () => {

      if (!subjectId) {

        setError(
          "Select a subject."
        );

        return;

      }

      if (
        documents.length === 0
      ) {

        setError(
          "Upload study material "
          + "to this subject first."
        );

        return;

      }

      try {

        setLoading(true);

        setError("");

        const result =
          await generateQuiz({

            subjectId,

            documentIds:
              selectedDocuments,

            questionCount:
              Number(
                questionCount
              ),

            difficulty,

          });


        if (
          result.success &&
          result.quiz
        ) {

          navigate(
            `/quiz/${result.quiz.id}`,
            {
              state: {
                quiz:
                  result.quiz,
              },
            }
          );

        } else {

          setError(
            result.message ||
            "Unable to generate quiz."
          );

        }

      } catch (err) {

        console.error(err);

        setError(
          err.response?.data?.message ||
          "Unable to generate quiz."
        );

      } finally {

        setLoading(false);

      }

    };


  return (

    <section className="quiz-generator">

      <div className="quiz-generator-header">

        <div className="quiz-generator-icon">
          <FaBrain />
        </div>

        <div>

          <span>
            AI POWERED
          </span>

          <h2>
            Generate a Quiz
          </h2>

          <p>
            Test your understanding using
            your own study materials.
          </p>

        </div>

      </div>


      <div className="quiz-form">

        {/* SUBJECT */}

        <div className="quiz-field">

          <label>
            Subject
          </label>

          <select
            value={subjectId}
            onChange={(event) =>
              setSubjectId(
                event.target.value
              )
            }
          >

            <option value="">
              Select Subject
            </option>

            {subjects.map(
              (subject) => (

                <option
                  key={
                    subject.id
                  }
                  value={
                    subject.id
                  }
                >
                  {subject.name}
                </option>

              )
            )}

          </select>

        </div>


        {/* DOCUMENTS */}

        {subjectId &&
          documents.length > 0 && (

            <div className="quiz-field">

              <label>
                Study Materials
              </label>

              <div className="quiz-documents">

                <button
                  type="button"
                  className={
                    selectedDocuments.length ===
                    documents.length
                      ? "quiz-doc active"
                      : "quiz-doc"
                  }
                  onClick={() => {

                    if (
                      selectedDocuments.length ===
                      documents.length
                    ) {

                      setSelectedDocuments(
                        []
                      );

                    } else {

                      setSelectedDocuments(
                        documents.map(
                          (doc) =>
                            doc.id
                        )
                      );

                    }

                  }}
                >

                  <FaFileAlt />

                  <span>
                    All materials
                  </span>

                </button>


                {documents.map(
                  (document) => (

                    <button
                      type="button"
                      key={
                        document.id
                      }
                      className={
                        selectedDocuments.includes(
                          document.id
                        )
                          ? "quiz-doc active"
                          : "quiz-doc"
                      }
                      onClick={() =>
                        toggleDocument(
                          document.id
                        )
                      }
                    >

                      <FaFileAlt />

                      <span>
                        {document.name}
                      </span>

                    </button>

                  )
                )}

              </div>

            </div>

          )}


        <div className="quiz-options">

          {/* QUESTION COUNT */}

          <div className="quiz-field">

            <label>
              Questions
            </label>

            <select
              value={
                questionCount
              }
              onChange={(
                event
              ) =>
                setQuestionCount(
                  event.target.value
                )
              }
            >

              <option value="5">
                5 Questions
              </option>

              <option value="10">
                10 Questions
              </option>

              <option value="15">
                15 Questions
              </option>

              <option value="20">
                20 Questions
              </option>

            </select>

          </div>


          {/* DIFFICULTY */}

          <div className="quiz-field">

            <label>
              Difficulty
            </label>

            <select
              value={
                difficulty
              }
              onChange={(
                event
              ) =>
                setDifficulty(
                  event.target.value
                )
              }
            >

              <option value="easy">
                Easy
              </option>

              <option value="medium">
                Medium
              </option>

              <option value="hard">
                Hard
              </option>

            </select>

          </div>

        </div>


        {error && (

          <div className="quiz-error">
            {error}
          </div>

        )}


        <button
          className="primary-button quiz-generate-button"
          onClick={
            handleGenerate
          }
          disabled={loading}
        >

          <FaRocket />

          {loading
            ? "Generating Quiz..."
            : "Generate Quiz"}

        </button>

      </div>

    </section>

  );

}


export default QuizGenerator;