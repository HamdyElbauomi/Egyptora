"""Finding a city in what a traveler typed. Shared by the rule-based chat agent and hotel search.

A city matches by its full name, by any part of a joined name ("Cairo & Giza" -> "cairo", "giza"),
or by a common other spelling (English short forms and Arabic).
"""

CITY_ALIASES: dict[str, tuple[str, ...]] = {
    "cairo": ("القاهرة", "القاهره"),
    "giza": ("الجيزة", "الجيزه"),
    "luxor": ("الأقصر", "الاقصر"),
    "aswan": ("أسوان", "اسوان"),
    "alexandria": ("alex", "الإسكندرية", "الاسكندرية", "اسكندرية", "إسكندرية"),
    "hurghada": ("الغردقة", "الغردقه"),
    "sharm el-sheikh": ("sharm", "شرم"),
    "dahab": ("دهب",),
    "siwa oasis": ("siwa", "سيوة", "سيوه"),
    "fayoum": ("faiyum", "fayum", "الفيوم"),
}


def name_parts(city_name: str) -> list[str]:
    """ "Cairo & Giza" -> ["cairo & giza", "cairo", "giza"]"""
    full = city_name.lower().strip()
    parts = [p.strip() for p in full.split("&")] if "&" in full else []
    return [full, *[p for p in parts if p]]


def mentions_city(city_name: str, text: str) -> bool:
    """True when `text` (already lower-cased) names this city in any accepted form."""
    for part in name_parts(city_name):
        if part in text or any(alias in text for alias in CITY_ALIASES.get(part, ())):
            return True
    return False
