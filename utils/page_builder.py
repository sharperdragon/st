import sys, json, hashlib, os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bs4 import BeautifulSoup
from utils.write_stats import write_them_stats
from utils.page_helpers.nav_builder import generate_drop_nav_html
from utils.page_helpers.html_utils import annotate_table_columns, generate_nav_html, extract_rr_associations_html, generate_label_and_slug

TABLE_DIR = ROOT / os.getenv("TABLE_DIR", "subdex")
OUTPUT_DIR = ROOT / os.getenv("OUTPUT_DIR", "pages")
NAV_DIR = ROOT / os.getenv("NAV_DIR", "utils/navs")
BASE_HTML_PATH = ROOT / os.getenv("BASE_HTML", "static/BASE.html")
MANIFEST_PATH = ROOT / os.getenv("MANIFEST_PATH", "static/data/table.manifest.json")

BASE_HASH_PATH = ROOT / "static" / "data" / ".base_hash.json"
TABLE_SUFFIX = ".table.html"

"""Module to update HTML pages by processing table files, annotating columns for toggling, generating navigation bars, and building a manifest."""

def write_if_changed(path: Path, content: str):
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True



def build_pages():
    """
    Main function to build all HTML pages from table files.
    Processes tables, annotates columns for toggling, generates navigation bars,
    writes output HTML files, and updates the manifest.
    """
    # Ensure output and navigation directories exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    NAV_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []
    card_manifest = []
    base_inputs = {
        "base_html": BASE_HTML_PATH.read_text(),
        "style_css": Path("styles/style.css").read_text(),
        "table_css": Path("styles/table.css").read_text(),
        "nav_css": Path("styles/nav.css").read_text(),
        "search_js": Path("java/static_search.js").read_text(),
        "table_utils_js": Path("java/table_page_utils.js").read_text(),
    }
    base_html = base_inputs["base_html"]
    # The base HTML must include {{PAGE_TITLE}}, {{NAV_CONTENT}}, and {{TABLE_CONTENT}} placeholders
    #required_placeholders = ["{{PAGE_TITLE}}", "{{NAV_CONTENT}}", "{{TABLE_CONTENT}}"]
    required_placeholders = ["{{PAGE_TITLE}}", "{{TABLE_CONTENT}}", "{{DROP_NAV_CONTENT}}"]
    missing = [ph for ph in required_placeholders if ph not in base_html]
    if missing:
        raise ValueError(f"❌ Missing required placeholder(s) in BASE.html: {', '.join(missing)}")

    full_base_hash = hashlib.sha256("".join(base_inputs.values()).encode("utf-8")).hexdigest()
    force_rebuild = False

    if BASE_HASH_PATH.exists():
        old_hash = json.loads(BASE_HASH_PATH.read_text()).get("hash", "")
        if full_base_hash != old_hash:
            print("🛠️  BASE.html or dependencies changed — forcing rebuild of all pages.")
            force_rebuild = True
    else:
        force_rebuild = True

    # Gather all table files to process
    table_files_all = sorted(TABLE_DIR.glob("*"))
    table_files = [f for f in table_files_all if f.name.endswith(TABLE_SUFFIX)]

    # Generate all drop navs once
    generate_drop_nav_html()

    # Loop over each table file to build individual pages
    for table_file in table_files:
        label, slug = generate_label_and_slug(table_file.name)

        table_html_raw = table_file.read_text()
        soup = BeautifulSoup(table_html_raw, "html.parser")

        # Annotate table columns and insert toggle buttons
        annotate_table_columns(soup)

        # Remove row-divider rows and insert rapid review associations if present
        for tr in soup.find_all("tr", class_="row-divider"):
            tr.decompose()

        rapid_associations = soup.find_all("div", class_="rr-assoc")
        if rapid_associations:
            html_snippets = [str(div) for div in rapid_associations]
            rr_html = extract_rr_associations_html(html_snippets)
            new_rr = BeautifulSoup(rr_html, "html.parser")
            soup.body.insert(0, new_rr)

        table_html = str(soup)

        print(f"📄 Processing: {table_file.name}")

        # Build improved navigation bar with Home and links to other pages
        nav_html = generate_nav_html(table_file, table_files)

        # Write navigation HTML to separate file for potential reuse
        nav_path = NAV_DIR / f"nav_{slug}.html"
        write_if_changed(nav_path, nav_html)

        # Load corresponding drop nav HTML
        drop_nav_path = NAV_DIR / "drop_navs" / f"drop_nav_{slug}.html"
        drop_nav_html = drop_nav_path.read_text() if drop_nav_path.exists() else ""

        # Compose final HTML by replacing placeholders in base template
        final_html = (
            base_html
            .replace("{{PAGE_TITLE}}", label)
            .replace("{{TABLE_CONTENT}}", table_html)
            .replace("{{DROP_NAV_CONTENT}}", drop_nav_html)
        )

        # Write the generated HTML page to output directory
        output_file = OUTPUT_DIR / f"{slug}.html"
        if force_rebuild or write_if_changed(output_file, final_html):
            print(f"📄 Built page: {output_file.name}")

        # Append page info to manifest list
        manifest.append({
            "name": label,
            "file": f"{slug}.html"
        })

        card_manifest.append({
            "name": label,
            "file": f"{slug}.html",
            "desc": f"A high-yield summary table for {label.lower()}."  # Placeholder, can be customized later
        })

    # Cleanup orphaned HTML files
    expected_files = {f"{generate_label_and_slug(f.name)[1]}.html" for f in table_files}
    actual_files = {f.name for f in OUTPUT_DIR.glob("*.html")}
    for file in actual_files - expected_files:
        orphan = OUTPUT_DIR / file
        orphan.unlink()
        print(f"🗑️ Removed stale page: {file}")

    # Ensure manifest parent directories exist
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Write the manifest JSON file with all pages info
    write_if_changed(MANIFEST_PATH, json.dumps(manifest, indent=2))
    BASE_HASH_PATH.write_text(json.dumps({"hash": full_base_hash}))
    print(f"\n🧾 Manifest updated: {MANIFEST_PATH}")

    card_manifest_path = Path("static/data/summary_cards.json")
    card_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_if_changed(card_manifest_path, json.dumps(card_manifest, indent=2))
    print(f"🧾 Summary cards written to: {card_manifest_path}")

    # 🔁 Generate full stats (structure, spans, headers, etc.)
    write_them_stats()

    summary = {
        "updated": datetime.now().isoformat(),
        "pages_built": [f.name for f in table_files],
        "manifest_count": len(manifest)
    }
    Path("build_summary.json").write_text(json.dumps(summary, indent=2))
