#!/bin/bash

echo "======================================"
echo "PBFT / PAXOS CHAOS TEST STARTED"
echo "======================================"

echo ""
echo "Current Containers"
docker ps

echo ""
echo "Waiting for cluster stabilization..."
sleep 15

echo ""
echo "Checking Leader"

curl http://localhost:5001/leader

echo ""
echo ""
echo "======================================"
echo "TEST 1 : NORMAL TRANSACTIONS"
echo "======================================"

curl -X POST http://localhost:5005/propose_transaction \
-H "Content-Type: application/json" \
-d '{"txn":"NORMAL_TXN_1"}'

sleep 2

curl -X POST http://localhost:5005/propose_transaction \
-H "Content-Type: application/json" \
-d '{"txn":"NORMAL_TXN_2"}'

sleep 2

echo ""
echo "Leader Ledger"

curl http://localhost:5005/ledger

echo ""
echo ""
echo "======================================"
echo "TEST 2 : LEADER CRASH"
echo "======================================"

docker stop node5

echo ""
echo "Leader stopped"

sleep 15

echo ""
echo "New Leader"

curl http://localhost:5001/leader

echo ""
echo ""
echo "======================================"
echo "TEST 3 : TRANSACTION AFTER FAILURE"
echo "======================================"

curl -X POST http://localhost:5004/propose_transaction \
-H "Content-Type: application/json" \
-d '{"txn":"AFTER_LEADER_FAILURE"}'

sleep 2

curl http://localhost:5004/ledger

echo ""
echo ""
echo "======================================"
echo "TEST 4 : LEADER RECOVERY"
echo "======================================"

docker start node5

sleep 15

echo ""
echo "Leader Status"

curl http://localhost:5005/leader

echo ""
echo ""
echo "======================================"
echo "TEST 5 : BYZANTINE NODE"
echo "======================================"

curl http://localhost:5099/status

echo ""
echo ""

curl -X POST http://localhost:5099/malicious_prepare \
-H "Content-Type: application/json" \
-d '{"target":"node1"}'

echo ""
echo ""

curl -X POST http://localhost:5099/malicious_prepare \
-H "Content-Type: application/json" \
-d '{"target":"node2"}'

echo ""
echo ""
echo "======================================"
echo "TEST 6 : NETWORK PARTITION"
echo "======================================"

docker network disconnect \
distributed-consensus-engine_default \
node3

echo ""
echo "Node3 isolated"

sleep 15

echo ""
echo "Remaining Cluster"

curl http://localhost:5001/leader

echo ""
echo ""
echo "======================================"
echo "TEST 7 : RECOVER PARTITION"
echo "======================================"

docker network connect \
distributed-consensus-engine_default \
node3

sleep 10

echo ""
echo "Node3 rejoined cluster"

curl http://localhost:5003/status

echo ""
echo ""
echo "======================================"
echo "TEST 8 : FINAL TRANSACTION"
echo "======================================"

curl -X POST http://localhost:5005/propose_transaction \
-H "Content-Type: application/json" \
-d '{"txn":"FINAL_TXN"}'

sleep 2

curl http://localhost:5005/ledger

echo ""
echo ""
echo "======================================"
echo "CHAOS TEST COMPLETED"
echo "======================================"