import API from "./api";

const SUBJECT_API = API;

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
  const selectedFiles = Array.from(files || []);
  const documents = [];
  const errors = [];
  const results = [];

  for (const file of selectedFiles) {
    const formData = new FormData();

    formData.append(
      "subject_id",
      subjectId
    );
    formData.append(
      "files",
      file
    );

    try {
      const response = await SUBJECT_API.post(
        "/upload-multiple",
        formData
      );
      const result = response.data || {};
      const uploadedDocuments =
        result.documents || [];
      const fileErrors = result.errors || [];

      documents.push(...uploadedDocuments);
      errors.push(...fileErrors);

      if (
        !result.success &&
        fileErrors.length === 0
      ) {
        errors.push({
          filename: file.name,
          message:
            result.message ||
            "The file could not be uploaded.",
        });
      }

      results.push({
        filename: file.name,
        success: Boolean(result.success),
        document: uploadedDocuments[0] || null,
        errors: fileErrors,
      });
    } catch (error) {
      const message =
        error?.response?.data?.message ||
        error?.message ||
        "The file could not be uploaded.";

      const fileError = {
        filename: file.name,
        message,
      };

      errors.push(fileError);
      results.push({
        filename: file.name,
        success: false,
        document: null,
        errors: [fileError],
      });
    }
  }

  const uploadedCount = documents.length;
  const failedCount = errors.length;

  return {
    success: uploadedCount > 0,
    message:
      failedCount > 0
        ? `${uploadedCount} document(s) uploaded; ${failedCount} failed.`
        : `${uploadedCount} document(s) uploaded.`,
    documents,
    errors,
    results,
  };
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
