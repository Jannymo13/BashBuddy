import { useEffect, useState } from "react";
import "./database.css";

type RequestRow = {
  cmd?: string;
  created_at?: string;
  query?: string;
  req_id?: string;
  response?: string;
  user?: string;
};

export default function DatabaseExample() {
  const [rows, setRows] = useState<RequestRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [flipped, setFlipped] = useState<Record<string, boolean>>({});
  const [filterCmd, setFilterCmd] = useState<string>("");
  const [sortOrder, setSortOrder] = useState<"newest" | "oldest">("newest");

  // Format date to EST without timezone
  const formatDateEST = (dateString?: string) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      timeZone: "America/New_York",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  };

  useEffect(() => {
    const fetchRows = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch("/api/db/query/requests");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        const data = Array.isArray(json.data) ? json.data : [];
        setRows(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchRows();
  }, []);

  const toggleFlip = (id?: string) => {
    if (!id) return;
    setFlipped((s) => ({ ...s, [id]: !s[id] }));
  };

  // Get unique commands for filter dropdown
  const uniqueCmds = Array.from(
    new Set(rows.map((r) => r.cmd).filter(Boolean))
  ).sort();

  // Filter and sort rows
  const filteredAndSortedRows = rows
    .filter((r) => {
      if (!filterCmd) return true;
      return r.cmd === filterCmd;
    })
    .sort((a, b) => {
      const dateA = new Date(a.created_at || 0).getTime();
      const dateB = new Date(b.created_at || 0).getTime();
      return sortOrder === "newest" ? dateB - dateA : dateA - dateB;
    });

  if (loading) return <div className="db-loading">Loading requests…</div>;
  if (error) return <div className="db-error">Error: {error}</div>;
  if (!rows.length) return <div className="db-empty">No requests found.</div>;

  return (
    <div className="db-container">
      <div className="terminal-header">
        <div className="dots">
          <span className="dot red" />
          <span className="dot yellow" />
          <span className="dot green" />
        </div>
        <div className="terminal-title">Requests — flashcards</div>
        <div className="filter-controls">
          <select
            value={filterCmd}
            onChange={(e) => setFilterCmd(e.target.value)}
            className="filter-select"
          >
            <option value="">All Commands</option>
            {uniqueCmds.map((cmd) => (
              <option key={cmd} value={cmd}>
                {cmd}
              </option>
            ))}
          </select>
          <select
            value={sortOrder}
            onChange={(e) =>
              setSortOrder(e.target.value as "newest" | "oldest")
            }
            className="filter-select"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
          </select>
        </div>
      </div>

      <div className="cards-grid">
        {filteredAndSortedRows.map((r, idx) => {
          const id = r.req_id ?? String(idx);
          const isFlipped = !!flipped[id];
          return (
            <div key={id} className={`card ${isFlipped ? "flipped" : ""}`}>
              <div
                className="card-inner"
                role="button"
                tabIndex={0}
                onClick={() => toggleFlip(id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") toggleFlip(id);
                }}
                aria-pressed={isFlipped}
                title="Click to flip"
              >
                <div className="card-face card-front">
                  <div className="cmd-line">
                    <span className="prompt user">user@bashbuddy</span>:
                    <span className="path">~</span>${" "}
                    <span className="cmd">{r.query ?? "(no query)"}</span>
                  </div>
                  <div className="meta-row">
                    <span className="badge">{r.cmd ?? "Terminal"}</span>
                    <span className="muted">{formatDateEST(r.created_at)}</span>
                  </div>
                </div>

                <div className="card-face card-back">
                  <div className="response-block">
                    <div className="response-header">
                      <span className="prompt">output</span>
                      <span className="muted small">{r.req_id ?? ""}</span>
                    </div>
                    <pre className="response-text">
                      {r.response ?? "(no response)"}
                    </pre>
                    <div className="meta-row back">
                      <span className="badge dark">{r.user ?? ""}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
