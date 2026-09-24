import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000/api",
  timeout: 120000,
});


// =====================================================
// UPLOAD STUDY MATERIAL
// =====================================================

export const uploadStudyMaterial = async (file) => {
  const formData = new FormData();

  formData.append("file", file);

  const response = await API.post(
    "/upload",
    formData,
    {
      headers: {
        "Content-Type":
          "multipart/form-data",
      },
    }
  );

  return response.data;
};


// =====================================================
// GET ALL DOCUMENTS
// =====================================================

export const getDocuments = async () => {
  const response = await API.get(
    "/documents"
  );

  return response.data;
};


// =====================================================
// GET SINGLE DOCUMENT
// =====================================================

export const getDocument = async (
  documentId
) => {
  const response = await API.get(
    `/documents/${documentId}`
  );

  return response.data;
};


// =====================================================
// DELETE DOCUMENT
// =====================================================

export const deleteDocument = async (
  documentId
) => {
  const response = await API.delete(
    `/documents/${documentId}`
  );

  return response.data;
};


// =====================================================
// GET PDF FILE URL
// =====================================================

export const getFileUrl = (
  storedName
) => {

  return `http://127.0.0.1:5000/api/files/${encodeURIComponent(
    storedName
  )}`;

};


// =====================================================
// AI CHAT WITH DOCUMENT
// =====================================================

export const chatWithDocument = async (
  documentId,
  question,
  history = []
) => {

  const response = await API.post(
    `/documents/${documentId}/chat`,
    {
      question,
      history,
    }
  );

  return response.data;
};


// =====================================================
// DEFAULT API
// =====================================================

export default API;