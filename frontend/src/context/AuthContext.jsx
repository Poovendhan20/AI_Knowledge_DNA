import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  getCurrentUser,
  loginUser,
  registerUser,
} from "../services/authApi";
import {
  AUTH_TOKEN_KEY,
  clearAuthToken,
  storeAuthToken,
} from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const restoreSession = async () => {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);

      if (!token) {
        if (isMounted) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const result = await getCurrentUser();

        if (isMounted && result?.success) {
          setUser(result.user);
        }
      } catch {
        clearAuthToken();
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    restoreSession();

    return () => {
      isMounted = false;
    };
  }, []);

  const completeAuthentication = useCallback((result) => {
    storeAuthToken(result.token);
    setUser(result.user);
  }, []);

  const login = useCallback(async (credentials) => {
    const result = await loginUser(credentials);
    completeAuthentication(result);
    return result.user;
  }, [completeAuthentication]);

  const register = useCallback(async (details) => {
    const result = await registerUser(details);
    completeAuthentication(result);
    return result.user;
  }, [completeAuthentication]);

  const logout = useCallback(() => {
    clearAuthToken();
    setUser(null);
  }, []);

  const value = useMemo(() => ({
    user,
    isLoading,
    isAuthenticated: Boolean(user),
    login,
    register,
    logout,
  }), [user, isLoading, login, register, logout]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }

  return context;
}
