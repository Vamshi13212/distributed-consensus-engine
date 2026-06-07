from flask import Flask, request, jsonify

import os
import socket
import requests
import threading
import time

# ==================================================
# Flask Application
# ==================================================

app = Flask(__name__)

# ==================================================
# Node Configuration
# ==================================================

NODE_ID = int(os.getenv("NODE_ID", "1"))

HOSTNAME = socket.gethostname()

# ==================================================
# Cluster Configuration
# ==================================================

nodes = {
    1: "http://node1:5000",
    2: "http://node2:5000",
    3: "http://node3:5000",
    4: "http://node4:5000",
    5: "http://node5:5000"
}

leader_id = None

# ==================================================
# In-Memory Ledger
# ==================================================

ledger = []

# ==================================================
# Bully Leader Election
# ==================================================

def bully_election():

    global leader_id

    alive_nodes = []

    for node_id, url in nodes.items():

        try:

            response = requests.get(
                f"{url}/status",
                timeout=1
            )

            if response.status_code == 200:

                alive_nodes.append(node_id)

        except Exception:

            pass

    if len(alive_nodes) > 0:

        new_leader = max(alive_nodes)

        if new_leader != leader_id:

            leader_id = new_leader

            print(
                f"[Node {NODE_ID}] New Leader Elected: Node {leader_id}"
            )

# ==================================================
# Election Background Thread
# ==================================================

def election_loop():

    while True:

        bully_election()

        time.sleep(10)

# ==================================================
# Home Endpoint
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "Distributed Consensus Node Running",
        "node_id": NODE_ID
    })

# ==================================================
# Status Endpoint
# ==================================================

@app.route("/status", methods=["GET"])
def status():

    return jsonify({
        "node_id": NODE_ID,
        "hostname": HOSTNAME,
        "leader_id": leader_id,
        "ledger_size": len(ledger),
        "status": "alive"
    })

# ==================================================
# Leader Endpoint
# ==================================================

@app.route("/leader", methods=["GET"])
def leader():

    return jsonify({
        "leader_id": leader_id
    })

# ==================================================
# Add Transaction
# ==================================================

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
        "leader_id": leader_id,
        "ledger_size": len(ledger),
        "transaction": data
    })

# ==================================================
# View Ledger
# ==================================================

@app.route("/ledger", methods=["GET"])
def get_ledger():

    return jsonify({
        "node_id": NODE_ID,
        "leader_id": leader_id,
        "ledger": ledger
    })

# ==================================================
# Clear Ledger
# ==================================================

@app.route("/clear", methods=["POST"])
def clear_ledger():

    ledger.clear()

    return jsonify({
        "status": "cleared",
        "node_id": NODE_ID
    })

# ==================================================
# Application Entry
# ==================================================

if __name__ == "__main__":

    print("\n===================================")
    print(f"Node {NODE_ID} Started")
    print(f"Hostname : {HOSTNAME}")
    print("Starting Leader Election Service")
    print("===================================\n")

    threading.Thread(
        target=election_loop,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )