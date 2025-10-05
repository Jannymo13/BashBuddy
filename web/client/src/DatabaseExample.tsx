import React, { useState, useEffect } from "react";
import "./database.css";

interface DatabaseEntry {
  id: number;
  query: string;
  response: string;
  timestamp: string;
}

interface CardProps {
  entry: DatabaseEntry;
}

const Card: React.FC<CardProps> = ({ entry }) => {
  const [isCardFlipped, setIsCardFlipped] = useState(false);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsCardFlipped(!isCardFlipped);
  };

  return (
    <div
      className={`card ${isCardFlipped ? "flipped" : ""}`}
      onClick={handleClick}
    >
      <div className="card-inner">
        <div className="card-face card-front">
          <div className="cmd-line">
            <span className="prompt user">user@bashbuddy</span>
            <span className="path">~</span>
            <span className="cmd">{entry.query}</span>
          </div>
          <div className="meta-row">
            <span className="badge dark">#{entry.id}</span>
            <span className="small muted">
              {new Date(entry.timestamp).toLocaleDateString()}
            </span>
          </div>
        </div>
        <div className="card-face card-back">
          <div className="response-block">
            <div className="response-header">
              <span className="badge">Response</span>
              <span className="muted">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <pre className="response-text">{entry.response}</pre>
          </div>
        </div>
      </div>
    </div>
  );
};

function DatabaseExample() {
  const [data, setData] = useState<DatabaseEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    fetchTableData();
  }, []);

  const fetchTableData = async () => {
    try {
      const response = await fetch(
        "http://localhost:8080/api/db/query/requests"
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      if (result.error) {
        throw new Error(result.error);
      }
      setData(result.data || []);
      setLoading(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
      console.error("Fetch error:", e);
      setLoading(false);
    }
  };

  if (loading)
    return <div className="db-loading">Loading database entries...</div>;
  if (error) return <div className="db-error">Error: {error}</div>;
  if (data.length === 0)
    return <div className="db-empty">No database entries available</div>;

  return (
    <div className="db-container">
      <div className="terminal-header">
        <div className="dots">
          <span className="dot red"></span>
          <span className="dot yellow"></span>
          <span className="dot green"></span>
        </div>
        <span className="terminal-title">BashBuddy Query History</span>
      </div>
      <div className="cards-grid">
        {data.map((entry) => (
          <Card key={entry.id} entry={entry} />
        ))}
      </div>
    </div>
  );
}

export default DatabaseExample;
