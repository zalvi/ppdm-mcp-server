"""
Mock PPDM Server — for local practice without real PPDM access.

Mimics the real endpoints and data shapes confirmed against a live PPDM server:
  POST /api/v2/login              -> returns access_token
  GET  /api/v2/activities         -> returns {page, content, _links}
  POST /api/v2/activities/<id>/retry -> returns retry result (207-style)

Run it:
    python mock_ppdm_server.py

Then point your scripts at:
    host = "http://localhost:5000"

No SSL, no port 8443, no verify=False needed — plain http on localhost.
"""

from flask import Flask, request, jsonify
import uuid
import random

app = Flask(__name__)

ASSET_NAMES = [
    "db-prod-01", "db-prod-02", "web-server-01", "web-server-02", "web-server-03",
    "analytics-node-01", "analytics-node-02", "payments-svc", "auth-svc",
    "cache-invalidation", "report-generation-weekly", "user-data-sync-etl",
    "invoice-pdf-generation", "email-campaign-dispatch", "cilium-secrets",
    "aws-dev-kubernetes-01", "aws-prod-kubernetes-01", "file-share-finance",
    "file-share-hr", "backup-proxy-02",
]

ASSET_TYPES = ["FILE_SYSTEM", "KUBERNETES", "VMWARE_VIRTUAL_MACHINE", "DATABASE"]

POLICIES = [
    "MD-AWS-DAILY-LINUX", "MD-AWS-WEEKLY-LINUX", "MD-AWS-DAILY-KUBE-PROD",
    "MD-AWS-MONTHLY-DB", "MD-AWS-DAILY-VM",
]

FAILURE_REASONS = [
    "Connection timeout to storage target",
    "Insufficient storage capacity",
    "Authentication failure with target host",
    "Asset unreachable during backup window",
    "Snapshot creation failed",
]


def _make_job(index):
    asset_name = ASSET_NAMES[index % len(ASSET_NAMES)]
    asset_type = random.choice(ASSET_TYPES)
    category = random.choice(["PROTECT", "PROTECT", "PROTECT", "CONFIG"])
    status = random.choices(["OK", "FAILED"], weights=[70, 30])[0]
    retryable = status == "FAILED" and random.choice([True, True, False])

    result = {"status": status, "summaries": [] if status == "OK" else [random.choice(FAILURE_REASONS)]}

    return {
        "id": str(uuid.uuid4()),
        "name": f"Backup - {asset_name}" if category == "PROTECT" else f"Configuring {asset_type.title()} - {asset_name}",
        "category": category,
        "subcategory": "BACKUP" if category == "PROTECT" else "ASSET_CONFIGURATION",
        "classType": "JOB",
        "source": {"type": "DATA_MANAGER"},
        "result": result,
        "actions": {"cancelable": False, "retryable": retryable},
        "asset": {"id": str(uuid.uuid4()), "name": asset_name, "type": asset_type},
        "protectionPolicy": {"id": str(uuid.uuid4()), "name": random.choice(POLICIES), "type": asset_type},
    }


random.seed(42)
FAKE_JOBS = [_make_job(i) for i in range(30)]


@app.route("/api/v2/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    return jsonify({"access_token": f"fake-token-for-{username}"}), 200


@app.route("/api/v2/activities", methods=["GET"])
def activities():
    return jsonify({
        "page": {"size": len(FAKE_JOBS), "totalElements": len(FAKE_JOBS), "totalPages": 1, "number": 0},
        "content": FAKE_JOBS,
        "_links": {"self": {"href": "/api/v2/activities"}},
    }), 200


@app.route("/api/v2/activities/<job_id>/retry", methods=["POST"])
def retry(job_id):
    job = next((j for j in FAKE_JOBS if j["id"] == job_id), None)
    if job is None:
        return jsonify({"error": f"No job found with id {job_id}"}), 404

    if not job["actions"]["retryable"]:
        return jsonify({
            "retryJobsReceivedCount": 1,
            "retryJobsInitiatedCount": 0,
            "retryResults": [{
                "retryJobId": job_id,
                "errorResponseObject": {
                    "code": 400,
                    "reason": "Retry is not available for this activity.",
                    "remediation": "Retry is not available for this activity.",
                    "timestamp": 0,
                },
            }],
        }), 207

    job["result"]["status"] = "OK"
    job["result"]["summaries"] = []
    job["actions"]["retryable"] = False

    return jsonify({
        "retryJobsReceivedCount": 1,
        "retryJobsInitiatedCount": 1,
        "retryResults": [{"retryJobId": job_id, "status": "INITIATED"}],
    }), 207


if __name__ == "__main__":
    print("Mock PPDM server starting on http://localhost:5000")
    print("Endpoints available:")
    print("  POST /api/v2/login")
    print("  GET  /api/v2/activities")
    print("  POST /api/v2/activities/<job_id>/retry")
    try:
        app.run(host="127.0.0.1", port=5000)
    except Exception as e:
        print(f"SERVER FAILED TO START: {e}")