"""Response shape for the admin overview. Owner: Person 3."""

import datetime as dt

from pydantic import BaseModel, Field


class UserStats(BaseModel):
    travelers: int
    company_accounts: int
    admins: int
    new_last_7_days: int


class DayCount(BaseModel):
    date: dt.date
    trips: int


class CityShare(BaseModel):
    city_id: int
    city_name: str
    trips: int
    share: float = Field(description="Share of all trips that visit this city (0-1)")


class TripStats(BaseModel):
    total: int
    saved: int
    drafts: int
    shared: int
    created_last_7_days: int
    avg_days: float | None
    avg_total_cost: float | None
    per_day: list[DayCount] = Field(description="Trips created on each of the last 14 days, oldest first")


class CompanyStats(BaseModel):
    pending: int
    approved: int
    rejected: int
    suspended: int


class OfferStats(BaseModel):
    active: int
    paused: int
    flagged: int
    hotels_with_offers: int
    nights_booked_in_trips: int


class CatalogStats(BaseModel):
    cities: int
    places: int
    hotels: int


class ReviewStats(BaseModel):
    total: int
    average_rating: float | None


class AIStats(BaseModel):
    search_success_rate: float | None
    scan_recognition_rate: float | None  # recognized / all scans
    chat_keep_rate: float | None


class NeedsAttention(BaseModel):
    """The admin's to-do list, each with the screen that handles it."""

    pending_companies: int  # GET /admin/companies?status=pending
    low_price_offers: int  # GET /admin/offers (price_check = low, not flagged yet)
    scans_to_review: int  # GET /admin/ai/scans
    failed_searches: int  # GET /admin/ai/queries?status=failed (not fixed yet)


class StatsOut(BaseModel):
    users: UserStats
    trips: TripStats
    companies: CompanyStats
    offers: OfferStats
    catalog: CatalogStats
    reviews: ReviewStats
    ai: AIStats
    top_destinations: list[CityShare] = Field(description="Cities by how many trips visit them, top 5")
    needs_attention: NeedsAttention
