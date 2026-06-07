from flask import Flask
from flask import request
from flask import jsonify

app = Flask(__name__)

ledger = []

@app.route("/")

def home():

    return "Node Running"

@app.route("/transaction", methods=["POST"])

def transaction():

    data = request.json

    ledger.append(data)

    return jsonify({
        "status":"committed",
        "ledger":len(ledger)
    })

@app.route("/ledger")

def get_ledger():

    return jsonify(ledger)

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )