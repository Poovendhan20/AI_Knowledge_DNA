import {
  FaBookOpen,
  FaCalendarAlt,
  FaRoute,
} from "react-icons/fa";
import "./PersonalizedStudyPlan.css";

const formatLastStudied = (value) => {
  if (!value) return "Not studied yet";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Recently studied"
    : `Last studied ${date.toLocaleDateString()}`;
};

function PersonalizedStudyPlan({ studyPlan, loading, error, onPracticeTopic }) {
  const planItems = Array.isArray(studyPlan?.items) ? studyPlan.items : [];

  const openPractice = (item) => {
    if (item?.subject_id && item?.topic && onPracticeTopic) {
      onPracticeTopic(item.topic, item.subject_id, item.subject_name);
    }
  };

  return (
    <section className="personalized-study-plan" aria-label="Personalized study plan">
      <article className="insights-card study-plan-card">
        <div className="insights-heading">
          <div className="insights-heading-icon plan-icon"><FaRoute /></div>
          <div>
            <p className="insights-eyebrow">NEXT BEST STEPS</p>
            <h2>Personalized Study Plan</h2>
            <p>Prioritized from your mastery, quiz performance, study time, and recency.</p>
          </div>
        </div>

        {loading ? (
          <div className="insights-empty">Personalizing today’s plan…</div>
        ) : planItems.length === 0 ? (
          <div className="insights-empty">
            Your plan will appear after you add a subject, upload material, or record a study session.
          </div>
        ) : (
          <>
            <div className="study-plan-summary">
              <FaCalendarAlt />
              <span>Today’s focused plan</span>
              <strong>{studyPlan.total_minutes} min</strong>
            </div>
            <ol className="study-plan-list">
              {planItems.map((item, index) => (
                <li className="study-plan-item" key={`${item.subject_id || "independent"}-${item.topic}`}>
                  <span className="plan-order">{index + 1}</span>
                  <div className="plan-item-content">
                    <div className="plan-item-title">
                      <div>
                        <span className="plan-subject">{item.subject_name}</span>
                        <h3>{item.topic}</h3>
                      </div>
                      <span className="plan-duration">{item.recommended_minutes} min</span>
                    </div>
                    <strong className="plan-action">{item.action}</strong>
                    <p>{item.reason}</p>
                    <div className="plan-meta">
                      <span>{Math.round(Number(item.mastery_score || 0))}% mastery</span>
                      <span>{Number(item.questions_attempted || 0)} quiz questions</span>
                      <span>{formatLastStudied(item.last_studied)}</span>
                    </div>
                    {item.subject_id ? (
                      <button type="button" className="plan-practice-button" onClick={() => openPractice(item)}>
                        <FaBookOpen /> Practice quiz
                      </button>
                    ) : null}
                  </div>
                </li>
              ))}
            </ol>
          </>
        )}
        {error && <p className="insights-error">{error}</p>}
      </article>
    </section>
  );
}

export default PersonalizedStudyPlan;
