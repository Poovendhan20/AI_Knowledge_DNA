import axios from "axios";

export const AUTH_TOKEN_KEY = "ai_knowledge_dna_token";

export const storeAuthToken = (token) => {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
};

export const clearAuthToken = () => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
};

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL ||"http://127.0.0.1:5000/api",
  timeout: 120000,
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
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
        "Content-Type": "multipart/form-data",
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

export const getDocument = async (documentId) => {
  const response = await API.get(
    `/documents/${documentId}`
  );

  return response.data;
};

// =====================================================
// DELETE DOCUMENT
// =====================================================

export const deleteDocument = async (documentId) => {
  const response = await API.delete(
    `/documents/${documentId}`
  );

  return response.data;
};

// =====================================================
// GET PDF FILE URL
// =====================================================

export const getFileUrl = (storedName) => {
  const baseUrl =
    import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api";
    
  return `${baseUrl}/files/${encodeURIComponent(
    storedName
  )}`;
};

// =====================================================
// GET PROTECTED PDF FILE AS BLOB
// =====================================================
// IMPORTANT:
// The PDF endpoint requires JWT authentication.
// Axios automatically adds the Authorization header
// through the interceptor above.

export const getFileBlob = async (storedName) => {
  const response = await API.get(
    `/files/${encodeURIComponent(storedName)}`,
    {
      responseType: "blob",
    }
  );

  return response.data;
};

// =====================================================
// AI CHAT WITH DOCUMENT
// =====================================================

export const chatWithDocument = async (
  documentId,
  question,
  history = [],
  options = {}
) => {
  const body = {
    question,
    history,
  };

  if (options.voiceResponse) {
    body.voice_response = true;
  }

  const response = await API.post(
    `/documents/${documentId}/chat`,
    body
  );

  return response.data;
};

// =====================================================
// DEFAULT API
// =====================================================

export default API;