from flask import Flask, request, jsonify
from flask_cors import CORS
from gemini import generate_response
from database import list_tables, fetch_all_from_table, execute_query

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/users')
def users(): 
    return {"users": ["Alice", "Bob", "Charlie"]}

@app.route('/api/generate', methods=["POST"])
def generate():
    try:
        # Get prompt from request body, or use hardcoded prompt
        data = request.get_json() if request.is_json else {}
        prompt = data.get('prompt', 'hi my name is parth j')
        
        result = generate_response(prompt)
        return jsonify(result)
    except Exception as e:
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
