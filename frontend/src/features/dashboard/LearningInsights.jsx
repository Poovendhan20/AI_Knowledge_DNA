import { useMemo, useState } from "react";
import {
  FaBookOpen,
  FaBrain,
  FaCalendarAlt,
  FaRoute,
} from "react-icons/fa";
import "./LearningInsights.css";

const EMPTY_NODES = [];
const EMPTY_EDGES = [];

const shortenLabel = (label, maxLength = 22) => {
  const value = String(label || "");
  return value.length > maxLength
    ? `${value.slice(0, maxLength - 1)}…`
    : value;
};

const formatLastStudied = (value) => {
  if (!value) return "Not studied yet";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Recently studied"
    : `Last studied ${date.toLocaleDateString()}`;
};

const buildGraphLayout = (nodes, edges) => {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const subjects = nodes.filter((node) => node.type === "subject");
  const topics = nodes.filter((node) => node.type === "topic");
  const documents = nodes.filter((node) => node.type === "document");
  const topicGroups = new Map();

  topics.forEach((topic) => {
    const key = topic.subject_id ?? "independent";
    topicGroups.set(key, [...(topicGroups.get(key) || []), topic]);
  });

  const positions = new Map();
  const subjectCount = Math.max(subjects.length, 1);
  subjects.forEach((subject, index) => {
    const y = subjectCount === 1
      ? 270
      : 70 + (index * 400) / (subjectCount - 1);
    positions.set(subject.id, { x: 130, y });

    const group = topicGroups.get(subject.subject_id ?? "independent") || [];
    const visibleTopics = group.slice(0, 10);
    visibleTopics.forEach((topic, topicIndex) => {
      const spacing = Math.min(48, 300 / Math.max(visibleTopics.length, 1));
      const topicY = Math.max(
        42,
        Math.min(498, y + (topicIndex - (visibleTopics.length - 1) / 2) * spacing)
      );
      positions.set(topic.id, { x: 500, y: topicY });
    });
  });

  const documentSources = new Map();
  edges.forEach((edge) => {
    const target = nodeById.get(edge.target);
    if (target?.type === "document") {
      documentSources.set(edge.target, [
        ...(documentSources.get(edge.target) || []),
        edge.source,
      ]);
    }
  });

  const documentsByApproximateY = new Map();
  documents.forEach((document, index) => {
    const sourcePositions = (documentSources.get(document.id) || [])
      .map((sourceId) => positions.get(sourceId))
      .filter(Boolean);
    const averageY = sourcePositions.length
      ? sourcePositions.reduce((total, position) => total + position.y, 0) / sourcePositions.length
      : 70 + (index * 400) / Math.max(documents.length - 1, 1);
    const bucket = Math.round(averageY / 34);
    const offset = (documentsByApproximateY.get(bucket) || 0) * 30;
    documentsByApproximateY.set(bucket, (documentsByApproximateY.get(bucket) || 0) + 1);
    positions.set(document.id, {
      x: 880,
      y: Math.max(38, Math.min(502, averageY + offset)),
    });
  });

  return { positions, nodeById };
};

function LearningInsights({ graph, studyPlan, loading, error, onPracticeTopic }) {
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [activeSubjectId, setActiveSubjectId] = useState("all");
  const nodes = Array.isArray(graph?.nodes) ? graph.nodes : EMPTY_NODES;
  const edges = Array.isArray(graph?.edges) ? graph.edges : EMPTY_EDGES;
  const planItems = Array.isArray(studyPlan?.items) ? studyPlan.items : [];
  const subjectNodes = useMemo(
    () => nodes.filter((node) => node.type === "subject"),
    [nodes]
  );
  const currentSubjectId = activeSubjectId !== "all" && !subjectNodes.some(
    (subject) => subject.id === activeSubjectId
  ) ? "all" : activeSubjectId;
  const visibleGraph = useMemo(() => {
    if (currentSubjectId === "all") {
      return { nodes, edges };
    }

    const visibleNodeIds = new Set([currentSubjectId]);
    const nodesToVisit = [currentSubjectId];

    while (nodesToVisit.length) {
      const sourceId = nodesToVisit.shift();
      edges.forEach((edge) => {
        if (edge.source !== sourceId || visibleNodeIds.has(edge.target)) {
          return;
        }
        visibleNodeIds.add(edge.target);
        nodesToVisit.push(edge.target);
      });
    }

    return {
      nodes: nodes.filter((node) => visibleNodeIds.has(node.id)),
      edges: edges.filter(
        (edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
      ),
    };
  }, [currentSubjectId, edges, nodes]);
  const { positions, nodeById } = useMemo(
    () => buildGraphLayout(visibleGraph.nodes, visibleGraph.edges),
    [visibleGraph]
  );
  const activeSubject = subjectNodes.find((subject) => subject.id === currentSubjectId);
  const selectedNode = selectedNodeId ? nodeById.get(selectedNodeId) : null;

  const openPractice = (item) => {
    if (item?.subject_id && item?.topic && onPracticeTopic) {
      onPracticeTopic(item.topic, item.subject_id, item.subject_name);
    }
  };

  const selectSubject = (subjectId) => {
    setActiveSubjectId(subjectId);
    setSelectedNodeId(null);
  };

  const selectGraphNode = (node) => {
    if (node.type === "subject") {
      selectSubject(node.id);
      return;
    }
    setSelectedNodeId(node.id);
  };

  return (
    <section className="learning-insights" aria-label="Knowledge graph and personalized study plan">
      <article className="insights-card knowledge-graph-card">
        <div className="insights-heading">
          <div className="insights-heading-icon"><FaBrain /></div>
          <div>
            <p className="insights-eyebrow">YOUR LEARNING MAP</p>
            <h2>Knowledge Graph</h2>
            <p>Subjects, topics, and source materials connected from your own study data.</p>
          </div>
        </div>

        {loading ? (
          <div className="insights-empty">Building your knowledge graph…</div>
        ) : nodes.length === 0 ? (
          <div className="insights-empty">
            Upload material or start studying a topic to create your personal knowledge graph.
          </div>
        ) : (
          <>
            <div className="graph-subject-selector" aria-label="Filter knowledge graph by subject">
              <button
                type="button"
                className={currentSubjectId === "all" ? "is-active" : ""}
                onClick={() => selectSubject("all")}
              >
                All subjects
              </button>
              {subjectNodes.map((subject) => (
                <button
                  type="button"
                  className={currentSubjectId === subject.id ? "is-active" : ""}
                  key={subject.id}
                  onClick={() => selectSubject(subject.id)}
                >
                  {subject.label}
                </button>
              ))}
            </div>
            <p className="graph-filter-summary">
              {activeSubject
                ? `Showing ${activeSubject.label} and its connected topics and study materials.`
                : "Showing all of your subjects and their learning connections."}
            </p>
            <div className="graph-legend" aria-label="Knowledge graph legend">
              <span><i className="graph-legend-subject" />Subject</span>
              <span><i className="graph-legend-topic" />Topic</span>
              <span><i className="graph-legend-document" />Source material</span>
            </div>
            <div className="graph-canvas">
              <svg viewBox="0 0 1080 540" role="img" aria-label="Knowledge graph of your subjects, topics, and study materials">
                <title>Knowledge graph of your current learning data</title>
                <g className="graph-links">
                  {visibleGraph.edges.map((edge) => {
                    const source = positions.get(edge.source);
                    const target = positions.get(edge.target);
                    if (!source || !target) return null;
                    return (
                      <path
                        key={`${edge.source}-${edge.target}`}
                        d={`M ${source.x + 28} ${source.y} C ${(source.x + target.x) / 2} ${source.y}, ${(source.x + target.x) / 2} ${target.y}, ${target.x - 28} ${target.y}`}
                      />
                    );
                  })}
                </g>
                {visibleGraph.nodes.map((node) => {
                  const position = positions.get(node.id);
                  if (!position) return null;
                  const selected = selectedNode?.id === node.id;
                  const className = `graph-node graph-node-${node.type}${selected ? " is-selected" : ""}`;
                  return (
                    <g
                      className={className}
                      key={node.id}
                      onClick={() => selectGraphNode(node)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          selectGraphNode(node);
                        }
                      }}
                      role="button"
                      tabIndex="0"
                    >
                      <title>{node.label}</title>
                      {node.type === "document" ? (
                        <rect x={position.x - 32} y={position.y - 17} width="64" height="34" rx="8" />
                      ) : (
                        <circle r={node.type === "subject" ? 25 : 18} cx={position.x} cy={position.y} />
                      )}
                      <text x={position.x} y={position.y + (node.type === "document" ? 4 : 43)}>
                        {shortenLabel(node.label)}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
            {selectedNode && (
              <div className="graph-selection">
                <div>
                  <strong>{selectedNode.label}</strong>
                  {selectedNode.type === "topic" && (
                    <span>
                      {Math.round(Number(selectedNode.mastery_score || 0))}% mastery · {Number(selectedNode.study_minutes || 0)} minutes studied
                    </span>
                  )}
                  {selectedNode.type === "document" && <span>Source material in your learning graph</span>}
                  {selectedNode.type === "subject" && <span>Subject in your learning library</span>}
                </div>
                {selectedNode.type === "topic" && selectedNode.subject_id ? (
                  <button type="button" onClick={() => openPractice({
                    topic: selectedNode.label,
                    subject_id: selectedNode.subject_id,
                    subject_name: selectedNode.subject_name,
                  })}>
                    Practice this topic
                  </button>
                ) : null}
              </div>
            )}
          </>
        )}
      </article>

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

export default LearningInsights;
