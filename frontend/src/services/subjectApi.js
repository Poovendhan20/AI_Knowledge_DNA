import axios from "axios";

const SUBJECT_API = axios.create({
  baseURL: "http://127.0.0.1:5000/api",
  timeout: 120000,
});

export const createSubject = async (
  name,
  description = ""
) => {
  const response = await SUBJECT_API.post(
    "/subjects",
    {
      name,
      description,
    }
  );

  return response.data;
};

export const getSubjects = async () => {
  const response = await SUBJECT_API.get(
    "/subjects"
  );

  return response.data;
};

export const getSubject = async (
  subjectId
) => {
  const response = await SUBJECT_API.get(
    `/subjects/${subjectId}`
  );

  return response.data;
};

export const deleteSubject = async (
  subjectId
) => {
  const response = await SUBJECT_API.delete(
    `/subjects/${subjectId}`
  );

  return response.data;
};

export const uploadMultipleDocuments = async (
  subjectId,
  files
) => {
  const formData = new FormData();

  formData.append(
    "subject_id",
    subjectId
  );

  files.forEach((file) => {
    formData.append(
      "files",
      file
    );
  });

  const response = await SUBJECT_API.post(
    "/upload-multiple",
    formData
  );

  return response.data;
};

export const getSubjectDocuments = async (
  subjectId
) => {
  const response = await SUBJECT_API.get(
    `/subjects/${subjectId}/documents`
  );

  return response.data;
};

export const generateQuiz = async ({
  subjectId,
  documentIds = [],
  questionCount = 10,
  difficulty = "medium",
}) => {
  const response = await SUBJECT_API.post(
    "/quiz/generate",
    {
      subject_id: subjectId,
      document_ids: documentIds,
      question_count: questionCount,
      difficulty,
    }
  );

  return response.data;
};

export const submitQuiz = async (
  quizId,
  answers
) => {
  const response = await SUBJECT_API.post(
    `/quiz/${quizId}/submit`,
    {
      answers,
    }
  );

  return response.data;
};

export const getQuizzes = async () => {
  const response = await SUBJECT_API.get(
    "/quizzes"
  );

  return response.data;
};

export const getDashboardStats = async () => {
  const response = await SUBJECT_API.get(
    "/dashboard/stats"
  );

  return response.data;
};

export default SUBJECT_API;