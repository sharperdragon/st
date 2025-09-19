from pathlib import Path
from utils.page_helpers.html_utils import generate_label_and_slug


BASE_HTML_PATH = Path("static/BASE.html")
TABLE_DIR = Path("subdex/")
NAV_DIR = Path("utils/navs/")
OUTPUT_DIR = Path("pages/")
MANIFEST_PATH = Path("static/data/table.manifest.json")

TABLE_SUFFIX = ".table.html"



def generate_drop_nav_html():
    """
    Generates a categorized dropdown-style nav with grouped sections and writes one per table
    into utils/navs/drop_navs/drop_nav_<slug>.html.
    """
    drop_nav_dir = Path("utils/navs/drop_navs")
    drop_nav_dir.mkdir(parents=True, exist_ok=True)

    table_files = sorted(TABLE_DIR.glob(f"*{TABLE_SUFFIX}"))

    def categorize(slug: str) -> str:
        if slug == "glossary":
            return "Glossary"
        elif any(x in slug for x in ["presentation", "finding", "associa"]):
            return "Rapid Review"
        elif any(x in slug for x in ["hla", "cytokine", "autoantibodies", "cd"]):
            return "Immune"
        elif any(x in slug for x in ["cardio", "respiratory", "embryo"]):
            return "System"
        elif any(x in slug for x in ["pharm"]):
            return "Reference"
        else:
            return "Misc"

    for table_file in table_files:
        filename = table_file.name
        label, slug = generate_label_and_slug(filename)

        # Build category → links map
        category_map = {}
        category = categorize(slug)
        category_map.setdefault(category, [])
        for other_file in table_files:
            other_label, other_slug = generate_label_and_slug(other_file.name)
            if other_slug == slug:
                continue  # ⛔ Skip linking to current page in its own nav
            other_category = categorize(other_slug)
            category_map.setdefault(other_category, []).append((other_label, other_slug))

        # Build HTML with just the dropdown contents (not the outer nav wrapper)
        nav_html = '    <div class="nav_dropdown_container" id="nav-dropdown">\n'

        for category, links in sorted(category_map.items()):
            category_id = f"category-{category.lower().replace(' ', '-')}"
            if category.lower() == "glossary":
                nav_html += f'      <!-- {category}: label (no direct link) -->\n'
                nav_html += f'      <div class="nav_category" id="{category_id}">\n'
                nav_html += f'        <a class="nav_category_link" href="../pages/glossary.html">{category}</a>\n'
                nav_html += f'      </div>\n'
            else:
                nav_html += f'      <!-- {category}: submenu -->\n'
                nav_html += f'      <div class="nav_category has-children" id="{category_id}">\n'
                nav_html += f'        <span>{category}</span>\n'
                nav_html += f'        <div class="nav_submenu">\n'
                for label, link_slug in sorted(links):
                    nav_html += f'          <a class="nav_link_tab" href="../pages/{link_slug}.html">{label}</a>\n'
                nav_html += f'        </div>\n'
                nav_html += f'      </div>\n'

        nav_html += '    </div>\n'

        output_path = drop_nav_dir / f"drop_nav_{slug}.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(nav_html.strip())


################################################################################################
################################################################################################
###### "BASE.html" contatins: ########
#<nav style="display:none" id="float-nav-container">
#    <div id="float-nav-button-container"><span>Navigate</span></div>
#    {{DROP_NAV_CONTENT}}
#</nav>



##################################################################

#### 'Update_Directory.py' contains:
# 
#
#        # Load corresponding drop nav HTML
#        drop_nav_path = Path(f"utils/navs/drop_navs/drop_nav_{slug}.html")
#        drop_nav_html = drop_nav_path.read_text() if drop_nav_path.exists() else ""
#
#
#
#
#
#        # Compose final HTML by replacing placeholders in base template
#        final_html = (
#            base_html
#           .replace("{{PAGE_TITLE}}", label)
#            # .replace("{{NAV_CONTENT}}", nav_html) 
#            .replace("{{TABLE_CONTENT}}", table_html)
#            .replace("{{DROP_NAV_CONTENT}}", drop_nav_html)
#        )
################################################################################
