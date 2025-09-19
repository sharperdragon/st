from bs4 import BeautifulSoup
from pathlib import Path
import json
from datetime import datetime
from time import time
from utils.static_search import generate_search_index
from utils.page_helpers.html_utils import generate_label_and_slug

BASE_PATH = Path(__file__).parent
PROJECT_ROOT = BASE_PATH.parent
MANIFEST_PATH = PROJECT_ROOT / "static/data/table.manifest.json"
INDEX_BASE_HTML_PATH = BASE_PATH / "index_utils/index_base.html"
OUTPUT_PATH = PROJECT_ROOT / "index.html"


def build_index(build_json=True):
    """Generate index.html from base template and manifest"""
    generate_search_index()
    try:
        with INDEX_BASE_HTML_PATH.open("r", encoding="utf-8") as f:
            base_html = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ index_base.html not found at {INDEX_BASE_HTML_PATH}. Double check the path or move the file back.")

    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Sort manifest entries by name
    manifest_sorted = sorted(manifest, key=lambda x: x["name"])

    PINNED_LABELS = ["Glossary", "Associations", "Presentations", "Findings"]
    pinned_links = []
    regular_links = []

    summary_cards = []
    card_descriptions = {
        "Metabolism": "Includes glycolysis, glycogen storage, and fatty acid oxidation disorders",
        "Hemeonc": "Summarizes hematologic malignancies, anemias, and blood-related findings",
        "Chromosomes": "Genetic disorders and syndromes organized by chromosome number",
        "Autoantibodies": "Autoimmune diseases and their associated antibodies",
        "Glossary": "Relevant terms across pathology, genetics, and neuro — clearly explained with examples",
        "Lab Tests": "High-yield lab tests for diagnosis and management, including tumor markers, infection assays, and metabolic workups",
        "Associations": "Rapid-fire 'most common' and high-yield exam associations",
        "Presentations": "Clinical buzzwords and presentation patterns linked to classic diagnoses — optimized for fast recall",
        "Findings": "Diagnostic clues and lab/physical findings tied to conditions, covering exam associations",
        "Pharm": "Work in progress, but go crazy with these Antibiotics and Immunologics"
    }
    for entry in manifest_sorted:
        try:
            label, slug = generate_label_and_slug(entry.get("label", entry["name"]))
            href = f'pages/{entry["file"]}'
        except KeyError as e:
            raise ValueError(f"Malformed entry in manifest: {entry}") from e

        nav_html_snippet = f'<a href="{href}" class="home-nav-link">{label}</a>'

        # Check if table.html file explicitly includes summary-card meta
        page_path = PROJECT_ROOT / href
        include_card = False
        if page_path.exists():
            soup = BeautifulSoup(page_path.read_text(encoding="utf-8"), "html.parser")
            meta = soup.find("meta", attrs={"name": "summary-card"})
            if meta and meta.get("content", "").lower() == "true":
                include_card = True

        if label in PINNED_LABELS:
            pinned_links.append(nav_html_snippet)
        else:
            regular_links.append(nav_html_snippet)

        if include_card:
            desc = card_descriptions.get(label, f"A high-yield summary table for {label.lower()}.")
            summary_cards.append(
                f'''<a class="summary-card" href="{href}">
  <div class="card-title">{label}</div>
  <div class="card-desc">{desc}</div>
</a>'''
            )

    nav_links = pinned_links + regular_links
    nav_html = (
        '<nav style="margin: 20px 0 40px 0; text-align: center; font-size: 0.9em;">\n'
        '<div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;">\n'
        + "\n".join(nav_links) +
        '\n</div>\n</nav>'
    )
    summary_html = "\n".join(summary_cards)

    buzzword_file = BASE_PATH / "Texts/buzzwords.txt"
    buzzwords = ""
    
    if buzzword_file.exists():
        buzzwords = buzzword_file.read_text(encoding="utf-8").strip().replace("\n", "  ")


    carousel_html = '<div id="RapidCarousel" class="carousel-wrapper"></div>'


    base_html = base_html.replace("{{BUZZWORDS}}", buzzwords)

    last_updated = datetime.now()
    formatted_date = last_updated.strftime("%B %d")
    last_updated_html = f'<time datetime="{last_updated.date()}">{formatted_date}</time>'

    final_html = base_html
    final_html = final_html.replace("{{NAV_CONTENT}}", nav_html)
    final_html = final_html.replace("{{SUMMARY_CARDS}}", summary_html)
    final_html = final_html.replace("{{RAPID_REVIEW_CAROUSEL}}", carousel_html)
    final_html = final_html.replace("{{LAST_UPDATED}}", last_updated_html)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        f.write(final_html)

    summary = {
        "generated": "index.html",
        "updated": datetime.now().isoformat(),
        "included_tables": [entry["name"] for entry in manifest_sorted]
    }
    (PROJECT_ROOT / "build_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"✅ index.html written to: {OUTPUT_PATH}")

if __name__ == "__main__":
    build_index()