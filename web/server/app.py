from flask import Flask, request, jsonify
from flask_cors import CORS
from gemini import generate_response
from database import list_tables, fetch_all_from_table, execute_query
import uuid
from datetime import datetime 
from prompt import generate_quiz_prompt, evaluate_correctness

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Store quiz sessions in memory (in production, use Redis or database)
quiz_sessions = {}

@app.route('/users')
def users(): 
    return {"users": ["Alice", "Bob", "Charlie"]}

@app.route('/api/quiz/start', methods=["POST"])
def start_quiz():
    """Start a new quiz session and generate all 3 questions"""
    try:
        # Get all commands from the database
        query = "SELECT query, suggested_command FROM requests"
        results = execute_query(query)
        
        if not results:
            return jsonify({"error": "No commands found in database"}), 404
            
        # Create a prompt for Gemini
        commands_text = "\n".join([
            f"Command: {r['query']}\nResponse: {r['response']}"
            for r in results
        ])

        prompt = generate_quiz_prompt(commands_text)
        
        # Get all 3 questions at once
        result = generate_response(prompt)
        response_text = result.get("generated_text", "").strip()
        
        # Parse the questions - they should be numbered 1., 2., 3.
        questions = []
        for line in response_text.split('\n'):
            line = line.strip()
            # Look for lines starting with "1.", "2.", or "3."
            if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                # Remove the number prefix
                question = line.split('.', 1)[1].strip()
                if question:
                    questions.append(question)
        
        # Ensure we have exactly 3 questions
        if len(questions) != 3:
            return jsonify({"error": f"Expected 3 questions but got {len(questions)}"}), 500
        
        # Create a new session
        session_id = str(uuid.uuid4())
        quiz_sessions[session_id] = {
            "questions": questions
        }
        
        return jsonify({
            "session_id": session_id,
            "questions": questions
        })
    except Exception as e:
        print(f"Error starting quiz: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/quiz/submit', methods=["POST"])
def submit_quiz():
    """Submit all answers and get evaluation for each question"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        qa_pairs = data.get('qa_pairs')  # List of {question, answer} objects
        
        if not session_id or session_id not in quiz_sessions:
            return jsonify({"error": "Invalid session"}), 400
        
        if not qa_pairs or len(qa_pairs) != 3:
            return jsonify({"error": "All 3 questions must be answered"}), 400
        
        # Evaluate each question-answer pair using Gemini
        evaluations = []
        for qa in qa_pairs:
            question = qa.get('question')
            answer = qa.get('answer')
            
            # Use the evaluate_correctness function to create evaluation prompt
            eval_prompt = evaluate_correctness(question, answer)
            
            # Get evaluation from Gemini
            result = generate_response(eval_prompt)
            evaluation = result.get("generated_text", "").strip()
            evaluations.append(evaluation)
        
        # Clean up session
        del quiz_sessions[session_id]
        
        return jsonify({
            "evaluations": evaluations
        })
    except Exception as e:
        print(f"Error submitting quiz: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Supabase endpoints
@app.route('/api/db/tables', methods=["GET"])
def get_tables():
    """List all tables in the database"""
    try:
        tables = list_tables()
        return jsonify({"tables": tables})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/db/query/<table_name>', methods=["GET"])
def query_table(table_name):
    """Fetch all data from a specific table"""
    try:
        data = fetch_all_from_table(table_name)
        return jsonify({"table": table_name, "data": data, "count": len(data)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/db/custom', methods=["POST"])
def custom_query():
    """Execute a custom SQL query"""
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        results = execute_query(query)
        return jsonify({"data": results, "count": len(results)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
