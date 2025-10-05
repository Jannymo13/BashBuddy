import { useState } from "react";
import "./QuizComponent.css";

function QuizComponent() {
  const [questions, setQuestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generateQuiz = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/quiz");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setQuestions(data.questions);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate quiz");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = (index: number) => {
    alert(`You submitted an answer for question ${index + 1}. `);
  };

  return (
    <div className="quiz-container">
      <button
        onClick={generateQuiz}
        disabled={loading}
        className="generate-quiz-btn"
      >
        {loading ? "Generating Quiz..." : "Generate Practice Questions"}
      </button>

      {error && <div className="quiz-error">{error}</div>}

      {questions.length > 0 && (
        <div className="questions-list">
          <div className="terminal-header">
            <div className="dots">
              <span className="dot red"></span>
              <span className="dot yellow"></span>
              <span className="dot green"></span>
            </div>
            <span className="terminal-title">Practice Questions</span>
          </div>
          {questions.map((question, index) => (
            <div key={index} className="question-card">
              <span className="question-number">{index + 1}</span>
              <p className="question-text">
                {question.split("\n").map((line, i) => (
                  <span key={i}>
                    {line}
                    {i < question.split("\n").length - 1 && <br />}
                  </span>
                ))}
              </p>
              <input
                type="text"
                className="quiz-answer-input"
                placeholder="Your answer..."
              />
              <button
                className="quiz-submit-btn"
                onClick={() => handleSubmitAnswer(index)}
              >
                Submit
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default QuizComponent;
