from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_receive_and_list():
    resp = client.post("/webhook", json={"event": "test", "value": 123}, headers={"User-Agent": "pytest"})
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
