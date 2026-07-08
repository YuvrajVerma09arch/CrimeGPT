"""Rule-based NLP entity extraction for crime narratives.

The primary engine is a pure-Python lexicon/regex extractor that works with
zero heavy dependencies. If spaCy and the ``en_core_web_sm`` model happen to
be installed, their PERSON / GPE / LOC / DATE entities are merged in as a
bonus — but nothing here requires them.
"""
import re

# ---------------------------------------------------------------------------
# Optional spaCy support (never required)
# ---------------------------------------------------------------------------
try:  # pragma: no cover - depends on optional heavy deps
    import spacy  # type: ignore

    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        _NLP = None
except Exception:  # ImportError or anything else — fall back to rules only
    _NLP = None


# ---------------------------------------------------------------------------
# Lexicons
# ---------------------------------------------------------------------------
CRIME_LEXICON: dict[str, list[str]] = {
    "murder": [
        "murder", "murdered", "killed", "homicide", "dead body",
        "beaten to death", "stabbed to death", "strangled", "strangulation",
    ],
    "attempt_to_murder": [
        "attempt to murder", "attempted murder", "attempted to kill",
        "tried to kill", "fired at", "shot at", "attempt on his life",
        "attempt on her life",
    ],
    "assault": [
        "assault", "assaulted", "attacked", "beaten", "beat him", "beat her",
        "slapped", "punched", "kicked", "hit him", "hit her", "hurt",
    ],
    "grievous_hurt": [
        "grievous hurt", "grievous injury", "grievous injuries", "fracture",
        "fractured", "acid attack", "disfigured", "permanent damage",
        "serious injuries", "severe injuries",
    ],
    "theft": [
        "theft", "stolen", "stole", "steal", "pickpocket", "pick-pocket",
        "shoplifting", "lifted the",
    ],
    "snatching": [
        "snatching", "snatched", "chain snatching", "purse snatched",
        "mobile snatched", "snatch",
    ],
    "burglary": [
        "burglary", "housebreaking", "house break", "house-break",
        "broke into", "break-in", "broke open the lock",
        "lurking house trespass",
    ],
    "robbery": [
        "robbery", "robbed", "loot", "looted", "at knifepoint",
        "at gunpoint", "forcibly took", "forcibly snatched",
    ],
    "dacoity": [
        "dacoity", "gang robbery", "armed gang", "gang of five",
        "five or more persons",
    ],
    "cheating_fraud": [
        "cheating", "cheated", "fraud", "fraudulent", "defrauded", "duped",
        "swindled", "misrepresentation", "fake scheme", "ponzi",
        "false promise",
    ],
    "cybercrime": [
        "cyber", "cybercrime", "online fraud", "online scam", "phishing",
        "otp", "hacked", "hacking", "upi fraud", "internet banking",
        "identity theft", "fake profile", "social media account",
        "email fraud",
    ],
    "criminal_breach_of_trust": [
        "criminal breach of trust", "breach of trust", "misappropriated",
        "misappropriation", "embezzled", "embezzlement", "entrusted",
    ],
    "kidnapping": [
        "kidnapping", "kidnapped", "abducted", "abduction", "ransom",
        "forcibly taken away", "missing child",
    ],
    "rape": [
        "rape", "raped", "sexual assault", "sexually assaulted",
        "forcible intercourse",
    ],
    "molestation": [
        "molestation", "molested", "outraged her modesty",
        "outraging modesty", "outraging the modesty", "groped",
        "inappropriately touched",
    ],
    "stalking": [
        "stalking", "stalked", "followed her", "repeatedly followed",
        "kept following",
    ],
    "dowry_cruelty": [
        "dowry", "dowry demand", "dowry death", "cruelty by husband",
        "harassment by in-laws", "harassed by her husband",
    ],
    "criminal_intimidation": [
        "criminal intimidation", "threatened", "threatening", "threats",
        "intimidated", "intimidation", "dire consequences",
    ],
    "trespass": [
        "trespass", "trespassed", "criminal trespass", "unlawfully entered",
        "entered illegally", "entered the house without",
    ],
    "mischief_damage": [
        "mischief", "vandalism", "vandalised", "vandalized",
        "damaged property", "damaged the", "set fire", "set on fire",
        "arson", "smashed", "destroyed property",
    ],
    "forgery": [
        "forgery", "forged", "fake document", "fake documents",
        "counterfeit", "fabricated document", "false document",
    ],
    "defamation": [
        "defamation", "defamed", "defamatory", "maligned",
        "false statement about", "damaged his reputation",
        "damaged her reputation",
    ],
}

WEAPONS: list[str] = [
    "knife", "iron rod", "gun", "pistol", "revolver", "rifle",
    "country-made pistol", "lathi", "acid", "sword", "hammer",
    "screwdriver", "rope", "stone", "brick", "axe", "chopper", "blade",
    "stick", "iron pipe", "chain",
]

# ---------------------------------------------------------------------------
# Gujarati / Hindi lexicons — used when the narrative reaches us untranslated
# (translation service absent -> passthrough). Substring matching, because
# Indic scripts agglutinate case suffixes onto the noun (e.g. "સળિયાથી").
# Labels map to the SAME canonical English labels so the RAG retrieval query
# stays in English regardless of input language.
# ---------------------------------------------------------------------------
INDIC_CRIME_LEXICON: dict[str, list[str]] = {
    "murder": ["હત્યા", "ખૂન", "મારી નાખ", "हत्या", "खून", "मार डाला", "क़त्ल", "कत्ल"],
    "attempt_to_murder": ["હત્યાનો પ્રયાસ", "જાનથી મારી", "हत्या का प्रयास", "जान से मारने"],
    "assault": ["હુમલો", "મારપીટ", "માર માર્ય", "हमला", "मारपीट", "पिटाई", "पीटा"],
    "grievous_hurt": ["ગંભીર ઈજા", "ગંભીર ઇજા", "गंभीर चोट", "हड्डी टूट"],
    "theft": ["ચોરી", "ચોરાઈ", "ચોરી થઈ", "चोरी", "चुरा"],
    "snatching": ["ખેંચી લીધ", "છીનવી", "ઝૂંટવી", "સ્નેચિંગ", "छीन", "झपट", "स्नैचिंग"],
    "burglary": ["ઘરફોડ", "તાળું તોડી", "ઘરમાં ઘૂસી", "सेंधमारी", "ताला तोड़", "घर में घुस"],
    "robbery": ["લૂંટ", "લૂંટી", "लूट", "लूटपाट"],
    "dacoity": ["ધાડ", "डकैती"],
    "cheating_fraud": ["છેતરપિંડી", "ઠગાઈ", "છેતરી", "धोखाधड़ी", "ठगी", "धोखा"],
    "cybercrime": [
        "સાયબર", "ઓનલાઈન", "ઓટીપી", "ઓ.ટી.પી", "યુપીઆઈ", "કેવાયસી",
        "साइबर", "ऑनलाइन", "ओटीपी", "यूपीआई", "केवाईसी", "नेट बैंकिंग",
    ],
    "criminal_breach_of_trust": ["વિશ્વાસઘાત", "ઉચાપત", "गबन", "विश्वासघात"],
    "kidnapping": ["અપહરણ", "अपहरण", "अगवा"],
    "rape": ["બળાત્કાર", "बलात्कार", "दुष्कर्म"],
    "molestation": ["છેડતી", "छेड़छाड़", "छेड़खानी"],
    "stalking": ["પીછો", "पीछा"],
    "dowry_cruelty": ["દહેજ", "दहेज"],
    "criminal_intimidation": ["ધમકી", "धमकी", "धमकाया"],
    "mischief_damage": ["તોડફોડ", "આગ લગાડી", "तोड़फोड़", "आग लगा"],
    "forgery": ["બનાવટી", "નકલી દસ્તાવેજ", "फर्जी", "जाली"],
    "defamation": ["બદનક્ષી", "मानहानि"],
}

# Indic weapon mention -> canonical English weapon name
INDIC_WEAPON_MAP: dict[str, list[str]] = {
    "iron rod": ["સળિયા", "સળિયો", "લોખંડ", "सरिया", "लोहे की रॉड", "लोहे की छड़"],
    "knife": ["છરી", "ચાકુ", "चाकू", "छुरी", "छुरा"],
    "gun": ["બંદૂક", "बंदूक"],
    "pistol": ["પિસ્તોલ", "पिस्तौल", "तमंचा"],
    "sword": ["તલવાર", "तलवार"],
    "lathi": ["લાકડી", "लाठी", "डंडा"],
    "acid": ["એસિડ", "तेजाब"],
    "hammer": ["હથોડી", "हथौड़ा"],
    "stone": ["પથ્થર", "पत्थर"],
}

# Simple gazetteer of Ahmedabad areas / landmarks
AHMEDABAD_AREAS: list[str] = [
    "Navrangpura", "Maninagar", "Satellite", "Vastrapur", "Bopal",
    "CG Road", "SG Highway", "Chandkheda", "Naroda", "Bapunagar",
    "Ellis Bridge", "Paldi", "Thaltej", "Gota", "Nikol", "Vatva",
    "Odhav", "Sabarmati", "Ranip", "Ghatlodia", "Ambawadi",
    "Lal Darwaja", "Kalupur", "Shahibaug", "Isanpur", "Vejalpur",
    "Bodakdev", "Ashram Road", "Gandhinagar", "Ahmedabad",
]

# Words that disqualify a capitalized phrase from being a person name
_NON_NAME_WORDS: set[str] = {
    "the", "a", "an", "on", "at", "in", "he", "she", "they", "it", "this",
    "that", "when", "after", "before", "during", "then", "there", "today",
    "yesterday", "police", "station", "complainant", "accused", "victim",
    "witness", "fir", "road", "highway", "hospital", "court", "india",
    "gujarat", "city", "district",
}

_HONORIFIC_RE = re.compile(
    r"\b(?:Shri|Smt|Shrimati|Mr|Mrs|Ms|Miss|Dr|Kumari)\.?\s+"
    r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})"
)
_CAP_SEQ_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")
_LOCATION_SUFFIX_RE = re.compile(
    r"\b([A-Z][\w]*(?:\s+[A-Z][\w]*)*\s+"
    r"(?:Road|Nagar|Society|Chowk|Circle|Bridge|Highway|Colony|Park|Area|"
    r"Cross\s+Roads|Char\s+Rasta))\b"
)
_DATE_RES = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),                # ISO 8601
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),    # dd/mm/yyyy, dd-mm-yyyy
]


def _dedup(values: list[str]) -> list[str]:
    """Deduplicate while preserving first-seen order."""
    return list(dict.fromkeys(v.strip() for v in values if v and v.strip()))


def _word_search(needle: str, haystack_lower: str) -> bool:
    """Case-insensitive whole-word/phrase search."""
    return re.search(rf"\b{re.escape(needle.lower())}\b", haystack_lower) is not None


def extract_entities(text: str) -> dict:
    """Extract crime entities from an (ideally English) narrative.

    Returns ``{crime_types, weapons, persons, locations, dates}`` where each
    value is a list of strings. Rule-based lexicons are the primary engine;
    spaCy entities are merged in only when the optional model is available.
    """
    if not text or not text.strip():
        return {
            "crime_types": [], "weapons": [], "persons": [],
            "locations": [], "dates": [],
        }

    lower = text.lower()

    # Crime types — every lexicon label with at least one keyword hit
    crime_types = [
        label
        for label, keywords in CRIME_LEXICON.items()
        if any(_word_search(kw, lower) for kw in keywords)
    ]
    # Gujarati / Hindi keywords (substring match on the raw text)
    for label, keywords in INDIC_CRIME_LEXICON.items():
        if label not in crime_types and any(kw in text for kw in keywords):
            crime_types.append(label)

    # Weapons
    weapons = [w for w in WEAPONS if _word_search(w, lower)]
    for eng_name, keywords in INDIC_WEAPON_MAP.items():
        if eng_name not in weapons and any(kw in text for kw in keywords):
            weapons.append(eng_name)

    # Locations — gazetteer first, then capitalized suffix heuristic
    locations: list[str] = [a for a in AHMEDABAD_AREAS if _word_search(a, lower)]
    for match in _LOCATION_SUFFIX_RE.finditer(text):
        locations.append(match.group(1))
    locations = _dedup(locations)
    location_words = {w.lower() for loc in locations for w in loc.split()}

    # Dates
    dates: list[str] = []
    for date_re in _DATE_RES:
        dates.extend(date_re.findall(text))

    # Persons — honorific patterns are high-confidence
    persons: list[str] = [m.group(1) for m in _HONORIFIC_RE.finditer(text)]
    # Consecutive-capitalized-words heuristic, excluding locations and
    # phrases that start with common sentence-starter / non-name words.
    for match in _CAP_SEQ_RE.finditer(text):
        candidate = match.group(1)
        words = [w.lower() for w in candidate.split()]
        if words[0] in _NON_NAME_WORDS:
            continue
        if any(w in _NON_NAME_WORDS for w in words[1:]):
            continue
        if any(w in location_words for w in words):
            continue
        if candidate.lower() in {loc.lower() for loc in locations}:
            continue
        persons.append(candidate)

    # Optional spaCy enrichment
    if _NLP is not None:
        try:
            doc = _NLP(text)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    persons.append(ent.text)
                elif ent.label_ in ("GPE", "LOC"):
                    locations.append(ent.text)
                elif ent.label_ == "DATE":
                    dates.append(ent.text)
        except Exception:
            pass

    return {
        "crime_types": _dedup(crime_types),
        "weapons": _dedup(weapons),
        "persons": _dedup(persons),
        "locations": _dedup(locations),
        "dates": _dedup(dates),
    }


def infer_crime_type(text: str) -> str | None:
    """Return the single best crime-type label for a narrative, or ``None``.

    The label whose lexicon has the most distinct keyword hits wins;
    ties go to the first label in ``CRIME_LEXICON`` insertion order.
    """
    if not text or not text.strip():
        return None
    lower = text.lower()
    best_label: str | None = None
    best_hits = 0
    for label, keywords in CRIME_LEXICON.items():
        hits = sum(1 for kw in keywords if _word_search(kw, lower))
        hits += sum(1 for kw in INDIC_CRIME_LEXICON.get(label, []) if kw in text)
        if hits > best_hits:
            best_label, best_hits = label, hits
    return best_label
