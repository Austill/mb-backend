from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "message": "Backend server is running!"})

@app.route('/api/test')
def test():
    return jsonify({"message": "Test endpoint working!"})

if __name__ == '__main__':
    print("Starting test server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
