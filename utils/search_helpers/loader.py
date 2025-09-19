import json
import requests
from pathlib import Path
from functools import lru_cache
import logging

HP_JSON_PATH = Path("assets/ontologies/hpo_terms.json")
WORDLIST_PATH = Path("assets/wordlist.txt")
SEARCH_INDEX_PATH = Path("assets/search_index.json")

_all_terms = None

def load_hpo_terms():
    try:
        with open(HP_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            terms = set()
            for entry in data:
                if "lbl" in entry:
                    terms.add(entry["lbl"].lower())
                synonyms = entry.get("meta", {}).get("synonyms", [])
                for syn in synonyms:
                    if "val" in syn:
                        terms.add(syn["val"].lower())
            return terms
    except Exception as e:
        return set()

def load_wordlist():
    try:
        return set(w.strip().lower() for w in WORDLIST_PATH.read_text(encoding="utf-8").splitlines() if w.strip())
    except Exception:
        return set()

def get_all_medical_terms():
    global _all_terms
    if _all_terms is not None:
        return _all_terms

    _all_terms = set()
    try:
        _all_terms.update(load_hpo_terms())
    except Exception as e:
        logging.warning(f"Error loading HP terms: {e}")

    try:
        _all_terms.update(load_wordlist())
    except Exception as e:
        logging.warning(f"Error loading wordlist: {e}")

    return _all_terms

def is_medical_term(word: str) -> bool:
    return word.lower() in get_all_medical_terms()

def is_medical_phrase(phrase: str) -> bool:
    return any(is_medical_term(w) for w in phrase.split())