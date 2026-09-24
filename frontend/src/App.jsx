import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import DocumentViewer from "./pages/DocumentViewer";
import Quiz from "./pages/Quiz";
function Login() {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Welcome Back</h1>
        <p>
          Sign in to continue your learning journey.
        </p>
        <input
          type="email"
          placeholder="Email address"
        />
        <input
          type="password"
          placeholder="Password"/>
        <button className="primary-button">
          Login
        </button>
        <p className="auth-switch">
          Don't have an account?{" "}
          <a href="/register">Create Account</a>
        </p>
      </div>
    </div>
  );
}
function Register() {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Create Account</h1>
        <p>
          Start building your Knowledge DNA.
        </p>
        <input
          type="text"
          placeholder="Full name"/>
        <input
          type="email"
          placeholder="Email address"/>
        <input
          type="password"
          placeholder="Password"/>
        <button className="primary-button">
          Create Account
        </button>
        <p className="auth-switch">
          Already have an account?{" "}
          <a href="/login">Login</a>
        </p>
      </div>
    </div>
  );
}
function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route
          path="/"
          element={<Home />}
        />
        <Route
          path="/login"
          element={<Login />}
        />
        <Route
          path="/register"
          element={<Register />}/>
        <Route
          path="/dashboard"
          element={<Dashboard />}/>
        <Route
          path="/document/:documentId"
          element={<DocumentViewer />}/>
        <Route
          path="/quiz/:quizId"
          element={<Quiz />}/>
      </Routes>
    </BrowserRouter>
  );
}
export default App;