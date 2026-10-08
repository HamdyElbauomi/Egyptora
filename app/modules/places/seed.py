"""Seed: places with verified info for Cairo, Luxor and Aswan.

Facts are summarized from the linked Wikipedia articles. Ticket prices and opening hours change often,
so they are left empty: the admin fills the current official values from the admin console.
visit_minutes is a typical visit length, used by the trip planner to fit a day.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.models import City, Interest
from app.modules.places.models import Place, PlaceInterest

HISTORY, MUSEUMS, FOOD, NILE, MARKETS, RELIGIOUS, PHOTO = (
    "Ancient history",
    "Museums",
    "Food",
    "Nile and nature",
    "Markets and shopping",
    "Religious sites",
    "Photography",
)

WIKI = "https://en.wikipedia.org/wiki/"

PLACES = [
    # ---- Cairo ----
    dict(
        city="Cairo",
        name="Pyramids of Giza",
        type="monument",
        era="Old Kingdom, 4th Dynasty",
        short_description="The three great pyramids of Khufu, Khafre and Menkaure on the Giza Plateau.",
        verified_info=(
            "The Giza pyramid complex includes the Great Pyramid of Khufu, the Pyramid of Khafre and the "
            "Pyramid of Menkaure, built during Egypt's Fourth Dynasty (around 2600-2500 BC). The Great Pyramid "
            "is the oldest of the Seven Wonders of the Ancient World and the only one still largely intact."
        ),
        source_url=WIKI + "Giza_pyramid_complex",
        lat=29.9792,
        lng=31.1342,
        visit_minutes=180,
        recognition_label="giza_pyramids",
        interests=[HISTORY, PHOTO],
    ),
    dict(
        city="Cairo",
        name="Great Sphinx of Giza",
        type="monument",
        era="Old Kingdom, 4th Dynasty",
        short_description="Limestone statue of a reclining sphinx guarding the Giza Plateau.",
        verified_info=(
            "The Great Sphinx is a limestone statue of a reclining sphinx, a creature with a lion's body and "
            "a human head. It is generally believed to represent the pharaoh Khafre and to date from his "
            "reign in the Fourth Dynasty."
        ),
        source_url=WIKI + "Great_Sphinx_of_Giza",
        lat=29.9753,
        lng=31.1376,
        visit_minutes=45,
        recognition_label="great_sphinx",
        interests=[HISTORY, PHOTO],
    ),
    dict(
        city="Cairo",
        name="Egyptian Museum",
        type="museum",
        era="Opened 1902",
        short_description="The historic museum of Egyptian antiquities on Tahrir Square.",
        verified_info=(
            "The Egyptian Museum in Cairo opened in its current building on Tahrir Square in 1902. "
            "It holds one of the largest collections of ancient Egyptian antiquities in the world."
        ),
        source_url=WIKI + "Egyptian_Museum",
        lat=30.0478,
        lng=31.2336,
        visit_minutes=180,
        interests=[HISTORY, MUSEUMS],
    ),
    dict(
        city="Cairo",
        name="Khan el-Khalili",
        type="activity",
        era="Founded 1382",
        short_description="Historic bazaar in the heart of Islamic Cairo.",
        verified_info=(
            "Khan el-Khalili is a famous bazaar in the historic center of Cairo. It began as a caravanserai "
            "built in 1382 by the emir Jarkas al-Khalili and grew into one of the city's main shopping districts."
        ),
        source_url=WIKI + "Khan_el-Khalili",
        lat=30.0477,
        lng=31.2623,
        visit_minutes=120,
        interests=[MARKETS, FOOD, PHOTO],
    ),
    dict(
        city="Cairo",
        name="Cairo Citadel",
        type="monument",
        era="Built 1176-1183",
        short_description="Salah ad-Din's hilltop fortress, home to the Mosque of Muhammad Ali.",
        verified_info=(
            "The Citadel of Cairo is a medieval Islamic fortification built by Salah ad-Din (Saladin) between "
            "1176 and 1183. Inside stands the Mosque of Muhammad Ali, built between 1830 and 1848."
        ),
        source_url=WIKI + "Cairo_Citadel",
        lat=30.0287,
        lng=31.2599,
        visit_minutes=120,
        recognition_label="cairo_citadel",
        interests=[HISTORY, RELIGIOUS, PHOTO],
    ),
    dict(
        city="Cairo",
        name="Al-Azhar Mosque",
        type="monument",
        era="Founded 970",
        short_description="One of the oldest mosques in Cairo and a historic center of learning.",
        verified_info=(
            "Al-Azhar Mosque was founded in 970 by the Fatimid dynasty, shortly after the founding of Cairo. "
            "It became one of the most important centers of Islamic learning in the world."
        ),
        source_url=WIKI + "Al-Azhar_Mosque",
        lat=30.0458,
        lng=31.2627,
        visit_minutes=45,
        interests=[RELIGIOUS, HISTORY],
    ),
    # ---- Luxor ----
    dict(
        city="Luxor",
        name="Karnak Temple Complex",
        type="monument",
        era="Middle Kingdom to Ptolemaic period",
        short_description="Vast complex of temples dedicated mainly to Amun-Ra.",
        verified_info=(
            "Karnak is a vast complex of temples, chapels and pylons built and expanded over about 2,000 years, "
            "from the Middle Kingdom to the Ptolemaic period. It was dedicated mainly to Amun-Ra. "
            "Its Great Hypostyle Hall contains 134 massive columns."
        ),
        source_url=WIKI + "Karnak",
        lat=25.7188,
        lng=32.6573,
        visit_minutes=180,
        recognition_label="karnak_temple",
        interests=[HISTORY, RELIGIOUS, PHOTO],
    ),
    dict(
        city="Luxor",
        name="Luxor Temple",
        type="monument",
        era="New Kingdom, about 1400 BC",
        short_description="Riverside temple linked to Karnak by the Avenue of Sphinxes.",
        verified_info=(
            "Luxor Temple stands on the east bank of the Nile. It was built mainly under Amenhotep III and "
            "Ramesses II, and it was connected to Karnak by a long avenue lined with sphinxes."
        ),
        source_url=WIKI + "Luxor_Temple",
        lat=25.6995,
        lng=32.6391,
        visit_minutes=90,
        recognition_label="luxor_temple",
        interests=[HISTORY, PHOTO],
    ),
    dict(
        city="Luxor",
        name="Valley of the Kings",
        type="monument",
        era="New Kingdom, 16th-11th century BC",
        short_description="Royal burial valley on the West Bank, including Tutankhamun's tomb.",
        verified_info=(
            "The Valley of the Kings on the West Bank of Luxor was the burial place of pharaohs of the New Kingdom. "
            "It contains more than 60 tombs, including the tomb of Tutankhamun (KV62), discovered by "
            "Howard Carter in 1922."
        ),
        source_url=WIKI + "Valley_of_the_Kings",
        lat=25.7402,
        lng=32.6014,
        visit_minutes=180,
        recognition_label="valley_of_the_kings",
        interests=[HISTORY],
    ),
    dict(
        city="Luxor",
        name="Temple of Hatshepsut",
        type="monument",
        era="New Kingdom, 18th Dynasty",
        short_description="Terraced mortuary temple of Queen Hatshepsut at Deir el-Bahari.",
        verified_info=(
            "The mortuary temple of Hatshepsut, one of the few female pharaohs, is built into the cliffs at "
            "Deir el-Bahari on the West Bank. Its terraced design is attributed to her official Senenmut."
        ),
        source_url=WIKI + "Mortuary_Temple_of_Hatshepsut",
        lat=25.7380,
        lng=32.6065,
        visit_minutes=90,
        recognition_label="hatshepsut_temple",
        interests=[HISTORY, PHOTO],
    ),
    dict(
        city="Luxor",
        name="Colossi of Memnon",
        type="monument",
        era="New Kingdom, 18th Dynasty",
        short_description="Two giant seated statues of Amenhotep III on the West Bank.",
        verified_info=(
            "The Colossi of Memnon are two massive stone statues of the pharaoh Amenhotep III, each about "
            "18 meters tall. They once stood at the entrance of his mortuary temple."
        ),
        source_url=WIKI + "Colossi_of_Memnon",
        lat=25.7206,
        lng=32.6104,
        visit_minutes=20,
        recognition_label="colossi_of_memnon",
        interests=[HISTORY, PHOTO],
    ),
    dict(
        city="Luxor",
        name="Luxor Museum",
        type="museum",
        era="Opened 1975",
        short_description="Compact museum of finds from the Theban temples and necropolis.",
        verified_info=(
            "The Luxor Museum, opened in 1975 on the Nile corniche, displays artifacts found in the temples "
            "and tombs of ancient Thebes."
        ),
        source_url=WIKI + "Luxor_Museum",
        lat=25.7074,
        lng=32.6440,
        visit_minutes=90,
        interests=[MUSEUMS, HISTORY],
    ),
    # ---- Aswan ----
    dict(
        city="Aswan",
        name="Philae Temple",
        type="monument",
        era="Ptolemaic and Roman periods",
        short_description="Island temple of Isis, moved stone by stone to Agilkia Island.",
        verified_info=(
            "The Philae temple complex was dedicated mainly to the goddess Isis. To save it from flooding after "
            "the Aswan dams were built, it was dismantled and rebuilt on nearby Agilkia Island, a project "
            "completed in 1980."
        ),
        source_url=WIKI + "Philae",
        lat=24.0250,
        lng=32.8844,
        visit_minutes=120,
        recognition_label="philae_temple",
        interests=[HISTORY, NILE, PHOTO],
    ),
    dict(
        city="Aswan",
        name="Abu Simbel Temples",
        type="monument",
        era="New Kingdom, 13th century BC",
        short_description="Rock-cut temples of Ramesses II, a day trip south of Aswan.",
        verified_info=(
            "Abu Simbel consists of two rock-cut temples built by Ramesses II in the 13th century BC. "
            "Between 1964 and 1968 the temples were cut into blocks and moved to higher ground to save them "
            "from the rising waters of Lake Nasser."
        ),
        source_url=WIKI + "Abu_Simbel",
        lat=22.3372,
        lng=31.6258,
        visit_minutes=180,
        recognition_label="abu_simbel",
        interests=[HISTORY, PHOTO],
    ),
    dict(
        city="Aswan",
        name="Unfinished Obelisk",
        type="monument",
        era="New Kingdom",
        short_description="A giant obelisk abandoned in the ancient granite quarries.",
        verified_info=(
            "The Unfinished Obelisk lies in an ancient granite quarry in Aswan. Had it been completed, it would "
            "have been about 42 meters tall, larger than any obelisk ever raised. It was abandoned after "
            "cracks appeared in the stone."
        ),
        source_url=WIKI + "Unfinished_obelisk",
        lat=24.0763,
        lng=32.8963,
        visit_minutes=45,
        recognition_label="unfinished_obelisk",
        interests=[HISTORY],
    ),
    dict(
        city="Aswan",
        name="Aswan High Dam",
        type="activity",
        era="Built 1960-1970",
        short_description="The modern dam that created Lake Nasser.",
        verified_info=(
            "The Aswan High Dam was built between 1960 and 1970 across the Nile. It created Lake Nasser, "
            "one of the largest artificial lakes in the world."
        ),
        source_url=WIKI + "Aswan_Dam",
        lat=23.9707,
        lng=32.8775,
        visit_minutes=45,
        interests=[NILE],
    ),
    dict(
        city="Aswan",
        name="Elephantine Island",
        type="nature",
        era="Inhabited since prehistoric times",
        short_description="Nile island with ancient ruins and Nubian villages.",
        verified_info=(
            "Elephantine is an island in the Nile at Aswan. In ancient times it marked Egypt's southern border, "
            "and it holds the ruins of temples including the Temple of Khnum."
        ),
        source_url=WIKI + "Elephantine",
        lat=24.0870,
        lng=32.8870,
        visit_minutes=120,
        interests=[NILE, HISTORY, PHOTO],
    ),
]


def seed(db: Session) -> None:
    cities = {c.name: c.id for c in db.scalars(select(City))}
    interests = {i.name: i.id for i in db.scalars(select(Interest))}
    for data in PLACES:
        data = dict(data)
        city_name = data.pop("city")
        interest_names = data.pop("interests")
        if city_name not in cities:
            continue  # cities are seeded by the catalog seed, which runs first
        if db.scalar(select(Place.id).where(Place.name == data["name"])):
            continue
        place = Place(city_id=cities[city_name], **data)
        db.add(place)
        db.flush()
        for name in interest_names:
            if name in interests:
                db.add(PlaceInterest(place_id=place.id, interest_id=interests[name]))
