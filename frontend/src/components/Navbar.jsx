import { useState } from "react";
import { Link } from "react-router-dom";
import {
  FaBrain,
  FaSignInAlt,
  FaUserPlus,
  FaChartPie,
  FaBars,
  FaTimes,
} from "react-icons/fa";

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => {
    setMenuOpen(false);
  };

  return (
    <nav className="navbar">
      {/* Logo */}
      <Link to="/" className="logo" onClick={closeMenu}>
        <span className="logo-icon">
          <FaBrain />
        </span>

        <span className="logo-text">
          AI Knowledge DNA
        </span>
      </Link>

      {/* Desktop Navigation */}
      <div className="nav-links">
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

        <Link to="/login" className="nav-login">
          <FaSignInAlt />
          <span>Login</span>
        </Link>

        <Link to="/register" className="nav-register">
          <FaUserPlus />
          <span>Get Started</span>
        </Link>
      </div>

      {/* Hamburger Button */}
      <button
        className="hamburger-button"
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Toggle navigation menu"
        aria-expanded={menuOpen}
      >
        {menuOpen ? <FaTimes /> : <FaBars />}
      </button>

      {/* Mobile Menu */}
      <div
        className={`mobile-menu ${
          menuOpen ? "mobile-menu-open" : ""
        }`}
      >
        <Link
          to="/"
          className="mobile-menu-link"
          onClick={closeMenu}
        >
          Home
        </Link>

        <a
          href="/#features"
          className="mobile-menu-link"
          onClick={closeMenu}
        >
          Features
        </a>

        <Link
          to="/dashboard"
          className="mobile-menu-link"
          onClick={closeMenu}
        >
          <FaChartPie />
          Dashboard
        </Link>

        <Link
          to="/login"
          className="mobile-menu-link"
          onClick={closeMenu}
        >
          <FaSignInAlt />
          Login
        </Link>

        <Link
          to="/register"
          className="mobile-menu-register"
          onClick={closeMenu}
        >
          <FaUserPlus />
          Get Started
        </Link>
      </div>
    </nav>
  );
}

export default Navbar;