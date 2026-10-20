"""Features C1, C2, C5 · Company sign up, profile, documents, reviews (company portal)."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.core.pagination import Page, PageParams, paginate_rows
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.core.storage import delete_file, save_document
from app.modules.accounts.models import User
from app.modules.companies.models import Company
from app.modules.companies.schemas import (
    CompanyOut,
    CompanyRegisteredOut,
    CompanyUpdateIn,
    ReviewInsightsOut,
    ReviewOut,
)
from app.modules.companies.service import company_of, review_insights, reviews_query, to_out, to_review_out

router = APIRouter(prefix="/company", tags=["C1-C2-C5 · Company account"])
company_role = require_role("company")
_email = TypeAdapter(EmailStr)


@router.post("/register", response_model=CompanyRegisteredOut, status_code=201)
async def register_company(
    license_file: UploadFile = File(..., description="Tourism license: PDF, JPEG, PNG or WebP, up to 10 MB"),
    owner_name: str = Form(..., min_length=2, max_length=120),
    email: str = Form(...),
    password: str = Form(..., min_length=8),
    company_name: str = Form(..., min_length=2, max_length=160),
    license_no: str = Form(..., min_length=3, max_length=80),
    phone: str | None = Form(None),
    website: str | None = Form(None),
    db: Session = Depends(get_db),
) -> CompanyRegisteredOut:
    """Why: tourism companies must apply before selling, with their license.
    Creates a login with role=company and a company with status=pending, and logs it in right away.
    Then: the company shows up in GET /admin/companies?status=pending for the admin to review."""
    try:
        email = _email.validate_python(email).lower()
    except ValidationError as exc:
        raise HTTPException(422, "email: not a valid email address") from exc
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    if db.scalar(select(Company.id).where(func.lower(Company.name) == company_name.strip().lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, f'A company named "{company_name}" already exists')

    user = User(name=owner_name, email=email, password_hash=hash_password(password), role="company")
    db.add(user)
    db.flush()
    license_url = await save_document(license_file, f"companies/{user.id}")
    company = Company(
        owner_user_id=user.id,
        name=company_name.strip(),
        license_no=license_no.strip(),
        license_doc_url=license_url,
        phone=phone,
        website=website,
        status="pending",
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return CompanyRegisteredOut(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
        role=user.role,
        company=to_out(company),
    )


@router.get("/me", response_model=CompanyOut)
def my_company(user: User = Depends(company_role), db: Session = Depends(get_db)) -> CompanyOut:
    """Why: the company sees whether it is pending, approved, rejected (with the reason) or suspended.
    Then: when approved, the portal unlocks offers."""
    return to_out(company_of(db, user))


@router.patch("/me", response_model=CompanyOut)
def update_my_company(
    body: CompanyUpdateIn, user: User = Depends(company_role), db: Session = Depends(get_db)
) -> CompanyOut:
    """Why: companies keep phone, website and social links current. Only the fields you send are changed.
    Then: travelers see these on GET /companies/{id}."""
    company = company_of(db, user)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(company, field, str(value) if value is not None else None)
    db.commit()
    db.refresh(company)
    return to_out(company)


@router.post("/me/documents", response_model=CompanyOut)
async def upload_document(
    file: UploadFile = File(..., description="New license: PDF, JPEG, PNG or WebP, up to 10 MB"),
    user: User = Depends(company_role),
    db: Session = Depends(get_db),
) -> CompanyOut:
    """Why: the license expired, or the admin rejected the company and asked for a better copy.
    Effect: replaces the license file. A rejected company goes back to pending so the admin reviews it again.
    Then: the admin sees the new file in GET /admin/companies/{id}."""
    company = company_of(db, user)
    new_url = await save_document(file, f"companies/{user.id}")
    old_url = company.license_doc_url
    company.license_doc_url = new_url
    if company.status == "rejected":
        company.status = "pending"
        company.reject_reason = None
    db.commit()
    db.refresh(company)
    delete_file(old_url)
    return to_out(company)


@router.get("/reviews", response_model=Page[ReviewOut])
def my_reviews(
    params: PageParams = Depends(), user: User = Depends(company_role), db: Session = Depends(get_db)
) -> Page[ReviewOut]:
    """Why: a company wants to see what travelers said about it, newest first, with each review's sentiment."""
    company = company_of(db, user)
    rows, total = paginate_rows(db, reviews_query(company.id), params)
    return Page(data=[to_review_out(*r) for r in rows], page=params.page, limit=params.limit, total=total)


@router.get("/reviews/insights", response_model=ReviewInsightsOut)
def my_review_insights(user: User = Depends(company_role), db: Session = Depends(get_db)) -> ReviewInsightsOut:
    """Why: the company sees what to fix: average rating, ratings 1-5, % positive comments,
    top complaints (from negative and neutral comments), trust score, and the latest negative reviews."""
    return review_insights(db, company_of(db, user))
