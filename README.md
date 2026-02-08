# ZMade Cakes Kuwait – Django Backend

## Setup

1. Create `backend/.env` (see `.env.example`) – set `ADMIN_PASSWORD`, `DATABASE_URL` (password with `#`/`@` → `%23`/`%40`)
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py runserver` → http://127.0.0.1:8000
5. `python manage.py seed_orders` – add test data
6. `python test_endpoints.py` – verify all endpoints

## API

**Admin** (send `X-Admin-Password` header or `password` in POST body):
- `POST /api/admin/login/` – verify password
- `GET/POST /api/admin/orders/` – list, create orders
- `GET/PUT/DELETE /api/admin/orders/:id/`
- `POST /api/admin/orders/:id/status/`
- `POST /api/admin/orders/:id/payment/`
- `GET /api/admin/notifications/`
- `POST /api/admin/notifications/:id/read/`

**Public** (use UUID tokens):
- `GET/PUT /api/orders/edit/:token/`
- `GET /api/orders/view/:token/`
