import sys
from pathlib import Path

# Add project root to sys.path for module imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from bs4 import BeautifulSoup
import json

from utils.page_helpers.html_utils import generate_label_and_slug


BASE_PATH = Path(__file__).parent
PROJECT_ROOT = BASE_PATH.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "static/data/table.manifest.json"
INDEX_BASE_HTML_PATH = BASE_PATH / "index_base.html"
OUTPUT_PATH = PROJECT_ROOT / "index.html"

# Example inputs to test label generation
test_inputs = [
    "cd-markers",
    "glossary",
    "autoantibodies",
    "lab-tests",
    "hla",
    "hemeonc",
    "chromosomes",
    "findings",
    "metabolism",
    "presentations"
]

# Print all generated labels
for slug in test_inputs:
    label, _ = generate_label_and_slug(slug)
    print(label)

# for print(label)