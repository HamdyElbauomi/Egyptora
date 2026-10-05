"""Features C1, C2, C5 · Company sign up, profile, reviews (company portal). Owner: Person 1."""

from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.companies.schemas import CompanyUpdateIn

router = APIRouter(prefix="/company", tags=["C1-C2-C5 · Company account"])
OWNER = "Person 1"


@router.post("/register", status_code=201)
async def register_company(
    license_file: UploadFile,
    owner_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    company_name: str = Form(...),
    license_no: str = Form(...),
    phone: str | None = Form(None),
    website: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """Why: tourism companies must apply before selling, with their license.
    Then: creates a user with role=company and a pending company that shows up in GET /admin/companies."""
    raise not_implemented(OWNER)


@router.get("/me")
def my_company(user: User = Depends(require_role("company")), db: Session = Depends(get_db)):
    """Why: the company sees whether it is pending, approved or rejected.
    Then: when approved, the portal unlocks offers (Person 6)."""
    raise not_implemented(OWNER)


@router.patch("/me")
def update_my_company(
    body: CompanyUpdateIn, user: User = Depends(require_role("company")), db: Session = Depends(get_db)
):
    """Why: companies keep phone, website and social links current.
    Then: travelers see these on GET /companies/{id}."""
    raise not_implemented(OWNER)


@router.post("/me/documents", status_code=201)
async def upload_document(
    file: UploadFile, user: User = Depends(require_role("company")), db: Session = Depends(get_db)
):
    """Why: the license expires or the admin asks for a better copy.
    Then: the admin reviews it in GET /admin/companies/{id}."""
    raise not_implemented(OWNER)


@router.get("/reviews")
def my_reviews(user: User = Depends(require_role("company")), db: Session = Depends(get_db)):
    """Why: a company wants to see what travelers said about it.
    Then: /company/reviews/insights summarizes these."""
    raise not_implemented(OWNER)


@router.get("/reviews/insights")
def my_review_insights(user: User = Depends(require_role("company")), db: Session = Depends(get_db)):
    """Why: reading every review is slow, so companies get % positive and top complaints (app/ai/sentiment.py).
    Then: helps companies improve and keeps the trust score honest."""
    raise not_implemented(OWNER)
