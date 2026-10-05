"""Trip generation logic. Owner: Person 2.

Steps for generate_trip():
1. Resolve cities (body.city_ids, or suggestions when body.suggest is true).
2. Collect candidate places for those cities and interests (Person 4's places + place_interests).
3. Collect the best offers per city (Person 6: app/modules/offers/service.py -> best_offers_for_cities).
4. Call app/ai/planner.py -> plan_trip().
5. Save trips, trip_interests, trip_cities, trip_days, trip_items.
6. recalculate_total() from totals.py, commit, return the full trip.
"""

from sqlalchemy.orm import Session

from app.modules.accounts.models import User
from app.modules.trips.schemas import GenerateTripIn


def generate_trip(db: Session, user: User, body: GenerateTripIn):
    raise NotImplementedError("TODO(Person 2)")
