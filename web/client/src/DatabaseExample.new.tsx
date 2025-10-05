import { useEffect, useState } from "react";

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
      </div>

      <div className="cards-grid">
        {rows.map((r, idx) => {
          const id = r.req_id ?? String(idx);
          const isFlipped = !!flipped[id];
          return (
            <div
              key={id}
              className={`card ${isFlipped ? "flipped" : ""}`}
            >
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
                    <span className="path">~</span>$ {" "}
                    <span className="cmd">{r.query ?? "(no query)"}</span>
                  </div>
                  <div className="meta-row">
                    <span className="badge">{r.cmd ?? "cmd: git"}</span>
                    <span className="muted">{r.created_at ?? ""}</span>
                  </div>
                </div>

                <div className="card-face card-back">
                  <div className="response-block">
                    <div className="response-header">
                      <span className="prompt">output</span>
                      <span className="muted small">{r.req_id ?? ""}</span>
                    </div>
                    <pre className="response-text">{r.response ?? "(no response)"}</pre>
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