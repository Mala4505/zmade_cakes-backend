"""
Test all API endpoints. Run: python test_endpoints.py
Set ADMIN_PASSWORD in .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "your-admin-password")

def req(method, path, data=None, headers=None, password=None):
    h = dict(headers or {})
    h["Content-Type"] = "application/json"
    if password:
        h["X-Admin-Password"] = password
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    def parse(r):
        b = r.read().decode()
        try:
            return json.loads(b)
        except json.JSONDecodeError:
            return {"raw": b[:200]}

    try:
        with urllib.request.urlopen(req) as r:
            return r.getcode(), parse(r)
    except urllib.error.HTTPError as e:
        return e.code, parse(e) if e.read() else {}

def main():
    errors = []
    print("=== Testing endpoints ===\n")

    # 1. Login (no password required - excluded from middleware)
    code, body = req("POST", "/api/admin/login/", {"password": ADMIN_PW})
    ok = code == 200 and body.get("success")
    print(f"POST /api/admin/login/ (wrong first): {req('POST', '/api/admin/login/', {'password': 'wrong'})[0]} (expect 401)")
    print(f"POST /api/admin/login/ (correct): {code} {'OK' if ok else 'FAIL'}")
    if not ok:
        errors.append("Login failed - check ADMIN_PASSWORD in .env")
    print()

    # 2. Admin orders list (requires password)
    code, body = req("GET", "/api/admin/orders/", password=ADMIN_PW)
    print(f"GET /api/admin/orders/ (no auth): {req('GET', '/api/admin/orders/')[0]} (expect 401)")
    print(f"GET /api/admin/orders/ (with auth): {code} {'OK' if code == 200 else 'FAIL'}")
    if code != 200:
        errors.append("GET orders failed")
    orders = body if isinstance(body, list) else []
    print(f"  Orders count: {len(orders)}")
    print()

    # 3. Admin order detail
    if orders:
        pk = orders[0]["id"]
        edit_token = orders[0]["edit_token"]
        invoice_token = orders[0]["invoice_token"]
        code, _ = req("GET", f"/api/admin/orders/{pk}/", password=ADMIN_PW)
        print(f"GET /api/admin/orders/{pk}/: {code} {'OK' if code == 200 else 'FAIL'}")
        if code != 200:
            errors.append("GET order detail failed")

        # 4. Status update
        code, _ = req("POST", f"/api/admin/orders/{pk}/status/", {"status": "customer_confirmed"}, password=ADMIN_PW)
        print(f"POST /api/admin/orders/{pk}/status/: {code} {'OK' if code == 200 else 'FAIL'}")
        if code != 200:
            errors.append("Status update failed")

        # 5. Payment update
        code, _ = req("POST", f"/api/admin/orders/{pk}/payment/", {"payment_status": "paid"}, password=ADMIN_PW)
        print(f"POST /api/admin/orders/{pk}/payment/: {code} {'OK' if code == 200 else 'FAIL'}")

        # 6. Public view (invoice_token)
        code, _ = req("GET", f"/api/orders/view/{invoice_token}/")
        print(f"GET /api/orders/view/{{token}}/: {code} {'OK' if code == 200 else 'FAIL'}")
        if code != 200:
            errors.append("Public view failed")

        # 7. Public edit (edit_token)
        code, _ = req("GET", f"/api/orders/edit/{edit_token}/")
        print(f"GET /api/orders/edit/{{token}}/: {code} {'OK' if code == 200 else 'FAIL'}")
        code2, _ = req("PUT", f"/api/orders/edit/{edit_token}/", {"customer_notes": "Updated by test"}, password=None)
        print(f"PUT /api/orders/edit/{{token}}/: {code2} {'OK' if code2 == 200 else 'FAIL'}")
    print()

    # 8. Create order
    new_order = {
        "customer_name": "Test Customer",
        "phone": "12345678",
        "area": "Test Area",
        "address": "Test Address",
        "pickup_or_delivery": "delivery",
        "items": [{"cake_type": "Test Cake", "flavor": "Chocolate", "size": "6 inch", "quantity": 1, "price": "15", "notes": ""}],
        "delivery_date": "2025-02-15",
        "delivery_time": "morning",
        "status": "draft",
        "collateral_items": [],
    }
    code, body = req("POST", "/api/admin/orders/", new_order, password=ADMIN_PW)
    print(f"POST /api/admin/orders/: {code} {'OK' if code == 201 else 'FAIL'}")
    if code != 201:
        errors.append(f"Create order failed: {body}")
    print()

    # 9. DELETE draft order (the one we just created)
    if code == 201 and isinstance(body, dict) and "id" in body:
        draft_id = body["id"]
        code_del, _ = req("DELETE", f"/api/admin/orders/{draft_id}/", password=ADMIN_PW)
        print(f"DELETE /api/admin/orders/{{draft_id}}/: {code_del} {'OK' if code_del == 204 else 'FAIL'}")

    # 10. delivery_date filter
    from datetime import date
    today = str(date.today())
    code, body = req("GET", f"/api/admin/orders/?delivery_date={today}", password=ADMIN_PW)
    print(f"GET /api/admin/orders/?delivery_date=: {code} {'OK' if code == 200 else 'FAIL'}")

    # 11. Invalid token (404)
    code, _ = req("GET", "/api/orders/view/00000000-0000-0000-0000-000000000000/")
    print(f"GET /api/orders/view/{{invalid}}: {code} (expect 404) {'OK' if code == 404 else 'FAIL'}")

    # 12. Notifications
    code, body = req("GET", "/api/admin/notifications/", password=ADMIN_PW)
    print(f"GET /api/admin/notifications/: {code} {'OK' if code == 200 else 'FAIL'}")
    notifs = body if isinstance(body, list) else []
    if notifs:
        code, _ = req("POST", f"/api/admin/notifications/{notifs[0]['id']}/read/", password=ADMIN_PW)
        print(f"POST /api/admin/notifications/{{id}}/read/: {code} {'OK' if code == 200 else 'FAIL'}")

    print("\n=== Summary ===")
    if errors:
        print("Errors:", errors)
    else:
        print("All endpoints OK")

if __name__ == "__main__":
    main()
