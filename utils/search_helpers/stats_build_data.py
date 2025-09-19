import sys
import json
from pathlib import Path

# ---------- Configurable thresholds ----------
THRESHOLDS = {
    "row_label_min": 2,
    "word_freq_min": 50,
}

STATS_PATH = Path(__file__).resolve().parent.parent.parent / "table_stats.json"
OUTPUT_PATH = Path(__file__).resolve().parent / "data_banks.py"

def build_data_banks():
    with open(STATS_PATH, "r") as f:
        stats = json.load(f)

    shared_row_labels = {
        k.lower()
        for k, v in stats.get("row_labels_in_multiple_files", {}).items()
        if v >= THRESHOLDS["row_label_min"] and len(k.split()) <= 4
    }

    overused_words = {
        k.lower()
        for k, v in stats.get("frequent_non_header_words", {}).items()
        if v >= THRESHOLDS["word_freq_min"] and len(k) > 3
    }

    genomic_keywords = {
        k.lower()
        for k in stats.get("frequent_non_header_words", {})
        if "chromosome" in k.lower() or "trisomy" in k.lower()
    }

    potential_tag_roots = {
        k.lower()
        for k in stats.get("common_column_headers", {})
        if len(k.split()) <= 3
    }

    content = f'''"""
Auto-generated from table_stats.json
"""

SHARED_ROW_LABELS = {{
    {", ".join(f'"{word}"' for word in sorted(shared_row_labels))}
}}

OVERUSED_WORDS = {{
    {", ".join(f'"{word}"' for word in sorted(overused_words))}
}}

GENOMIC_KEYWORDS = {{
    {", ".join(f'"{word}"' for word in sorted(genomic_keywords))}
}}

POTENTIAL_TAG_ROOTS = {{
    {", ".join(f'"{word}"' for word in sorted(potential_tag_roots))}
}}
'''

    with open(OUTPUT_PATH, "w") as f:
        f.write(content.strip())

    print(f"✅ Data banks written to {OUTPUT_PATH}")

if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent))
    build_data_banks()