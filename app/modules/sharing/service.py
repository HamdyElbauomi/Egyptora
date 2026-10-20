"""Summary numbers for a trip. Owner: Person 3.

Built from the same TripOut that GET /trips/{id} returns, so the summary always matches the Home screen.
"""

from app.modules.sharing.schemas import CitySummary, CostSplit, DaySummary, HotelBooking, SummaryOut
from app.modules.trips.models import Trip
from app.modules.trips.schemas import TripDayOut, TripOut


def split(days: list[TripDayOut]) -> CostSplit:
    hotels = sum(d.hotel.price_per_night for d in days if d.hotel)
    tickets = sum(i.cost for d in days for i in d.items if i.type == "visit")
    other = sum(i.cost for d in days for i in d.items if i.type != "visit")
    return CostSplit(hotels=hotels, tickets=tickets, other=other, total=hotels + tickets + other)


def hotel_bookings(days: list[TripDayOut]) -> list[HotelBooking]:
    bookings: dict[int, HotelBooking] = {}
    for d in days:
        if d.hotel is None:
            continue
        h = d.hotel
        if h.offer_id not in bookings:
            bookings[h.offer_id] = HotelBooking(
                offer_id=h.offer_id,
                hotel_name=h.hotel_name,
                company_id=h.company_id,
                company_name=h.company_name,
                room_type=h.room_type,
                nights=0,
                first_night=d.date,
                price_per_night=h.price_per_night,
                subtotal=0,
                free_cancellation=h.free_cancellation,
                breakfast_included=h.breakfast_included,
            )
        booking = bookings[h.offer_id]
        booking.nights += 1
        booking.subtotal += h.price_per_night
    return list(bookings.values())


def build_summary(trip: Trip, full: TripOut) -> SummaryOut:
    days = full.itinerary
    costs = split(days)
    city_order = [c.id for c in full.cities] + [d.city_id for d in days if d.city_id not in {c.id for c in full.cities}]
    cities = []
    for city_id in dict.fromkeys(city_order):
        city_days = [d for d in days if d.city_id == city_id]
        if city_days:
            cities.append(
                CitySummary(
                    city_id=city_id, city_name=city_days[0].city_name, days=len(city_days), costs=split(city_days)
                )
            )
    return SummaryOut(
        trip_id=full.id,
        title=full.title,
        status=full.status,
        start_date=full.start_date,
        end_date=full.end_date,
        days=full.days,
        nights_with_hotel=sum(1 for d in days if d.hotel),
        places_count=sum(1 for d in days for i in d.items if i.place_id),
        costs=costs,
        budget_total=full.budget_total,
        remaining=full.budget_total - costs.total if full.budget_total is not None else None,
        over_budget=full.over_budget,
        cities=cities,
        hotels=hotel_bookings(days),
        per_day=[
            DaySummary(
                day_number=d.day_number,
                date=d.date,
                city_name=d.city_name,
                hotel_name=d.hotel.hotel_name if d.hotel else None,
                visits=sum(1 for i in d.items if i.type == "visit"),
                costs=split([d]),
            )
            for d in days
        ],
        is_shared=trip.share_token is not None,
        share_token=trip.share_token,
    )
