import json
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import re
from nltk.corpus import stopwords
from collections import defaultdict, Counter
from utils.search_helpers.data_banks import OVERUSED_WORDS, SHARED_ROW_LABELS
from utils.search_helpers.loader import is_medical_term, is_medical_phrase, get_all_medical_terms

with open("assets/ontologies/hpo_terms.json", "r", encoding="utf-8") as f:
    HPO_SYNONYMS = {
        v["lbl"].lower(): set(s["val"].lower() for s in v.get("meta", {}).get("synonyms", []) if isinstance(s.get("val"), str))
        for v in json.load(f)
        if "lbl" in v and "meta" in v and "synonyms" in v["meta"]
    }


MEDICAL_TERMS = get_all_medical_terms()
# Ensure NLTK stopwords are available
try:
    STOPWORDS = set(stopwords.words("english"))
except LookupError:
    import nltk
    nltk.download("stopwords")
    STOPWORDS = set(stopwords.words("english"))

# Configurable paths
PAGES_DIR = Path("pages")
OUTPUT_FILE = Path("assets/search_index.json")

def extract_terms_from_table(table):
    BAD_WORDS = {
        "syndrome", "disease", "disorder", "defect", "condition", "abnormality", "problem"
    }

    def _is_medical_phrase_local(phrase):
        if len(phrase.split()) > 8:
            return False
        if any(char.isdigit() for char in phrase) or re.search(r"(c\d+|q\d+|hba\d|t\d+)", phrase):
            return True
        return False

    def score_phrase(phrase):
        words = phrase.split()
        score = 0
        if len(phrase) >= 15:
            score += 1
        if re.search(r"\b(c\d+|q\d+|p\d+|cd\d+|hba\d+|il-\d+|22q\d+)\b", phrase):
            score += 2
        if any(char.isdigit() for char in phrase):
            score += 1
        if "-" in phrase or "/" in phrase or "(" in phrase:
            score += 1
        if len(words) >= 2:
            score += 1
        stopword_ratio = sum(1 for w in words if w in STOPWORDS) / len(words)
        if stopword_ratio > 0.5:
            score -= 1
        if _is_medical_phrase_local(phrase):
            score += 2
        return max(score, 0)

    def looks_like_junk(phrase):
        # Skip sequences like "of the", "in a", etc.
        return bool(re.fullmatch(r"(the|of|with|and|for|to|in|on|a)+", phrase.replace(" ", "")))

    terms = set()
    for row in table.find_all("tr"):
        for cell in row.find_all("td"):
            text = cell.get_text(separator=" ", strip=True).lower()
            text = re.sub(r"\s+", " ", text)
            text = text.replace("–", "-")

            chunks = re.split(r"[;•·\u2022,\n]", text)
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue

                subphrases = re.split(r"[()]| - ", chunk)
                for phrase in subphrases:
                    phrase = phrase.strip()
                    if not phrase or len(phrase) < 4:
                        continue

                    if phrase in OVERUSED_WORDS or phrase in SHARED_ROW_LABELS:
                        continue

                    words = phrase.split()
                    if all(w in BAD_WORDS for w in words):
                        continue
                    if len(words) == 1 and words[0] in OVERUSED_WORDS:
                        continue

                    if (score_phrase(phrase) >= 3 or _is_medical_phrase_local(phrase)) and not looks_like_junk(phrase):
                        terms.add(phrase)
                    elif len(words) == 1 and is_medical_term(words[0]):
                        terms.add(phrase)
                    elif phrase in SHARED_ROW_LABELS:
                        terms.add(phrase)

                # Phrase recombination
                for i in range(len(subphrases) - 1):
                    combined = f"{subphrases[i].strip()} {subphrases[i+1].strip()}"
                    combined = combined.strip()
                    if combined in OVERUSED_WORDS or combined in SHARED_ROW_LABELS:
                        continue
                    if len(combined.split()) <= 6 and (score_phrase(combined) >= 3 or _is_medical_phrase_local(combined)) and not looks_like_junk(combined):
                        terms.add(combined)
    return terms

def generate_search_index():
    global_term_count = Counter()
    term_to_pages = defaultdict(set)

    index = []
    for html_file in PAGES_DIR.glob("*.html"):
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        tables = soup.find_all("table")
        if not tables:
            continue

        all_terms = set()
        for table in tables:
            all_terms.update(extract_terms_from_table(table))

        for term in all_terms:
            global_term_count[term] += 1
            term_to_pages[term].add(html_file.name)

        section = html_file.stem.replace("-", " ").title()
        page_text = " ".join(t.get_text(separator=" ", strip=True).lower() for t in tables)
        for term in sorted(all_terms):
            if global_term_count[term] > 5 and len(term_to_pages[term]) > 3:
                continue  # Overused term
            index.append({
                "term": term,
                "page": html_file.name,
                "section": section,
                "medical": is_medical_phrase(term)
            })
            # Include synonym if present in page text and not globally overused
            for synonym in HPO_SYNONYMS.get(term, set()):
                if synonym in page_text and synonym not in global_term_count:
                    index.append({
                        "term": synonym,
                        "page": html_file.name,
                        "section": section,
                        "medical": is_medical_phrase(synonym)
                    })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(index, indent=2))
    print(f"✅ Search index written to {OUTPUT_FILE} with {len(index)} entries.")

if __name__ == "__main__":
    generate_search_index()