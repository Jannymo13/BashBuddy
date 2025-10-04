from flask import Flask

app = Flask(__name__)

@app.route('/users')
def users(): 
    return {"users": ["Alice", "Bob", "Charlie"]}

if __name__ == '__main__':
    app.run(debug=True, port=8080)