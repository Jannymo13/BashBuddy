from flask import Flask, request, jsonify
from flask_cors import CORS
from gemini import generate_response
from database import list_tables, fetch_all_from_table, execute_query
import uuid
from datetime import datetime 
from prompt import generate_quiz_prompt

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/users')
def users(): 
    return {"users": ["Alice", "Bob", "Charlie"]}

@app.route('/api/quiz', methods=["GET"])
def generate_quiz():
    try:
        # Get all commands from the database
        query = "SELECT query, response FROM requests"
        results = execute_query(query)
        
        if not results:
            return jsonify({"error": "No commands found in database"}), 404
            
        # Create a prompt for Gemini
        commands_text = "\n".join([
            f"Command: {r['query']}\nResponse: {r['response']}"
            for r in results
        ])

        prompt = generate_quiz_prompt(commands_text)
        result = generate_response(prompt)
        
        # Clean and parse the response
        try:
            import json
            response_text = result.get("generated_text", "")
            
            # Clean up any formatting issues
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.removeprefix("```json").removesuffix("```").strip()
            
            # Parse JSON and clean up each question
            questions = json.loads(response_text)
            questions = [q.strip().strip('"').replace('\\n', '\n') for q in questions]
            
            return jsonify({"questions": questions})
        except Exception as e:
            print(f"Error parsing questions: {str(e)}")
            # Fallback: split by line numbers and clean up
            text = result.get("generated_text", "")
            questions = []
            for line in text.split('\n'):
                line = line.strip()
                if line and not line.startswith(('[', ']', '{', '}')):
                    # Remove numbering, quotes, and clean up
                    cleaned = line.split('.', 1)[-1].strip().strip('"')
                    if cleaned:
                        questions.append(cleaned)
            return jsonify({"questions": questions[:3]})  # Ensure we return max 3 questions
    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
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
