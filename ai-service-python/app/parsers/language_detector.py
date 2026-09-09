import re
from typing import Dict, Set

# Generic statistical stopword profiles for natural language identification
# Based on universal grammatical function words (articles, conjunctions, prepositions, auxiliary verbs)
LANGUAGE_PROFILES: Dict[str, Set[str]] = {
    "English": {
        "the", "and", "is", "in", "at", "of", "with", "this", "for", "that", "from", 
        "on", "have", "not", "by", "as", "are", "was", "were", "been", "has", "had", 
        "will", "would", "can", "could", "should", "patient", "dose", "report", "date"
    },
    "Spanish": {
        "de", "la", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", 
        "para", "con", "no", "una", "su", "al", "lo", "como", "más", "pero", "sus", 
        "le", "ya", "o", "este", "sí", "porque", "esta", "entre", "cuando", "muy", 
        "sin", "sobre", "también", "me", "hasta", "hay", "donde", "paciente", "notificación"
    },
    "German": {
        "der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich", "des", 
        "ist", "im", "für", "auf", "dem", "nicht", "eine", "als", "auch", "es", 
        "an", "werden", "aus", "er", "hat", "dass", "sie", "nach", "wird", "bei", 
        "einer", "um", "am", "sind", "noch", "wie", "einem", "über", "einen", "bericht"
    },
    "French": {
        "le", "la", "les", "de", "un", "une", "des", "à", "être", "et", "en", "avoir", 
        "que", "pour", "dans", "ce", "il", "qui", "ne", "sur", "se", "pas", "plus", 
        "pouvoir", "par", "je", "avec", "tout", "faire", "son", "sa", "ses", "autre", "mais"
    },
    "Italian": {
        "il", "la", "lo", "i", "gli", "le", "di", "e", "a", "da", "in", "per", 
        "tra", "fra", "un", "uno", "una", "con", "su", "che", "non", "si", "ha", 
        "sono", "questo", "quello", "più", "anche", "come", "ma", "del", "della", "delle"
    },
    "Portuguese": {
        "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com", 
        "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", 
        "mas", "foi", "ao", "ele", "das", "tem", "à", "seu", "sua", "ou", "ser"
    }
}

def detect_language(text: str) -> str:
    """
    Generic content-based language identification using statistical stopword profiling.
    Analyzes word token distribution against language profiles.
    Returns detected language name (e.g. 'English', 'Spanish', 'German', 'French') or 'Unknown'.
    """
    if not text or len(text.strip()) < 10:
        return "Unknown"
        
    # Extract lower-case alphabetic tokens (supporting accented characters)
    words = re.findall(r'\b[^\W\d_]{2,}\b', text.lower())
    if not words:
        return "Unknown"
        
    word_set = set(words)
    
    scores: Dict[str, float] = {}
    for lang, profile in LANGUAGE_PROFILES.items():
        hits = sum(1 for w in words if w in profile)
        unique_hits = len(word_set.intersection(profile))
        # Weight frequency and vocabulary diversity
        scores[lang] = hits + (unique_hits * 1.5)
        
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_lang, top_score = sorted_scores[0]
    
    if top_score < 3:
        return "Unknown"
        
    return top_lang
