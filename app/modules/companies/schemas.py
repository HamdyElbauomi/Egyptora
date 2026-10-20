"""Request/response shapes for companies and reviews."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.ai.sentiment import SentimentOut


class CompanyUpdateIn(BaseModel):
    """Only the fields you send are changed."""

    phone: str | None = Field(default=None, max_length=40, examples=["+20 100 000 0000"])
    website: HttpUrl | None = Field(default=None, examples=["https://sunrise-travel.example"])
    facebook_url: HttpUrl | None = None
    instagram_url: HttpUrl | None = None


class CompanyOut(BaseModel):
    """What the company itself sees in the portal."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    license_no: str | None
    license_doc_url: str | None
    phone: str | None
    website: str | None
    facebook_url: str | None
    instagram_url: str | None
    status: str
    reject_reason: str | None
    google_rating: float | None
    years_active: int | None
    initial_score: float | None
    trust_score: float | None
    reviews_count: int
    created_at: datetime
    approved_at: datetime | None


class CompanyRegisteredOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    company: CompanyOut


class CompanyAdminOut(CompanyOut):
    """What the admin sees: the company plus its owner and activity."""

    owner_user_id: int
    owner_name: str
    owner_email: str
    active_offers: int
    approved_by: int | None


class CompanyPublicOut(BaseModel):
    """What travelers see next to an offer. Only approved companies are public."""

    id: int
    name: str
    trust_score: float | None
    reviews_count: int
    years_active: int | None
    google_rating: float | None
    website: str | None
    facebook_url: str | None
    instagram_url: str | None


class ApproveChecklistIn(BaseModel):
    license_verified: bool = Field(description="The admin checked the tourism license is real and valid")
    google_rating: float | None = Field(default=None, ge=0, le=5, examples=[4.4])
    years_active: int | None = Field(default=None, ge=0, le=100, examples=[8])
    social_presence: int = Field(ge=0, le=5, description="Admin's 0-5 judgment of the company's social pages")


class ApproveOut(BaseModel):
    company: CompanyAdminOut
    initial_score: float
    trust_score: float


class RejectIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500, examples=["The license number does not match the document."])


class SuspendOut(BaseModel):
    company: CompanyAdminOut
    paused_offers: int


class AnalyzeReviewsIn(BaseModel):
    reviews: list[str] = Field(min_length=1, max_length=200)


class AnalyzeReviewsOut(SentimentOut):
    suggested_social_presence: int = Field(description="0-5, a starting point for the approve checklist")


class ReviewIn(BaseModel):
    trip_id: int | None = None
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewOut(BaseModel):
    """A review as travelers and the company see it: first name only, no trip or account details."""

    id: int
    company_id: int
    rating: int
    comment: str | None
    sentiment: str | None  # positive | neutral | negative (null when there is no comment)
    reviewer_name: str
    created_at: datetime


class ReviewAddedOut(BaseModel):
    review: ReviewOut
    trust_score: float | None  # the company's new trust score
    reviews_count: int


class ReviewInsightsOut(BaseModel):
    reviews_count: int
    average_rating: float | None
    rating_counts: dict[str, int]  # {"1": 0, ..., "5": 12}
    sentiment_counts: dict[str, int]  # {"positive": 9, "neutral": 2, "negative": 1}
    positive_share: float | None  # among reviews with a comment
    top_complaints: list[str]
    trust_score: float | None
    initial_score: float | None
    recent_negative: list[ReviewOut]
