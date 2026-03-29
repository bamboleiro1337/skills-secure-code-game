# Buy Service

A lightweight e-commerce **buy service** built with **Python FastAPI** and **PostgreSQL**.

## Features

| Feature | Details |
|---|---|
| User registration & JWT login | `POST /auth/register`, `POST /auth/token` |
| Product catalogue | `GET /products/`, `GET /products/{id}` |
| Admin product management | `POST /products/`, `PATCH /products/{id}`, `DELETE /products/{id}` |
| Shopping cart | `GET /cart/`, `POST /cart/`, `DELETE /cart/{id}`, `DELETE /cart/` |
| Order placement | `POST /orders/` — creates an order from the active cart |
| Order history | `GET /orders/`, `GET /orders/{id}` |

## Quick Start (Docker)

```bash
cd buy-service
docker compose up --build
```

The API is now available at **http://localhost:8000**.  
Interactive documentation: **http://localhost:8000/docs**

## Local Development

```bash
cd buy-service
pip install -r requirements.txt
# Set environment variable or create a .env file:
export DATABASE_URL=postgresql://buyuser:buypass@localhost:5432/buydb
export SECRET_KEY=change-me-in-production-use-a-long-random-string
uvicorn app.main:app --reload
```

## Running Tests

Tests use an in-memory **SQLite** database — no PostgreSQL required.

```bash
cd buy-service
pip install -r requirements.txt
pytest tests/ -v
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://buyuser:buypass@localhost:5432/buydb` | PostgreSQL connection string |
| `SECRET_KEY` | `change-me-in-production-...` | JWT signing secret — **change in production** |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime |

## API Endpoints

### Auth

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/token` | Obtain a JWT access token |
| GET | `/auth/me` | Get current user info |

### Products

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/products/` | — | List active products |
| GET | `/products/{id}` | — | Get a product |
| POST | `/products/` | Admin | Create a product |
| PATCH | `/products/{id}` | Admin | Update a product |
| DELETE | `/products/{id}` | Admin | Deactivate a product |

### Cart

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/cart/` | User | View cart |
| POST | `/cart/` | User | Add item to cart |
| DELETE | `/cart/{id}` | User | Remove item from cart |
| DELETE | `/cart/` | User | Clear cart |

### Orders

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/orders/` | User | Create order from cart |
| GET | `/orders/` | User | List orders |
| GET | `/orders/{id}` | User | Get an order |
