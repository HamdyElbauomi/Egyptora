"""Imports every model so SQLAlchemy and Alembic see the full schema.

If you add a new models file, import it here.
"""

from app.core.database import Base
from app.modules.accounts.models import User
from app.modules.ai_quality.models import NLQuery, TrainingExample
from app.modules.catalog.models import City, Interest
from app.modules.chat.models import ChatMessage, TripChange
from app.modules.companies.models import Company, Review
from app.modules.hotels.models import Hotel
from app.modules.offers.models import Offer, PriceAlert, hotel_best_price
from app.modules.places.models import Place, PlaceImage, PlaceInterest, Scan
from app.modules.trips.models import Trip, TripCity, TripDay, TripInterest, TripItem

__all__ = [
    "Base",
    "ChatMessage",
    "City",
    "Company",
    "Hotel",
    "Interest",
    "NLQuery",
    "Offer",
    "Place",
    "PlaceImage",
    "PlaceInterest",
    "PriceAlert",
    "Review",
    "Scan",
    "TrainingExample",
    "Trip",
    "TripChange",
    "TripCity",
    "TripDay",
    "TripInterest",
    "TripItem",
    "User",
    "hotel_best_price",
]
