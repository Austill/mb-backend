from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Use the same URI as your config
MONGO_URI = "mongodb://localhost:27017/mindbuddy"
client = MongoClient(MONGO_URI)
db = client.mindbuddy

@app.route("/api/test")
def test_connection():
    try:
        # Ping MongoDB
        client.admin.command("ping")
        # Try to get a collection count
        count = db.journals.count_documents({})
        return jsonify({
            "status": "ok",
            "mongo_ping": True,
            "journal_count": count
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

if __name__ == "__main__":
    app.run(debug=True)
