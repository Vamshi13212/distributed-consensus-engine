from flask import Flask, request, jsonify
import os
import socket

# --------------------------------------------------
# Flask Application
# --------------------------------------------------

app = Flask(__name__)

# --------------------------------------------------
# Node Configuration
# --------------------------------------------------

NODE_ID = int(os.getenv("NODE_ID", "1"))

HOSTNAME = socket.gethostname()

# --------------------------------------------------
# In-Memory Ledger
# --------------------------------------------------

ledger = []

# --------------------------------------------------
# Home Endpoint
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "Distributed Consensus Node Running",
        "node_id": NODE_ID
    })


# --------------------------------------------------
# Status Endpoint
# --------------------------------------------------

@app.route("/status", methods=["GET"])
def status():

    return jsonify({
        "node_id": NODE_ID,
        "hostname": HOSTNAME,
        "ledger_size": len(ledger),
        "status": "alive"
    })


# --------------------------------------------------
# Add Transaction
# --------------------------------------------------

@app.route("/transaction", methods=["POST"])
def add_transaction():

    data = request.get_json()

    if not data:

        return jsonify({
            "status": "error",
            "message": "No transaction received"
        }), 400

    ledger.append(data)

    return jsonify({
        "status": "committed",
        "node_id": NODE_ID,
        "ledger_size": len(ledger),
        "transaction": data
    })


# --------------------------------------------------
# View Ledger
# --------------------------------------------------

@app.route("/ledger", methods=["GET"])
def get_ledger():

    return jsonify({
        "node_id": NODE_ID,
        "ledger": ledger
    })


# --------------------------------------------------
# Clear Ledger (Testing Only)
# --------------------------------------------------

@app.route("/clear", methods=["POST"])
def clear_ledger():

    ledger.clear()

    return jsonify({
        "status": "cleared",
        "node_id": NODE_ID
    })


# --------------------------------------------------
# Application Entry
# --------------------------------------------------

if __name__ == "__main__":

    print(f"\nNode {NODE_ID} Started")
    print(f"Hostname : {HOSTNAME}")
    print("Waiting for requests...\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )