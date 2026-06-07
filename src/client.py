import requests

for i in range(10):

    requests.post(
        "http://localhost:5000/transaction",
        json={
            "id":i,
            "txn":f"TXN-{i}"
        }
    )

print("Done")