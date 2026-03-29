from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import cart, orders, products, users


@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Buy Service",
    description="A simple e-commerce buy service built with FastAPI and PostgreSQL.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "buy-service"}
