import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import Navbar from "./components/layout/Navbar";
import Home from "./features/home/Home";
import Dashboard from "./features/dashboard/Dashboard";
import DocumentViewer from "./features/documents/DocumentViewer";
import Quiz from "./features/quiz/Quiz";
import VoiceAssistant from "./features/voice-assistant/VoiceAssistant";
import Login from "./features/authentication/Login";
import Register from "./features/authentication/Register";

import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import { StudyTrackerProvider } from "./context/StudyTrackerContext";


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
          <StudyTrackerProvider>
            <AppRoutes />
          </StudyTrackerProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
