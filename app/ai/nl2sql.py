"""AI piece: natural language to SQL for hotel search. Owner: Person 5.

Why: travelers ask in plain words ("4-star in Luxor under 1500 with free cancellation").
Then: POST /hotels/search runs the SQL with a READ-ONLY database user and logs it in nl_queries.
Only these may be queried: the hotel_best_price view and the offers table.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])

ALLOWED_TABLES = ("hotel_best_price", "offers")


class NL2SQLIn(BaseModel):
    question: str
    city_id: int | None = None
    examples: list[dict] = []  # [{"question": ..., "sql": ...}] from training_examples


class NL2SQLOut(BaseModel):
    sql: str


def to_sql(body: NL2SQLIn) -> NL2SQLOut:
    if settings.ai_mock:
        city_filter = f" WHERE city_id = {int(body.city_id)}" if body.city_id else ""
        return NL2SQLOut(sql=f"SELECT * FROM hotel_best_price{city_filter} ORDER BY min_price LIMIT 20")
    # TODO(Person 5): call the LLM with the schema + examples here.
    raise NotImplementedError


@router.post("/nl2sql", response_model=NL2SQLOut, summary="NL to SQL (AI)")
def nl2sql_route(body: NL2SQLIn) -> NL2SQLOut:
    return to_sql(body)
