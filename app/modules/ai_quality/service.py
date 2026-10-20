"""NL search pipeline and its safety checks. Owner: Person 5.

AI-written SQL is never trusted:
1. check_sql(): one SELECT, no comments, no write/admin keywords, no system tables or functions,
   and only the tables in nl2sql.ALLOWED_TABLES.
2. run_readonly(): a separate connection (settings.readonly_database_url when set), inside a
   READ ONLY transaction with a 3-second statement timeout, and at most MAX_ROWS rows.
"""

import re
import time
from functools import lru_cache

from sqlalchemy import Engine, create_engine, select, text
from sqlalchemy.orm import Session

from app.ai.nl2sql import ALLOWED_TABLES, CityRef, NL2SQLIn, to_sql
from app.core.config import settings
from app.modules.ai_quality.models import NLQuery, TrainingExample
from app.modules.catalog.models import City
from app.modules.hotels.models import Hotel
from app.modules.hotels.schemas import HotelCardOut
from app.modules.hotels.service import cards_query, to_card

MAX_ROWS = 50
TIMEOUT_MS = 3000
EXAMPLES_LIMIT = 30

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|merge|call|execute|vacuum|analyze"
    r"|set|reset|lock|listen|notify|unlisten|comment|security|into|dblink|with)\b"
    r"|\bpg_\w+|\blo_\w+|information_schema",
    re.IGNORECASE,
)
TABLE_REF = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][\w.\"]*)", re.IGNORECASE)


class UnsafeSQL(Exception):
    pass


def check_sql(sql: str) -> str:
    """Returns the cleaned SQL, or raises UnsafeSQL with the reason."""
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        raise UnsafeSQL("empty SQL")
    if ";" in cleaned:
        raise UnsafeSQL("only one statement is allowed")
    if "--" in cleaned or "/*" in cleaned:
        raise UnsafeSQL("comments are not allowed")
    if not re.match(r"^select\b", cleaned, re.IGNORECASE):
        raise UnsafeSQL("only SELECT is allowed")
    bad = FORBIDDEN.search(cleaned)
    if bad:
        raise UnsafeSQL(f'"{bad.group(0)}" is not allowed')
    tables = {t.strip('"').lower() for t in TABLE_REF.findall(cleaned)}
    if not tables:
        raise UnsafeSQL("no table to read from")
    outside = sorted(tables - set(ALLOWED_TABLES))
    if outside:
        raise UnsafeSQL(f"only {', '.join(ALLOWED_TABLES)} can be queried, not {', '.join(outside)}")
    return cleaned


@lru_cache
def readonly_engine() -> Engine:
    return create_engine(settings.readonly_database_url or settings.database_url, pool_pre_ping=True)


def run_readonly(sql: str) -> list[dict]:
    """Runs checked SQL safely. Rows must include hotel_id. Raises UnsafeSQL or a database error."""
    safe = check_sql(sql)
    with readonly_engine().connect() as conn, conn.begin():
        conn.execute(text("SET TRANSACTION READ ONLY"))
        conn.execute(text(f"SET LOCAL statement_timeout = {TIMEOUT_MS}"))
        rows = [dict(r) for r in conn.execute(text(f"SELECT * FROM ({safe}) AS q LIMIT {MAX_ROWS}")).mappings()]
    if rows and "hotel_id" not in rows[0]:
        raise UnsafeSQL("the SQL must return a hotel_id column")
    return rows


def hotel_ids_in_order(rows: list[dict]) -> list[int]:
    return list(dict.fromkeys(int(r["hotel_id"]) for r in rows if r.get("hotel_id") is not None))


def cards_for_ids(db: Session, hotel_ids: list[int]) -> list[HotelCardOut]:
    if not hotel_ids:
        return []
    stmt, _ = cards_query()
    cards = {row[0].id: to_card(*row) for row in db.execute(stmt.where(Hotel.id.in_(hotel_ids))).all()}
    return [cards[i] for i in hotel_ids if i in cards]


def training_examples(db: Session) -> list[dict]:
    rows = db.scalars(select(TrainingExample).order_by(TrainingExample.id.desc()).limit(EXAMPLES_LIMIT))
    return [{"question": e.question, "sql": e.sql} for e in rows]


def search(db: Session, user_id: int | None, question: str, city_id: int | None):
    """Runs the whole pipeline and logs it. Returns (NLQuery, cards, understood)."""
    started = time.perf_counter()
    cities = [CityRef(id=i, name=n) for i, n in db.execute(select(City.id, City.name)).all()]
    log = NLQuery(user_id=user_id, question=question)
    understood, cards = None, []
    try:
        out = to_sql(NL2SQLIn(question=question, city_id=city_id, cities=cities, examples=training_examples(db)))
        log.generated_sql = out.sql
        understood = out.understood
        rows = run_readonly(out.sql)
        cards = cards_for_ids(db, hotel_ids_in_order(rows))
        log.result_count = len(cards)
        # No results is not an error, but it often means the question was misunderstood: flag it for review.
        log.status = "ok" if cards else "flagged"
    except Exception as exc:  # noqa: BLE001 - any AI or SQL failure becomes a logged failed query
        log.status = "failed"
        log.error = f"{type(exc).__name__}: {exc}"[:1000]
    log.latency_ms = int((time.perf_counter() - started) * 1000)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log, cards, understood
