from flask import Flask, request, jsonify
from crypto_utils import *

import os
import socket
import requests
import threading
import time

# =====================================================
# Flask Application
# =====================================================

app = Flask(__name__)

# =====================================================
# Node Configuration
# =====================================================

NODE_ID = int(os.getenv("NODE_ID", "1"))

HOSTNAME = socket.gethostname()
private_key, public_key = generate_key_pair()
# =====================================================
# Cluster Configuration
# =====================================================

nodes = {
    1: "http://node1:5000",
    2: "http://node2:5000",
    3: "http://node3:5000",
    4: "http://node4:5000",
    5: "http://node5:5000"
}

# =====================================================
# Global State
# =====================================================

leader_id = None

last_heartbeat = time.time()

ledger = []

# =====================================================
# Paxos State
# =====================================================

proposal_number = 0

highest_prepare_seen = 0

accepted_value = None

# =====================================================
# PBFT State
# =====================================================

view_number = 1

sequence_number = 0

prepare_votes = {}

commit_votes = {}

pbft_committed = set()

# =====================================================
# Bully Leader Election
# =====================================================

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

        if new_leader != leader_id:

            leader_id = new_leader

            print(
                f"[Node {NODE_ID}] New Leader Elected -> Node {leader_id}"
            )

#
def create_signed_payload(message):

    signature = sign_message(
        private_key,
        message
    )

    return signature.hex()


def verify_payload_signature(
    sender_public_key,
    message,
    signature_hex
):

    try:

        signature = bytes.fromhex(
            signature_hex
        )

        return verify_signature(
            sender_public_key,
            message,
            signature
        )

    except:

        return False


node_public_keys = {
    NODE_ID: public_key
}
#
# =====================================================
# Heartbeat Endpoint
# =====================================================

@app.route("/heartbeat", methods=["POST"])
def heartbeat():

    global last_heartbeat

    last_heartbeat = time.time()

    return jsonify({
        "status": "heartbeat_received",
        "node_id": NODE_ID
    })

# =====================================================
# Heartbeat Sender
# =====================================================

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

# =====================================================
# Leader Monitoring
# =====================================================

def monitor_leader():

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

# =====================================================
# Paxos Prepare
# =====================================================

@app.route("/prepare", methods=["POST"])
def prepare():

    global highest_prepare_seen

    data = request.get_json()

    proposal = data["proposal"]

    if proposal > highest_prepare_seen:

        highest_prepare_seen = proposal

        return jsonify({
            "promise": True,
            "node_id": NODE_ID
        })

    return jsonify({
        "promise": False,
        "node_id": NODE_ID
    })

# =====================================================
# Paxos Accept
# =====================================================

@app.route("/accept", methods=["POST"])
def accept():

    global accepted_value

    data = request.get_json()

    proposal = data["proposal"]

    txn = data["txn"]

    if proposal >= highest_prepare_seen:

        accepted_value = txn

        return jsonify({
            "accepted": True,
            "node_id": NODE_ID
        })

    return jsonify({
        "accepted": False,
        "node_id": NODE_ID
    })

# =====================================================
# Paxos Coordinator
# =====================================================

def run_paxos(txn):

    global proposal_number

    proposal_number += 1

    proposal = proposal_number

    promises = 0

    print(
        f"[Leader {NODE_ID}] Starting Paxos Proposal {proposal}"
    )

    # -------------------------------------------
    # PREPARE PHASE
    # -------------------------------------------

    for node_id, url in nodes.items():

        try:

            response = requests.post(
                f"{url}/prepare",
                json={
                    "proposal": proposal
                },
                timeout=2
            )

            result = response.json()

            if result["promise"]:

                promises += 1

        except Exception:
            pass

    print(
        f"[Leader {NODE_ID}] Promises Received = {promises}"
    )

    if promises < 3:

        print(
            f"[Leader {NODE_ID}] Prepare Phase Failed"
        )

        return False

    # -------------------------------------------
    # ACCEPT PHASE
    # -------------------------------------------

    accepted = 0

    for node_id, url in nodes.items():

        try:

            response = requests.post(
                f"{url}/accept",
                json={
                    "proposal": proposal,
                    "txn": txn
                },
                timeout=2
            )

            result = response.json()

            if result["accepted"]:

                accepted += 1

        except Exception:
            pass

    print(
        f"[Leader {NODE_ID}] Accepted Responses = {accepted}"
    )

    if accepted >= 3:

        ledger.append(txn)

        print(
            f"[Leader {NODE_ID}] Consensus Reached"
        )

        return True

    print(
        f"[Leader {NODE_ID}] Consensus Failed"
    )

    return False


@app.route("/pre_prepare", methods=["POST"])
def pre_prepare():

    data = request.get_json()

    txn = data["txn"]

    sequence = data["sequence"]

    signature = data["signature"]

    print(
        f"[Node {NODE_ID}] PRE-PREPARE received"
    )

    return jsonify({
        "status": "accepted",
        "node_id": NODE_ID
    })

@app.route("/prepare_pbft", methods=["POST"])
def prepare_pbft():

    global prepare_votes

    data = request.get_json()

    sequence = data["sequence"]

    if sequence not in prepare_votes:

        prepare_votes[sequence] = set()

    prepare_votes[sequence].add(
        data["node_id"]
    )

    return jsonify({
        "prepared": True,
        "votes":
            len(
                prepare_votes[sequence]
            )
    })

@app.route("/commit_pbft", methods=["POST"])
def commit_pbft():

    global commit_votes

    data = request.get_json()

    sequence = data["sequence"]

    if sequence not in commit_votes:

        commit_votes[sequence] = set()

    commit_votes[sequence].add(
        data["node_id"]
    )

    return jsonify({
        "committed": True,
        "votes":
            len(
                commit_votes[sequence]
            )
    })

def run_pbft(txn):

    global sequence_number

    sequence_number += 1

    sequence = sequence_number

    message = str(txn)

    signature = create_signed_payload(
        message
    )

    # ==========================
    # PRE-PREPARE
    # ==========================

    pre_prepare_count = 0

    for node_id, url in nodes.items():

        try:

            response = requests.post(
                f"{url}/pre_prepare",
                json={
                    "txn": txn,
                    "sequence": sequence,
                    "signature": signature
                },
                timeout=2
            )

            if response.status_code == 200:

                pre_prepare_count += 1

        except:

            pass

    print(
        f"PRE-PREPARE ACKS = {pre_prepare_count}"
    )

    # ==========================
    # PREPARE
    # ==========================

    prepare_count = 0

    for node_id, url in nodes.items():

        try:

            response = requests.post(
                f"{url}/prepare_pbft",
                json={
                    "sequence": sequence,
                    "node_id": NODE_ID
                },
                timeout=2
            )

            result = response.json()

            if result["prepared"]:

                prepare_count += 1

        except:

            pass

    print(
        f"PREPARE VOTES = {prepare_count}"
    )

    if prepare_count < 3:

        return False

    # ==========================
    # COMMIT
    # ==========================

    commit_count = 0

    for node_id, url in nodes.items():

        try:

            response = requests.post(
                f"{url}/commit_pbft",
                json={
                    "sequence": sequence,
                    "node_id": NODE_ID
                },
                timeout=2
            )

            result = response.json()

            if result["committed"]:

                commit_count += 1

        except:

            pass

    print(
        f"COMMIT VOTES = {commit_count}"
    )

    if commit_count >= 3:

        ledger.append(txn)

        pbft_committed.add(sequence)

        print(
            f"PBFT COMMIT SUCCESS {txn}"
        )

        return True

    return False

@app.route(
    "/pbft_transaction",
    methods=["POST"]
)
def pbft_transaction():

    if NODE_ID != leader_id:

        return jsonify({
            "status": "rejected",
            "leader_id": leader_id
        }), 400

    data = request.get_json()

    success = run_pbft(data)

    if success:

        return jsonify({
            "status": "committed",
            "mode": "PBFT"
        })

    return jsonify({
        "status": "failed"
    }), 500


# =====================================================
# Home Endpoint
# =====================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "Distributed Consensus Node Running",
        "node_id": NODE_ID
    })

# =====================================================
# Status Endpoint
# =====================================================

@app.route("/status", methods=["GET"])
def status():

    return jsonify({
        "node_id": NODE_ID,
        "hostname": HOSTNAME,
        "leader_id": leader_id,
        "ledger_size": len(ledger),
        "status": "alive"
    })

# =====================================================
# Leader Endpoint
# =====================================================

@app.route("/leader", methods=["GET"])
def get_leader():

    return jsonify({
        "leader_id": leader_id
    })

# =====================================================
# Client Transaction Endpoint
# =====================================================

@app.route("/propose_transaction", methods=["POST"])
def propose_transaction():

    if NODE_ID != leader_id:

        return jsonify({
            "status": "rejected",
            "reason": "not leader",
            "leader_id": leader_id
        }), 400

    data = request.get_json()

    success = run_paxos(data)

    if success:

        return jsonify({
            "status": "committed",
            "leader": NODE_ID
        })

    return jsonify({
        "status": "failed"
    }), 500

# =====================================================
# Legacy Transaction Endpoint
# =====================================================

@app.route("/transaction", methods=["POST"])
def add_transaction():

    data = request.get_json()

    ledger.append(data)

    return jsonify({
        "status": "committed",
        "node_id": NODE_ID
    })

# =====================================================
# Ledger Endpoint
# =====================================================

@app.route("/ledger", methods=["GET"])
def get_ledger():

    return jsonify({
        "node_id": NODE_ID,
        "leader_id": leader_id,
        "ledger": ledger
    })

# =====================================================
# Clear Ledger
# =====================================================

@app.route("/clear", methods=["POST"])
def clear_ledger():

    ledger.clear()

    return jsonify({
        "status": "cleared",
        "node_id": NODE_ID
    })


def create_signed_message(message):

    signature = sign_message(
        private_key,
        message
    )

    return {
        "message": message,
        "signature": signature.hex()
    }

def verify_signed_message(
    sender_public_key,
    message,
    signature_hex
):

    signature = bytes.fromhex(
        signature_hex
    )

    return verify_signature(
        sender_public_key,
        message,
        signature
    )

@app.route("/pbft_test")
def pbft_test():

    message = "TEST_PBFT"

    signed = create_signed_message(
        message
    )

    return jsonify({
        "message": signed["message"],
        "signature":
            signed["signature"][:50]
    })


# =====================================================
# Main
# =====================================================

if __name__ == "__main__":

    print("\n====================================")
    print(f"Node {NODE_ID} Started")
    print(f"Hostname : {HOSTNAME}")
    print("Leader Election + Paxos Enabled")
    print("====================================\n")

    time.sleep(5)

    bully_election()

    threading.Thread(
        target=send_heartbeats,
        daemon=True
    ).start()

    threading.Thread(
        target=monitor_leader,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )