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

# ==================================================
# Global State
# ==================================================

leader_id = None

last_heartbeat = time.time()

ledger = []

# ==================================================
# Bully Election
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

    if alive_nodes:

        new_leader = max(alive_nodes)

        if leader_id != new_leader:

            leader_id = new_leader

            print(
                f"[Node {NODE_ID}] New Leader Elected: Node {leader_id}"
            )

# ==================================================
# Heartbeat Endpoint
# ==================================================

@app.route("/heartbeat", methods=["POST"])
def heartbeat():

    global last_heartbeat

    last_heartbeat = time.time()

    return jsonify({
        "status": "heartbeat_received",
        "node_id": NODE_ID
    })

# ==================================================
# Heartbeat Sender
# ==================================================

def send_heartbeats():

    while True:

        if leader_id == NODE_ID:

            for node_id, url in nodes.items():

                if node_id == NODE_ID:
                    continue

                try:

                    requests.post(
                        f"{url}/heartbeat",
                        timeout=1
                    )

                except Exception:

                    pass

        time.sleep(2)

# ==================================================
# Monitor Leader
# ==================================================

def monitor_leader():

    global leader_id

    while True:

        if leader_id is not None:

            if NODE_ID != leader_id:

                elapsed = time.time() - last_heartbeat

                if elapsed > 5:

                    print(
                        f"[Node {NODE_ID}] Leader timeout detected"
                    )

                    bully_election()

        time.sleep(1)

# ==================================================
# Home
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "Distributed Consensus Node Running",
        "node_id": NODE_ID
    })

# ==================================================
# Status
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
# Leader
# ==================================================

@app.route("/leader", methods=["GET"])
def leader():

    return jsonify({
        "leader_id": leader_id
    })

# ==================================================
# Transaction
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
        "ledger_size": len(ledger)
    })

# ==================================================
# Ledger
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
# Main
# ==================================================

if __name__ == "__main__":

    print("\n================================")
    print(f"Node {NODE_ID} Started")
    print(f"Hostname : {HOSTNAME}")
    print("================================\n")

    # Initial Election
    time.sleep(5)
    bully_election()

    # Heartbeat Sender
    threading.Thread(
        target=send_heartbeats,
        daemon=True
    ).start()

    # Failure Monitor
    threading.Thread(
        target=monitor_leader,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )