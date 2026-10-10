import { useState } from "react";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import Navbar from "./components/layout/Navbar";
import Home from "./features/home/Home";
import Dashboard from "./features/dashboard/Dashboard";
import DocumentViewer from "./features/documents/DocumentViewer";
import Quiz from "./features/quiz/Quiz";
import VoiceAssistant from "./features/voice-assistant/VoiceAssistant";

import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";


/* =========================================================
   LOGIN
========================================================= */

function Login() {
  const { login } = useAuth();

  const location = useLocation();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setIsLoading(true);

    try {
      await login({
        email,
        password,
      });

      navigate(
        location.state?.from || "/dashboard",
        {
          replace: true,
        }
      );
    } catch (err) {
      setError(
        err.response?.data?.message ||
        "Login failed. Please check your credentials."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">

        <h1>Welcome Back</h1>

        <p>
          Sign in to continue your learning journey.
        </p>

        <form onSubmit={handleSubmit}>

          <input
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) =>
              setEmail(e.target.value)
            }
            autoComplete="email"
            required
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            autoComplete="current-password"
            required
          />

          {error && (
            <p className="auth-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="primary-button"
            disabled={isLoading}
          >
            {isLoading
              ? "Logging in..."
              : "Login"}
          </button>

        </form>

        <p className="auth-switch">
          Don't have an account?{" "}
          <Link to="/register">
            Create Account
          </Link>
        </p>

      </div>
    </div>
  );
}


/* =========================================================
   REGISTER
========================================================= */

function Register() {
  const { register } = useAuth();

  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setIsLoading(true);

    try {
      await register({
        name,
        email,
        password,
      });

      navigate("/dashboard", {
        replace: true,
      });
    } catch (err) {
      setError(
        err.response?.data?.message ||
        "Registration failed. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">

        <h1>Create Account</h1>

        <p>
          Start building your Knowledge DNA.
        </p>

        <form onSubmit={handleSubmit}>

          <input
            type="text"
            placeholder="Full name"
            value={name}
            onChange={(e) =>
              setName(e.target.value)
            }
            autoComplete="name"
            required
          />

          <input
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) =>
              setEmail(e.target.value)
            }
            autoComplete="email"
            required
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            autoComplete="new-password"
            minLength={6}
            required
          />

          {error && (
            <p className="auth-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="primary-button"
            disabled={isLoading}
          >
            {isLoading
              ? "Creating Account..."
              : "Create Account"}
          </button>

        </form>

        <p className="auth-switch">
          Already have an account?{" "}
          <Link to="/login">
            Login
          </Link>
        </p>

      </div>
    </div>
  );
}


/* =========================================================
   AUTH PROTECTION
========================================================= */

function RequireAuth({ children }) {
  const {
    isAuthenticated,
    isLoading,
  } = useAuth();

  const location = useLocation();

  if (isLoading) {
    return (
      <main className="auth-page">
        <div className="auth-card">
          <p>
            Checking your session…
          </p>
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
        }}
      />
    );
  }

  return children;
}


/* =========================================================
   PUBLIC-ONLY ROUTES
   Prevent logged-in users from opening
   Login/Register again.
========================================================= */

function PublicOnly({ children }) {
  const {
    isAuthenticated,
    isLoading,
  } = useAuth();

  if (isLoading) {
    return (
      <main className="auth-page">
        <div className="auth-card">
          <p>
            Checking your session…
          </p>
        </div>
      </main>
    );
  }

  if (isAuthenticated) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  return children;
}


/* =========================================================
   APP ROUTES
========================================================= */

function AppRoutes() {
  return (
    <>
      <Navbar />

      <Routes>

        {/* PUBLIC */}

        <Route
          path="/"
          element={<Home />}
        />

        <Route
          path="/login"
          element={
            <PublicOnly>
              <Login />
            </PublicOnly>
          }
        />

        <Route
          path="/register"
          element={
            <PublicOnly>
              <Register />
            </PublicOnly>
          }
        />


        {/* PROTECTED */}

        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />

        <Route
          path="/voice-assistant"
          element={
            <RequireAuth>
              <VoiceAssistant />
            </RequireAuth>
          }
        />

        <Route
          path="/document/:documentId"
          element={
            <RequireAuth>
              <DocumentViewer />
            </RequireAuth>
          }
        />

        <Route
          path="/quiz/:quizId"
          element={
            <RequireAuth>
              <Quiz />
            </RequireAuth>
          }
        />

        {/* UNKNOWN ROUTES */}

        <Route
          path="*"
          element={
            <Navigate
              to="/"
              replace
            />
          }
        />

      </Routes>
    </>
  );
}


/* =========================================================
   APP
========================================================= */

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
