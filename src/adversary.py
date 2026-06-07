from flask import Flask, jsonify, request

import os
import socket

app = Flask(__name__)

NODE_ID = int(
    os.getenv("NODE_ID", "99")
)

HOSTNAME = socket.gethostname()

# ==========================================
# Status
# ==========================================

@app.route("/status")
def status():

    return jsonify({
        "node_id": NODE_ID,
        "hostname": HOSTNAME,
        "role": "BYZANTINE"
    })

# ==========================================
# Malicious PREPARE
# ==========================================

@app.route(
    "/malicious_prepare",
    methods=["POST"]
)
def malicious_prepare():

    target = request.json.get(
        "target",
        "unknown"
    )

    if target == "node1":

        txn = "TXN-100"

    elif target == "node2":

        txn = "TXN-999"

    else:

        txn = "TXN-555"

    return jsonify({
        "status": "malicious",
        "fake_txn": txn
    })

# ==========================================
# Drop Commit Messages
# ==========================================

@app.route(
    "/commit_pbft",
    methods=["POST"]
)
def fake_commit():

    print(
        "[BYZANTINE] Dropping COMMIT"
    )

    return jsonify({
        "status": "ignored"
    })

# ==========================================
# Home
# ==========================================

@app.route("/")
def home():

    return jsonify({
        "node_id": NODE_ID,
        "role": "BYZANTINE"
    })

# ==========================================
# Main
# ==========================================

if __name__ == "__main__":

    print(
        f"Byzantine Node {NODE_ID} Started"
    )

    app.run(
        host="0.0.0.0",
        port=5000
    )