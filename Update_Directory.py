import os
import json
from pathlib import Path
from bs4 import BeautifulSoup
from utils.page_builder import build_pages
from utils.update_index import build_index
from utils.Texts.buzzword_json_builder import convert_buzzwords_to_json
from utils.write_stats import write_them_stats
from utils.static_search import generate_search_index, extract_terms_from_table


BASE_HTML_PATH = Path("static/BASE.html")
TABLE_DIR = Path("subdex/")
NAV_DIR = Path("utils/navs/")
OUTPUT_DIR = Path("pages/")
MANIFEST_PATH = Path("static/data/table.manifest.json")

TABLE_SUFFIX = ".table.html"

"""Module to update HTML pages by processing table files, annotating columns for toggling, generating navigation bars, and building a manifest."""

def write_if_changed(path: Path, content: str):
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True




if __name__ == "__main__":
    build_pages()
    generate_search_index()

    print("🧪 Extracting terms from tables for logging:")
    for html_file in OUTPUT_DIR.glob("*.html"):
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        for table in soup.find_all("table"):
            terms = extract_terms_from_table(table)
            print(f"🔍 {html_file.name} → {len(terms)} terms")

    convert_buzzwords_to_json()
    build_index()
    write_them_stats()