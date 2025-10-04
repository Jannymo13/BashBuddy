import { useState } from "react";
import "./App.css";
import DatabaseExample from "./DatabaseExample";

interface GeminiResponse {
  generated_text?: string;
  error?: string;
}

function App() {
  const [response, setResponse] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const handleGenerateClick = async () => {
    setLoading(true);
    setError("");
    setResponse("");

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: "Hi my name is parth j. say hi to me.",
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data: GeminiResponse = await res.json();

      if (data.error) {
        setError(data.error);
      } else if (data.generated_text) {
        setResponse(data.generated_text);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1>✨ Gemini AI Generator</h1>
      <p className="subtitle">Click the button to generate a creative story!</p>

      <button
        onClick={handleGenerateClick}
        disabled={loading}
        className="generate-btn"
      >
        {loading ? "Generating..." : "Generate Story"}
      </button>

      {error && (
        <div className="error-box">
          <strong>Error:</strong> {error}
        </div>
      )}

      {response && (
        <div className="response-box">
          <h2>Generated Response:</h2>
          <p>{response}</p>
        </div>
      )}

      <hr style={{ margin: "3rem 0", border: "1px solid #e0e0e0" }} />

      {/* Supabase Database Section */}
      <DatabaseExample />
    </div>
  );
}

export default App;
