import base64
import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

from echo_service.main import app

client = TestClient(app)


def test_receive_and_list():
    resp = client.post(
        "/webhook",
        json={"event": "test", "value": 123},
        headers={"User-Agent": "pytest"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    eid = body["id"]

    r2 = client.get("/api/webhooks")
    assert r2.status_code == 200
    items = r2.json()
    assert any(i["id"] == eid for i in items)


def test_detail_page():
    resp = client.post("/webhook", json={"foo": "bar"})
    eid = resp.json()["id"]
    r = client.get(f"/webhooks/{eid}")
    assert r.status_code == 200
    assert "Webhook" in r.text


def test_verify_signature_missing_headers():
    resp = client.post("/webhook", json={"foo": "bar"})
    eid = resp.json()["id"]
    r = client.post(f"/api/webhooks/{eid}/verify", json={"secret": "whatever"})
    assert r.status_code == 400
    assert (
        "signature" in r.json()["detail"].lower()
        or "missing" in r.json()["detail"].lower()
    )


def test_verify_signature_valid():
    payload = {"event": "test", "value": 1}
    # use compact JSON representation to match raw body
    payload_str = json.dumps(payload, separators=(",", ":"))
    delivery_id = "delivery-123"
    timestamp = str(int(time.time()))
    secret = "my-secret"
    signed_content = f"{delivery_id}.{timestamp}.{payload_str}"
    expected_sig = hmac.new(
        secret.encode("utf-8"), signed_content.encode("utf-8"), hashlib.sha256
    ).digest()
    sig_b64 = base64.b64encode(expected_sig).decode("utf-8")
    sig_header = f"v1,{sig_b64}"
    headers = {
        "x-mlflow-delivery-id": delivery_id,
        "x-mlflow-timestamp": timestamp,
        "x-mlflow-signature": sig_header,
        "content-type": "application/json",
    }
    # send the webhook with the exact body used for signature
    resp = client.post("/webhook", content=payload_str, headers=headers)
    assert resp.status_code == 200
    eid = resp.json()["id"]
    r = client.post(f"/api/webhooks/{eid}/verify", json={"secret": secret})
    assert r.status_code == 200
    assert r.json().get("verified") is True
