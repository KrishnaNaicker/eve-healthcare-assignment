from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.dependencies import DbSession
from app.dependencies import require_admin
from app.models import DiagnosticCentre, DiagnosticTest, User
from app.schemas import CentreCreate, CentreResponse, CentreUpdate, PaginatedCentres, TestCreate, TestResponse, TestUpdate

router = APIRouter(prefix="/centres", tags=["diagnostic centres"])
tests_router = APIRouter(prefix="/tests", tags=["diagnostic tests"])


@router.get("/", response_model=PaginatedCentres)
def list_centres(db: DbSession, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)) -> PaginatedCentres:
    query = select(DiagnosticCentre).where(DiagnosticCentre.is_active.is_(True)).options(selectinload(DiagnosticCentre.tests)).order_by(DiagnosticCentre.id).offset(offset).limit(limit)
    items = list(db.scalars(query).all())
    total = db.scalar(select(func.count()).select_from(DiagnosticCentre).where(DiagnosticCentre.is_active.is_(True))) or 0
    return PaginatedCentres(items=items, offset=offset, limit=limit, total=total)


@router.post("/", response_model=CentreResponse, status_code=status.HTTP_201_CREATED)
def create_centre(payload: CentreCreate, db: DbSession, _: User = Depends(require_admin)) -> DiagnosticCentre:
    centre = DiagnosticCentre(name=payload.name.strip(), location=payload.location.strip())
    db.add(centre)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Centre name already exists") from exc
    db.refresh(centre)
    return centre


@router.get("/{centre_id}", response_model=CentreResponse)
def get_centre(centre_id: int, db: DbSession) -> DiagnosticCentre:
    centre = db.scalar(select(DiagnosticCentre).where(DiagnosticCentre.id == centre_id, DiagnosticCentre.is_active.is_(True)).options(selectinload(DiagnosticCentre.tests)))
    if centre is None:
        raise HTTPException(status_code=404, detail="Diagnostic centre not found")
    return centre


@router.patch("/{centre_id}", response_model=CentreResponse)
def update_centre(centre_id: int, payload: CentreUpdate, db: DbSession, _: User = Depends(require_admin)) -> DiagnosticCentre:
    centre = db.get(DiagnosticCentre, centre_id)
    if centre is None:
        raise HTTPException(status_code=404, detail="Diagnostic centre not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(centre, field, value.strip() if isinstance(value, str) else value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Centre name already exists") from exc
    db.refresh(centre)
    return centre


@router.delete("/{centre_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_centre(centre_id: int, db: DbSession, _: User = Depends(require_admin)) -> None:
    centre = db.get(DiagnosticCentre, centre_id)
    if centre is None:
        raise HTTPException(status_code=404, detail="Diagnostic centre not found")
    centre.is_active = False
    for test in centre.tests:
        test.is_active = False
    db.commit()


@router.get("/{centre_id}/tests", response_model=list[TestResponse])
def list_centre_tests(centre_id: int, db: DbSession) -> list[DiagnosticTest]:
    if db.scalar(select(DiagnosticCentre.id).where(DiagnosticCentre.id == centre_id, DiagnosticCentre.is_active.is_(True))) is None:
        raise HTTPException(status_code=404, detail="Diagnostic centre not found")
    return list(db.scalars(select(DiagnosticTest).where(DiagnosticTest.centre_id == centre_id, DiagnosticTest.is_active.is_(True)).order_by(DiagnosticTest.id)).all())


@router.post("/{centre_id}/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
def create_test(centre_id: int, payload: TestCreate, db: DbSession, _: User = Depends(require_admin)) -> DiagnosticTest:
    if db.scalar(select(DiagnosticCentre.id).where(DiagnosticCentre.id == centre_id, DiagnosticCentre.is_active.is_(True))) is None:
        raise HTTPException(status_code=404, detail="Diagnostic centre not found")
    test = DiagnosticTest(centre_id=centre_id, name=payload.name.strip(), description=payload.description, price=payload.price)
    db.add(test)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Test name already exists at this centre") from exc
    db.refresh(test)
    return test


@tests_router.get("/", response_model=list[TestResponse])
def list_tests(db: DbSession, centre_id: int | None = None) -> list[DiagnosticTest]:
    query = select(DiagnosticTest).where(DiagnosticTest.is_active.is_(True)).order_by(DiagnosticTest.id)
    if centre_id is not None:
        query = query.where(DiagnosticTest.centre_id == centre_id)
    return list(db.scalars(query).all())


@tests_router.patch("/{test_id}", response_model=TestResponse)
def update_test(test_id: int, payload: TestUpdate, db: DbSession, _: User = Depends(require_admin)) -> DiagnosticTest:
    test = db.get(DiagnosticTest, test_id)
    if test is None:
        raise HTTPException(status_code=404, detail="Diagnostic test not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(test, field, value.strip() if isinstance(value, str) else value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Test name already exists at this centre") from exc
    db.refresh(test)
    return test


@tests_router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_test(test_id: int, db: DbSession, _: User = Depends(require_admin)) -> None:
    test = db.get(DiagnosticTest, test_id)
    if test is None:
        raise HTTPException(status_code=404, detail="Diagnostic test not found")
    test.is_active = False
    db.commit()
