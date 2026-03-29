"""
Tests for the Buy Service API.

Uses an SQLite database (via DATABASE_URL env set in conftest.py)
so no PostgreSQL is required at test time.
"""
import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine, SessionLocal
from app.main import app

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ── Helpers ───────────────────────────────────────────────────────────────────

def register_and_login(client: TestClient, username: str, password: str = "Password123"):
    client.post(
        "/auth/register",
        json={"email": f"{username}@example.com", "username": username, "password": password},
    )
    resp = client.post(
        "/auth/token",
        data={"username": username, "password": password},
    )
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Health check ──────────────────────────────────────────────────────────────

def test_health_check(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_register_success(client):
    resp = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "username": "alice", "password": "secret123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    client.post(
        "/auth/register",
        json={"email": "bob@example.com", "username": "bob", "password": "secret123"},
    )
    resp = client.post(
        "/auth/register",
        json={"email": "bob@example.com", "username": "bob2", "password": "secret123"},
    )
    assert resp.status_code == 400


def test_register_duplicate_username(client):
    client.post(
        "/auth/register",
        json={"email": "charlie@example.com", "username": "charlie", "password": "secret123"},
    )
    resp = client.post(
        "/auth/register",
        json={"email": "charlie2@example.com", "username": "charlie", "password": "secret123"},
    )
    assert resp.status_code == 400


def test_login_success(client):
    client.post(
        "/auth/register",
        json={"email": "dave@example.com", "username": "dave", "password": "secret123"},
    )
    resp = client.post("/auth/token", data={"username": "dave", "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    resp = client.post("/auth/token", data={"username": "alice", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_get_me(client):
    token = register_and_login(client, "eve")
    resp = client.get("/auth/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["username"] == "eve"


# ── Products ──────────────────────────────────────────────────────────────────

def _create_admin(client: TestClient) -> str:
    """Register a user and manually set is_admin=True via DB."""
    from app import models
    from app.auth import hash_password
    from app.database import SessionLocal

    db = SessionLocal()
    existing = db.query(models.User).filter(models.User.username == "admin").first()
    if not existing:
        admin = models.User(
            email="admin@example.com",
            username="admin",
            hashed_password=hash_password("adminpass"),
            is_admin=True,
        )
        db.add(admin)
        db.commit()
    db.close()

    resp = client.post("/auth/token", data={"username": "admin", "password": "adminpass"})
    return resp.json()["access_token"]


def test_list_products_empty(client):
    resp = client.get("/products/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_product_requires_admin(client):
    token = register_and_login(client, "normaluser")
    resp = client.post(
        "/products/",
        json={"name": "Widget", "price": 9.99, "stock": 10},
        headers=auth_headers(token),
    )
    assert resp.status_code == 403


def test_create_product_as_admin(client):
    token = _create_admin(client)
    resp = client.post(
        "/products/",
        json={"name": "Gadget", "description": "A cool gadget", "price": 19.99, "stock": 5},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Gadget"
    assert data["price"] == 19.99


def test_get_product(client):
    admin_token = _create_admin(client)
    create_resp = client.post(
        "/products/",
        json={"name": "Thingamajig", "price": 4.99, "stock": 20},
        headers=auth_headers(admin_token),
    )
    product_id = create_resp.json()["id"]
    resp = client.get(f"/products/{product_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == product_id


def test_get_product_not_found(client):
    resp = client.get("/products/99999")
    assert resp.status_code == 404


def test_update_product(client):
    admin_token = _create_admin(client)
    create_resp = client.post(
        "/products/",
        json={"name": "OldName", "price": 1.00, "stock": 3},
        headers=auth_headers(admin_token),
    )
    product_id = create_resp.json()["id"]
    resp = client.patch(
        f"/products/{product_id}",
        json={"name": "NewName", "price": 2.50},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "NewName"
    assert resp.json()["price"] == 2.50


# ── Cart ──────────────────────────────────────────────────────────────────────

def test_cart_add_and_view(client):
    admin_token = _create_admin(client)
    prod_resp = client.post(
        "/products/",
        json={"name": "CartItem", "price": 3.00, "stock": 10},
        headers=auth_headers(admin_token),
    )
    product_id = prod_resp.json()["id"]

    user_token = register_and_login(client, "shopper")
    resp = client.post(
        "/cart/",
        json={"product_id": product_id, "quantity": 2},
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 2

    cart_resp = client.get("/cart/", headers=auth_headers(user_token))
    assert cart_resp.status_code == 200
    assert len(cart_resp.json()) >= 1


def test_cart_insufficient_stock(client):
    admin_token = _create_admin(client)
    prod_resp = client.post(
        "/products/",
        json={"name": "LimitedItem", "price": 99.00, "stock": 1},
        headers=auth_headers(admin_token),
    )
    product_id = prod_resp.json()["id"]

    user_token = register_and_login(client, "buyer2")
    resp = client.post(
        "/cart/",
        json={"product_id": product_id, "quantity": 100},
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 400


def test_cart_remove_item(client):
    admin_token = _create_admin(client)
    prod_resp = client.post(
        "/products/",
        json={"name": "RemovableItem", "price": 5.00, "stock": 10},
        headers=auth_headers(admin_token),
    )
    product_id = prod_resp.json()["id"]

    user_token = register_and_login(client, "remover")
    add_resp = client.post(
        "/cart/",
        json={"product_id": product_id, "quantity": 1},
        headers=auth_headers(user_token),
    )
    item_id = add_resp.json()["id"]
    del_resp = client.delete(f"/cart/{item_id}", headers=auth_headers(user_token))
    assert del_resp.status_code == 204


# ── Orders ────────────────────────────────────────────────────────────────────

def test_create_order(client):
    admin_token = _create_admin(client)
    prod_resp = client.post(
        "/products/",
        json={"name": "OrderProduct", "price": 10.00, "stock": 10},
        headers=auth_headers(admin_token),
    )
    product_id = prod_resp.json()["id"]

    user_token = register_and_login(client, "orderer")
    client.post(
        "/cart/",
        json={"product_id": product_id, "quantity": 2},
        headers=auth_headers(user_token),
    )
    order_resp = client.post("/orders/", headers=auth_headers(user_token))
    assert order_resp.status_code == 201
    data = order_resp.json()
    assert data["total"] == 20.0
    assert data["status"] == "pending"
    assert len(data["items"]) == 1


def test_create_order_empty_cart(client):
    user_token = register_and_login(client, "emptycart")
    resp = client.post("/orders/", headers=auth_headers(user_token))
    assert resp.status_code == 400


def test_list_orders(client):
    user_token = register_and_login(client, "lister")
    resp = client.get("/orders/", headers=auth_headers(user_token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_order_not_found(client):
    user_token = register_and_login(client, "notfound")
    resp = client.get("/orders/99999", headers=auth_headers(user_token))
    assert resp.status_code == 404
