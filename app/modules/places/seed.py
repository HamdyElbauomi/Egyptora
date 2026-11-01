"""Seed: places with verified info for the 9 seeded cities.

Facts are summarized from the linked Wikipedia articles. Ticket prices and opening hours change often,
so they are left empty: the admin fills the current official values from the admin console.
visit_minutes is a typical visit length, used by the trip planner to fit a day.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.models import City, Interest
from app.modules.places.models import Place, PlaceInterest

# The design's interests (catalog/seed.py). The first seed had finer ones; they map onto these.
HISTORY = MUSEUMS = RELIGIOUS = "History & monuments"
FOOD = MARKETS = "Food & markets"
NILE = CALM = "Calm & slow"
ADVENTURE = "Adventure"
SEA = "Sea & beaches"
ART = "Art & culture"
PHOTO = "Photography"
NIGHTS = "Nights out"

WIKI = "https://en.wikipedia.org/wiki/"

PLACES = [
    # ---- Cairo ----
    dict(
        city="Cairo & Giza",
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
        city="Cairo & Giza",
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
        city="Cairo & Giza",
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
        city="Cairo & Giza",
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
        city="Cairo & Giza",
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
        city="Cairo & Giza",
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
    # ---- Alexandria ----
    dict(
        city="Alexandria",
        name="Bibliotheca Alexandrina",
        type="museum",
        era="Opened 2002",
        short_description="Modern library and cultural center on the Mediterranean shore.",
        verified_info=(
            "The Bibliotheca Alexandrina is a major library and cultural center that opened in 2002. "
            "It commemorates the ancient Library of Alexandria, one of the largest libraries of the ancient world. "
            "Besides the main reading room it holds museums, exhibitions and a planetarium."
        ),
        source_url=WIKI + "Bibliotheca_Alexandrina",
        lat=31.2089,
        lng=29.9092,
        visit_minutes=120,
        interests=[HISTORY, ART, PHOTO],
    ),
    dict(
        city="Alexandria",
        name="Citadel of Qaitbay",
        type="monument",
        era="Mamluk period, 1477",
        short_description="15th-century sea fortress at the end of the Eastern Harbour.",
        verified_info=(
            "The Citadel of Qaitbay is a 15th-century defensive fortress built by Sultan Qaitbay in 1477. "
            "It stands on the site where the Lighthouse of Alexandria, one of the Seven Wonders of the Ancient World, "
            "once stood."
        ),
        source_url=WIKI + "Citadel_of_Qaitbay",
        lat=31.2140,
        lng=29.8856,
        visit_minutes=90,
        interests=[HISTORY, SEA, PHOTO],
    ),
    dict(
        city="Alexandria",
        name="Catacombs of Kom El Shoqafa",
        type="monument",
        era="Roman period, 2nd century AD",
        short_description="Underground tombs mixing Egyptian, Greek and Roman art.",
        verified_info=(
            "The Catacombs of Kom El Shoqafa are a Roman-era burial site from around the 2nd century AD, "
            "cut into the rock on several levels. Their decoration mixes Egyptian, Greek and Roman styles. "
            "They were rediscovered in 1900."
        ),
        source_url=WIKI + "Catacombs_of_Kom_El_Shoqafa",
        lat=31.1786,
        lng=29.8933,
        visit_minutes=60,
        interests=[HISTORY],
    ),
    dict(
        city="Alexandria",
        name="Montaza Palace Gardens",
        type="nature",
        era="Late 19th and early 20th century",
        short_description="Royal palace gardens and beaches on the eastern edge of the city.",
        verified_info=(
            "Montaza is a palace and large park in eastern Alexandria. Khedive Abbas II built the first palace, "
            "the Salamlek, in 1892, and King Fuad I added the larger Haramlik in 1932. "
            "The gardens run down to small beaches on the Mediterranean."
        ),
        source_url=WIKI + "Montaza_Palace",
        lat=31.2884,
        lng=30.0160,
        visit_minutes=120,
        interests=[CALM, SEA, PHOTO],
    ),
    # ---- Hurghada ----
    dict(
        city="Hurghada",
        name="Giftun Islands",
        type="nature",
        short_description="Protected islands with coral reefs, a short boat ride from Hurghada.",
        verified_info=(
            "The Giftun Islands are two islands in the Red Sea off Hurghada, inside a protected area. "
            "Boats from the city's marina take visitors to snorkel and dive on their coral reefs and to swim "
            "from their beaches."
        ),
        source_url=WIKI + "Giftun_Islands",
        lat=27.1950,
        lng=33.9500,
        visit_minutes=360,
        interests=[SEA, ADVENTURE, PHOTO],
    ),
    dict(
        city="Hurghada",
        name="Hurghada Marina",
        type="activity",
        short_description="Waterfront promenade with cafés, restaurants and boats.",
        verified_info=(
            "Hurghada grew from a small fishing village into one of Egypt's largest Red Sea resorts. "
            "Its marina is the starting point for boat trips and a busy place to eat and walk in the evening."
        ),
        source_url=WIKI + "Hurghada",
        lat=27.2290,
        lng=33.8460,
        visit_minutes=120,
        interests=[NIGHTS, FOOD, SEA],
    ),
    dict(
        city="Hurghada",
        name="El Dahar Old Town",
        type="food",
        short_description="The old center of Hurghada, with its market and local food.",
        verified_info=(
            "El Dahar is the oldest part of Hurghada, away from the resort strip. "
            "Its market streets sell spices, fabrics and souvenirs, and it has small local restaurants."
        ),
        source_url=WIKI + "Hurghada",
        lat=27.2580,
        lng=33.8120,
        visit_minutes=90,
        interests=[FOOD, ART],
    ),
    dict(
        city="Hurghada",
        name="Eastern Desert Safari",
        type="activity",
        short_description="Jeep or quad trip into the desert hills behind the coast.",
        verified_info=(
            "The Eastern Desert is the part of the Sahara between the Nile and the Red Sea. "
            "Its mountains and wadis start just behind Hurghada, and safari trips visit Bedouin camps there."
        ),
        source_url=WIKI + "Eastern_Desert",
        lat=27.1500,
        lng=33.6500,
        visit_minutes=240,
        interests=[ADVENTURE, PHOTO],
    ),
    # ---- Sharm El-Sheikh ----
    dict(
        city="Sharm El-Sheikh",
        name="Ras Muhammad National Park",
        type="nature",
        era="Protected since 1983",
        short_description="Egypt's first national park, with famous coral reefs.",
        verified_info=(
            "Ras Muhammad, at the southern tip of the Sinai Peninsula, was declared Egypt's first national park "
            "in 1983. Its coral reefs, including Shark Reef and Yolanda Reef, are among the best-known dive sites "
            "in the Red Sea."
        ),
        source_url=WIKI + "Ras_Muhammad_National_Park",
        lat=27.7300,
        lng=34.2500,
        visit_minutes=300,
        interests=[SEA, ADVENTURE, PHOTO],
    ),
    dict(
        city="Sharm El-Sheikh",
        name="Naama Bay",
        type="activity",
        short_description="Sheltered bay and the busiest promenade in Sharm.",
        verified_info=(
            "Naama Bay is a natural bay north of the old town of Sharm El-Sheikh. "
            "Its sheltered beach is good for swimming, and its promenade is lined with restaurants and cafés."
        ),
        source_url=WIKI + "Naama_Bay",
        lat=27.9130,
        lng=34.3290,
        visit_minutes=180,
        interests=[SEA, NIGHTS, FOOD],
    ),
    dict(
        city="Sharm El-Sheikh",
        name="Strait of Tiran Reefs",
        type="nature",
        short_description="Four coral reefs in the strait between Sinai and Tiran Island.",
        verified_info=(
            "The Strait of Tiran separates the Sinai Peninsula from Tiran Island. "
            "Its four reefs, Jackson, Woodhouse, Thomas and Gordon, are popular day-boat dive and snorkel sites."
        ),
        source_url=WIKI + "Strait_of_Tiran",
        lat=27.9900,
        lng=34.4600,
        visit_minutes=360,
        interests=[SEA, ADVENTURE],
    ),
    # ---- Dahab ----
    dict(
        city="Dahab",
        name="Blue Hole",
        type="nature",
        short_description="Deep reef sinkhole north of Dahab, famous with divers.",
        verified_info=(
            "The Blue Hole is a submarine sinkhole on the coast north of Dahab, more than 100 meters deep. "
            "Snorkelers can enjoy its rim, while the deep arch is only for highly trained divers: it is known "
            "as one of the world's most dangerous dive sites."
        ),
        source_url=WIKI + "Blue_Hole_(Red_Sea)",
        lat=28.5720,
        lng=34.5370,
        visit_minutes=240,
        interests=[SEA, ADVENTURE, PHOTO],
    ),
    dict(
        city="Dahab",
        name="Dahab Lagoon",
        type="activity",
        short_description="Shallow lagoon for windsurfing, kitesurfing and calm swims.",
        verified_info=(
            "Dahab is a former Bedouin fishing village on the Gulf of Aqaba, now known for diving and windsurfing. "
            "Its lagoon has shallow water and steady wind, which makes it a favorite place to learn."
        ),
        source_url=WIKI + "Dahab",
        lat=28.4700,
        lng=34.5000,
        visit_minutes=180,
        interests=[SEA, ADVENTURE, CALM],
    ),
    dict(
        city="Dahab",
        name="Dahab Promenade",
        type="food",
        short_description="Seafront walk of small restaurants and cafés.",
        verified_info=(
            "Dahab grew from a Bedouin village into a relaxed seaside town. "
            "Its seafront walkway is lined with small restaurants serving fresh fish, and it gets lively at sunset."
        ),
        source_url=WIKI + "Dahab",
        lat=28.4990,
        lng=34.5170,
        visit_minutes=120,
        interests=[FOOD, CALM, NIGHTS],
    ),
    # ---- Siwa Oasis ----
    dict(
        city="Siwa Oasis",
        name="Shali Fortress",
        type="monument",
        era="13th century",
        short_description="Ruins of the old mud-brick town in the middle of Siwa.",
        verified_info=(
            "Shali is the old fortified town of Siwa, built in the 13th century from kershef, a mix of salt and mud. "
            "Heavy rains in 1926 damaged it badly, and its ruins now stand over the modern town."
        ),
        source_url=WIKI + "Siwa_Oasis",
        lat=29.2040,
        lng=25.5190,
        visit_minutes=60,
        interests=[HISTORY, PHOTO],
    ),
    dict(
        city="Siwa Oasis",
        name="Temple of the Oracle of Amun",
        type="monument",
        era="Late Period, 6th century BC",
        short_description="Hilltop temple where Alexander the Great consulted the oracle.",
        verified_info=(
            "The Temple of the Oracle of Amun stands on a hill in the village of Aghurmi in Siwa. "
            "Its oracle was famous across the ancient world, and Alexander the Great visited it in 331 BC."
        ),
        source_url=WIKI + "Siwa_Oasis",
        lat=29.2010,
        lng=25.5470,
        visit_minutes=60,
        interests=[HISTORY],
    ),
    dict(
        city="Siwa Oasis",
        name="Cleopatra's Spring",
        type="nature",
        short_description="Natural spring pool among the palm groves.",
        verified_info=(
            "Siwa has hundreds of natural springs that water its palm and olive groves. "
            "Cleopatra's Spring is the best-known one: a stone-lined pool where visitors swim."
        ),
        source_url=WIKI + "Siwa_Oasis",
        lat=29.1920,
        lng=25.5560,
        visit_minutes=60,
        interests=[CALM],
    ),
    dict(
        city="Siwa Oasis",
        name="Great Sand Sea",
        type="activity",
        short_description="Desert dunes for 4x4 trips, sandboarding and sunsets.",
        verified_info=(
            "The Great Sand Sea is a vast field of sand dunes in the Western Desert that starts south of Siwa. "
            "Trips from Siwa cross the dunes and stop at hot and cold springs."
        ),
        source_url=WIKI + "Great_Sand_Sea",
        lat=29.0500,
        lng=25.4000,
        visit_minutes=240,
        interests=[ADVENTURE, PHOTO],
    ),
    # ---- Fayoum ----
    dict(
        city="Fayoum",
        name="Wadi El Hitan",
        type="nature",
        era="Eocene, about 40 million years ago",
        short_description="Valley of the Whales: a UNESCO site with fossils of early whales.",
        verified_info=(
            "Wadi El Hitan, the Valley of the Whales, is a UNESCO World Heritage Site since 2005. "
            "It holds fossils of the earliest whales, such as Basilosaurus, from about 40 million years ago, "
            "when the area was under the sea."
        ),
        source_url=WIKI + "Wadi_El_Hitan",
        lat=29.2700,
        lng=30.0430,
        visit_minutes=180,
        interests=[HISTORY, ADVENTURE, PHOTO],
    ),
    dict(
        city="Fayoum",
        name="Wadi El Rayan Waterfalls",
        type="nature",
        short_description="Desert lakes joined by small waterfalls.",
        verified_info=(
            "Wadi El Rayan is a protected area in the desert of Fayoum with two man-made lakes joined by "
            "waterfalls, the only ones in Egypt. Dunes and springs surround the lakes."
        ),
        source_url=WIKI + "Wadi_El_Rayan",
        lat=29.1950,
        lng=30.4100,
        visit_minutes=120,
        interests=[CALM, PHOTO],
    ),
    dict(
        city="Fayoum",
        name="Lake Qarun",
        type="nature",
        short_description="Large salt lake, good for birdwatching and sunsets.",
        verified_info=(
            "Lake Qarun, in the north of the Fayoum depression, is what remains of the ancient Lake Moeris. "
            "It is a salt lake today, and its shores attract many water birds in winter."
        ),
        source_url=WIKI + "Lake_Moeris",
        lat=29.4700,
        lng=30.6000,
        visit_minutes=90,
        interests=[CALM, PHOTO],
    ),
    dict(
        city="Fayoum",
        name="Tunis Village",
        type="activity",
        short_description="Village of pottery workshops above Lake Qarun.",
        verified_info=(
            "Tunis is a village on the edge of the Fayoum oasis overlooking Lake Qarun. "
            "It is known for its pottery workshops, where local potters make and sell their work."
        ),
        source_url=WIKI + "Faiyum_Oasis",
        lat=29.4110,
        lng=30.5960,
        visit_minutes=120,
        interests=[ART, CALM],
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
        for name in dict.fromkeys(interest_names):  # several old tags map to one interest
            if name in interests:
                db.add(PlaceInterest(place_id=place.id, interest_id=interests[name]))
