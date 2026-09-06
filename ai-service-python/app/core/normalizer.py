import re
from typing import Optional, Any
from datetime import datetime

class Normalizer:
    @staticmethod
    def normalize_age(age_str: Optional[str]) -> Optional[int]:
        if not age_str or age_str.strip().lower() in ("not stated", "unknown", "n/a", ""):
            return None
        match = re.search(r"(\d+)\s*(?:yrs?|years?|ans|jahre|años)?", age_str, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    @staticmethod
    def normalize_route(route_str: Optional[str]) -> Optional[str]:
        if not route_str or route_str.strip().lower() in ("not stated", "unknown", "n/a", ""):
            return None
        r = route_str.strip().lower()
        if any(term in r for term in ["oral", "p.o.", "po", "oralmente", "per os", "tablets", "capsules"]):
            return "Oral"
        if any(term in r for term in ["intravenous", "i.v.", "iv", "intravenosa", "infusion"]):
            return "Intravenous"
        if any(term in r for term in ["intramuscular", "i.m.", "im"]):
            return "Intramuscular"
        if any(term in r for term in ["subcutaneous", "s.c.", "sc"]):
            return "Subcutaneous"
        if any(term in r for term in ["topical", "derm", "cutaneous"]):
            return "Topical"
        if any(term in r for term in ["inhalation", "inh"]):
            return "Inhalation"
        return route_str.capitalize()

    @staticmethod
    def normalize_country(country_str: Optional[str]) -> Optional[str]:
        if not country_str or country_str.strip().lower() in ("not stated", "unknown", "n/a", ""):
            return None
        c = country_str.strip().lower()
        if c in ("usa", "us", "united states", "united states of america", "u.s.", "u.s.a."):
            return "United States"
        if c in ("spain", "españa", "espana"):
            return "Spain"
        if c in ("germany", "deutschland"):
            return "Germany"
        if c in ("france", "francia"):
            return "France"
        if c in ("uk", "united kingdom", "great britain", "england"):
            return "United Kingdom"
        if c in ("italy", "italia"):
            return "Italy"
        if c in ("japan", "nippon"):
            return "Japan"
        return country_str.title()

    @staticmethod
    def normalize_sex(sex_str: Optional[str]) -> Optional[str]:
        if not sex_str or sex_str.strip().lower() in ("not stated", "unknown", "n/a", ""):
            return None
        s = sex_str.strip().lower()
        if s in ("f", "female", "fem", "mujer", "weiblich", "femenino", "w"):
            return "Female"
        if s in ("m", "male", "masc", "hombre", "männlich", "masculino"):
            return "Male"
        return sex_str.capitalize()

    @staticmethod
    def normalize_date(date_str: Optional[str]) -> Optional[str]:
        if not date_str or date_str.strip().lower() in ("not stated", "unknown", "n/a", ""):
            return None
        raw = date_str.strip()
        # Try standard formats: YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY, DD-Mon-YYYY, Month DD, YYYY
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d.%m.%Y",
            "%d-%b-%Y",
            "%d-%B-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y/%m/%d",
            "%Y.%m.%d"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(raw, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        # Check regex for YYYY-MM-DD pattern inside string
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        # Check regex for DD.MM.YYYY pattern inside string
        m_dot = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", raw)
        if m_dot:
            return f"{m_dot.group(3)}-{m_dot.group(2)}-{m_dot.group(1)}"
        return None

normalizer = Normalizer()
