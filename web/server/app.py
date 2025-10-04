from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/users')
def users(): 
    return {"users": ["Alice", "Bob", "Charlie"]}

if __name__ == '__main__':
    app.run(debug=True, port=8080)