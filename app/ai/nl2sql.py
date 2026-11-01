"""AI piece: natural language to SQL for hotel search. Owner: Person 5.

Why: travelers ask in plain words ("4-star in Luxor under 1500 with free cancellation").
Then: POST /hotels/search checks the SQL (ai_quality/service.py), runs it on a READ-ONLY connection
and logs it in nl_queries.

Contract for the real LLM:
- Only these may be queried: the hotel_best_price view and the offers table (see SCHEMA).
- One SELECT, no CTEs, no comments, and it must return a hotel_id column.
- `examples` are admin-fixed questions with their correct SQL: follow them.

USE_LLM=true asks the language model (llm_sql). rules_sql() below is the default and the fallback:
it understands city names (English and Arabic), stars, a max price,
free cancellation, breakfast, and cheap/luxury ordering. A question that matches a training example
exactly uses that example's SQL.
"""

import json
import re

from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.cities import mentions_city
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])

ALLOWED_TABLES = ("hotel_best_price", "offers")
SCHEMA = """
hotel_best_price(hotel_id, city_id, hotel_name, stars, min_price, offers_count, best_company_id)
offers(id, hotel_id, company_id, room_type, price_per_night, breakfast_included, free_cancellation,
       cancellation_days, valid_from, valid_to, status)  -- status 'active' = on sale
"""

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


class CityRef(BaseModel):
    id: int
    name: str


class NL2SQLIn(BaseModel):
    question: str
    city_id: int | None = None  # a city already chosen by the screen (or the trip)
    cities: list[CityRef] = []  # every city, so names in the question can be matched
    examples: list[dict] = []  # [{"question": ..., "sql": ...}] from training_examples


class NL2SQLOut(BaseModel):
    sql: str
    understood: str | None = None  # plain words of what was searched, shown to the traveler


def rules_sql(body: NL2SQLIn) -> NL2SQLOut:
    q = body.question.lower().translate(ARABIC_DIGITS)
    for example in body.examples:
        if example["question"].strip().lower() == q.strip():
            return NL2SQLOut(sql=example["sql"], understood="A search our team checked by hand")

    where, words, noun = [], [], "Hotels"
    city = next(
        (c for c in body.cities if mentions_city(c.name, q)),
        None,
    )
    city_id = city.id if city else body.city_id
    if city_id:
        where.append(f"city_id = {int(city_id)}")
        words.append(f"in {city.name}" if city else "in your city")

    stars = re.search(r"(\d)\s*[- ]?\s*(?:stars?|نجوم|نجمة|نجمات|★)", q)
    if stars:
        where.append(f"stars = {int(stars.group(1))}")
        noun = f"{stars.group(1)}-star hotels"

    price = re.search(r"(?:under|below|less than|max|up to|cheaper than|تحت|أقل من|اقل من|بأقل من)\s*(\d[\d,]*)", q)
    if price:
        amount = int(price.group(1).replace(",", ""))
        where.append(f"min_price <= {amount}")
        words.append(f"under {amount} EGP/night")

    offer_rules = []
    if "free cancel" in q or "إلغاء مجاني" in q or "الغاء مجاني" in q:
        offer_rules.append("free_cancellation")
        words.append("with free cancellation")
    if "breakfast" in q or "فطار" in q or "إفطار" in q or "افطار" in q:
        offer_rules.append("breakfast_included")
        words.append("with breakfast")
    if offer_rules:
        where.append(
            "hotel_id IN (SELECT hotel_id FROM offers WHERE status = 'active' AND " + " AND ".join(offer_rules) + ")"
        )

    if any(w in q for w in ("luxury", "best", "fancy", "فخم", "أحسن", "احسن")):
        order = "stars DESC NULLS LAST, min_price ASC"
    else:
        order = "min_price ASC"
    sql = "SELECT hotel_id, hotel_name, stars, min_price FROM hotel_best_price"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY {order} LIMIT 20"
    return NL2SQLOut(sql=sql, understood=" ".join([noun, *words]) if where else "All hotels, cheapest first")


SQL_SYSTEM = """You turn a traveler's hotel search into ONE PostgreSQL SELECT.

Schema (nothing else exists):
{schema}
Rules:
- Query only hotel_best_price; use offers only inside a sub-query (hotel_id IN (SELECT hotel_id FROM offers ...)).
- The result MUST include a hotel_id column. Order sensibly and end with LIMIT 20.
- Use city ids from the cities list; never compare city names.
- One statement, no comments, no WITH, no semicolons, no other tables or functions.
- "understood": a short English summary of what you searched for, like "4-star hotels in Luxor under 1500 EGP/night".
Reply with a JSON object only: {{"sql": "...", "understood": "..."}}"""


def llm_sql(body: NL2SQLIn) -> NL2SQLOut:
    from app.ai.llm import LLMError, complete_json

    payload = {
        "question": body.question,
        "city_already_chosen": body.city_id,
        "cities": [{"id": c.id, "name": c.name} for c in body.cities],
        "checked_examples": body.examples[:8],
    }
    system = SQL_SYSTEM.format(schema=SCHEMA.strip())
    out = complete_json(system, json.dumps(payload, ensure_ascii=False), max_tokens=400)
    sql, understood = out.get("sql"), out.get("understood")
    if not isinstance(sql, str) or not sql.strip().lower().startswith("select"):
        raise LLMError("the model did not write a SELECT")
    if not re.search(r"\bhotel_id\b", sql.lower().split(" from ", 1)[0]):
        raise LLMError("the SELECT has no hotel_id column")
    return NL2SQLOut(sql=sql.strip().rstrip(";"), understood=understood if isinstance(understood, str) else None)


def exact_example(body: NL2SQLIn) -> NL2SQLOut | None:
    q = body.question.lower().strip()
    for example in body.examples:
        if example["question"].strip().lower() == q:
            return NL2SQLOut(sql=example["sql"], understood="A search our team checked by hand")
    return None


def to_sql(body: NL2SQLIn) -> NL2SQLOut:
    """A question the admin already fixed uses that SQL. Otherwise the model writes it (USE_LLM=true);
    if the model fails or writes SQL our guard would refuse, the rules below answer instead."""
    if settings.llm_ready and exact_example(body) is None:
        from app.ai.llm import LLMError
        from app.modules.ai_quality.service import UnsafeSQL, check_sql

        try:
            out = llm_sql(body)
            check_sql(out.sql)
            return out
        except (LLMError, UnsafeSQL):
            pass
    return rules_sql(body)


@router.post("/nl2sql", response_model=NL2SQLOut, summary="NL to SQL (AI)")
def nl2sql_route(body: NL2SQLIn) -> NL2SQLOut:
    return to_sql(body)
