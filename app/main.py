#application entry point.
import logging

from fastapi import FastAPI
from pythonjsonlogger.json import JsonFormatter # type: ignore

from app.routers import auth, bookings, centres, payments


def configure_logging() -> None:
    """Write one JSON object per log line for easier searching in Docker logs."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


configure_logging()
app = FastAPI(title="EVE Healthcare API", version="0.1.0")

app.include_router(auth.router)
app.include_router(centres.router)
app.include_router(bookings.router)
app.include_router(payments.router)

@app.get("/")
def root():
    return {"message": "Welcome to EVE Healthcare API. Please refer to the documentation at /docs for available endpoints."}

@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Simple process health check; database readiness will be added later."""
    return {"status": "ok"}