from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)   # VERY IMPORTANT

@app.route("/")
def home():
    return "Backend is running"

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    text = data.get("resume_text", "")

    # Dummy AI result (you can replace later with ML model)
    result = "Good Resume"

    return jsonify({"result": result})

if __name__ == "__main__":
    app.run()
