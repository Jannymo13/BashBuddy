import "./App.css";
import DatabaseExample from "./DatabaseExample.new";
import QuizComponent from "./QuizComponent";

function App() {
  return (
    <div className="app-container">
      <h1>✨ BashBuddy</h1>
      <p className="subtitle">Learn from your command history</p>

      <QuizComponent />

      <hr style={{ margin: "3rem 0", border: "1px solid #e0e0e0" }} />

      <DatabaseExample />
    </div>
  );
}

export default App;
