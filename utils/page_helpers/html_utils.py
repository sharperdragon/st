TABLES_WITH_TOGGLE = {"table1", "table2", "table3"}

from bs4 import BeautifulSoup
from pathlib import Path


BASE_HTML_PATH = Path("static/BASE.html")
TABLE_DIR = Path("subdex/")
NAV_DIR = Path("utils/navs/")
OUTPUT_DIR = Path("pages/")
MANIFEST_PATH = Path("static/data/table.manifest.json")

TABLE_SUFFIX = ".table.html"

table_files_all = sorted(TABLE_DIR.glob("*"))
table_files = [f for f in table_files_all if f.name.endswith(TABLE_SUFFIX)]

def generate_label_and_slug(filename: str) -> tuple[str, str]:
    base = filename.replace(".table.html", "").lower()

    # Primary hardcoded overrides
    label_overrides = {
        "cd-markers": "CD Markers",
        "hla": "HLA",
        "lab-tests": "Labs",
        "hemeonc": "Heme-Onc",
        "omm": "OMM"
    }

    if base in label_overrides:
        label = label_overrides[base]
    elif "cd" in base and "marker" in base:
        label = "CD Markers"
    elif "lab" in base and "test" in base:
        label = "Labs"
    elif base.startswith("rapid_"):
        label = base.replace("rapid_", "", 1).replace("_", " ").title()
    else:
        label = base.replace("_", " ").title()

    slug = label.lower().replace(" ", "-")
    return label, slug

# is safe, but if someone hardcoded label = "CD Markers" without sanitizing the input, 
# it could mismatch during category checks. You’re fine as-is given the current flow, but be aware if you ever decouple slug from label generation.


def extract_rr_associations_html(items):
    """
    Given a list of HTML strings representing rapid associations, returns
    a carousel container where only the first item is visible on page load.
    """
    html = ['<div class="carousel-container">']
    for i, item in enumerate(items):
        if i == 0:
            item_visible = item.replace('class="answer"', 'class="answer" style="display:none;"')
            html.append(item_visible)
        else:
            item_hidden = item.replace('class="carousel-item"', 'class="carousel-item" style="display:none;"')
            item_hidden = item_hidden.replace('class="answer"', 'class="answer" style="display:none;"')
            html.append(item_hidden)
    html.append("</div>")
    return "\n".join(html)




def annotate_table_columns(soup: BeautifulSoup):
    """
    Adds data-col attributes to <td> and <th> elements for column-based control.
    Injects a dropdown toggle menu into <th> headers (excluding colspans).
    """
    assigned_table_title = False
    for row in soup.find_all("tr"):
        if row.find_parent("thead") or row.find_parent("tfoot"):
            continue  # Skip header and footer rows
        # Apply .row-divider class to <td> with colspan outside thead and tfoot
        if not row.find_parent("thead") and not row.find_parent("tfoot"):
            for cell in row.find_all("td"):
                if cell.has_attr("colspan"):
                    existing_classes = cell.get("class", [])
                    if "row-divider" not in existing_classes:
                        cell["class"] = existing_classes + ["row-divider"]

        if not assigned_table_title and row.find("th", colspan=True):
            for cell in row.find_all("th"):
                if cell.has_attr("colspan"):
                    existing_classes = cell.get("class", [])
                    if "table-title" not in existing_classes:
                        cell["class"] = existing_classes + ["table-title"]
            assigned_table_title = True

        cells = row.find_all(["td", "th"])
        for idx, cell in enumerate(cells):
            cell["data-col"] = str(idx)

            if cell.name == "th" and not cell.has_attr("colspan"):
                clean_text = cell.get_text(strip=True)
                original_content = cell.decode_contents()
                cell.clear()

                parent_table = cell.find_parent("table")
                table_class = ""
                if parent_table and parent_table.has_attr("class"):
                    for cls in parent_table["class"]:
                        if cls in TABLES_WITH_TOGGLE:
                            table_class = cls
                            break

                menu = soup.new_tag("div", **{"class": "th-menu-wrapper"})
                label = soup.new_tag("span", **{"class": "col-title"})
                label["data-title"] = clean_text.lower()
                label.append(BeautifulSoup(original_content, "html.parser"))

                dropdown = soup.new_tag("div", **{"class": "th-dropdown"})
                action = soup.new_tag("a", href="#", onclick=f"toggleColumn({idx}); return false;")
                action["class"] = "col-toggle"
                action["role"] = "button"
                action["aria-label"] = "Toggle column visibility"
                action["title"] = "Toggle this column"
                action.string = "Toggle Hide"
                dropdown.append(action)


                menu.append(label)
                menu.append(dropdown)
                cell.append(menu)


# Navigation HTML utilities
def generate_nav_html(current_file: Path, table_files: list[Path]) -> str:
    """Generate navigation HTML with Home link and all other tables except the current one."""
    other_links = []
    for other in table_files:
        if other.name == current_file.name:
            continue
        label, slug = generate_label_and_slug(other.name)
        other_links.append(f'<a href="../pages/{slug}.html" class="nav-link">{label}</a>')
    centered_links = '<div style="text-align: center;">' + ' | '.join(other_links) + '</div>'
    return f"<nav style='margin: 10px 0;'>\n{centered_links}\n</nav>\n"


def remove_row_dividers(soup: BeautifulSoup):
    """
    Removes all <tr> elements with class 'row-divider' from the soup.
    """
    for tr in soup.find_all("tr", class_="row-divider"):
        tr.decompose()





