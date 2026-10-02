import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  FaBrain,
  FaSignInAlt,
  FaUserPlus,
  FaChartPie,
  FaMicrophone,
  FaBars,
  FaTimes,
  FaUserCircle,
  FaChevronDown,
  FaSignOutAlt,
} from "react-icons/fa";
import { useAuth } from "../context/AuthContext";

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);

  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const closeMenu = () => {
    setMenuOpen(false);
  };

  const handleLogout = () => {
    logout();
    setAccountOpen(false);
    setMenuOpen(false);
    navigate("/");
  };

  const handleAccountToggle = () => {
    setAccountOpen((prev) => !prev);
  };

  return (
    <nav className="navbar">
      {/* LOGO */}
      <Link to="/" className="logo" onClick={closeMenu}>
        <span className="logo-icon">
          <FaBrain />
        </span>

        <span className="logo-text">
          AI Knowledge DNA
        </span>
      </Link>

      {/* DESKTOP NAVIGATION */}
      <div className="nav-links desktop-nav">
        <Link to="/" className="nav-link">
          Home
        </Link>

        <a href="/#features" className="nav-link">
          Features
        </a>

        <Link to="/dashboard" className="nav-dashboard">
          <FaChartPie />
          <span>Dashboard</span>
        </Link>

        {isAuthenticated && (
          <Link to="/voice-assistant" className="nav-link">
            <FaMicrophone />
            <span>Voice Assistant</span>
          </Link>
        )}

        {!isAuthenticated ? (
          <>
            <Link to="/login" className="nav-login">
              <FaSignInAlt />
              <span>Login</span>
            </Link>

            <Link to="/register" className="nav-register">
              <FaUserPlus />
              <span>Get Started</span>
            </Link>
          </>
        ) : (
          <div className="account-menu">
            <button
              type="button"
              className="account-button"
              onClick={handleAccountToggle}
              aria-expanded={accountOpen}
              aria-haspopup="true"
            >
              <FaUserCircle />

              <span>
                {user?.name || "Account"}
              </span>

              <FaChevronDown
                className={
                  accountOpen
                    ? "account-chevron account-chevron-open"
                    : "account-chevron"
                }
              />
            </button>

            {accountOpen && (
              <div className="account-dropdown">
                <div className="account-info">
                  <div className="account-name">
                    {user?.name || "User"}
                  </div>

                  <div className="account-email">
                    {user?.email || ""}
                  </div>
                </div>

                <div className="account-divider" />

                <Link
                  to="/dashboard"
                  className="account-dropdown-item"
                  onClick={() => setAccountOpen(false)}
                >
                  <FaChartPie />
                  <span>Dashboard</span>
                </Link>

                <button
                  type="button"
                  className="account-dropdown-item account-logout"
                  onClick={handleLogout}
                >
                  <FaSignOutAlt />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* MOBILE HAMBURGER */}
      <button
        type="button"
        className="hamburger-button"
        onClick={() => setMenuOpen((prev) => !prev)}
        aria-label="Toggle navigation menu"
        aria-expanded={menuOpen}
      >
        {menuOpen ? <FaTimes /> : <FaBars />}
      </button>

      {/* MOBILE NAVIGATION */}
      <div
        className={
          menuOpen
            ? "mobile-menu mobile-menu-open"
            : "mobile-menu"
        }
      >
        <Link
          to="/"
          className="mobile-menu-link"
          onClick={closeMenu}
        >
          <span>Home</span>
        </Link>

        <a
          href="/#features"
          className="mobile-menu-link"
          onClick={closeMenu}
        >
          <span>Features</span>
        </a>

        <Link
          to="/dashboard"
          className="mobile-menu-link"
          onClick={closeMenu}
        >
          <FaChartPie />
          <span>Dashboard</span>
        </Link>

        {isAuthenticated && (
          <Link
            to="/voice-assistant"
            className="mobile-menu-link"
            onClick={closeMenu}
          >
            <FaMicrophone />
            <span>Voice Assistant</span>
          </Link>
        )}

        {!isAuthenticated ? (
          <>
            <Link
              to="/login"
              className="mobile-menu-link"
              onClick={closeMenu}
            >
              <FaSignInAlt />
              <span>Login</span>
            </Link>

            <Link
              to="/register"
              className="mobile-menu-register"
              onClick={closeMenu}
            >
              <FaUserPlus />
              <span>Get Started</span>
            </Link>
          </>
        ) : (
          <>
            <div className="mobile-account-info">
              <FaUserCircle />

              <div>
                <strong>
                  {user?.name || "User"}
                </strong>

                <span>
                  {user?.email || ""}
                </span>
              </div>
            </div>

            <button
              type="button"
              className="mobile-logout"
              onClick={handleLogout}
            >
              <FaSignOutAlt />
              <span>Logout</span>
            </button>
          </>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
