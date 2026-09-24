import { Link } from "react-router-dom";
import {
  FaArrowRight,
  FaBrain,
  FaBookOpen,
  FaChartLine,
  FaMicrophone,
  FaProjectDiagram,
  FaFilePdf,
} from "react-icons/fa";

function Home() {
  return (
    <main className="home-page">

      {/* =====================================================
          HERO SECTION
      ===================================================== */}

      <section className="hero-section">

        <div className="hero-badge">
          🧬 AI-Powered Personalized Learning
        </div>

        <h1 className="hero-title">
          Discover Your
          <br />
          <span>Knowledge DNA</span>
        </h1>

        <p className="hero-description">
          AI Knowledge DNA understands how you learn,
          identifies your strengths and weaknesses,
          and creates a personalized learning journey
          just for you.
        </p>

        <div className="hero-buttons">

          {/* GET STARTED */}

          <Link
            to="/register"
            className="hero-primary-button"
          >
            Get Started
            <FaArrowRight />
          </Link>

          {/* EXPLORE FEATURES */}

          <a
            href="#features"
            className="hero-secondary-button"
          >
            Explore Features
          </a>

        </div>

      </section>


      {/* =====================================================
          FEATURES SECTION
      ===================================================== */}

      <section
        id="features"
        className="features-section"
      >

        <div className="section-heading">

          <span>
            SMARTER LEARNING
          </span>

          <h2>
            Everything you need to
            <br />
            learn smarter
          </h2>

          <p>
            Your learning experience becomes
            personalized with AI-powered insights.
          </p>

        </div>


        <div className="features-grid">

          <div className="feature-card">

            <div className="feature-icon">
              <FaBrain />
            </div>

            <h3>
              Knowledge DNA
            </h3>

            <p>
              Build a personalized profile of
              your strengths, weaknesses and
              learning progress.
            </p>

          </div>


          <div className="feature-card">

            <div className="feature-icon">
              <FaFilePdf />
            </div>

            <h3>
              Smart Document Analysis
            </h3>

            <p>
              Upload PDFs, PowerPoint files,
              lecture notes and study materials.
            </p>

          </div>


          <div className="feature-card">

            <div className="feature-icon">
              <FaChartLine />
            </div>

            <h3>
              Learning Analytics
            </h3>

            <p>
              Track your learning progress,
              quiz accuracy and weak concepts.
            </p>

          </div>


          <div className="feature-card">

            <div className="feature-icon">
              <FaMicrophone />
            </div>

            <h3>
              AI Voice Assistant
            </h3>

            <p>
              Ask questions naturally using
              your voice and get instant answers.
            </p>

          </div>


          <div className="feature-card">

            <div className="feature-icon">
              <FaProjectDiagram />
            </div>

            <h3>
              Knowledge Graph
            </h3>

            <p>
              Understand relationships between
              concepts using intelligent knowledge maps.
            </p>

          </div>


          <div className="feature-card">

            <div className="feature-icon">
              <FaBookOpen />
            </div>

            <h3>
              Personalized Study Plan
            </h3>

            <p>
              Get a study journey based on your
              current knowledge and learning goals.
            </p>

          </div>

        </div>


        {/* =================================================
            DASHBOARD CTA
        ================================================= */}

        <div className="home-dashboard-cta">

          <div>

            <span>
              READY TO START?
            </span>

            <h2>
              Build your Knowledge DNA
            </h2>

            <p>
              Start learning with an AI assistant
              that understands you.
            </p>

          </div>

          <Link
            to="/register"
            className="cta-button"
          >
            Get Started
            <FaArrowRight />
          </Link>

        </div>

      </section>

    </main>
  );
}

export default Home;