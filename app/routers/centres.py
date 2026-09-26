"""Diagnostic centre and offered-test routes; pagination shape is scaffolded."""

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/centres", tags=["centres and tests"])


@router.get("/")
def list_centres(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    """Placeholder response; offset/limit demonstrate bounded pagination inputs."""
    return {"items": [], "offset": offset, "limit": limit, "total": 0}


@router.get("/{centre_id}/tests")
def list_centre_tests(centre_id: int) -> None:
    """Placeholder: list the tests and prices offered by a centre."""
    raise HTTPException(status_code=501, detail="Centre tests are not implemented yet")
