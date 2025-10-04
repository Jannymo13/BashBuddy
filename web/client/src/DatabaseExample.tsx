import { useState } from "react";

interface DatabaseData {
  tables?: string[];
  data?: string[];
  table?: string;
  count?: number;
  error?: string;
}

function DatabaseExample() {
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>("");
  const [tableData, setTableData] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const fetchTables = async () => {
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/db/tables");

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data: DatabaseData = await res.json();

      if (data.error) {
        setError(data.error);
      } else if (data.tables) {
        setTables(data.tables);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTableData = async (tableName: string) => {
    setLoading(true);
    setError("");
    setTableData([]);

    try {
      const res = await fetch(`/api/db/query/${tableName}`);

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data: DatabaseData = await res.json();

      if (data.error) {
        setError(data.error);
      } else if (data.data) {
        setTableData(data.data);
        setSelectedTable(tableName);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      <h2>📊 Supabase Database Explorer</h2>

      <button
        onClick={fetchTables}
        disabled={loading}
        style={{
          padding: "0.75rem 1.5rem",
          background: "#10b981",
          color: "white",
          border: "none",
          borderRadius: "6px",
          cursor: loading ? "not-allowed" : "pointer",
          fontSize: "1rem",
          marginBottom: "1rem",
        }}
      >
        {loading ? "Loading..." : "Fetch Tables"}
      </button>

      {error && (
        <div
          style={{
            background: "#fee",
            border: "1px solid #fcc",
            borderRadius: "6px",
            padding: "1rem",
            margin: "1rem 0",
            color: "#c33",
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      {tables.length > 0 && (
        <div style={{ marginTop: "1rem" }}>
          <h3>Available Tables:</h3>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {tables.map((table) => (
              <button
                key={table}
                onClick={() => fetchTableData(table)}
                style={{
                  padding: "0.5rem 1rem",
                  background: selectedTable === table ? "#667eea" : "#e5e7eb",
                  color: selectedTable === table ? "white" : "#333",
                  border: "none",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                }}
              >
                {table}
              </button>
            ))}
          </div>
        </div>
      )}

      {tableData.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h3>
            Data from "{selectedTable}" ({tableData.length} rows):
          </h3>
          <div
            style={{
              background: "#f8f9fa",
              border: "1px solid #e0e0e0",
              borderRadius: "8px",
              padding: "1rem",
              maxHeight: "400px",
              overflow: "auto",
            }}
          >
            <pre style={{ margin: 0, fontSize: "0.85rem" }}>
              {JSON.stringify(tableData, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default DatabaseExample;
