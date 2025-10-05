import { useState, useEffect } from "react";
import "./QuizComponent.css";

interface QuizQuestion {
  question: string;
  answer: string;
  feedback?: string;
}

function QuizComponent() {
  const [quizStarted, setQuizStarted] = useState(false);
  const [currentQuestionNum, setCurrentQuestionNum] = useState(0);
  const [allQuestions, setAllQuestions] = useState<string[]>([]); // All 3 questions
  const [displayedQuestions, setDisplayedQuestions] = useState<QuizQuestion[]>(
    []
  ); // Questions shown to user
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  // Fetch categories on component mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch("/api/db/categories");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setCategories(data.categories || []);
      } catch (e) {
        console.error("Failed to fetch categories:", e);
      }
    };
    fetchCategories();
  }, []);

  const startQuiz = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/quiz/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          category: selectedCategory,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }

      setSessionId(data.session_id);
      setAllQuestions(data.questions); // Store all 3 questions
      setDisplayedQuestions([{ question: data.questions[0], answer: "" }]); // Show only first question
      setCurrentQuestionNum(1);
      setQuizStarted(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start quiz");
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (index: number, value: string) => {
    const newQuestions = [...displayedQuestions];
    newQuestions[index].answer = value;
    setDisplayedQuestions(newQuestions);
  };

  const handleNext = (index: number) => {
    if (!displayedQuestions[index].answer.trim()) {
      setError("Please provide an answer before proceeding.");
      return;
    }

    setError("");

    // Add the next question to the top of displayed questions
    const nextQuestionIndex = currentQuestionNum; // 0-indexed: 0, 1, 2 -> we want questions[1] then questions[2]
    if (nextQuestionIndex < allQuestions.length) {
      const newDisplayedQuestions = [
        { question: allQuestions[nextQuestionIndex], answer: "" },
        ...displayedQuestions,
      ];
      setDisplayedQuestions(newDisplayedQuestions);
      setCurrentQuestionNum(currentQuestionNum + 1);
    }
  };

  const handleSubmit = async () => {
    if (!displayedQuestions[0].answer.trim()) {
      setError("Please provide an answer before submitting.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      // Prepare question-answer pairs
      const qaData = displayedQuestions
        .map((q) => ({
          question: q.question,
          answer: q.answer,
        }))
        .reverse(); // Reverse to get original order (Q1, Q2, Q3)

      const response = await fetch("/api/quiz/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          qa_pairs: qaData,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }

      // Update each question with its individual feedback (in reverse order)
      const newQuestions = [...displayedQuestions];
      const reversedEvaluations = [...data.evaluations].reverse();
      reversedEvaluations.forEach((evaluation: string, index: number) => {
        if (newQuestions[index]) {
          newQuestions[index].feedback = evaluation;
        }
      });
      setDisplayedQuestions(newQuestions);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit quiz");
    } finally {
      setLoading(false);
    }
  };

  const resetQuiz = () => {
    setQuizStarted(false);
    setCurrentQuestionNum(0);
    setAllQuestions([]);
    setDisplayedQuestions([]);
    setSessionId("");
    setError("");
  };

  return (
    <div className="quiz-container">
      <div className="quiz-header">
        {!quizStarted ? (
          <>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="category-filter"
              disabled={loading}
            >
              <option value="all">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
            <button
              onClick={startQuiz}
              disabled={loading}
              className="generate-quiz-btn"
            >
              {loading ? "Starting Quiz..." : "Generate Practice Questions"}
            </button>
          </>
        ) : (
          <button
            onClick={resetQuiz}
            disabled={loading}
            className="generate-quiz-btn"
          >
            Start New Quiz
          </button>
        )}
      </div>

      {error && <div className="quiz-error">{error}</div>}

      {displayedQuestions.length > 0 && (
        <div className="questions-list">
          <div className="terminal-header">
            <div className="dots">
              <span className="dot red"></span>
              <span className="dot yellow"></span>
              <span className="dot green"></span>
            </div>
            <span className="terminal-title">Practice Questions</span>
          </div>
          {displayedQuestions.map((q, index) => {
            const questionNum = displayedQuestions.length - index;
            return (
              <div
                key={`q-${questionNum}`}
                className="question-card question-card-animate"
              >
                <div className="question-header">
                  <span className="question-number">{questionNum}</span>
                  <p className="question-text">
                    {q.question.split("\n").map((line, i) => (
                      <span key={i}>
                        {line}
                        {i < q.question.split("\n").length - 1 && <br />}
                      </span>
                    ))}
                  </p>
                </div>
                <input
                  type="text"
                  className="quiz-answer-input"
                  placeholder="Your answer..."
                  value={q.answer}
                  onChange={(e) => handleAnswerChange(index, e.target.value)}
                  disabled={q.feedback !== undefined}
                />

                {q.feedback && (
                  <div
                    className={`feedback-text ${
                      q.feedback.toLowerCase().includes("correct!") ||
                      q.feedback.toLowerCase().startsWith("correct")
                        ? "correct"
                        : "incorrect"
                    }`}
                  >
                    {q.feedback}
                  </div>
                )}

                {index === 0 && currentQuestionNum < 3 && (
                  <button
                    className="quiz-submit-btn"
                    onClick={() => handleNext(index)}
                    disabled={!q.answer.trim()}
                  >
                    Next
                  </button>
                )}

                {index === 0 && currentQuestionNum === 3 && (
                  <button
                    className="quiz-submit-btn"
                    onClick={handleSubmit}
                    disabled={
                      loading ||
                      displayedQuestions.some(
                        (q) => !q.answer.trim() || q.feedback
                      )
                    }
                  >
                    {loading ? "Evaluating..." : "Submit"}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default QuizComponent;
