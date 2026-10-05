"""Request/response shapes for companies and reviews. Owner: Person 1."""

from pydantic import BaseModel, EmailStr, Field


class CompanyRegisterIn(BaseModel):
    # Sent as multipart form fields together with the license file.
    owner_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    company_name: str
    license_no: str
    phone: str | None = None
    website: str | None = None
    facebook_url: str | None = None
    instagram_url: str | None = None


class CompanyUpdateIn(BaseModel):
    phone: str | None = None
    website: str | None = None
    facebook_url: str | None = None
    instagram_url: str | None = None


class ApproveChecklistIn(BaseModel):
    license_verified: bool
    google_rating: float | None = Field(default=None, ge=0, le=5)
    years_active: int | None = Field(default=None, ge=0)
    social_presence: int = Field(ge=0, le=5, description="Admin's 0-5 judgment of social pages")


class RejectIn(BaseModel):
    reason: str


class AnalyzeReviewsIn(BaseModel):
    reviews: list[str]


class ReviewIn(BaseModel):
    trip_id: int | None = None
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
