from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is running"

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    text = data["resume_text"]

    # Dummy result (later we add AI model)
    result = "Good Resume"

    return jsonify({"result": result})

if __name__ == "__main__":
    app.run()
