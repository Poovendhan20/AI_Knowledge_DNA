import API from "./api";

export const registerUser = async ({ name, email, password }) => {
  const response = await API.post("/auth/register", {
    name,
    email,
    password,
  });
  return response.data;
};

export const loginUser = async ({ email, password }) => {
  const response = await API.post("/auth/login", {
    email,
    password,
  });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await API.get("/auth/me");
  return response.data;
};